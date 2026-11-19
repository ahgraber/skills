#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pydantic>=2.7",
# ]
# ///
"""Keep the state of a code review: the partition list and the review's records.

A deep code review searches for defects over a list of domain features
(partitions); a standard review does not use the list. The list belongs to the repository, not to a branch, so later
reviews inspect only what earlier reviews did not. Each review also keeps its
own records: every claim a finder wrote, each decision made about it, and
which records repeat one another.

Two files hold this state:

- The **state file** (``review-state.json``) holds the partition list and its
  inspections for the whole repository, and the finished reviews. It does not
  hold findings, because the next review's inspectors read it.
- The **review file** (``reviews/<review_id>/review.json``) holds one
  review's dispatches and records.

Commands (each prints JSON on stdout; diagnostics go to stderr):

- ``status``: resolve the review directory and the state file, and list the
  partitions waiting for inspection and this branch's previous review. With
  ``--review``, add that review's pending work and the one next step.
- ``start-review``: start a review from the packet script's JSON output.
- ``update-review``: change the values ``start-review`` took (the intent, how
  to run the code), which fill every role's prompt.
- ``dispatch [<role>]``: register one role's dispatch, or with no role every
  dispatch the next step names, up to a limit on open dispatches; write each
  one's input file and filled prompt, and print the prompt files.
- ``submit <dispatch_id>``: validate a role's output file against its schema
  and its assignment, and record it. Subagents run this on their own output.
  Submitting the synthesizer's report records the finished review in the state.
- ``start-round``: start the next round once every dispatch is done and every
  record has a verdict.
- ``rule <record_id>``: record the user's ruling on a disputed record.
- ``schema <role>``: print a role's output schema.

Every command that changes state is safe to repeat: run again with the same
arguments, it returns its first result, marked ``already_<done>: true``. A
repeated ``start-review`` or list builder ``dispatch`` that gives other values
is refused. Once the synthesizer is dispatched, only ``submit`` changes the
review.

Exit codes: 0 success, 1 error (the message names the cause), 2 bad usage.

The state lives in the main worktree's ``.review/`` when that directory exists,
so every linked worktree shares it; otherwise under ``$TMPDIR``, keyed by the
main worktree's path. Writers hold an operating-system lock on a lock file
beside each file, re-read it, merge, and replace it atomically; the operating
system releases the lock when a writer exits, so a crashed writer never blocks
the next one. A writer that needs both files locks the review file first.

What an inspection covered is the content on disk when its inspector was
dispatched, because inspectors read files from disk, and the status the
inspector reports for each input form. ``dispatch`` keeps that content's file
hashes (git blob ids) on the inspector's dispatch in the review file, and the
inspector's ``submit`` writes the finished inspection to the state file, so the
state file holds only finished inspections. A later review compares those
hashes with the content its own scope reviews (the index, ``HEAD``, or the
working tree), so an inspection counts after a commit, across branches, and
after a rebase, and any difference sends the partition back for inspection.
A branch review checks the commit it started on, so a later commit on the
branch does not change what the review checks.

A hunter searches for the other places that have a failure mode's fault. Its
``submit`` keeps on its dispatch the rule it states (``expected``), what its
list of places is built from (``searched``), and each place's status
(``sites``: ``handled``, ``claims``, or ``not checked``). A failure mode whose
hunter left sites not checked gets one more hunter in the round, for those
sites only. The consolidator and the synthesizer read what each failure
mode's hunters searched.

A hunter also lists in ``misgrouped`` the records it was given that break a
different rule than the one it states. The first time a record is listed,
``submit`` takes it out of its failure mode and keeps on the record the
failure mode it left, the reason, and the hunter's dispatch; the consolidator
then places it in another failure mode. A record listed a second time stays
where it is, so a record moves once in a review.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator
import contextlib
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import time
from typing import IO, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


# --- constants and errors ----------------------------------------------------------------


STATE_VERSION = 5
REVIEW_VERSION = 2
STATE_FILE = "review-state.json"
REVIEWS_DIR = "reviews"
REVIEW_FILE = "review.json"
LOCK_TIMEOUT_SECONDS = 10.0
SCOPES = ("staged", "branch", "worktree")
DEPTHS = ("standard", "deep")
NEW_ID_PREFIX = "new-"
MAX_IDS_IN_ERROR = 50
MAX_ROUNDS = 2
NONE_WORDS = frozenset({"", "none", "n/a", "null"})

Scope = Literal["staged", "branch", "worktree"]


class ReviewStateError(Exception):
    """A failure the caller can act on; the message names the cause."""


# --- shared: git, paths, files, and locks ------------------------------------------------


class _Stored(BaseModel):
    """Base for stored files: unknown keys mean the file is not ours or is corrupt."""

    model_config = ConfigDict(extra="forbid")


class _Draft(BaseModel):
    """Base for role output: an unknown key is a misnamed field, so it is an error."""

    model_config = ConfigDict(extra="forbid")


def git(repo: Path, *args: str, stdin: bytes | None = None) -> str:
    """Run a git subcommand in `repo` with literal pathspecs; return stdout or raise ReviewStateError."""
    # Args are git subcommands chosen by this script, not untrusted input.
    proc = subprocess.run(  # noqa: S603
        ["git", "--literal-pathspecs", "-C", str(repo), *args],
        capture_output=True,
        input=stdin,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ReviewStateError(f"git {args[0]} failed in {repo}: {detail}")
    return proc.stdout.decode("utf-8", errors="surrogateescape")


class Locations(BaseModel):
    """Where this repository's review files live."""

    worktree: Path
    main_worktree: Path
    review_dir: Path
    state_path: Path

    @property
    def review_dir_in_repo(self) -> bool:
        """Return True when the review directory is inside the main worktree."""
        return self.review_dir.is_relative_to(self.main_worktree)


def resolve_locations(repo: Path, review_dir: Path | None) -> Locations:
    """Resolve the worktree, the main worktree, and the review directory for `repo`."""
    try:
        worktree = Path(git(repo, "rev-parse", "--show-toplevel").strip()).resolve()
    except ReviewStateError as exc:
        raise ReviewStateError(f"{exc}; pass --repo <a directory inside the repository under review>") from exc
    common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()).resolve()
    main = common.parent if common.name == ".git" else worktree
    if review_dir is not None:
        chosen = review_dir.resolve()
    elif (main / ".review").is_dir():
        chosen = main / ".review"
    else:
        key = hashlib.sha256(str(main).encode()).hexdigest()[:8]
        chosen = Path(tempfile.gettempdir()).resolve() / "code-review" / f"{main.name}-{key}"
    return Locations(worktree=worktree, main_worktree=main, review_dir=chosen, state_path=chosen / STATE_FILE)


def normalize_path(worktree: Path, raw: str) -> str:
    """Return `raw` as a repository-relative POSIX path, or raise when it is outside the repository."""
    given = Path(raw)
    full = Path(os.path.normpath(given if given.is_absolute() else worktree / given))
    if full == worktree:
        raise ReviewStateError(f"path {raw!r} is the repository root; give the path of a file in it")
    for candidate in (full, Path(os.path.realpath(full.parent)) / full.name):
        with contextlib.suppress(ValueError):
            relative = candidate.relative_to(worktree)
            if relative.parts:
                return relative.as_posix()
    raise ReviewStateError(
        f"path is outside the repository {worktree}: {raw}; give paths relative to the repository root"
    )


def _parse_index_lines(output: str, wanted: set[str], oid_field: int) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in output.split("\0"):
        if "\t" in line:
            meta, path = line.split("\t", 1)
            if path in wanted:
                found[path] = meta.split()[oid_field]
    return found


def scope_hashes(worktree: Path, scope: Scope, paths: list[str], commit: str = "") -> dict[str, str]:
    """Return each path's content hash (git blob id) in the content `scope` reviews; an absent path maps to "".

    A branch review checks the commit it started on, given as `commit`; without one, the content is ``HEAD``.
    """
    commit = commit or "HEAD"
    blobs = dict.fromkeys(paths, "")
    if not paths:
        return blobs
    wanted = set(paths)
    if scope == "staged":
        blobs.update(_parse_index_lines(git(worktree, "ls-files", "-s", "-z", "--", *paths), wanted, 1))
    elif scope == "branch":
        try:
            git(worktree, "rev-parse", "--verify", "-q", f"{commit}^{{commit}}")
        except ReviewStateError:
            return blobs
        blobs.update(_parse_index_lines(git(worktree, "ls-tree", "-r", "-z", commit, "--", *paths), wanted, 2))
    else:
        blobs.update(disk_hashes(worktree, paths))
    return blobs


def disk_hashes(worktree: Path, paths: list[str]) -> dict[str, str]:
    """Return each path's content hash (git blob id) as git would store it from disk; a symlink is its link text."""
    blobs = dict.fromkeys(paths, "")
    regular: list[str] = []
    for path in paths:
        try:
            mode = os.lstat(worktree / path).st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            target = os.fsencode(os.readlink(worktree / path))
            blobs[path] = git(worktree, "hash-object", "--stdin", stdin=target).strip()
        elif stat.S_ISREG(mode):
            regular.append(path)
    if regular:
        ids = git(worktree, "hash-object", "--", *regular).split()
        blobs.update(zip(regular, ids, strict=True))
    return blobs


def head_and_branch(worktree: Path) -> tuple[str, str]:
    """Return the HEAD commit (empty in a repo without commits) and the branch (empty when detached)."""
    try:
        head = git(worktree, "rev-parse", "--verify", "-q", "HEAD").strip()
    except ReviewStateError:
        head = ""
    try:
        branch = git(worktree, "symbolic-ref", "--short", "-q", "HEAD").strip()
    except ReviewStateError:
        branch = ""
    return head, branch


def _brief(exc: Exception) -> str:
    """Return one line per validation error: where it is, then what is wrong."""
    if isinstance(exc, ValidationError):
        lines = []
        for e in exc.errors():
            where = ".".join(str(part) for part in e["loc"]) or "the whole file"
            lines.append(f"- {where}: {e['msg'].removeprefix('Value error, ')}")
        return "\n" + "\n".join(lines)
    return str(exc)


def _try_lock(handle: IO[str]) -> bool:
    try:
        if sys.platform == "win32":
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(handle: IO[str]) -> None:
    if sys.platform == "win32":
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def locked(path: Path) -> Iterator[None]:
    """Hold an operating-system lock on the lock file beside `path`.

    The lock file is never deleted: deleting it would let two writers lock two
    different files. The operating system releases the lock when the process
    exits, so a crashed writer leaves only an unlocked file behind.
    """
    lock = path.with_name(path.name + ".lock")
    with lock.open("a+") as handle:
        start = time.monotonic()
        attempt = 0
        while not _try_lock(handle):
            if time.monotonic() - start > LOCK_TIMEOUT_SECONDS:
                msg = f"{path.name} is locked by another writer: {lock}; retry when that write finishes"
                raise ReviewStateError(msg)
            time.sleep(min(0.02 * 2**attempt, 0.5) * (0.5 + random.random()))
            attempt += 1
        try:
            yield
        finally:
            _unlock(handle)


def write_json(path: Path, model: BaseModel) -> None:
    """Replace `path` atomically with `model`; remove the temporary file if the write fails."""
    with tempfile.NamedTemporaryFile("w", dir=path.parent, prefix=f".{path.stem}-", delete=False) as tmp:
        try:
            tmp.write(model.model_dump_json(indent=2) + "\n")
            tmp.flush()
            os.fsync(tmp.fileno())
        except BaseException:
            tmp.close()
            Path(tmp.name).unlink(missing_ok=True)
            raise
    try:
        Path(tmp.name).replace(path)
    except BaseException:
        Path(tmp.name).unlink(missing_ok=True)
        raise


def _union(existing: list[str], new: list[str]) -> list[str]:
    seen = set(existing)
    return existing + [item for item in new if not (item in seen or seen.add(item))]


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def _key(text: str) -> str:
    return " ".join(text.lower().split())


# --- partition state: models -------------------------------------------------------------


class Snapshot(_Stored):
    """The content hash of each of a partition's files on disk when its inspector was dispatched."""

    date: str
    head: str
    file_hashes: dict[str, str]


class InputFormStatus(_Draft):
    """What an inspector found for one of its input forms."""

    input_form: str
    status: Literal["handled", "claims", "not checked"]


class Inspection(Snapshot):
    """One inspector's pass over a partition: the content it was dispatched against, and each form's status."""

    scope: Scope
    input_forms: list[InputFormStatus]


class Partition(_Stored):
    """One feature of the domain, with the input forms the domain allows for it."""

    partition_id: str = Field(min_length=1)
    feature: str
    origin: str = ""
    input_forms: list[str] = Field(default_factory=list)
    paths: list[str] = Field(default_factory=list)
    inspections: list[Inspection] = Field(default_factory=list)
    child_ids: list[str] = Field(default_factory=list)


class FinishedReview(_Stored):
    """One finished review, recorded when its report is submitted."""

    review_id: str
    head: str
    branch: str
    date: str
    report: str
    scope: Scope
    blocking_record_ids: list[str] = Field(default_factory=list)


class State(_Stored):
    """The repository's review state."""

    version: Literal[5] = STATE_VERSION
    partitions: list[Partition] = Field(default_factory=list)
    reviews: list[FinishedReview] = Field(default_factory=list)


class PartitionInput(BaseModel):
    """A partition as the partition keeper returns it; extra keys are ignored."""

    model_config = ConfigDict(extra="ignore")

    partition_id: str = Field(min_length=1)
    feature: str = Field(min_length=1)
    origin: str = ""
    input_forms: list[str] = Field(default_factory=list)
    paths: list[str] = Field(default_factory=list)
    child_ids: list[str] = Field(default_factory=list)


class ListInput(BaseModel):
    """A partition list to merge into the state; only `partitions` is read."""

    model_config = ConfigDict(extra="ignore")

    partitions: list[PartitionInput]


# --- partition state: operations ---------------------------------------------------------


def read_state(path: Path) -> State | None:
    """Read the state file, or return None when it does not exist."""
    if not path.exists():
        return None
    try:
        return State.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError) as exc:
        msg = (
            f"state file {path} is invalid:{_brief(exc)}\n"
            "Only review_state.py writes it. Restore it from a backup, or move it aside to start a new partition list."
        )
        raise ReviewStateError(msg) from exc


@contextlib.contextmanager
def updating(locations: Locations) -> Iterator[State]:
    """Yield the current state under the lock; write it back when the block succeeds."""
    locations.review_dir.mkdir(parents=True, exist_ok=True)
    with locked(locations.state_path):
        state = read_state(locations.state_path) or State()
        yield state
        state.version = STATE_VERSION
        write_json(locations.state_path, state)


def _find(state: State, partition_id: str) -> Partition:
    part = next((p for p in state.partitions if p.partition_id == partition_id), None)
    if part is None:
        ids = [p.partition_id for p in state.partitions]
        shown = ", ".join(ids[:MAX_IDS_IN_ERROR]) + (" ..." if len(ids) > MAX_IDS_IN_ERROR else "")
        raise ReviewStateError(f"unknown partition {partition_id!r}; known ids: {shown or '(none)'}")
    return part


def _current_inspections(part: Partition, hashes: dict[str, str]) -> list[Inspection]:
    """Return the inspections that saw the content `hashes` describes in every one of the partition's files."""
    return [e for e in part.inspections if all(e.file_hashes.get(p) == hashes.get(p, "") for p in part.paths)]


def _checked_forms(part: Partition, hashes: dict[str, str]) -> set[str]:
    """Return the forms an inspection of the current content checked."""
    current = _current_inspections(part, hashes)
    return {f.input_form for entry in current for f in entry.input_forms if f.status != "not checked"}


def inspection_reasons(part: Partition, hashes: dict[str, str]) -> list[str]:
    """Return why `part` needs inspecting against the current file `hashes`; empty when it does not."""
    if not part.inspections:
        return ["never inspected"]
    if not part.paths:
        return ["no paths recorded"]
    if not _current_inspections(part, hashes):
        return ["files changed"]
    checked = _checked_forms(part, hashes)
    return ["unchecked input forms"] if any(form not in checked for form in part.input_forms) else []


def pending_input_forms(part: Partition, reasons: list[str], hashes: dict[str, str]) -> list[str]:
    """Return the input forms an inspector must check: all of them unless the only reason is unchecked forms."""
    if reasons != ["unchecked input forms"]:
        return list(part.input_forms)
    checked = _checked_forms(part, hashes)
    return [form for form in part.input_forms if form not in checked]


def _all_paths(state: State) -> list[str]:
    return sorted({p for part in state.partitions for p in part.paths})


def pending_inspection(state: State, hashes: dict[str, str]) -> list[dict[str, object]]:
    """List each partition that is not split and needs inspecting, with the reasons and the forms to check."""
    pending: list[dict[str, object]] = []
    for part in state.partitions:
        reasons = [] if part.child_ids else inspection_reasons(part, hashes)
        if reasons:
            pending.append(
                {
                    "partition_id": part.partition_id,
                    "feature": part.feature,
                    "reasons": reasons,
                    "pending_input_forms": pending_input_forms(part, reasons, hashes),
                }
            )
    return pending


def _state_pending(
    locations: Locations, state: State | None, scope: Scope, commit: str = ""
) -> list[dict[str, object]]:
    if state is None:
        return []
    return pending_inspection(state, scope_hashes(locations.worktree, scope, _all_paths(state), commit))


def _inherit_inspections(state: State) -> None:
    """Give each split piece that has never been inspected its parent's inspections."""
    by_id = {part.partition_id: part for part in state.partitions}
    for parent in state.partitions:
        for child_id in parent.child_ids:
            child = by_id.get(child_id)
            if child is not None and not child.inspections and child is not parent:
                child.inspections = [entry.model_copy(deep=True) for entry in parent.inspections]


def _previous_review(state: State, branch: str) -> dict[str, object] | None:
    """Return this branch's latest finished review with whether its report still exists; none when detached."""
    reviews = [r for r in state.reviews if branch and r.branch == branch]
    if not reviews:
        return None
    return {**reviews[-1].model_dump(), "report_exists": Path(reviews[-1].report).exists()}


def _assign_ids(state: State, incoming: ListInput) -> dict[str, str]:
    """Map each `new-<n>` id to an existing partition with the same feature, or to a fresh id."""
    known = {p.partition_id for p in state.partitions}
    by_feature = {_key(p.feature): p.partition_id for p in state.partitions}
    numbers = [int(pid[1:]) for pid in known if pid[:1] == "P" and pid[1:].isdigit()]
    next_number = max(numbers, default=0) + 1
    id_map: dict[str, str] = {}
    for item in incoming.partitions:
        if item.partition_id in known or item.partition_id in id_map:
            continue
        if not item.partition_id.startswith(NEW_ID_PREFIX):
            msg = (
                f"unknown partition id {item.partition_id!r}; use an id from the saved list,"
                f" or {NEW_ID_PREFIX}<n> for a new partition"
            )
            raise ReviewStateError(msg)
        existing = by_feature.get(_key(item.feature))
        if existing is None:
            existing = f"P{next_number}"
            next_number += 1
            by_feature[_key(item.feature)] = existing
        id_map[item.partition_id] = existing
    return id_map


def _merge_item(part: Partition, item: PartitionInput, paths: list[str], child_ids: list[str]) -> bool:
    """Merge `item` into `part`; return True when anything changed."""
    before = part.model_dump()
    part.feature = item.feature
    part.origin = item.origin or part.origin
    part.input_forms = _union(part.input_forms, item.input_forms)
    part.paths = _union(part.paths, paths)
    part.child_ids = _union(part.child_ids, child_ids)
    return part.model_dump() != before


def _resolve_item(
    item: PartitionInput, id_map: dict[str, str], known: set[str], worktree: Path
) -> tuple[str, list[str], list[str]]:
    """Return the item's real id, its repository-relative paths, and its pieces' real ids."""
    child_ids = [id_map.get(s, s) for s in item.child_ids]
    missing = [s for s in child_ids if s not in known]
    if missing:
        raise ReviewStateError(
            f"partition {item.partition_id!r} splits into unknown ids: {', '.join(missing)};"
            f" each piece must be a saved id or a {NEW_ID_PREFIX}<n> partition in the same list"
        )
    pid = id_map.get(item.partition_id, item.partition_id)
    return pid, [normalize_path(worktree, p) for p in item.paths], child_ids


def save_list(locations: Locations, incoming: ListInput) -> dict[str, object]:
    """Merge a partition list into the state; never drop a partition."""
    added: list[str] = []
    changed: set[str] = set()
    touched: list[str] = []
    with updating(locations) as state:
        id_map = _assign_ids(state, incoming)
        by_id = {part.partition_id: part for part in state.partitions}
        known_after = set(by_id) | set(id_map.values())
        for item in incoming.partitions:
            pid, paths, child_ids = _resolve_item(item, id_map, known_after, locations.worktree)
            part = by_id.get(pid)
            if part is None:
                part = Partition(partition_id=pid, feature=item.feature, origin=item.origin)
                state.partitions.append(part)
                by_id[pid] = part
                added.append(pid)
            elif pid not in touched:
                touched.append(pid)
            if _merge_item(part, item, paths, child_ids):
                changed.add(pid)
        _inherit_inspections(state)
    updated = [pid for pid in touched if pid in changed]
    unchanged = [pid for pid in touched if pid not in changed]
    return {"added": added, "updated": updated, "unchanged": unchanged, "id_map": id_map}


def check_disk_matches(locations: Locations, scope: Scope, paths: list[str], commit: str = "") -> None:
    """Refuse when a file on disk differs from the content `scope` reviews.

    Roles read and run the files on disk, so a review of content that differs
    from the disk would check other code than the scope names, and its
    inspections would never count. A branch review checks `commit`, the commit
    it started on, so a later commit on the branch does not change what it
    reviews.
    """
    if scope == "worktree" or not paths:
        return
    reviewed = scope_hashes(locations.worktree, scope, paths, commit)
    on_disk = disk_hashes(locations.worktree, paths)
    stale = [p for p in paths if reviewed[p] != on_disk[p]]
    if not stale:
        return
    if scope == "staged":
        content, fix = "the index", "git stash --keep-index"
    elif commit:
        content, fix = f"commit {commit[:7]}", f"git stash, or check out {commit[:7]} again"
    else:
        content, fix = "HEAD", "git stash, or commit them"
    elsewhere = (
        f"; when the changes are not yours to set aside, check out {commit[:7]} in a separate directory"
        " (git worktree add --detach <dir>) and pass --repo <dir> to each command"
        if scope == "branch" and commit
        else ""
    )
    raise ReviewStateError(
        f"these files on disk differ from {content}, which a {scope} review checks: {', '.join(stale)};"
        f" set the changes aside ({fix}), or review them as they stand with a worktree packet (--worktree){elsewhere}"
    )


def check_packet_current(locations: Locations, scope: Scope, content: dict[str, str], commit: str = "") -> None:
    """Refuse when a changed file's reviewed content differs from the content the packet was built from.

    The packet fixes what changed, so a file staged again after the packet was
    built would be reviewed from a diff that does not show it.
    """
    if not content:
        return
    now = scope_hashes(locations.worktree, scope, list(content), commit)
    if stale := [p for p in content if now[p] != content[p]]:
        raise ReviewStateError(
            f"these files changed after the packet was built: {', '.join(stale)}; rebuild the packet with"
            " build_review_packet.py and start a new review from it"
        )


def take_snapshot(locations: Locations, part: Partition) -> Snapshot:
    """Return the content hashes of a partition's files on disk, taken just before its inspector is dispatched.

    Inspectors read files from disk, and the files can change while one runs, so
    an inspection records this content rather than the content when it ends.
    """
    head, _ = head_and_branch(locations.worktree)
    return Snapshot(date=_now(), head=head, file_hashes=disk_hashes(locations.worktree, part.paths))


def record_inspection(
    locations: Locations, partition_id: str, snapshot: Snapshot, scope: Scope, statuses: list[InputFormStatus]
) -> bool:
    """Record an inspection of `snapshot` with each form's status; return True when it was added."""
    entry = Inspection(**snapshot.model_dump(), scope=scope, input_forms=statuses)
    with updating(locations) as state:
        part = _find(state, partition_id)
        latest = part.inspections[-1] if part.inspections else None
        duplicate = (
            latest is not None
            and latest.scope == entry.scope
            and latest.file_hashes == entry.file_hashes
            and {(f.input_form, f.status) for f in latest.input_forms}
            == {(f.input_form, f.status) for f in entry.input_forms}
        )
        if not duplicate:
            part.inspections.append(entry)
    return not duplicate


def record_finished_review(locations: Locations, finished: FinishedReview) -> bool:
    """Record a finished review in the state; return True when it was added."""
    with updating(locations) as state:
        duplicate = any((r.review_id, r.report) == (finished.review_id, finished.report) for r in state.reviews)
        if not duplicate:
            state.reviews.append(finished)
    return not duplicate


# --- review: roles -----------------------------------------------------------------------


Priority = Literal["critical", "high", "medium", "low"]
Role = Literal[
    "list-builder",
    "keeper",
    "inspector",
    "quality-lens",
    "security-lens",
    "spec-lens",
    "test-adversary",
    "forms-checker",
    "consolidator",
    "runner",
    "challenger",
    "hunter",
    "synthesizer",
]
ROLES: tuple[str, ...] = Role.__args__


# --- review: role output models (what a subagent writes) ---------------------------------


def _none_if_empty(value: object) -> object:
    if isinstance(value, str) and value.strip().lower() in NONE_WORDS:
        return None
    return value


class ProbeRun(_Draft):
    """One probe run."""

    command: str = Field(min_length=1)
    output: str
    probe_path: str = Field(min_length=1)
    reached_path: bool
    verdict: Literal["confirmed", "refuted", "test gap", "not runnable"]
    reason: str = ""

    @model_validator(mode="after")
    def _evidence(self) -> ProbeRun:
        if self.verdict == "not runnable":
            if not self.reason.strip():
                raise ValueError("a not runnable verdict needs a reason")
        elif not self.reached_path:
            raise ValueError(
                f"verdict {self.verdict!r} needs a probe that reached the path;"
                " a probe that did not reach it is not runnable, with the reason"
            )
        return self


class FailureMode(_Draft):
    """How the code fails: a name, and a description of the mechanism that holds at any site."""

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)


class Claim(_Draft):
    """A suspected defect, as the finder that found it wrote it."""

    site: str = Field(min_length=1, description="file:line")
    input_form: str = Field(min_length=1)
    input: str | None = None
    expected: str = Field(min_length=1)
    source: str | None = None
    predicted: str | None = None
    observation: str = Field(min_length=1)
    direction: str = ""
    priority: Priority
    reachable: Literal["yes", "no", "unknown"]
    introduced: Literal["this change", "pre-existing", "unknown"]
    failure_mode: FailureMode
    run: ProbeRun | None = None

    _none = field_validator("input", "source", "predicted", mode="before")(_none_if_empty)


class InspectorOutput(_Draft):
    """An inspector's output."""

    read_through: int
    files_read: list[str] = Field(default_factory=list)
    input_forms: list[InputFormStatus]
    claims: list[Claim] = Field(default_factory=list)
    result: Literal["handled", "claims", "too coarse"]
    proposed_split: str = ""

    @model_validator(mode="after")
    def _consistent(self) -> InspectorOutput:
        unchecked = [f.input_form for f in self.input_forms if f.status == "not checked"]
        if self.result == "too coarse" and not self.proposed_split.strip():
            raise ValueError("result 'too coarse' needs a proposed split in proposed_split")
        if unchecked and self.result != "too coarse":
            raise ValueError(
                f"input forms not checked ({'; '.join(unchecked)}) need result 'too coarse' with a proposed_split"
            )
        if self.result == "handled" and self.claims:
            raise ValueError("result 'handled' cannot carry claims; use 'claims'")
        if self.result == "claims" and not self.claims:
            raise ValueError("result 'claims' needs at least one claim")
        return self


class Proposal(_Draft):
    """One partition a list builder proposes."""

    feature: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    input_forms: list[str] = Field(default_factory=list)
    paths: list[str] = Field(default_factory=list)


class ListBuilderOutput(_Draft):
    """A list builder's output."""

    read_through: int
    proposals: list[Proposal]


class KeeperOutput(_Draft):
    """The partition keeper's output."""

    partitions: list[PartitionInput]
    changes: list[str] = Field(default_factory=list)


class LensOutput(_Draft):
    """A lens's output."""

    read_through: int
    claims: list[Claim] = Field(default_factory=list)
    summary: str = ""


class TestAdversaryOutput(_Draft):
    """The test adversary's output; every claim carries its run."""

    read_through: int
    test_paths: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    already_tested: int = 0


class InputFormRef(_Draft):
    """One input form of one partition."""

    partition_id: str
    input_form: str


class InputFormTests(InputFormRef):
    """The tests that exercise one assigned input form, and the claims from probing it."""

    tests: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)

    @model_validator(mode="after")
    def _claims_test_this_form(self) -> InputFormTests:
        other = [c.input_form for c in self.claims if c.input_form != self.input_form]
        if other:
            raise ValueError(
                f"{self.partition_id}: {self.input_form}: a claim under this form tests {other[0]!r};"
                " put each claim under the form it tests"
            )
        return self


class FormsCheckerOutput(_Draft):
    """The forms checker's output."""

    read_through: int
    test_paths: list[str] = Field(default_factory=list)
    input_forms: list[InputFormTests]


class DuplicateDraft(_Draft):
    """A record the consolidator marks as the same defect as its primary."""

    record_id: str
    primary_id: str


class FailureModeGroup(FailureMode):
    """One failure mode from the consolidator, with the records that belong to it."""

    record_ids: list[str]


class ConsolidatorOutput(_Draft):
    """The consolidator's output."""

    duplicates: list[DuplicateDraft] = Field(default_factory=list)
    failure_modes: list[FailureModeGroup] = Field(default_factory=list)


class RunnerResult(ProbeRun):
    """One runner result for one assigned record; a runner does not judge test gaps."""

    record_id: str
    verdict: Literal["confirmed", "refuted", "not runnable"]


class RunnerOutput(_Draft):
    """The runner's output."""

    results: list[RunnerResult]


class RevisedPriority(_Draft):
    """A priority the challenger sets in place of the finder's, with its reason."""

    priority: Priority
    reason: str = Field(min_length=1)


class ChallengerResult(_Draft):
    """The challenger's verdict on one assigned record."""

    record_id: str
    verdict: Literal["upheld", "disputed", "refuted"]
    strength: Literal["strong", "moderate", "weak"]
    argument: str = Field(min_length=1)
    revised_priority: RevisedPriority | None = None

    _none = field_validator("revised_priority", mode="before")(_none_if_empty)


class ChallengerOutput(_Draft):
    """The challenger's output."""

    read_through: int
    results: list[ChallengerResult]
    review_critique: str = ""


class Expectation(_Draft):
    """Whether a record's cited source supports its expected result."""

    record_id: str
    expected_supported: bool
    reason: str = Field(min_length=1)


class HuntSite(_Draft):
    """One place a hunter's search produced, and whether its code keeps the hunter's rule."""

    site: str = Field(min_length=1, description="file:line")
    status: Literal["handled", "claims", "not checked"]
    reason: str = Field(
        min_length=1,
        description="handled: the line that keeps the rule; claims: how the site breaks it; not checked: why",
    )


class MisgroupedDraft(_Draft):
    """A given record a hunter found to break a different rule than the one it states."""

    record_id: str
    reason: str = Field(min_length=1)


class HunterOutput(_Draft):
    """A hunter's output: the rule every place must keep, what produces the places, and each place's status."""

    read_through: int
    expectations: list[Expectation]
    misgrouped: list[MisgroupedDraft] = Field(
        default_factory=list,
        description="The given records that break a different rule than expected, each with the reason",
    )
    expected: str = Field(
        default="",
        description="The records' expected result as one rule for a set of places, in one sentence"
        " that does not name a file, function, or variable",
    )
    searched: list[str] = Field(
        default_factory=list,
        description="What produces every place the rule applies to: each entry a table, a set of definitions,"
        " or a search, and where it is",
    )
    sites: list[HuntSite] = Field(
        default_factory=list,
        description="Every place that searched produces, among them the site of each given record"
        " that is not in misgrouped",
    )
    suspected_input_forms: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)


# --- review: stored models and the review file -------------------------------------------


class Check(_Stored):
    """One project check from before the review started: whether it ran, and whether it passed."""

    command: str = Field(min_length=1)
    passed: bool
    ran: bool = True


class StoredRun(ProbeRun):
    """The runner's run of a record's probe."""

    dispatch_id: str


class Challenge(_Stored):
    """The challenger's verdict on a record."""

    dispatch_id: str
    verdict: Literal["upheld", "disputed", "refuted"]
    strength: Literal["strong", "moderate", "weak"]
    argument: str
    revised_priority: RevisedPriority | None = None


class Grouping(_Stored):
    """The consolidator's decision: a failure mode, or the primary this record duplicates."""

    failure_mode: str | None = None
    primary_id: str | None = None
    dispatch_id: str


class Split(_Stored):
    """The script's undoing of a duplicate link, when this record's run and its primary's disagree."""

    primary_id: str
    failure_mode: str | None
    dispatch_id: str


class Hunt(_Stored):
    """The hunter's check of whether the cited source supports the record's expected result."""

    expected_supported: bool
    reason: str
    dispatch_id: str


class Misgrouped(_Stored):
    """A hunter's finding that the record breaks a different rule than the failure mode it was hunted in.

    The first one takes the record out of that failure mode, so the
    consolidator places it again. A later one leaves it where it is.
    """

    failure_mode: str
    reason: str
    dispatch_id: str


class Ruling(_Stored):
    """The user's ruling on a disputed record."""

    verdict: Literal["upheld", "refuted"]
    reason: str


class CarriedFrom(_Stored):
    """The earlier review's blocking finding a record repeats, and whether the files it depends on are unchanged."""

    review_id: str
    record_id: str
    files_unchanged: bool


class Record(_Stored):
    """One claim, kept as its finder wrote it, with each decision made about it."""

    record_id: str
    round: int
    dispatch_id: str
    claim: Claim
    grouping: Grouping | None = None
    split: Split | None = None
    run: StoredRun | None = None
    challenge: Challenge | None = None
    hunt: Hunt | None = None
    misgrouped: list[Misgrouped] = Field(default_factory=list)
    ruling: Ruling | None = None
    carried_from: CarriedFrom | None = None
    keeper_dispatch_id: str = ""


class CheckedInputForm(InputFormRef):
    """One input form the forms checker checked, with the tests that exercise it (none when it wrote a probe)."""

    tests: list[str] = Field(default_factory=list)
    dispatch_id: str


class Dispatch(_Stored):
    """One role's dispatch: what it was given and what it returned."""

    dispatch_id: str
    role: Role
    round: int
    date: str
    status: Literal["open", "done"] = "open"
    input_path: str
    output_path: str
    packet_ranges: list[tuple[int, int]] = Field(default_factory=list)
    assigned_record_ids: list[str] = Field(default_factory=list)
    assigned_input_forms: list[InputFormRef] = Field(default_factory=list)
    partition_id: str = ""
    component: str = ""
    paths: list[str] = Field(default_factory=list)
    failure_mode: str = ""
    snapshot: Snapshot | None = None
    reasons: list[str] = Field(default_factory=list)
    keeper_dispatch_id: str = ""
    result: str = ""
    proposed_split: str = ""
    input_forms: list[InputFormStatus] = Field(default_factory=list)
    proposals: list[Proposal] = Field(default_factory=list)
    expected: str = ""
    searched: list[str] = Field(default_factory=list)
    sites: list[HuntSite] = Field(default_factory=list)
    suspected_input_forms: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)
    summary: str = ""
    review_critique: str = ""
    submit_result: dict[str, Any] = Field(default_factory=dict)


class Packet(_Stored):
    """The review's copy of the packet and its line index."""

    path: str
    sections: dict[str, tuple[int, int]]
    files: dict[str, tuple[int, int]]
    has_source_of_truth: bool = False
    json_hash: str = ""
    content: dict[str, str] = Field(default_factory=dict)  # each changed file's blob id when the packet was built


class ReviewUpdate(_Stored):
    """One ``update-review``: when it ran and the values it set."""

    date: str
    values: dict[str, str | bool]


class Review(_Stored):
    """One review's dispatches and records.

    ``depth`` selects the procedure: only a deep review has the partition
    list, runners, and hunters.
    """

    version: Literal[2] = REVIEW_VERSION
    review_id: str
    scope: Scope
    date: str
    head: str
    branch: str
    base: str = ""
    root: str
    packet: Packet
    depth: Literal["standard", "deep"] = "standard"
    models: str = ""
    round: int = 1
    plan_frozen: bool = False
    dispatches: list[Dispatch] = Field(default_factory=list)
    records: list[Record] = Field(default_factory=list)
    failure_modes: list[FailureMode] = Field(default_factory=list)
    checks: list[Check] = Field(default_factory=list)
    checks_reason: str = ""
    checked_input_forms: list[CheckedInputForm] = Field(default_factory=list)
    blocking_file_hashes: dict[str, dict[str, str]] = Field(default_factory=dict)
    missing_previous_review: str = ""
    intent: str = ""
    how_to_run: str = ""
    feature_type: str = "other"
    spec: str = ""
    flagged_claims: str = "none"
    domain_checks: str = ""
    architecture: bool = False
    one_context: bool = False
    updates: list[ReviewUpdate] = Field(default_factory=list)


class PacketIndex(BaseModel):
    """The packet's line index."""

    sections: dict[str, tuple[int, int]]
    files: dict[str, tuple[int, int]]


class PacketInfo(BaseModel):
    """The JSON that ``build_review_packet.py`` prints; extra keys are ignored."""

    model_config = ConfigDict(extra="ignore")

    packet_path: str
    index: PacketIndex
    scope: str
    base: str = ""
    head: str = ""
    branch: str = ""
    diff_truncated: bool
    has_source_of_truth: bool = False
    content: dict[str, str] = Field(default_factory=dict)


def _work_dir(locations: Locations, review_id: str) -> Path:
    return locations.review_dir / REVIEWS_DIR / review_id


def _no_review(work: Path) -> str:
    return (
        f"no review {work.name} in {work.parent}; pass the review_id start-review printed,"
        " and run inside the reviewed repository or pass --repo <a directory inside it>"
    )


def read_review(work: Path) -> Review:
    """Read a review file."""
    path = work / REVIEW_FILE
    if not path.exists():
        raise ReviewStateError(_no_review(work))
    try:
        return Review.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError) as exc:
        msg = (
            f"review file {path} is invalid:{_brief(exc)}\n"
            "Only review_state.py writes it. Move its directory aside and run start-review to start the review again."
        )
        raise ReviewStateError(msg) from exc


@contextlib.contextmanager
def updating_review(work: Path) -> Iterator[Review]:
    """Yield the review under its lock; write it back when the block succeeds."""
    path = work / REVIEW_FILE
    if not path.exists():
        raise ReviewStateError(_no_review(work))
    with locked(path):
        review = read_review(work)
        yield review
        write_json(path, review)


# --- review: verdicts and routing --------------------------------------------------------


def _run_of(rec: Record) -> ProbeRun | None:
    return rec.run or rec.claim.run


def _wrong(run: ProbeRun | None) -> bool | None:
    """Return whether a run showed the code wrong, or None when the run did not settle anything."""
    if run is None or run.verdict == "not runnable":
        return None
    return run.verdict == "confirmed"


def is_duplicate(rec: Record) -> bool:
    """Return whether the consolidator marked `rec` a duplicate and no run split it back out."""
    return rec.grouping is not None and rec.grouping.primary_id is not None and rec.split is None


def failure_mode_of(rec: Record) -> str | None:
    """Return the failure mode the review gave `rec`: the split's copy, else the consolidator's."""
    if rec.split is not None:
        return rec.split.failure_mode
    return None if rec.grouping is None else rec.grouping.failure_mode


def verdict(review: Review, rec: Record) -> str | None:
    """Return the record's verdict, or None while it still needs a run or a challenge.

    In a deep review a duplicate with an input waits for its run, which tests
    the grouping. A standard review does not dispatch a runner, so its
    duplicates do not wait.
    """
    run = _run_of(rec)
    if is_duplicate(rec):
        runs = review.depth == "deep" and rec.claim.input is not None and rec.challenge is None
        return "duplicate" if not runs or run is not None else None
    if rec.hunt is not None and not rec.hunt.expected_supported:
        return "unsupported"
    if rec.ruling is not None:
        return rec.ruling.verdict
    if rec.challenge is not None:
        return rec.challenge.verdict
    if run is None or run.verdict == "not runnable":
        return None
    if run.verdict == "confirmed" and rec.claim.source is None:
        return None
    return run.verdict


def _assigned_open(review: Review, role: str) -> set[str]:
    return {i for d in review.dispatches if d.role == role and d.status == "open" for i in d.assigned_record_ids}


def to_consolidate(review: Review) -> list[str]:
    """Return the ids of the records with no grouping that no open consolidator was given."""
    given = _assigned_open(review, "consolidator")
    return [r.record_id for r in review.records if r.grouping is None and r.record_id not in given]


def to_run(review: Review) -> list[str]:
    """Return the grouped ids with an input and no run, including duplicates, which run to test the grouping.

    A standard review does not dispatch a runner: its challenger judges those records.
    A record a challenger already judged is not run.
    """
    if review.depth == "standard":
        return []
    given = _assigned_open(review, "runner")
    return [
        r.record_id
        for r in review.records
        if r.grouping is not None
        and r.claim.input is not None
        and _run_of(r) is None
        and r.challenge is None
        and r.record_id not in given
    ]


def to_challenge(review: Review) -> list[str]:
    """Return the ids a run cannot settle: no input, not runnable, or confirmed against no source.

    In a standard review, that is also every record with an input and no run.
    """
    given = _assigned_open(review, "challenger")
    no_runner = review.depth == "standard"
    out = []
    for r in review.records:
        if r.grouping is None or is_duplicate(r) or r.challenge is not None or verdict(review, r) == "unsupported":
            continue
        if r.record_id in given:
            continue
        run = _run_of(r)
        if ((no_runner or r.claim.input is None) and run is None) or (
            run is not None
            and (run.verdict == "not runnable" or (run.verdict == "confirmed" and r.claim.source is None))
        ):
            out.append(r.record_id)
    return out


def _unhunted(review: Review) -> dict[str, list[Record]]:
    """Return, by failure mode, the confirmed or upheld records that still start a hunt.

    Those are the records no hunter of their failure mode was given and the
    keeper has not taken. A record a hunter listed in misgrouped was given to
    the hunter of the failure mode it left, not of the one it is in now. A
    record a hunter filed does not start one: its hunter already searched the change
    for that kind of defect and sent its suspected input forms to the keeper.
    """
    given = {(d.failure_mode, i) for d in review.dispatches if d.role == "hunter" for i in d.assigned_record_ids}
    hunters = {d.dispatch_id for d in review.dispatches if d.role == "hunter"}
    found: dict[str, list[Record]] = {}
    for r in review.records:
        mode = failure_mode_of(r)
        hunted = (mode, r.record_id) in given
        if is_duplicate(r) or hunted or not mode or (r.carried_from and r.carried_from.files_unchanged):
            continue
        if r.dispatch_id in hunters or r.keeper_dispatch_id:
            continue
        if verdict(review, r) in ("confirmed", "upheld"):
            found.setdefault(mode, []).append(r)
    return found


def _hunted_this_round(review: Review) -> set[str]:
    return {d.failure_mode for d in review.dispatches if d.role == "hunter" and d.round == review.round}


def _unchecked_hunts(review: Review) -> dict[str, Dispatch]:
    """Return, by failure mode, this round's only hunter when it is done and left sites not checked.

    Such a failure mode waits for one more hunter, which decides those sites.
    The second hunter's unchecked sites do not start a third, so that hunting ends.
    """
    hunts: dict[str, list[Dispatch]] = {}
    for d in review.dispatches:
        if d.role == "hunter" and d.round == review.round:
            hunts.setdefault(d.failure_mode, []).append(d)
    return {
        m: ds[0]
        for m, ds in hunts.items()
        if len(ds) == 1 and ds[0].status == "done" and any(s.status == "not checked" for s in ds[0].sites)
    }


def to_hunt(review: Review) -> dict[str, list[str]]:
    """Return each failure mode that waits for a hunter, with the records the hunter is given.

    A failure mode no hunter has searched this round comes with its unhunted
    confirmed or upheld records. A failure mode whose hunter left sites not
    checked comes without a record (`_unchecked_hunts`). A failure mode does not get
    another hunter in a round, so that hunting ends: a record confirmed in a mode
    after its hunt, or moved into it, goes to the keeper instead
    (`_records_for_keeper`), and inspectors check its input form.
    """
    if review.depth == "standard":
        return {}
    hunted = _hunted_this_round(review)
    fresh = {m: [r.record_id for r in rs] for m, rs in _unhunted(review).items() if m not in hunted}
    return fresh | {m: [] for m in _unchecked_hunts(review)}


def _records_for_keeper(review: Review) -> list[Record]:
    """Return the records confirmed in or moved into a failure mode after this round's hunter searched it."""
    hunted = _hunted_this_round(review)
    return [r for m, rs in _unhunted(review).items() if m in hunted for r in rs]


def _for_keeper(review: Review) -> list[Dispatch]:
    """Return the finished dispatches whose output the keeper has not taken, in dispatch order.

    Those are list builders' proposals, hunters with suspected input forms, and
    inspectors that reported their partition too coarse.
    """
    return [
        d
        for d in review.dispatches
        if d.status == "done"
        and not d.keeper_dispatch_id
        and (
            d.role == "list-builder"
            or (d.role == "hunter" and d.suspected_input_forms)
            or (d.role == "inspector" and d.result == "too coarse")
        )
    ]


def _coarse_pending(review: Review) -> set[str]:
    return {d.partition_id for d in _for_keeper(review) if d.role == "inspector"}


def _owed_partitions(review: Review, state: State | None) -> set[str]:
    """Return the partitions this round's inspectors reported too coarse, and all their pieces."""
    owed = {
        d.partition_id
        for d in review.dispatches
        if d.role == "inspector" and d.round == review.round and d.result == "too coarse"
    }
    children = {} if state is None else {p.partition_id: p.child_ids for p in state.partitions}
    frontier = set(owed)
    while frontier:
        frontier = {c for pid in frontier for c in children.get(pid, [])} - owed
        owed |= frontier
    return owed


def _refined_this_round(review: Review) -> bool:
    """Return whether the keeper has refined the list since this round's first inspector."""
    in_round = [(i, d) for i, d in enumerate(review.dispatches) if d.round == review.round]
    first = next((i for i, d in in_round if d.role == "inspector"), None)
    return first is not None and any(d.role == "keeper" and i > first for i, d in in_round)


def _inspection(locations: Locations, review: Review, state: State | None) -> tuple[bool, list[dict[str, object]]]:
    """Return whether the plan is frozen, and the partitions this review inspects next.

    A partition reported too coarse waits for the keeper to split it. A round
    inspects every partition waiting at its start, in as many batches as it
    takes, until the keeper refines the list. The plan freezes when a round
    whose inspection is finished has converged or is the last round; for a
    converged round the keeper's submit records the freeze, so later claims
    cannot undo it. Once the plan is frozen, the review inspects only the pieces of the partitions its last
    round reported too coarse; later reviews inspect the rest.
    """
    if review.depth == "standard":
        return True, []
    skip = _coarse_pending(review)
    pending = [n for n in _state_pending(locations, state, review.scope, review.head) if n["partition_id"] not in skip]
    inspecting = bool(pending) and not _refined_this_round(review)
    last = review.round >= MAX_ROUNDS
    frozen = review.plan_frozen or (not inspecting and (last or bool(convergence(review, review.round)["converged"])))
    if frozen:
        owed = _owed_partitions(review, state)
        pending = [n for n in pending if n["partition_id"] in owed]
    return frozen, pending


def _ref_key(ref: InputFormRef) -> tuple[str, str]:
    return ref.partition_id, ref.input_form


def _touched_forms(review: Review, state: State | None) -> list[InputFormRef]:
    if state is None:
        return []
    changed = set(review.packet.files)
    return [
        InputFormRef(partition_id=p.partition_id, input_form=form)
        for p in state.partitions
        if not p.child_ids and changed.intersection(p.paths)
        for form in p.input_forms
    ]


def _forms_pending(review: Review, state: State | None) -> list[InputFormRef]:
    """Return the input forms of the touched partitions that no forms checker has checked."""
    checked = {_ref_key(c) for c in review.checked_input_forms}
    return [f for f in _touched_forms(review, state) if _ref_key(f) not in checked]


def _apply_splits(review: Review, dispatch_id: str) -> list[str]:
    """Return a duplicate to a record of its own when its run disagrees with its primary's run."""
    by_id = {r.record_id: r for r in review.records}
    split = []
    for r in review.records:
        if not is_duplicate(r):
            continue
        primary = by_id[r.grouping.primary_id]
        mine, theirs = _wrong(_run_of(r)), _wrong(_run_of(primary))
        if mine is not None and theirs is not None and mine != theirs:
            r.split = Split(
                primary_id=r.grouping.primary_id, failure_mode=failure_mode_of(primary), dispatch_id=dispatch_id
            )
            split.append(r.record_id)
    return split


def _role_of(review: Review, rec: Record) -> str:
    return next((d.role for d in review.dispatches if d.dispatch_id == rec.dispatch_id), "previous review")


def convergence(review: Review, round_number: int) -> dict[str, object]:
    """Count this round's inspector claims that repeat a claim grouped in an earlier batch.

    A duplicate repeats an earlier batch's claim when its primary was not in
    the batch of the consolidator that marked it.
    """
    batches = {d.dispatch_id: d.assigned_record_ids for d in review.dispatches if d.role == "consolidator"}
    mine = [r for r in review.records if r.round == round_number and _role_of(review, r) == "inspector"]
    grouped = [r for r in mine if r.grouping is not None]
    repeats = [
        r for r in grouped if is_duplicate(r) and r.grouping.primary_id not in batches.get(r.grouping.dispatch_id, [])
    ]
    complete = bool(mine) and len(grouped) == len(mine)
    ratio = len(repeats) / len(grouped) if grouped else 0.0
    return {
        "round": round_number,
        "inspector_claims": len(mine),
        "grouped": len(grouped),
        "repeats": len(repeats),
        "ratio": round(ratio, 3),
        "converged": complete and round_number >= 2 and ratio >= 0.5,
    }


# --- review: starting a review -----------------------------------------------------------


def cmd_start_review(locations: Locations, args: argparse.Namespace) -> dict[str, object]:
    """Start a review from the packet script's JSON; refuse a truncated or mismatched packet."""
    try:
        raw = Path(args.packet_json).read_bytes()
        info = PacketInfo.model_validate_json(raw)
    except (OSError, ValidationError) as exc:
        raise ReviewStateError(
            f"packet JSON {args.packet_json} is invalid:{_brief(exc)}\n"
            "Pass the file that build_review_packet.py's standard output was written to."
        ) from exc
    if info.diff_truncated:
        raise ReviewStateError(
            "the packet's diff is truncated, so inspectors would miss changed lines;"
            " rebuild the packet with a larger --max-diff-bytes"
        )
    if info.scope != args.scope:
        raise ReviewStateError(
            f"the packet's scope is {info.scope!r}, not {args.scope!r}; pass --scope {info.scope},"
            " or rebuild the packet with the flag for the scope you mean (--staged, --worktree, or --base)"
        )
    if not info.index.files:
        raise ReviewStateError(
            "the packet has no changed files: there is nothing to review in this scope; check the scope"
        )
    check_disk_matches(locations, args.scope, list(info.index.files), info.head)
    check_packet_current(locations, args.scope, info.content, info.head)
    if args.failed_checks and not args.reason.strip():
        raise ReviewStateError(
            "a review despite failing checks needs the user's decision: ask the user, then pass their reason"
            " with --reason; otherwise fix the failures and run the checks again first"
        )
    if args.skipped_checks and not args.reason.strip():
        raise ReviewStateError(
            "a review with a check that did not run needs the user's decision: ask the user, then pass their"
            " reason with --reason; otherwise run the check first"
        )
    values = _given_values(args)
    checks = [Check(command=c, passed=True) for c in args.passed_checks]
    checks += [Check(command=c, passed=False) for c in args.failed_checks]
    checks += [Check(command=c, passed=False, ran=False) for c in args.skipped_checks]
    json_hash = hashlib.sha256(raw).hexdigest()
    started = _review_from_packet(locations, json_hash, args.scope)
    if started is not None:
        _check_same_values(started, values)
        return {"review_id": started.name, "path": str(started), "already_started": True}
    head, branch = head_and_branch(locations.worktree)
    review_id, work = _create_work_dir(locations, info.head or head)
    for sub_dir in ("in", "out", "prompts"):
        (work / sub_dir).mkdir()
    packet = _copy_packet(info, Path(args.packet_json), work)
    review = Review(
        review_id=review_id,
        scope=args.scope,
        date=_now(),
        head=info.head or head,
        branch=info.branch or branch,
        base=info.base,
        root=str(locations.worktree),
        packet=Packet(
            path=str(packet),
            sections=info.index.sections,
            files=info.index.files,
            has_source_of_truth=info.has_source_of_truth,
            json_hash=json_hash,
            content=info.content,
        ),
        checks=checks,
        checks_reason=args.reason.strip() if args.failed_checks or args.skipped_checks else "",
        **values,
    )
    _carry_blockers(locations, review)
    write_json(work / REVIEW_FILE, review)
    return {"review_id": review_id, "path": str(work), "already_started": False}


def _check_same_values(started: Path, values: dict[str, str | bool]) -> None:
    """Refuse a repeated start-review that gives a value the started review does not hold."""
    stored = read_review(started)
    differing = [name for name, value in values.items() if getattr(stored, name) != value]
    if differing:
        flags = ", ".join(f"--{VALUE_FLAG_OF.get(n, n).replace('_', '-')}" for n in differing)
        raise ReviewStateError(
            f"review {started.name} is already started from this packet with other values for {flags};"
            f" to change them, run update-review --review {started.name} with those flags"
        )


def _carry_blockers(locations: Locations, review: Review) -> None:
    """Add this branch's previous blocking findings to a new review.

    A finding whose files still hold the content its review saw keeps its
    verdict. A finding whose files changed starts over as a candidate, so the
    judges run it again on the current code.
    """
    state = read_state(locations.state_path)
    reviews = [] if state is None else [r for r in state.reviews if review.branch and r.branch == review.branch]
    if not reviews or not reviews[-1].blocking_record_ids:
        return
    previous = reviews[-1]
    try:
        old = read_review(_work_dir(locations, previous.review_id))
    except ReviewStateError:
        review.missing_previous_review = previous.review_id
        return
    by_id = {r.record_id: r for r in old.records}
    modes = {m.name: m for m in old.failure_modes}
    for rid in previous.blocking_record_ids:
        rec, hashes = by_id.get(rid), old.blocking_file_hashes.get(rid)
        if rec is None or hashes is None:
            review.missing_previous_review = previous.review_id
            continue
        unchanged = scope_hashes(locations.worktree, review.scope, list(hashes), review.head) == hashes
        carried = Record(
            record_id=f"R1-{len(review.records) + 1}",
            round=1,
            dispatch_id="",
            claim=rec.claim if unchanged else rec.claim.model_copy(update={"run": None}),
            carried_from=CarriedFrom(review_id=previous.review_id, record_id=rid, files_unchanged=unchanged),
        )
        if unchanged:
            mode = failure_mode_of(rec)
            carried.grouping = Grouping(failure_mode=mode, dispatch_id="")
            carried.run, carried.challenge, carried.ruling, carried.hunt = rec.run, rec.challenge, rec.ruling, rec.hunt
            if mode and mode in modes and all(m.name != mode for m in review.failure_modes):
                review.failure_modes.append(modes[mode])
        review.records.append(carried)


def _blocking_files(locations: Locations, review: Review, rec: Record) -> list[str]:
    """Return the files a blocking finding depends on: the file its claim cites, and its partition's files."""
    if rec.carried_from is not None:
        old = _work_dir(locations, rec.carried_from.review_id)
        try:
            return list(read_review(old).blocking_file_hashes.get(rec.carried_from.record_id, {}))
        except ReviewStateError:
            pass
    files = [p for p in [_site_path(locations, rec.claim.site)] if p]
    partition = next((d.partition_id for d in review.dispatches if d.dispatch_id == rec.dispatch_id), "")
    state = read_state(locations.state_path)
    if partition and state is not None:
        files += next((p.paths for p in state.partitions if p.partition_id == partition), [])
    return sorted(set(files))


def _review_from_packet(locations: Locations, json_hash: str, scope: str) -> Path | None:
    """Return the directory of the review already started from this packet JSON in this scope, if any."""
    parent = locations.review_dir / REVIEWS_DIR
    if not parent.is_dir():
        return None
    for work in sorted(parent.iterdir()):
        try:
            review = read_review(work)
        except ReviewStateError:
            continue
        if review.packet.json_hash == json_hash and review.scope == scope:
            return work
    return None


def _create_work_dir(locations: Locations, head: str) -> tuple[str, Path]:
    """Create the review's directory, named `<UTC date>-<UTC time>-<short head>`, and return its id and path.

    The name says which commit the review started from. Linked worktrees share
    one reviews directory, so two reviews can start from one commit in the same
    second; the directory is created exclusively, and a taken name gets `-2`,
    `-3`, and so on.
    """
    parent = locations.review_dir / REVIEWS_DIR
    parent.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now(_dt.UTC).strftime("%Y%m%d-%H%M%S")
    base = f"{stamp}-{head[:7] or 'nohead'}"
    for n in range(1, 100):
        review_id = base if n == 1 else f"{base}-{n}"
        try:
            (parent / review_id).mkdir()
        except FileExistsError:
            continue
        return review_id, parent / review_id
    raise ReviewStateError(f"cannot create a review directory for {base} in {parent}: every suffix up to -99 is taken")


def _copy_packet(info: PacketInfo, packet_json: Path, work: Path) -> Path:
    """Copy the packet and its JSON into the review's directory, so the review holds its own inputs."""
    source = Path(info.packet_path)
    try:
        packet = work / "packet.md"
        packet.write_bytes(source.read_bytes())
        (work / "packet.json").write_bytes(packet_json.read_bytes())
    except OSError as exc:
        raise ReviewStateError(f"cannot copy the packet {source} into {work}: {exc}") from exc
    return packet


# --- review: dispatch --------------------------------------------------------------------


def _site_path(locations: Locations, site: str) -> str | None:
    path, _, line = site.rpartition(":")
    if not path or not re.fullmatch(r"\d+(-\d+)?", line.strip()):
        path = site
    try:
        return normalize_path(locations.worktree, path.strip())
    except ReviewStateError:
        return None


def _ranges(review: Review, role: str, files: list[str]) -> list[tuple[int, int]]:
    """Return the packet line ranges a role reads, in packet order."""
    sections = review.packet.sections
    if ROLE_SPECS[role].packet == "whole" or (role in COMPONENT_ROLES and not files):
        return [(1, max(end for _, end in sections.values()))]
    picked = [review.packet.files[f] for f in files if f in review.packet.files]
    if role in ("list-builder", *COMPONENT_ROLES):
        picked += [sections[s] for s in ("Metadata", "Changed files (name-status)") if s in sections]
    elif role == "challenger" and "Metadata" in sections:
        picked.append(sections["Metadata"])
    if "Source of truth" in sections:
        picked.append(sections["Source of truth"])
    return sorted(set(picked))


def _record_view(review: Review, rec: Record) -> dict[str, object]:
    run = _run_of(rec)
    return {
        "record_id": rec.record_id,
        "role": _role_of(review, rec),
        "claim": rec.claim.model_dump(),
        "failure_mode": failure_mode_of(rec),
        "primary_id": rec.grouping.primary_id if is_duplicate(rec) else None,
        "run": None if run is None else run.model_dump(exclude={"dispatch_id"}),
        "challenge": None if rec.challenge is None else rec.challenge.model_dump(exclude={"dispatch_id"}),
        "misgrouped": [m.model_dump() for m in rec.misgrouped],
        "ruling": None if rec.ruling is None else rec.ruling.model_dump(),
        "verdict": verdict(review, rec),
        "carried_from": None if rec.carried_from is None else rec.carried_from.model_dump(),
    }


def _new_dispatch(review: Review, role: str, work: Path) -> Dispatch:
    number = len(review.dispatches) + 1
    did = f"D{number}"
    return Dispatch(
        dispatch_id=did,
        role=role,
        round=review.round,
        date=_now(),
        input_path=str(work / "in" / f"{did}-{role}.json"),
        output_path=str(work / "out" / f"{did}-{role}.{'json' if ROLE_SPECS[role].output else 'md'}"),
    )


def _open_of(review: Review, role: str, **match: str) -> Dispatch | None:
    return next(
        (
            d
            for d in review.dispatches
            if d.role == role and d.status == "open" and all(getattr(d, k) == v for k, v in match.items())
        ),
        None,
    )


class _Prep(BaseModel):
    """What preparing a dispatch produced: the input file's role-specific content and the files it reads."""

    payload: dict[str, object] = Field(default_factory=dict)
    files: list[str] = Field(default_factory=list)


def _views(review: Review, ids: list[str]) -> list[dict[str, object]]:
    by_id = {r.record_id: r for r in review.records}
    return [_record_view(review, by_id[i]) for i in ids]


def _prep_inspector(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    if not args.partition:
        raise ReviewStateError(
            "an inspector dispatch needs --partition <partition_id>, an id from status's pending.inspect"
        )
    state = read_state(locations.state_path)
    if state is None:
        raise ReviewStateError(
            f"no partition list is saved in {locations.state_path}; dispatch the list builders and the keeper first"
        )
    part = _find(state, args.partition)
    if part.partition_id in _coarse_pending(review):
        raise ReviewStateError(
            f"partition {part.partition_id} was reported too coarse and waits for the keeper to split it;"
            " dispatch keeper, then inspect the pieces"
        )
    frozen, pending = _inspection(locations, review, state)
    if not frozen and _refined_this_round(review):
        raise ReviewStateError(
            f"the keeper refined the list in round {review.round}, so this round does not inspect any more partitions;"
            f" run start-round --review <review_id>, then dispatch inspector --partition {part.partition_id}"
        )
    entry = next((n for n in pending if n["partition_id"] == part.partition_id), None)
    if entry is None and frozen:
        raise ReviewStateError(
            f"partition {part.partition_id} is not part of this review's remaining work: the plan froze when"
            f" round {review.round} converged, so later reviews inspect it; status's pending.inspect lists"
            " the partitions this review still inspects"
        )
    if entry is None:
        raise ReviewStateError(
            f"partition {part.partition_id} does not need inspecting;"
            " status's pending.inspect lists the partitions that do"
        )
    check_disk_matches(locations, review.scope, part.paths, review.head)
    forms = list(entry["pending_input_forms"])
    d.partition_id, d.reasons = part.partition_id, list(entry["reasons"])
    d.assigned_input_forms = [InputFormRef(partition_id=part.partition_id, input_form=f) for f in forms]
    d.snapshot = take_snapshot(locations, part)
    return _Prep(
        payload={
            "partition_id": part.partition_id,
            "feature": part.feature,
            "pending_input_forms": forms,
            "paths": part.paths,
        },
        files=part.paths,
    )


def _prep_list_builder(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    if not args.component or not args.paths:
        raise ReviewStateError("a list builder dispatch needs --component and --paths with at least one path")
    paths = [normalize_path(locations.worktree, p) for p in args.paths]
    if error := _unchanged_paths_error(review, paths):
        raise error
    d.component, d.paths = args.component, paths
    state = read_state(locations.state_path)
    saved = [] if state is None else [p for p in state.partitions if not p.child_ids]
    fields = {"feature", "origin", "input_forms", "paths"}
    return _Prep(
        payload={
            "component": args.component,
            "paths": paths,
            "partitions": [p.model_dump(include=fields) for p in saved],
        },
        files=paths,
    )


COMPONENT_ROLES = ("quality-lens", "test-adversary")
COMPONENT_LIMIT = 3


def _component_paths(review: Review) -> dict[str, list[str]]:
    """Map each component of the change to its changed files, in dispatch order.

    A component is a set of changed files that one subagent reads together.
    In a deep review the list builders name the components. In a standard
    review the first quality lens or test adversary dispatched with a
    component's paths names it.
    """
    found: dict[str, list[str]] = {}
    builders_first = sorted(review.dispatches, key=lambda d: d.role != "list-builder")
    for d in builders_first:
        if d.component and d.paths and d.role in ("list-builder", *COMPONENT_ROLES):
            found.setdefault(d.component, d.paths)
    return found


def _uncovered_files(review: Review) -> list[str]:
    """Return the changed files that are in none of a standard review's components."""
    components = _component_paths(review)
    if review.depth == "deep" or not components:
        return []
    covered = {path for paths in components.values() for path in paths}
    return [f for f in review.packet.files if f not in covered]


def _unchanged_paths_error(review: Review, paths: list[str]) -> ReviewStateError | None:
    unchanged = [p for p in paths if p not in review.packet.files]
    if not unchanged:
        return None
    return ReviewStateError(
        f"the packet does not change {', '.join(unchanged)}; give --paths only the component's changed files,"
        f" from: {', '.join(review.packet.files)}"
    )


def _new_component(review: Review, name: str, paths: list[str]) -> list[str]:
    """Check the paths of a component that a standard review's dispatch names, and return them."""
    components = _component_paths(review)
    shown = ", ".join(repr(c) for c in components) or "none"
    if not paths:
        raise ReviewStateError(
            f"the review has no component {name!r} (the components: {shown}); to name it, give its changed files"
            " with --paths <file>..."
        )
    if error := _unchanged_paths_error(review, paths):
        raise error
    for path in paths:
        if owner := next((c for c, taken in components.items() if path in taken), None):
            raise ReviewStateError(f"{path} is in component {owner!r}; a changed file is in one component only")
    if len(components) >= COMPONENT_LIMIT:
        raise ReviewStateError(
            f"a standard review takes at most {COMPONENT_LIMIT} components, and this one has {shown};"
            " divide the changed files among that many before the first dispatch"
        )
    return paths


def _prep_by_component(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    """Give a quality lens or a test adversary its component's files, or the whole packet with no component."""
    role = d.role.replace("-", " ")
    paths = [normalize_path(locations.worktree, p) for p in args.paths]
    if not args.component:
        if paths:
            raise ReviewStateError(f"a {role} takes --paths only with --component <name>")
        return _Prep()
    components = _component_paths(review)
    known = components.get(args.component)
    if review.depth == "deep":
        if paths:
            raise ReviewStateError(f"a {role} takes its paths from its component's list builder; drop --paths")
        if known is None:
            shown = ", ".join(repr(c) for c in components) or "none"
            raise ReviewStateError(f"no list builder covered component {args.component!r}; the components: {shown}")
    elif known is None:
        known = _new_component(review, args.component, paths)
    elif paths and sorted(paths) != sorted(known):
        raise ReviewStateError(
            f"component {args.component!r} has the paths {' '.join(known)}, not {' '.join(paths)}; drop --paths,"
            " or give the other files their own component"
        )
    d.component, d.paths = args.component, known
    return _Prep(payload={"component": d.component, "paths": d.paths}, files=d.paths)


def _prep_keeper(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    state = read_state(locations.state_path)
    waiting = _for_keeper(review)
    proposals = [x for x in waiting if x.role == "list-builder"]
    hunts = [x for x in waiting if x.role == "hunter"]
    coarse = [x for x in waiting if x.role == "inspector"]
    frozen, pending_inspect = _inspection(locations, review, state)
    later = _records_for_keeper(review)
    suspected = [{"input_form": f, "failure_mode": x.failure_mode} for x in hunts for f in x.suspected_input_forms]
    suspected += [
        {"input_form": r.claim.input_form.removeprefix("new:").strip(), "failure_mode": failure_mode_of(r)}
        for r in later
    ]
    for x in (*waiting, *later):
        x.keeper_dispatch_id = d.dispatch_id
    fields = {"partition_id", "feature", "origin", "input_forms", "paths", "child_ids"}
    return _Prep(
        payload={
            "partitions": [] if state is None else [p.model_dump(include=fields) for p in state.partitions],
            "plan_frozen": frozen,
            "pending": {"inspect": pending_inspect},
            "proposals": [p.model_dump() for x in proposals for p in x.proposals],
            "suspected_input_forms": suspected,
            "too_coarse": [{"partition_id": x.partition_id, "proposed_split": x.proposed_split} for x in coarse],
        }
    )


def _searched(review: Review, name: str, *, reasons: bool) -> dict[str, object]:
    """Return what the failure mode's hunters searched in this review, or nothing when none searched.

    That is the latest hunter's rule and search, and every site any of them
    listed, with the status the latest one gave it.
    """
    hunts = [d for d in review.dispatches if d.role == "hunter" and d.failure_mode == name and d.sites]
    if not hunts:
        return {}
    sites = {s.site: s for d in hunts for s in d.sites}
    return {
        "expected": hunts[-1].expected,
        "searched": hunts[-1].searched,
        "sites": [s.model_dump(exclude=None if reasons else {"reason"}) for s in sites.values()],
    }


def _failure_modes(review: Review, *, reasons: bool) -> list[dict[str, object]]:
    """Return the review's failure modes, each hunted one with what its hunters searched."""
    return [m.model_dump() | _searched(review, m.name, reasons=reasons) for m in review.failure_modes]


def _prep_consolidator(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    d.assigned_record_ids = to_consolidate(review)
    if not d.assigned_record_ids:
        raise ReviewStateError(
            "no records wait for consolidation; run status --review <review_id> and follow its next field"
        )
    claim_keys = {"site", "input_form", "input", "expected", "source", "observation", "failure_mode"}
    primaries = [r for r in review.records if r.grouping is not None and not is_duplicate(r)]
    return _Prep(
        payload={
            "records": _views(review, d.assigned_record_ids),
            "primaries": [
                {
                    "record_id": r.record_id,
                    "claim": r.claim.model_dump(include=claim_keys),
                    "failure_mode": failure_mode_of(r),
                    "verdict": verdict(review, r),
                }
                for r in primaries
            ],
            "failure_modes": _failure_modes(review, reasons=False),
        }
    )


def _check_records(review: Review, args: argparse.Namespace) -> None:
    """Refuse a runner or challenger request that names a record not waiting for it nor held by an open one."""
    if commas := [i for i in args.records if "," in i]:
        raise ReviewStateError(
            f"separate record ids with spaces, not commas: --records {' '.join(commas[0].replace(',', ' ').split())}"
        )
    key, pool = ("run", to_run(review)) if args.role == "runner" else ("challenge", to_challenge(review))
    known = {*pool, *_assigned_open(review, args.role)}
    if unknown := [i for i in args.records if i not in known]:
        raise ReviewStateError(
            f"these records do not wait for the {args.role}: {', '.join(unknown[:MAX_IDS_IN_ERROR])};"
            f" run status --review <review_id>, whose pending.{key} lists the ones that do"
        )


def _prep_judge(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    pool = to_run(review) if d.role == "runner" else to_challenge(review)
    d.assigned_record_ids = [i for i in (args.records or pool) if i in pool]
    if not d.assigned_record_ids:
        raise ReviewStateError(
            f"no records wait for the {d.role}; run status --review <review_id> and follow its next field"
        )
    by_id = {r.record_id: r for r in review.records}
    files = (
        sorted({p for i in d.assigned_record_ids if (p := _site_path(locations, by_id[i].claim.site))})
        if d.role == "challenger"
        else []
    )
    return _Prep(payload={"records": _views(review, d.assigned_record_ids)}, files=files)


def _without_run(view: dict[str, object]) -> dict[str, object]:
    """Return a record's view without its probe run: one probed input would anchor a hunter's search."""
    claim = {k: v for k, v in view["claim"].items() if k != "run"}
    return {k: v for k, v in view.items() if k != "run"} | {"claim": claim}


def _prep_hunter(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    if not args.failure_mode:
        raise ReviewStateError("a hunter dispatch needs --failure-mode <name>, a name from status's pending.hunt")
    waiting = to_hunt(review)
    name = {_key(k): k for k in waiting}.get(_key(args.failure_mode))
    if name is None:
        shown = ", ".join(repr(k) for k in waiting) or "none"
        raise ReviewStateError(
            f"failure mode {args.failure_mode!r} has no confirmed or upheld record left to hunt,"
            f" and no site a hunter left not checked; the failure modes waiting for a hunter: {shown}"
        )
    first = _unchecked_hunts(review).get(name)
    d.failure_mode, d.assigned_record_ids = name, waiting[name]
    mode = next((m for m in review.failure_modes if m.name == name), FailureMode(name=name, description=name))
    payload: dict[str, object] = {
        "failure_mode": mode.model_dump(),
        "records": [_without_run(v) for v in _views(review, d.assigned_record_ids)],
        "check_expectations": _with_source(review, d.assigned_record_ids),
    }
    if first is not None:
        unchecked = [s.model_dump() for s in first.sites if s.status == "not checked"]
        payload |= {"expected": first.expected, "searched": first.searched, "sites": unchecked}
    elif earlier := _searched(review, name, reasons=True):
        payload["earlier_hunt"] = earlier
    return _Prep(payload=payload)


def _with_source(review: Review, ids: list[str]) -> list[str]:
    """Return the ids whose claims cite a source; a record without one was upheld by the challenger."""
    by_id = {r.record_id: r for r in review.records}
    return [i for i in ids if by_id[i].claim.source is not None]


def _prep_forms_checker(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    state = read_state(locations.state_path)
    status = _review_status(locations, review)
    blockers = _unfinished(review, status)
    if status["pending"]["inspect"]:
        blockers["inspect"] = status["pending"]["inspect"]
    if blockers:
        raise ReviewStateError(
            f"the forms checker runs after the partition loop stops, and this work is unfinished: {json.dumps(blockers)};"
            " run status --review <review_id> and follow its next field"
        )
    d.assigned_input_forms = _forms_pending(review, state)
    if not d.assigned_input_forms:
        raise ReviewStateError(
            "no input form waits for the forms checker; run status --review <review_id> and follow its next field"
        )
    parts = [_find(state, pid) for pid in dict.fromkeys(f.partition_id for f in d.assigned_input_forms)]
    return _Prep(
        payload={
            "pending_input_forms": [f.model_dump() for f in d.assigned_input_forms],
            "partitions": [{"partition_id": p.partition_id, "feature": p.feature, "paths": p.paths} for p in parts],
        }
    )


def _prep_synthesizer(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    payload = synthesis_input(locations, review, read_state(locations.state_path))
    d.assigned_record_ids = [r.record_id for r in review.records]
    d.output_path = str((Path(args.report) if args.report else _new_report_path(locations, review)).resolve())
    return _Prep(payload=payload)


def _new_report_path(locations: Locations, review: Review) -> Path:
    """Create and return an empty report file whose name no other review has taken.

    The name holds the time to the second and the scope, so two reviews that
    finish in one second would share it; the second one gets a number.
    """
    stamp = _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%d-%H%M%S")
    locations.review_dir.mkdir(parents=True, exist_ok=True)
    for n in range(1, 1000):
        suffix = "" if n == 1 else f"-{n}"
        path = locations.review_dir / f"code-review-{stamp}-{review.scope}{suffix}.md"
        try:
            path.touch(exist_ok=False)
        except FileExistsError:
            continue
        return path
    raise ReviewStateError(f"every report name for {stamp} is taken in {locations.review_dir}")


def _prep_plain(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    return _Prep()


def _has_spec(review: Review) -> bool:
    """Return whether the spec lens has something to check against: the packet's source of truth, or a spec."""
    return review.packet.has_source_of_truth or bool(review.spec.strip())


def _prep_spec_lens(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> _Prep:
    if not _has_spec(review):
        raise ReviewStateError(
            "the packet has no source of truth and the review does not name a spec, so the spec lens would invent one;"
            " review without it, or name the spec with update-review --review <review_id> --spec <where it is>"
        )
    return _Prep()


def _prepare(locations: Locations, review: Review, d: Dispatch, args: argparse.Namespace) -> dict[str, object]:
    """Fill the dispatch's assignment and return the content of its input file."""
    spec = ROLE_SPECS[d.role]
    prep = spec.prepare(locations, review, d, args)
    if spec.packet == "none":
        return prep.payload
    d.packet_ranges = _ranges(review, d.role, prep.files)
    return {"packet": review.packet.path, "packet_ranges": d.packet_ranges, **prep.payload}


ASSETS = Path(__file__).resolve().parent.parent / "assets"
REFERENCES = ASSETS.parent / "references"
SCOPE_TEXT = {"staged": "pre-commit (staged changes)", "worktree": "the working tree as it stands"}
_SECTION = re.compile(r"^\{\{#(\w+)\}\}\n(.*?)^\{\{/\1\}\}\n", re.DOTALL | re.MULTILINE)
_SLOT = re.compile(r"\{\{(\w+)\}\}")


def _text_block(path: Path) -> str:
    """Return the content of a file's ``text`` code block."""
    text = path.read_text(encoding="utf-8")
    start = text.index("```text\n") + len("```text\n")
    return text[start : text.rindex("```")]


def _data_representation_tests() -> str:
    text = (REFERENCES / "data-representation.md").read_text(encoding="utf-8")
    return text[text.index("## Test 1") : text.index("## Evidence")].strip()


def _slot_values(review: Review, d: Dispatch) -> dict[str, str]:
    """Return the value of every template slot; an empty value leaves its optional section out."""
    architecture = review.architecture and d.role == "quality-lens" and not d.component
    branch_scope = f"pre-merge against {review.base or 'the base branch'}"
    return {
        "input_path": d.input_path,
        "claim": _text_block(ASSETS / "claim.md").strip(),
        "issue_template": (ASSETS / "issue-template.md").read_text(encoding="utf-8").strip(),
        "how_to_run": review.how_to_run,
        "intent": review.intent,
        "scope": SCOPE_TEXT.get(review.scope, branch_scope),
        "feature_type": review.feature_type,
        "spec": review.spec or ("in the packet" if review.packet.has_source_of_truth else "none"),
        "flagged_claims": review.flagged_claims,
        "domain_checks": review.domain_checks.strip(),
        "architecture": "yes" if architecture else "",
        "data_representation": _data_representation_tests() if architecture else "",
        "one_context": "yes" if review.one_context else "",
    }


def render_prompt(review: Review, d: Dispatch) -> str:
    """Fill the role's template: the review's values, the claim fields, and the dispatch's input path."""
    values = _slot_values(review, d)
    text = _text_block(ASSETS / f"prompt-{d.role}.md")
    text = _SECTION.sub(lambda m: m.group(2) if values[m.group(1)] else "", text)
    return _SLOT.sub(lambda m: values[m.group(1)], text)


VALUE_FLAGS = (
    "depth",
    "intent",
    "how_to_run",
    "feature_type",
    "spec",
    "flagged_claims",
    "domain_checks_file",
    "architecture",
    "one_context",
    "models",
)
VALUE_FLAG_OF = {"domain_checks": "domain_checks_file"}  # the stored names whose flag has another name


def _given_values(args: argparse.Namespace) -> dict[str, str | bool]:
    """Return the review values the command line gave, by stored name."""
    values: dict[str, str | bool] = {}
    for flag in VALUE_FLAGS:
        given = getattr(args, flag)
        if given is None:
            continue
        if flag in ("intent", "how_to_run") and not given.strip():
            raise ReviewStateError(f"--{flag.replace('_', '-')} needs text; say so when the user did not give any")
        if flag == "domain_checks_file":
            values["domain_checks"] = Path(given).read_text(encoding="utf-8") if given else ""
        elif flag in ("architecture", "one_context"):
            values[flag] = given == "yes"
        else:
            values[flag] = given
    return values


def cmd_update_review(locations: Locations, args: argparse.Namespace) -> dict[str, object]:
    """Change the values that fill the prompts; prompts written before keep what they had."""
    given = _given_values(args)
    if not given:
        raise ReviewStateError("update-review needs a value to change, such as --how-to-run <text>")
    work = _work_dir(locations, args.review)
    with updating_review(work) as review:
        changed = {name: value for name, value in given.items() if getattr(review, name) != value}
        if changed:
            _require_no_synthesizer(review)
        for name, value in changed.items():
            setattr(review, name, value)
        if changed:
            review.updates.append(ReviewUpdate(date=_now(), values=changed))
    return {"review_id": review.review_id, "updated": sorted(changed), "already_updated": not changed}


def _prompt_path(work: Path, d: Dispatch) -> Path:
    return work / "prompts" / f"{d.dispatch_id}-{d.role}.md"


RECORD_ROLES = ("keeper", "consolidator", "synthesizer")  # they read the review's records, not the reviewed files
DEEP_ROLES = ("list-builder", "keeper", "inspector", "forms-checker", "runner", "hunter")


def _register(locations: Locations, review: Review, work: Path, args: argparse.Namespace) -> tuple[Dispatch, bool]:
    """Register one dispatch and write its input file and prompt; return it, and whether it repeats an open one."""
    if review.depth == "standard" and args.role in DEEP_ROLES:
        raise ReviewStateError(
            f"a standard review does not dispatch a {args.role}; run status --review <review_id> and follow its next"
            " field, or change the review with update-review --review <review_id> --depth deep"
        )
    if args.role in ("runner", "challenger"):
        _check_records(review, args)
    if args.role not in RECORD_ROLES:
        _check_files(locations, review)
    existing = _same_open_dispatch(review, args)
    if existing is not None:
        component_role = args.role in ("list-builder", *COMPONENT_ROLES)
        paths = [normalize_path(locations.worktree, p) for p in args.paths] if component_role else []
        if paths and sorted(paths) != sorted(existing.paths):
            raise ReviewStateError(
                f"{args.role} {existing.dispatch_id} is open for component {existing.component!r} with other paths"
                f" ({' '.join(existing.paths)}), not {' '.join(paths)}; wait for it, or give the other files"
                f" their own component: dispatch {args.role} --component <another name> --paths <file>..."
            )
        return existing, True
    d = _new_dispatch(review, args.role, work)
    payload = _prepare(locations, review, d, args)
    payload = {
        "dispatch_id": d.dispatch_id,
        "role": d.role,
        "root": str(locations.worktree),
        **payload,
        "output_path": d.output_path,
        "submit_command": _submit_command(locations, review, d.dispatch_id),
    }
    Path(d.input_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _prompt_path(work, d).write_text(render_prompt(review, d), encoding="utf-8")
    review.dispatches.append(d)
    return d, False


def _check_files(locations: Locations, review: Review) -> None:
    """Refuse while a reviewed file on disk, or in the reviewed content, differs from what the review checks."""
    check_disk_matches(locations, review.scope, list(review.packet.files), review.head)
    check_packet_current(locations, review.scope, review.packet.content, review.head)


def _rebind_open(locations: Locations, review: Review) -> None:
    """Point each open dispatch that reads the files at this checkout.

    A review goes on in a separate checkout of its commit with --repo, so an
    open dispatch sent again must read and submit from that checkout.
    """
    for d in review.dispatches:
        if d.status != "open" or d.role in RECORD_ROLES:
            continue
        path = Path(d.input_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("root") == str(locations.worktree):
            continue
        data["root"] = str(locations.worktree)
        data["submit_command"] = _submit_command(locations, review, d.dispatch_id)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


ROLE_OPTIONS = ("partition", "component", "paths", "failure_mode", "records")


def _step_split(
    locations: Locations, review: Review, args: argparse.Namespace
) -> tuple[list[argparse.Namespace], list[argparse.Namespace]]:
    """Return the next step's dispatches that fit under the limit, and those the limit holds back.

    While dispatches are open, only the step they belong to gets more, so a
    step's records reach the next step together.
    """
    stage = _stage(review, _review_status(locations, review), args.report)
    open_roles = [d.role for d in review.dispatches if d.status == "open"]
    if _finished_report(review) is not None or any(r not in stage.beside for r in open_roles):
        return [], []
    room = max(args.limit - len(open_roles), 0)
    return stage.requests[:room], stage.requests[room:]


def _request_name(a: argparse.Namespace) -> str:
    detail = a.component or a.partition or a.failure_mode
    return f"{a.role} {detail}".strip()


def cmd_dispatch(locations: Locations, args: argparse.Namespace) -> dict[str, object]:
    """Register dispatches; write each one's input file and prompt; print the prompts to send.

    With a role, register that one dispatch. With no role, register every
    dispatch the next step names, up to the limit on open dispatches.
    """
    if not args.role and (given := [f"--{n.replace('_', '-')}" for n in ROLE_OPTIONS if getattr(args, n)]):
        raise ReviewStateError(
            f"{', '.join(given)} needs a role: dispatch <role> {given[0]} ...;"
            " dispatch with no role registers every dispatch the next step names"
        )
    work = _work_dir(locations, args.review)
    repeated = False
    held: list[argparse.Namespace] = []
    with updating_review(work) as review:
        if any(d.status == "open" and d.role not in RECORD_ROLES for d in review.dispatches):
            _check_files(locations, review)
            _rebind_open(locations, review)
        if args.role:
            if args.role != "synthesizer" or _finished_report(review) is not None:
                _require_no_synthesizer(review)
            d, repeated = _register(locations, review, work, args)
            new = [d]
        else:
            ready, held = _step_split(locations, review, args)
            new = [_register(locations, review, work, a)[0] for a in ready]
        status = _review_status(locations, review)
        rulings = _rulings(review) if not status["open_dispatches"] else []
    return {
        "dispatches": [_entry(work, d) for d in new],
        "open_dispatches": status["open_dispatches"],
        "next": status["next"],
        "already_dispatched": repeated,
        "deferred": [_request_name(a) for a in held],
        "rulings": rulings,
    }


def _same_open_dispatch(review: Review, args: argparse.Namespace) -> Dispatch | None:
    """Return the open dispatch this request repeats, or None when it asks for new work.

    A runner or challenger request repeats an open dispatch when none of the
    records it asks for (all waiting records, when it does not name any) still waits.
    """
    role = args.role
    if role == "inspector":
        return _open_of(review, role, partition_id=args.partition or "")
    if role == "hunter":
        name = {_key(d.failure_mode): d.failure_mode for d in review.dispatches}.get(_key(args.failure_mode or ""))
        return _open_of(review, role, failure_mode=name or args.failure_mode or "")
    if role in ("list-builder", *COMPONENT_ROLES):
        return _open_of(review, role, component=args.component or "")
    if role in ("runner", "challenger"):
        pool = to_run(review) if role == "runner" else to_challenge(review)
        if any(i in pool for i in args.records or pool):
            return None
        wanted = set(args.records) if args.records else None
        matches = [
            d
            for d in review.dispatches
            if d.role == role and d.status == "open" and (wanted is None or set(d.assigned_record_ids) <= wanted)
        ]
        return matches[-1] if matches else None
    return _open_of(review, role)


def _submit_command(locations: Locations, review: Review, did: str) -> str:
    parts = [str(Path(__file__).resolve()), "submit", did, "--repo", str(locations.worktree)]
    return shlex.join([*parts, "--review-dir", str(locations.review_dir), "--review", review.review_id])


# --- review: submit ----------------------------------------------------------------------


def _find_dispatch(review: Review, did: str) -> Dispatch:
    d = next((x for x in review.dispatches if x.dispatch_id == did), None)
    if d is None:
        known = ", ".join(x.dispatch_id for x in review.dispatches if x.status == "open") or "none"
        raise ReviewStateError(f"unknown dispatch {did!r}; the open dispatches: {known}")
    return d


def _check_read(d: Dispatch, read_through: int) -> None:
    if d.packet_ranges and read_through < max(end for _, end in d.packet_ranges):
        last = max(end for _, end in d.packet_ranges)
        raise ReviewStateError(
            f"read_through is {read_through}, but your packet ranges end at line {last};"
            f" read the packet from line {read_through + 1} through {last}, then submit again"
        )


def _check_ids(assigned: list[str], given: list[str], what: str) -> None:
    missing = [i for i in assigned if i not in given]
    extra = [i for i in given if i not in assigned]
    repeated = sorted({i for i in given if given.count(i) > 1})
    problems = []
    if missing:
        problems.append(f"no {what} for: {', '.join(missing)}")
    if extra:
        problems.append(f"items you were not given: {', '.join(extra)}")
    if repeated:
        problems.append(f"more than one {what} for: {', '.join(repeated)}")
    if problems:
        raise ReviewStateError("your output does not cover your assignment:\n" + "\n".join(f"- {x}" for x in problems))


def _add_records(review: Review, d: Dispatch, claims: list[Claim]) -> list[str]:
    ids = []
    for claim in claims:
        n = sum(1 for r in review.records if r.round == review.round) + 1
        rec = Record(record_id=f"R{review.round}-{n}", round=review.round, dispatch_id=d.dispatch_id, claim=claim)
        review.records.append(rec)
        ids.append(rec.record_id)
    return ids


def _where(i: int, claim: Claim) -> str:
    return f"claims.{i} (site {claim.site})"


def _check_runs_present(claims: list[Claim]) -> None:
    for i, claim in enumerate(claims):
        if claim.run is None:
            raise ReviewStateError(f"{_where(i, claim)}: this role runs every probe; fill in its run")
        if claim.run.verdict == "refuted":
            raise ReviewStateError(
                f"{_where(i, claim)}: run.verdict 'refuted' is not used here; a right result that no test checks is"
                " 'test gap', and a probe whose behavior a test already checks is left out"
            )


def _check_no_runs(claims: list[Claim]) -> None:
    for i, claim in enumerate(claims):
        if claim.run is not None:
            raise ReviewStateError(
                f"{_where(i, claim)}: set run to null; only the test adversary, the forms checker,"
                " and the runner record runs"
            )


def _apply_inspector(locations: Locations, review: Review, d: Dispatch, out: InspectorOutput) -> dict[str, object]:
    assigned = [f.input_form for f in d.assigned_input_forms]
    _check_ids(assigned, [f.input_form for f in out.input_forms], "input form status")
    for i, claim in enumerate(out.claims):
        if claim.input_form not in assigned and not claim.input_form.startswith("new: "):
            raise ReviewStateError(
                f"{_where(i, claim)}: input_form {claim.input_form!r} must be one of your pending input forms,"
                " or 'new: <form>' for one you found"
            )
    _check_no_runs(out.claims)
    d.result, d.proposed_split, d.input_forms = out.result, out.proposed_split, out.input_forms
    checked = [f for f in out.input_forms if f.status != "not checked"]
    if checked or not assigned:
        record_inspection(locations, d.partition_id, d.snapshot, review.scope, out.input_forms)
    return {"record_ids": _add_records(review, d, out.claims)}


def _apply_list_builder(
    locations: Locations, review: Review, d: Dispatch, out: ListBuilderOutput
) -> dict[str, object]:
    d.proposals = out.proposals
    return {}


def _apply_keeper(locations: Locations, review: Review, d: Dispatch, out: KeeperOutput) -> dict[str, object]:
    d.changes = out.changes
    result = save_list(locations, ListInput(partitions=out.partitions))
    if review.depth == "deep" and convergence(review, review.round)["converged"]:
        review.plan_frozen = True
    return result


def _apply_lens(locations: Locations, review: Review, d: Dispatch, out: LensOutput) -> dict[str, object]:
    _check_no_runs(out.claims)
    d.summary = out.summary
    return {"record_ids": _add_records(review, d, out.claims)}


def _apply_test_adversary(
    locations: Locations, review: Review, d: Dispatch, out: TestAdversaryOutput
) -> dict[str, object]:
    _check_runs_present(out.claims)
    return {"record_ids": _add_records(review, d, out.claims)}


def _apply_forms_checker(
    locations: Locations, review: Review, d: Dispatch, out: FormsCheckerOutput
) -> dict[str, object]:
    def label(ref: InputFormRef) -> str:
        return f"{ref.partition_id}: {ref.input_form}"

    _check_ids([label(f) for f in d.assigned_input_forms], [label(f) for f in out.input_forms], "coverage entry")
    claims = [c for f in out.input_forms for c in f.claims]
    _check_runs_present(claims)
    missing = [label(f) for f in out.input_forms if not f.tests and not f.claims]
    if missing:
        raise ReviewStateError(f"each form no test exercises needs a probe claim under it: {'; '.join(missing)}")
    known = {_ref_key(c) for c in review.checked_input_forms}
    review.checked_input_forms += [
        CheckedInputForm(**f.model_dump(exclude={"claims"}), dispatch_id=d.dispatch_id)
        for f in out.input_forms
        if _ref_key(f) not in known
    ]
    return {"record_ids": _add_records(review, d, claims)}


def _apply_runner(locations: Locations, review: Review, d: Dispatch, out: RunnerOutput) -> dict[str, object]:
    _check_ids(d.assigned_record_ids, [r.record_id for r in out.results], "result")
    by_id = {r.record_id: r for r in review.records}
    for res in out.results:
        by_id[res.record_id].run = StoredRun(**res.model_dump(exclude={"record_id"}), dispatch_id=d.dispatch_id)
    return {"record_ids": d.assigned_record_ids, "split_record_ids": _apply_splits(review, d.dispatch_id)}


def _apply_challenger(locations: Locations, review: Review, d: Dispatch, out: ChallengerOutput) -> dict[str, object]:
    _check_ids(d.assigned_record_ids, [r.record_id for r in out.results], "verdict")
    by_id = {r.record_id: r for r in review.records}
    for res in out.results:
        by_id[res.record_id].challenge = Challenge(dispatch_id=d.dispatch_id, **res.model_dump(exclude={"record_id"}))
    d.review_critique = out.review_critique
    return {"record_ids": d.assigned_record_ids}


def _check_misgrouped(out: HunterOutput, given: list[Record], *, rule_given: bool) -> None:
    """Refuse a misgrouped list that names anything but supported given records, once each, or names all of them.

    A hunter not given a record decides only the sites an earlier hunter left, so it does not list any.
    A hunter given an earlier hunt's rule may list all of its records: the rule stays the earlier hunt's.
    """
    listed = [m.record_id for m in out.misgrouped]
    if listed and not given:
        raise ReviewStateError(
            "misgrouped must be empty: your input file holds sites and does not hold records, so your task is only those sites"
        )
    ids = {r.record_id for r in given}
    unsupported = {e.record_id for e in out.expectations if not e.expected_supported}
    if unknown := [i for i in listed if i not in ids]:
        raise ReviewStateError(
            f"misgrouped names {unknown[0]}, which is not one of your records; list only records from your input file"
        )
    if dropped := [i for i in listed if i in unsupported]:
        raise ReviewStateError(
            f"misgrouped names {dropped[0]}, which your expectations mark unsupported;"
            " an unsupported record is dropped, so leave it out of misgrouped"
        )
    if twice := [i for i in listed if listed.count(i) > 1]:
        raise ReviewStateError(f"misgrouped lists {twice[0]} more than once; list each record once")
    if not rule_given and ids - unsupported and ids - unsupported <= set(listed):
        raise ReviewStateError(
            "misgrouped lists every supported record, so no record is left for expected;"
            " write expected for the largest group of records that break one rule,"
            " and list only the other records in misgrouped"
        )


def _check_hunt(out: HunterOutput, given: list[Record], *, rule_given: bool) -> None:
    """Refuse a hunt that does not state its rule, its search, and its sites, the given records' among them.

    A hunter that did not find any checked record supported stops before it searches,
    so it does not state any. `given` leaves out the records the hunter listed in
    misgrouped: their sites break another rule. A hunter given an earlier hunt's
    rule that keeps none of its records has nothing to add to that hunt.
    """
    if out.expectations and not any(e.expected_supported for e in out.expectations):
        filed = {
            "expected": out.expected.strip(),
            "searched": out.searched,
            "sites": out.sites,
            "claims": out.claims,
            "suspected_input_forms": out.suspected_input_forms,
        }
        if filled := [k for k, v in filed.items() if v]:
            raise ReviewStateError(
                f"no checked record is supported, so the hunt stops there: leave {', '.join(filled)} empty"
            )
        return
    if rule_given and not given:
        return
    fixes = {
        "expected": "write the rule every place must keep, in one sentence that does not name a file, function, or variable",
        "searched": "name the table, the set of definitions, or the search that produces every place, and where it is",
        "sites": "list every place that searched produces, each with its status and reason",
    }
    stated = {"expected": out.expected.strip(), "searched": out.searched, "sites": out.sites}
    for field, fix in fixes.items():
        if not stated[field]:
            raise ReviewStateError(f"{field} is empty; {fix}")
    unsupported = {e.record_id for e in out.expectations if not e.expected_supported}
    listed = {s.site for s in out.sites}
    status = {s.site: s.status for s in out.sites}
    for rec in given:
        if rec.record_id not in unsupported and status.get(rec.claim.site, "claims") != "claims":
            raise ReviewStateError(
                f"{rec.record_id}'s site {rec.claim.site} has status {status[rec.claim.site]!r}; a supported record"
                " breaks the rule at its site, so give that site status claims, or list the record in misgrouped"
            )
        if rec.record_id not in unsupported and rec.claim.site not in listed:
            raise ReviewStateError(
                f"sites has no entry for {rec.record_id}'s site; the list must reproduce the places already known,"
                f" so check that searched produces this place, then copy the site text exactly: add"
                f' {{"site": {json.dumps(rec.claim.site)}, "status": "claims", "reason": "<how it breaks expected>"}}'
            )


def _check_hunt_sites(out: HunterOutput, given: list[Record]) -> None:
    """Refuse a hunt whose claims and whose sites with status claims name different places.

    A site with status claims may also be the site of a record in `given`, which
    leaves out the records the hunter listed in misgrouped.
    """
    breaks = {s.site for s in out.sites if s.status == "claims"}
    for i, claim in enumerate(out.claims):
        if claim.site not in breaks:
            raise ReviewStateError(
                f"{_where(i, claim)}: sites has no entry for this site with status claims;"
                f' add {{"site": {json.dumps(claim.site)}, "status": "claims", "reason": "<how it breaks expected>"}}'
                " to sites, with the site text exactly as the claim gives it"
            )
    claimed = {c.site for c in out.claims} | {r.claim.site for r in given}
    for i, s in enumerate(out.sites):
        if s.status == "claims" and s.site not in claimed:
            raise ReviewStateError(
                f"sites.{i} (site {s.site}): status claims needs a claim at this site, and neither your claims nor"
                " your records have one; add a claim whose site is exactly this text, or set the status the code shows"
            )


def _check_follow_up(out: HunterOutput, first: Dispatch) -> None:
    """Refuse a follow-up hunt that does not decide exactly the sites the first hunter left, under its rule."""
    if out.expected.strip() != first.expected.strip():
        raise ReviewStateError("expected differs from your input file's expected; copy it exactly")
    if out.searched != first.searched:
        raise ReviewStateError("searched differs from your input file's searched; copy it exactly")
    assigned = {s.site for s in first.sites if s.status == "not checked"}
    returned = {s.site for s in out.sites}
    if missing := sorted(assigned - returned):
        raise ReviewStateError(f"sites leaves out {', '.join(missing)}; decide each site your input file gives")
    if extra := sorted(returned - assigned):
        raise ReviewStateError(
            f"sites adds {', '.join(extra)}, which your input file does not give; decide only the sites it gives"
        )


def _record_misgrouped(rec: Record, d: Dispatch, reason: str) -> None:
    """Record that hunter `d` found `rec` misgrouped; the first time, take it out of its failure mode.

    The record then has no grouping, so it waits for the consolidator. It keeps
    its run, its challenge, and its ruling. A record moves once in a review, so
    that regrouping ends: listed again, it stays in its failure mode.
    """
    if not rec.misgrouped:
        rec.grouping = rec.split = None
    rec.misgrouped.append(Misgrouped(failure_mode=d.failure_mode, reason=reason, dispatch_id=d.dispatch_id))


def _apply_hunter(locations: Locations, review: Review, d: Dispatch, out: HunterOutput) -> dict[str, object]:
    _check_ids(
        _with_source(review, d.assigned_record_ids), [e.record_id for e in out.expectations], "expectation check"
    )
    _check_no_runs(out.claims)
    by_id = {r.record_id: r for r in review.records}
    given = [by_id[i] for i in d.assigned_record_ids]
    earlier = [
        h
        for h in review.dispatches
        if h.role == "hunter" and h.failure_mode == d.failure_mode and h.sites and h.dispatch_id != d.dispatch_id
    ]
    rule_given = bool(given) and bool(earlier)
    if not given and earlier:
        _check_follow_up(out, earlier[-1])
    _check_misgrouped(out, given, rule_given=rule_given)
    moved = {m.record_id for m in out.misgrouped}
    kept = [r for r in given if r.record_id not in moved]
    if rule_given and kept and out.expected.strip() != earlier[-1].expected.strip():
        raise ReviewStateError(
            "expected differs from earlier_hunt's expected; copy expected from earlier_hunt exactly, and list in"
            " misgrouped each record that breaks a different rule"
        )
    _check_hunt(out, kept, rule_given=rule_given)
    _check_hunt_sites(out, kept)
    for exp in out.expectations:
        by_id[exp.record_id].hunt = Hunt(
            expected_supported=exp.expected_supported, reason=exp.reason, dispatch_id=d.dispatch_id
        )
    for item in out.misgrouped:
        _record_misgrouped(by_id[item.record_id], d, item.reason)
    d.expected, d.searched, d.sites = out.expected, out.searched, out.sites
    d.suspected_input_forms = out.suspected_input_forms
    return {"record_ids": _add_records(review, d, out.claims)}


def _duplicate_problem(x: DuplicateDraft, by_id: dict[str, Record], dup_ids: list[str], assigned: set[str]) -> str:
    """Return what is wrong with one duplicate marking, or "" when nothing is."""
    if x.primary_id == x.record_id:
        return f"{x.record_id} cannot be a duplicate of itself"
    target = by_id.get(x.primary_id)
    if target is None:
        return f"{x.record_id} is a duplicate of an unknown id {x.primary_id}"
    if x.primary_id in dup_ids or is_duplicate(target):
        return (
            f"{x.record_id} is a duplicate of {x.primary_id}, which is itself a duplicate; name the record it repeats"
        )
    if x.primary_id not in assigned and target.grouping is None:
        return f"{x.record_id} is a duplicate of {x.primary_id}, which no consolidator has grouped yet"
    return ""


def _grouping_problems(review: Review, d: Dispatch, out: ConsolidatorOutput) -> list[str]:
    """Return every reason the grouping is invalid: each assigned id must be placed once, and each duplicate valid."""
    by_id = {r.record_id: r for r in review.records}
    assigned = set(d.assigned_record_ids)
    dup_ids = [x.record_id for x in out.duplicates]
    placed = dup_ids + [m for g in out.failure_modes for m in g.record_ids]
    problems = []
    if unknown := sorted(set(placed) - assigned):
        problems.append(f"ids you were not given: {', '.join(unknown)}")
    if missing := sorted(assigned - set(placed)):
        problems.append(f"place each of these as a duplicate or in one failure mode: {', '.join(missing)}")
    if twice := sorted({i for i in placed if placed.count(i) > 1}):
        problems.append(f"placed more than once: {', '.join(twice)}")
    problems += [p for x in out.duplicates if (p := _duplicate_problem(x, by_id, dup_ids, assigned))]
    return problems + _placed_back(by_id, d, out)


def _placed_back(by_id: dict[str, Record], d: Dispatch, out: ConsolidatorOutput) -> list[str]:
    """Return a problem for each record the grouping returns to the failure mode a hunter took it out of.

    A record returns there when it is placed in that failure mode, or marked a
    duplicate of a record in it.
    """
    placed = {i: g.name for g in out.failure_modes for i in g.record_ids}
    for x in out.duplicates:
        primary = by_id.get(x.primary_id)
        placed[x.record_id] = placed.get(x.primary_id) or (primary and failure_mode_of(primary)) or ""
    problems = []
    for i in d.assigned_record_ids:
        left = by_id[i].misgrouped[0].failure_mode if by_id[i].misgrouped else None
        if left is not None and _key(placed.get(i, "")) == _key(left):
            problems.append(
                f"{i} left failure mode {left!r}, where a hunter found that it breaks a different rule;"
                " place it in another failure mode, or mark it a duplicate of a record in another failure mode"
            )
    return problems


def _record_grouping(review: Review, d: Dispatch, out: ConsolidatorOutput) -> None:
    """Record failure modes, joining an existing one whose name differs only in case or spacing, then duplicates.

    An existing failure mode keeps its description, unless a record of this
    batch left it as misgrouped: the records that defined it changed, so the
    consolidator's description of it replaces the stored one.
    """
    by_id = {r.record_id: r for r in review.records}
    existing = {_key(m.name): m for m in review.failure_modes}
    left = {_key(m.failure_mode) for i in d.assigned_record_ids for m in by_id[i].misgrouped}
    for g in out.failure_modes:
        stored = existing.get(_key(g.name))
        if stored is None:
            stored = FailureMode(name=g.name, description=g.description)
            existing[_key(g.name)] = stored
            review.failure_modes.append(stored)
        elif _key(g.name) in left:
            stored.description = g.description
        for m in g.record_ids:
            by_id[m].grouping = Grouping(failure_mode=stored.name, dispatch_id=d.dispatch_id)
    for x in out.duplicates:
        by_id[x.record_id].grouping = Grouping(primary_id=x.primary_id, dispatch_id=d.dispatch_id)
        for r in review.records:
            if r.grouping is not None and r.grouping.primary_id == x.record_id:
                r.grouping = r.grouping.model_copy(update={"primary_id": x.primary_id})


def _apply_consolidation(
    locations: Locations, review: Review, d: Dispatch, out: ConsolidatorOutput
) -> dict[str, object]:
    """Check that every assigned id is placed once, as a duplicate or in one failure mode, and record it."""
    if problems := _grouping_problems(review, d, out):
        raise ReviewStateError("your grouping is not valid:\n" + "\n".join(f"- {x}" for x in problems))
    _record_grouping(review, d, out)
    return {"record_ids": d.assigned_record_ids, "split_record_ids": _apply_splits(review, d.dispatch_id)}


def _apply(locations: Locations, review: Review, d: Dispatch, out: BaseModel) -> dict[str, object]:
    """Check `out` against the dispatch's assignment and record it; return the ids it created or changed."""
    read_through = getattr(out, "read_through", None)
    if read_through is not None:
        _check_read(d, read_through)
    return ROLE_SPECS[d.role].apply(locations, review, d, out)


def _submitted(d: Dispatch, result: dict[str, object], *, already: bool) -> dict[str, object]:
    """Return what ``submit`` prints; the reply comes last, so it is the last thing the role reads."""
    reply = (
        f"Recorded. To signal that you are done, reply with exactly `recorded {d.dispatch_id}` and nothing more."
        " Your output file holds your findings; findings in a reply bias the roles that judge them."
    )
    return {"dispatch_id": d.dispatch_id, "role": d.role, **result, "already_submitted": already, "reply": reply}


def cmd_submit(locations: Locations, args: argparse.Namespace) -> dict[str, object]:
    """Validate a role's output file against its schema and assignment; record it."""
    work = _work_dir(locations, args.review)
    with updating_review(work) as review:
        d = _find_dispatch(review, args.dispatch_id)
        if d.status == "done":
            return _submitted(d, d.submit_result, already=True)
        path = Path(args.output or d.output_path)
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ReviewStateError(
                f"cannot read {path}: {exc}; write your output there first, then run submit again"
            ) from exc
        output = ROLE_SPECS[d.role].output
        if output is None:
            missing = [i for i in d.assigned_record_ids if not re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", raw)]
            if missing:
                raise ReviewStateError(f"the report never names these records; place each one: {', '.join(missing)}")
            by_id = {r.record_id: r for r in review.records}
            blocking = [v["record_id"] for v in _sections(review)["findings"] if v["blocking"]]
            for rid in blocking:
                files = _blocking_files(locations, review, by_id[rid])
                review.blocking_file_hashes[rid] = scope_hashes(locations.worktree, review.scope, files, review.head)
            finished = FinishedReview(
                review_id=review.review_id,
                head=review.head,
                branch=review.branch,
                date=_now(),
                report=str(path.resolve()),
                scope=review.scope,
                blocking_record_ids=blocking,
            )
            record_finished_review(locations, finished)
            result: dict[str, object] = {}
        else:
            try:
                out = output.model_validate_json(raw)
            except ValidationError as exc:
                schema = shlex.join([str(Path(__file__).resolve()), "schema", d.role])
                msg = f"{path} does not match the {d.role} format:{_brief(exc)}\nThe format: {schema}"
                raise ReviewStateError(msg) from exc
            result = _apply(locations, review, d, out)
        d.status = "done"
        d.submit_result = result
    return _submitted(d, result, already=False)


def cmd_schema(locations: Locations | None, args: argparse.Namespace) -> dict[str, object]:
    """Print the JSON schema of a role's output file."""
    output = ROLE_SPECS[args.role].output
    if output is None:
        return {"role": args.role, "format": "markdown report that names every record id"}
    return output.model_json_schema()


# --- review: the role registry ---------------------------------------------------------


class RoleSpec(BaseModel):
    """Everything the script does differently for one role."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    output: type[BaseModel] | None  # None: the role writes a markdown report
    apply: Callable[[Locations, Review, Dispatch, BaseModel], dict[str, object]] | None
    prepare: Callable[[Locations, Review, Dispatch, argparse.Namespace], _Prep] = _prep_plain
    packet: Literal["whole", "ranges", "none"]
    one_open: bool = False
    round_one: bool = False  # dispatched in round 1 beside the inspectors; the spec lens only with a spec to check
    lens: bool = False
    small: bool = False  # works best on a small, fast model


# Round-one roles are listed in the order the next step names them.
ROLE_SPECS: dict[str, RoleSpec] = {
    "list-builder": RoleSpec(
        output=ListBuilderOutput, apply=_apply_list_builder, prepare=_prep_list_builder, packet="ranges"
    ),
    "keeper": RoleSpec(output=KeeperOutput, apply=_apply_keeper, prepare=_prep_keeper, packet="none", one_open=True),
    "inspector": RoleSpec(
        output=InspectorOutput, apply=_apply_inspector, prepare=_prep_inspector, packet="ranges", small=True
    ),
    "quality-lens": RoleSpec(
        output=LensOutput, apply=_apply_lens, prepare=_prep_by_component, packet="ranges", round_one=True, lens=True
    ),
    "security-lens": RoleSpec(output=LensOutput, apply=_apply_lens, packet="whole", round_one=True, lens=True),
    "test-adversary": RoleSpec(
        output=TestAdversaryOutput,
        apply=_apply_test_adversary,
        prepare=_prep_by_component,
        packet="ranges",
        round_one=True,
    ),
    "spec-lens": RoleSpec(
        output=LensOutput, apply=_apply_lens, prepare=_prep_spec_lens, packet="whole", round_one=True, lens=True
    ),
    "forms-checker": RoleSpec(
        output=FormsCheckerOutput,
        apply=_apply_forms_checker,
        prepare=_prep_forms_checker,
        packet="whole",
        one_open=True,
    ),
    "consolidator": RoleSpec(
        output=ConsolidatorOutput,
        apply=_apply_consolidation,
        prepare=_prep_consolidator,
        packet="none",
        one_open=True,
    ),
    "runner": RoleSpec(output=RunnerOutput, apply=_apply_runner, prepare=_prep_judge, packet="none", small=True),
    "challenger": RoleSpec(output=ChallengerOutput, apply=_apply_challenger, prepare=_prep_judge, packet="ranges"),
    "hunter": RoleSpec(output=HunterOutput, apply=_apply_hunter, prepare=_prep_hunter, packet="whole"),
    "synthesizer": RoleSpec(output=None, apply=None, prepare=_prep_synthesizer, packet="none", one_open=True),
}


# --- review: status, rounds, and rulings -------------------------------------------------


def cmd_status(locations: Locations, args: argparse.Namespace) -> dict[str, object]:
    """Report locations and the partitions waiting for inspection; with --review, that review's state and next step."""
    review = read_review(_work_dir(locations, args.review)) if args.review else None
    scope = review.scope if review is not None else args.scope
    if scope is None:
        raise ReviewStateError("status needs --scope <staged|branch|worktree>, or --review <review_id>")
    state = read_state(locations.state_path)
    head, branch = head_and_branch(locations.worktree)
    result: dict[str, object] = {
        "root": str(locations.worktree),
        "main_worktree": str(locations.main_worktree),
        "review_dir": str(locations.review_dir),
        "review_dir_in_repo": locations.review_dir_in_repo,
        "review_dir_exists": locations.review_dir.is_dir(),
        "state_path": str(locations.state_path),
        "state_exists": state is not None,
        "scope": scope,
        "branch": branch,
        "head": review.head if review is not None else head,
        "pending": {"inspect": _state_pending(locations, state, scope, review.head if review is not None else "")},
        "previous_review": None if state is None else _previous_review(state, branch),
    }
    if review is not None:
        result |= _review_status(locations, review)
    else:
        result["unfinished_reviews"] = _unfinished_reviews(locations, branch)
    return result


def _unfinished_reviews(locations: Locations, branch: str) -> list[dict[str, object]]:
    """Return each review of `branch` whose report is not written, so a new session can go on with it."""
    found = []
    reviews = locations.review_dir / REVIEWS_DIR
    for work in sorted(reviews.iterdir()) if reviews.is_dir() else []:
        try:
            review = read_review(work)
        except ReviewStateError:
            continue
        if _finished_report(review) is None and review.branch == branch:
            found.append(
                {
                    "review_id": review.review_id,
                    "depth": review.depth,
                    "scope": review.scope,
                    "branch": review.branch,
                    "date": review.date,
                    "open_dispatches": sum(d.status == "open" for d in review.dispatches),
                }
            )
    return found


RUNNER_RECORDS = 3  # a runner given more than a few records returns before it finishes them
CHALLENGER_RECORDS = 12
NO_ROLE = "dispatch --review <review_id>, with no role, which gives each"
JUDGE_ORDER = (
    ("consolidate", "dispatch consolidator"),
    ("run", f"{NO_ROLE} runner at most {RUNNER_RECORDS} records"),
    ("challenge", f"{NO_ROLE} challenger at most {CHALLENGER_RECORDS} records"),
    ("hunt", "dispatch hunter --failure-mode <name> for each failure mode in pending.hunt"),
    ("refine", "dispatch keeper"),
)


def _unfinished(review: Review, status: dict[str, object]) -> dict[str, object]:
    """Return the work that must finish before a round ends or synthesis starts."""
    blockers: dict[str, object] = {}
    if missing := _round_one_missing(review):
        blockers["round_one_roles"] = missing
    if status["open_dispatches"]:
        blockers["open_dispatches"] = status["open_dispatches"]
    if status["candidates"]:
        blockers["candidates"] = status["candidates"]
    pending = status["pending"]
    for key in ("consolidate", "run", "challenge", "hunt", "refine"):
        if pending[key]:
            blockers[key] = pending[key]
    return blockers


def _missing_by_component(review: Review, role: str) -> list[str]:
    """Name each dispatch of a quality lens or a test adversary not made yet.

    A change with several components takes one for each. A change with one
    component takes the one with no component, which reads the whole packet.
    A quality lens whose review checks architecture also takes the one with no
    component.
    """
    components = list(_component_paths(review))
    covered = {d.component for d in review.dispatches if d.role == role}
    several = len(components) > 1 or bool(_uncovered_files(review))
    missing = [f"{role} --component {c}" for c in components if several and c not in covered]
    whole = not several or (role == "quality-lens" and review.architecture)
    if whole and "" not in covered:
        missing.append(role)
    return missing


def _round_one_missing(review: Review) -> list[str]:
    """Name each round-one dispatch not made yet."""
    roles = {d.role for d in review.dispatches}
    missing: list[str] = []
    for role, spec in ROLE_SPECS.items():
        if not spec.round_one or (role == "spec-lens" and not _has_spec(review)):
            continue
        if role in COMPONENT_ROLES:
            missing += _missing_by_component(review, role)
        elif role not in roles:
            missing.append(role)
    if uncovered := _uncovered_files(review):
        missing.append(f"quality-lens --component <name> --paths {' '.join(uncovered)}")
    return missing


class _Stage(BaseModel):
    """The next step: its text, the dispatches it names, and the roles that may still be open beside them."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    requests: list[argparse.Namespace] = Field(default_factory=list)
    beside: frozenset[str] = frozenset()


def _request(role: str, **options: object) -> argparse.Namespace:
    """Return the arguments of one ``dispatch`` call."""
    blank = {"partition": "", "component": "", "paths": [], "failure_mode": "", "records": [], "report": ""}
    return argparse.Namespace(role=role, **(blank | options))


def _chunks(ids: list[str], size: int) -> list[list[str]]:
    return [ids[i : i + size] for i in range(0, len(ids), size)]


def _judge_stage(key: str, text: str, waiting: list[str]) -> _Stage:
    if key == "run":
        requests = [_request("runner", records=c) for c in _chunks(waiting, RUNNER_RECORDS)]
        return _Stage(text=text, requests=requests, beside={"runner"})
    if key == "challenge":
        requests = [_request("challenger", records=c) for c in _chunks(waiting, CHALLENGER_RECORDS)]
        return _Stage(text=text, requests=requests, beside={"challenger"})
    if key == "hunt":
        return _Stage(text=text, requests=[_request("hunter", failure_mode=m) for m in waiting], beside={"hunter"})
    return _Stage(text=text, requests=[_request("consolidator" if key == "consolidate" else "keeper")])


def _stage(review: Review, s: dict[str, object], report: str = "") -> _Stage:
    """Return the next step in the procedure's order, as if no dispatch were open."""
    roles = {d.role for d in review.dispatches}
    pending = s["pending"]
    frozen = s["plan_frozen"]
    missing = _round_one_missing(review)
    inspecting = {d.partition_id for d in review.dispatches if d.role == "inspector" and d.status == "open"}
    inspectors = [
        _request("inspector", partition=n["partition_id"])
        for n in pending["inspect"]
        if n["partition_id"] not in inspecting
    ]
    lenses = [_request(m.split()[0], component=m.partition(" --component ")[2]) for m in missing if "<" not in m]
    round_one = frozenset({"inspector", *(role for role, spec in ROLE_SPECS.items() if spec.round_one)})
    each = "dispatch inspector --partition <partition_id> for each entry in pending.inspect"
    deep = review.depth == "deep"
    if deep and "keeper" not in roles and "list-builder" not in roles:
        return _Stage(text="dispatch list-builder for each component")
    if deep and "keeper" not in roles:
        return _Stage(text="dispatch keeper", requests=[_request("keeper")])
    if pending["inspect"] and not frozen and not _refined_this_round(review):
        also = f", and {', '.join(missing)}" if missing else ""
        return _Stage(text=each + also, requests=inspectors + lenses, beside=round_one)
    if missing:
        return _Stage(text=f"dispatch {', '.join(missing)}", requests=lenses, beside=round_one)
    if pending["inspect"] and frozen:
        return _Stage(text=each, requests=inspectors, beside={"inspector"})
    for key, step in JUDGE_ORDER:
        if pending[key]:
            return _judge_stage(key, step, pending[key])
    if frozen or not pending["inspect"]:
        if pending["check_forms"]:
            return _Stage(text="dispatch forms-checker", requests=[_request("forms-checker")])
        if pending["rule"]:
            return _Stage(
                text=f"ask the user to rule on each disputed record ({', '.join(pending['rule'])}), then run"
                " rule <record_id> --review <review_id> --verdict upheld|refuted --reason <reason>;"
                " to report the unruled ones as disputed, run dispatch synthesizer"
            )
        return _Stage(text="dispatch synthesizer", requests=[_request("synthesizer", report=report)])
    return _Stage(text=f"run start-round, then {each}")


def _priority(rec: Record) -> str:
    """Return the record's priority after any revision the challenger made."""
    revised = rec.challenge.revised_priority if rec.challenge else None
    return revised.priority if revised else rec.claim.priority


def _to_rule(review: Review) -> list[Record]:
    """Return the disputed records the user rules on: those of critical or high priority.

    Another disputed record could not block the merge if upheld, so the report
    gives it with both arguments and the review goes on without asking.
    """
    return [r for r in review.records if verdict(review, r) == "disputed" and _priority(r) in ("critical", "high")]


def _rulings(review: Review) -> list[dict[str, object]]:
    """Return what the user needs to rule on each record in pending.rule: its claim and the challenger's argument."""
    return [
        {"record_id": r.record_id, "claim": r.claim.model_dump(exclude={"run"}), "argument": r.challenge.argument}
        for r in _to_rule(review)
        if r.challenge is not None
    ]


def _finished_report(review: Review) -> str | None:
    return next((d.output_path for d in review.dispatches if d.role == "synthesizer" and d.status == "done"), None)


def _require_no_synthesizer(review: Review) -> None:
    """Refuse a change to a review whose report is written or being written.

    The synthesizer's input holds the review's state at its dispatch, so a
    later change would not reach the report.
    """
    report = _finished_report(review)
    if report is not None:
        raise ReviewStateError(
            f"the review is finished and cannot be changed; present the report at {report}."
            " To review again, build a new packet and run start-review"
        )
    if _open_of(review, "synthesizer") is not None:
        raise ReviewStateError(
            "the synthesizer is writing the report from the review's state at its dispatch, so the review cannot be"
            " changed now; wait for it, and if it returned unrecorded run dispatch synthesizer and send it again"
        )


def _next_step(review: Review, s: dict[str, object]) -> str:
    """Name the one next action, in the procedure's order."""
    report = _finished_report(review)
    if report is not None:
        return f"the review is finished; present the report at {report}"
    if s["open_dispatches"]:
        return "wait for the open dispatches; dispatch again, with its own input file, any that returned unrecorded"
    return _stage(review, s).text


def _describe(d: Dispatch) -> str:
    """Return a few words that name a dispatch for the harness's task list."""
    detail = d.partition_id or d.component or d.failure_mode
    if d.role in ("runner", "challenger"):
        detail = f"{len(d.assigned_record_ids)} records"
    return f"{d.role}: {detail}" if detail else d.role


def _entry(work: Path, d: Dispatch) -> dict[str, object]:
    return {
        "dispatch_id": d.dispatch_id,
        "role": d.role,
        "model": "small" if ROLE_SPECS[d.role].small else "strong",
        "description": _describe(d),
        "prompt_path": str(_prompt_path(work, d)),
    }


def _review_status(locations: Locations, review: Review) -> dict[str, object]:
    state = read_state(locations.state_path)
    work = _work_dir(locations, review.review_id)
    open_dispatches = [_entry(work, d) for d in review.dispatches if d.status == "open"]
    frozen, pending_inspect = _inspection(locations, review, state)
    deep = review.depth == "deep"
    status: dict[str, object] = {
        "review_id": review.review_id,
        "depth": review.depth,
        "models": review.models,
        "round": review.round,
        "plan_frozen": frozen,
        "open_dispatches": open_dispatches,
        "pending": {
            "inspect": pending_inspect,
            "consolidate": to_consolidate(review),
            "run": to_run(review),
            "challenge": to_challenge(review),
            "hunt": to_hunt(review),
            "refine": [d.dispatch_id for d in _for_keeper(review)] + [r.record_id for r in _records_for_keeper(review)]
            if deep
            else [],
            "rule": [r.record_id for r in _to_rule(review)],
            "check_forms": [f.model_dump() for f in _forms_pending(review, state)] if deep else [],
        },
        "candidates": [r.record_id for r in review.records if verdict(review, r) is None],
        "convergence": convergence(review, review.round),
    }
    status["next"] = _next_step(review, status)
    return status


def cmd_start_round(locations: Locations, args: argparse.Namespace) -> dict[str, object]:
    """Start the next round once the current one is finished."""
    work = _work_dir(locations, args.review)
    with updating_review(work) as review:
        if review.round > 1 and not any(d.round == review.round for d in review.dispatches):
            finished = convergence(review, review.round - 1)
            return {"round": review.round, "finished_round": finished, "already_started": True}
        _require_no_synthesizer(review)
        status = _review_status(locations, review)
        if review.depth == "standard":
            raise ReviewStateError(
                "a standard review does not start a round; run status --review <review_id> and follow its next field,"
                " or change the review with update-review --review <review_id> --depth deep"
            )
        if status["plan_frozen"]:
            raise ReviewStateError(
                f"the plan is frozen after round {review.round}, so a further round does not start;"
                " run status --review <review_id> and follow its next field"
            )
        if review.round >= MAX_ROUNDS:
            raise ReviewStateError(
                f"round {review.round} is the last round: a deep review inspects in at most {MAX_ROUNDS} rounds, and"
                " later reviews inspect the rest; run status --review <review_id> and follow its next field"
            )
        blockers = _unfinished(review, status)
        if blockers:
            raise ReviewStateError(
                f"round {review.round} is not finished: {json.dumps(blockers)};"
                " run status --review <review_id> and follow its next field"
            )
        finished = convergence(review, review.round)
        review.round += 1
    return {"round": review.round, "finished_round": finished, "already_started": False}


def cmd_rule(locations: Locations, args: argparse.Namespace) -> dict[str, object]:
    """Record the user's ruling on a disputed record."""
    work = _work_dir(locations, args.review)
    with updating_review(work) as review:
        rec = next((r for r in review.records if r.record_id == args.record_id), None)
        if rec is None:
            disputed = ", ".join(r.record_id for r in review.records if verdict(review, r) == "disputed") or "none"
            raise ReviewStateError(f"unknown record {args.record_id!r}; the disputed records: {disputed}")
        if rec.ruling is not None:
            if (rec.ruling.verdict, rec.ruling.reason) == (args.verdict, args.reason):
                return {"record_id": args.record_id, "verdict": rec.ruling.verdict, "already_ruled": True}
            raise ReviewStateError(
                f"{args.record_id} is already ruled {rec.ruling.verdict} ({rec.ruling.reason!r}); a ruling is not changed"
            )
        _require_no_synthesizer(review)
        if verdict(review, rec) != "disputed":
            raise ReviewStateError(f"{args.record_id} is not disputed (its verdict is {verdict(review, rec)!r})")
        if not args.reason.strip():
            raise ReviewStateError("--reason is empty; give the user's reason for the ruling in one sentence")
        rec.ruling = Ruling(verdict=args.verdict, reason=args.reason)
    return {"record_id": args.record_id, "verdict": rec.ruling.verdict, "already_ruled": False}


# --- review: synthesis -------------------------------------------------------------------


def _blocking(rec: Record, v: str | None) -> bool:
    claim = rec.claim
    return (
        v in ("confirmed", "upheld")
        and _priority(rec) in ("critical", "high")
        and claim.introduced != "pre-existing"
        and claim.reachable != "no"
    )


def _confidence(rec: Record, v: str | None) -> str:
    if v == "confirmed" and _wrong(_run_of(rec)):
        return "high"
    if v == "upheld" and rec.challenge is not None:
        return {"strong": "high", "moderate": "medium"}.get(rec.challenge.strength, "low")
    return "low"


def _drop_reason(rec: Record) -> str:
    if is_duplicate(rec):
        return f"duplicate of {rec.grouping.primary_id}"
    if rec.hunt is not None and not rec.hunt.expected_supported:
        return rec.hunt.reason
    if rec.ruling is not None:
        return f"user ruling: {rec.ruling.reason}"
    if rec.challenge is not None:
        return rec.challenge.argument
    run = _run_of(rec)
    return f"the probe's result matched the expected result: {run.output}" if run else ""


def _merge_readiness(review: Review, blocking: list[str]) -> str:
    """Return no when a finding blocks; unverified when a check did not run or the user proceeded past a failing one."""
    if blocking:
        return "no"
    if not review.checks or not all(c.passed for c in review.checks) or review.missing_previous_review:
        return "unverified"
    return "yes"


def _sections(review: Review) -> dict[str, list[dict[str, object]]]:
    by_dispatch = {d.dispatch_id: d.role for d in review.dispatches}
    found_by: dict[str, set[str]] = {r.record_id: {r.dispatch_id} for r in review.records}
    for r in review.records:
        if is_duplicate(r):
            found_by[r.grouping.primary_id].add(r.dispatch_id)
    sections: dict[str, list[dict[str, object]]] = {"findings": [], "disputed": [], "test_gaps": [], "dropped": []}
    for r in review.records:
        v = verdict(review, r)
        view = _record_view(review, r)
        if v in ("confirmed", "upheld"):
            view |= {
                "blocking": _blocking(r, v),
                "confidence": _confidence(r, v),
                "roles": sorted({by_dispatch.get(i, "previous review") for i in found_by[r.record_id]}),
                "corroborated": len(found_by[r.record_id]) > 1,
            }
            sections["findings"].append(view)
        elif v == "disputed":
            sections["disputed"].append(view)
        elif v == "test gap":
            sections["test_gaps"].append(view)
        else:
            sections["dropped"].append(
                {"record_id": r.record_id, "verdict": v, "site": r.claim.site, "reason": _drop_reason(r)}
            )
    return sections


def _require_ready(locations: Locations, review: Review) -> None:
    """Refuse synthesis while any work is unfinished or the forms checker has forms left."""
    status = _review_status(locations, review)
    blockers = _unfinished(review, status)
    for key in ("inspect", "check_forms"):
        if status["pending"][key]:
            blockers[key] = status["pending"][key]
    if blockers:
        raise ReviewStateError(
            f"not ready for synthesis: {json.dumps(blockers)}; run status --review <review_id> and follow its next field"
        )


def _inspections(review: Review, state: State | None) -> list[dict[str, object]]:
    """Return each finished inspection of this review with its partition's feature."""
    features = {} if state is None else {p.partition_id: p.feature for p in state.partitions}
    return [
        {
            "partition_id": d.partition_id,
            "feature": features.get(d.partition_id, ""),
            "reasons": d.reasons,
            "result": d.result,
            "proposed_split": d.proposed_split,
            "input_forms": [f.model_dump() for f in d.input_forms],
        }
        for d in review.dispatches
        if d.role == "inspector" and d.status == "done"
    ]


def synthesis_input(locations: Locations, review: Review, state: State | None) -> dict[str, object]:
    """Return the synthesizer's input: every record in its section, with blocking, confidence, and checks."""
    _require_ready(locations, review)
    sections = _sections(review)
    blocking = [v["record_id"] for v in sections["findings"] if v["blocking"]]
    merge_readiness = _merge_readiness(review, blocking)
    rounds = sorted({r.round for r in review.records} | {review.round})
    done = [d for d in review.dispatches if d.status == "done"]
    return {
        "review_id": review.review_id,
        "depth": review.depth,
        "scope": review.scope,
        "head": review.head,
        "branch": review.branch,
        "base": review.base,
        "date": _now(),
        "packet": review.packet.path,
        "spec_lens_ran": any(d.role == "spec-lens" for d in review.dispatches),
        "lens_summaries": [
            {"role": d.role, "component": d.component or None, "summary": d.summary}
            for d in done
            if ROLE_SPECS[d.role].lens and d.summary
        ],
        "list_changes": [c for d in done if d.role == "keeper" for c in d.changes],
        "review_critiques": [d.review_critique for d in done if d.role == "challenger" and d.review_critique],
        "merge_readiness": merge_readiness,
        "blocking_record_ids": blocking,
        "checks": [c.model_dump() for c in review.checks],
        "checks_reason": review.checks_reason,
        "updates": [u.model_dump() for u in review.updates],
        "missing_previous_review": review.missing_previous_review,
        "failure_modes": _failure_modes(review, reasons=True),
        **sections,
        "inspections": _inspections(review, state),
        "convergence": [convergence(review, n) for n in rounds],
        "previous_review": None if state is None else _previous_review(state, review.branch),
    }


# --- CLI ---------------------------------------------------------------------------------


def _add_value_flags(parser: argparse.ArgumentParser, *, starting: bool) -> None:
    """Add the flags for the values that fill the prompts.

    A flag left out is not a value: a new review takes the stored default for
    it, and update-review and a repeated start-review leave it alone.
    """
    parser.add_argument(
        "--depth",
        choices=DEPTHS,
        help="standard: lenses, test adversary, challenger; deep adds partitions, runners, hunters (default: standard)",
    )
    parser.add_argument("--intent", required=starting, help="What the change is for, and its constraints")
    parser.add_argument(
        "--how-to-run", required=starting, help="The test command, interpreter or build tool, and setup"
    )
    parser.add_argument("--feature-type", help="Security lens: the kind of feature (default: other)")
    parser.add_argument("--spec", help="Where the spec is (default: in the packet)")
    parser.add_argument("--flagged-claims", help="Claims an sdd-verify run flagged (default: none)")
    parser.add_argument("--domain-checks-file", help="Security lens: a file of domain checks")
    parser.add_argument("--architecture", choices=("yes", "no"), help="Add the quality lens's architecture section")
    parser.add_argument("--one-context", choices=("yes", "no"), help="The roles run in one context, no subagents")
    parser.add_argument("--models", help="The models the user chose for each class, such as 'strong: X; small: Y'")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--repo",
        default=None,
        help="Any directory inside the repository (default: the review's repository with --review, else .)",
    )
    common.add_argument(
        "--review-dir", type=Path, default=None, help="Use this review directory instead of resolving one"
    )
    scope = argparse.ArgumentParser(add_help=False)
    scope.add_argument(
        "--scope", required=True, choices=SCOPES, help="What the review covers: the index, HEAD, or the working tree"
    )
    review = argparse.ArgumentParser(add_help=False)
    review.add_argument("--review", required=True, help="The review_id start-review printed")

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser(
        "status", parents=[common], help="Partitions waiting for inspection; with --review, that review's next step"
    )
    status.add_argument("--scope", choices=SCOPES, default=None, help="What the review covers (default: the review's)")
    status.add_argument("--review", default=None, help="A review_id: add that review's pending work and next step")
    start = sub.add_parser("start-review", parents=[common, scope], help="Start a review from the packet JSON")
    start.add_argument("--packet-json", required=True, help="File holding build_review_packet.py's JSON output")
    start.add_argument(
        "--passed-checks", nargs="+", default=[], help="The check commands that passed before the review"
    )
    start.add_argument(
        "--failed-checks", nargs="+", default=[], help="The check commands that failed, which the user chose to pass"
    )
    start.add_argument(
        "--skipped-checks", nargs="+", default=[], help="The check commands that did not run, by the user's decision"
    )
    start.add_argument(
        "--reason", default="", help="With --failed-checks or --skipped-checks: the user's reason to review anyway"
    )
    _add_value_flags(start, starting=True)
    disp = sub.add_parser(
        "dispatch", parents=[common, review], help="Register one role's dispatch, or with no role the next step's"
    )
    disp.add_argument("role", nargs="?", default="", choices=("", *ROLES))
    disp.add_argument("--limit", type=int, default=8, help="No role: the most dispatches open at one time")
    disp.add_argument("--partition", default="", help="Inspector: the partition_id")
    disp.add_argument("--component", default="", help="List builder, quality lens: the component's name")
    disp.add_argument("--paths", nargs="+", default=[], help="List builder: the component's changed files")
    disp.add_argument("--failure-mode", default="", help="Hunter: the failure mode's name")
    disp.add_argument("--records", nargs="+", default=[], help="Runner or challenger: a subset of the waiting ids")
    disp.add_argument(
        "--report",
        default="",
        help="Synthesizer: the report file to write (default: code-review-<UTC date-time>-<scope>.md in the review dir)",
    )
    update = sub.add_parser(
        "update-review", parents=[common, review], help="Change the values that fill the roles' prompts"
    )
    _add_value_flags(update, starting=False)
    submit = sub.add_parser("submit", parents=[common, review], help="Validate and record a role's output file")
    submit.add_argument("dispatch_id", help="The dispatch id, such as D3")
    submit.add_argument("--output", default="", help="The output file (default: the dispatch's output path)")
    sub.add_parser("start-round", parents=[common, review], help="Start the next round")
    rule = sub.add_parser("rule", parents=[common, review], help="Record the user's ruling on a disputed record")
    rule.add_argument("record_id", help="The disputed record's id")
    rule.add_argument("--verdict", required=True, choices=("upheld", "refuted"))
    rule.add_argument("--reason", required=True, help="The user's reason, in one sentence")
    schema = sub.add_parser("schema", parents=[common], help="Print a role's output schema")
    schema.add_argument("role", choices=ROLES)
    return parser


COMMANDS = {
    "status": cmd_status,
    "start-review": cmd_start_review,
    "dispatch": cmd_dispatch,
    "submit": cmd_submit,
    "update-review": cmd_update_review,
    "start-round": cmd_start_round,
    "rule": cmd_rule,
    "schema": cmd_schema,
}


def _locations(args: argparse.Namespace) -> Locations | None:
    """Resolve locations; a command with --review and no --repo uses the review's own repository."""
    if args.command == "schema":
        return None
    locations = resolve_locations(Path(args.repo or "."), args.review_dir)
    review_id = getattr(args, "review", None)
    if review_id and args.repo is None:
        review = read_review(_work_dir(locations, review_id))
        return resolve_locations(Path(review.root), locations.review_dir)
    return locations


def main(argv: list[str] | None = None) -> int:
    """Run one command; print its JSON result on stdout."""
    args = build_parser().parse_args(argv)
    try:
        locations = _locations(args)
        result = COMMANDS[args.command](locations, args)
    except (ReviewStateError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
