# Calibrated examples

These examples come from one calibration session on a Python virtual file system.
Each shows the failure, the verdict, and the agreed rewrite.

## Long, but mostly contract: restructure

Before (26 lines): a search method whose paragraphs stated scope rules, cursor binding, result order, and per-page cost, followed by an underlined "Dispatch" section that described internal routing ("the built-in search over metadata", "the store's capability").

Verdict: keep the contract, give each fact its section, and replace the routing description with the outcomes a caller sees.

After:

```text
Return one page of search results in ``scope``, leaving out what the principal cannot read.

``scope`` names a directory, so ``"/src"`` searches ``/src/``.  ``recursive=False`` searches
only the files directly under it.  ``match_mode`` applies only to FULLTEXT: ``ALL`` requires
every term, ``ANY`` ranks files by any term.  A cursor works only with the same arguments.

Raises:
    ValueError: ``scope`` lacks a trailing slash and names a file the principal may read.
    ReindexRequiredError: a REGEX or FULLTEXT page covers a file the store's index has not caught up with.
    ReadBudgetExceededError: without a native index, a REGEX page read 10 files and none matched.
    SearchTypeUnsupportedError: FULLTEXT on a store without a native index.

Notes:
    GLOB and FIND return paths in path order and read no file content.  REGEX returns matches
    in ``grep -r`` order; FULLTEXT returns files by descending rank.  A page's cost follows the
    page size, not the size of ``scope``.

See also:
    iter_search: consume every page.
    paging: how pages and cursors work.
```

Lesson: the first draft said the budget error fires "past 10 files".
The code raises it only when 10 files hold no match.
Verify every condition against the code.

## Short, but too dense: restructure

Before (11 lines): one paragraph that packed the return types, a trailing-slash rule, a permission rule with three conditions and an exception, trash behavior, and root behavior.

After:

```text
Return what is at ``path``: a file's ``FileStat``, a ``DirectoryEntry``, or ``None`` when nothing is there.

Unlike ``stat``, absence is ``None``, not an error, so use this to probe a path.  Without a
trailing ``/``, a file at ``path`` wins over a directory of the same name; with one, only a
directory is reported.  A deleted file counts as nothing.

Raises:
    ValueError: ``path`` is not canonical.
    PermissionDeniedError: ``path`` has no trailing ``/`` and the principal may read neither a file nor a directory there.

Notes:
    A directory is reported only when the principal may read a live file beneath it.

See also:
    stat: report a file, raising ``NotFoundError`` when there is none.
```

## Rationale in a docstring: move or delete

Before: a sandbox `write` helper whose docstring explained that it returns a dict because the interpreter cannot convert the model, and justified its size check.

After:

```text
write: write ``data`` to ``path``; return ``{"version_number", "size", "error"}``.

When ``data`` exceeds ``resource_limits.max_write_bytes``, write nothing and return
``error="oversized_write"`` with ``version_number`` None.
```

The dict explanation moves to a comment on the `return`, because a maintainer would otherwise return the model and break the sandbox.
The justification of the size check is deleted.

## A module page as orientation

Before (41 lines): underlined "Architecture", "VFS error unwrapping", and a limits mapping table, all internals.

After:

```text
Monty: run sandboxed Python over the VFS.

``vfs.execute(code, ..., provider_name="monty")`` runs ``code`` in pydantic-monty, a sandboxed
Python interpreter.  The code reads and writes VFS files with ``open``, ``pathlib``, and ``os``,
and can call the shell verbs (``ls``, ``cat``, ``grep``, and others) as functions.  Each file
operation runs on behalf of the calling principal, with that principal's permissions, and a
write creates a version.  The code cannot reach the host filesystem.

To use this provider, install the ``monty`` extra: ``pip install 'ai-vfs[monty]'``.

Notes:
    Monty enforces ``ResourceLimits.timeout_seconds`` and ``max_memory_bytes``.  The VFS enforces
    the operation budget and the read, write, and result-count limits.  A VFS error inside the
    code ends the run, and ``error_type`` names it (for example ``"permission_denied"``).

See also:
    VFS.execute: run code with a provider.
    just_bash_provider: run Bash over the VFS instead.
```

## A landing page

Before: "Virtual file system orchestrator."

After: the class that is the package's entry point explains the model a reader needs first, leaves call conventions to the method pages, warns about the first surprise, and shows a minimal setup.

```text
A versioned file system for AI agents, with permissions on every call, stored in a database and a blob store.

Each file lives in a namespace at an absolute path, such as ``/docs/a.md``.  Each call names a
principal, and the VFS checks that principal's grants: a grant gives operations (``read``,
``write``, ``delete``, ``execute``, or ``admin``) on a path prefix.  Each write creates a version;
earlier versions stay readable, and :meth:`rollback` restores one.

A :class:`Session` holds a namespace, a principal, and a working directory, for code that works in
one place.  Configure the stores with :class:`VFSConfig`.  Call :meth:`initialize` before the first
operation and :meth:`close` when done.

Notes:
    The ``admin`` operation lets a principal manage grants, not use files.  An admin that reads or
    writes files needs a grant that includes those operations.

Examples:
    (a minimal setup: configure, initialize, create a namespace and principal, grant, write, close)
```
