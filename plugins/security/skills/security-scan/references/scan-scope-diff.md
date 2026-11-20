# Diff-Scoped Scan Mode

Use this reference when the scan target is a Git-backed change set: a pull request, commit, branch diff, or working-tree patch.
It defines the diff-specific target resolution, scope, discovery input, and sibling-coverage rules.
The shared pipeline (preflight → threat model → finding discovery → validation → attack-path analysis → report) and shared artifact paths (`scan-artifacts.md`) are unchanged; only scope and discovery input differ.

## Diff Target Resolution

Resolve the exact Git-backed diff before starting:

- PR: compare base branch against current `HEAD`
- commit: scan the target commit against its parent or requested baseline
- branch diff: scan the requested merge-base to head range
- local patch: scan staged and unstaged working-tree changes against the requested base

## Phase Scope

- Phase 1 (threat model generation) is repository-scope by default, unless the user explicitly asks for narrower scope or provides an authoritative threat model or sufficiently repository-specific guidance such as `AGENTS.md`.
- Phase 2 onward (finding discovery, validation, attack path analysis) are diff-focused and follow the changed code and its supporting files.

Treat this asymmetry as intentional:

- use the diff to locate the scan target for later phases
- do not let the diff bias Phase 1 threat model generation
- do not let the touched subsystem become the repository threat model unless the user explicitly asks for that narrower scope

## Diff-Scoped Discovery

Use `scan-artifacts-and-ledger.md` for the shared scoped file-review, candidate-ledger, subagent, and dedupe rules.

Diff scans should:

- generate `rank_input.jsonl` deterministically from changed source-like files with `<python_command> <plugin_dir>/scripts/generate_rank_input.py make-diff-rank-input --repo <repo_root> --base <base> --mode revisions --head <head> --out <artifacts_dir>/rank_input.jsonl` for PR, commit, and branch diffs, or `<python_command> <plugin_dir>/scripts/generate_rank_input.py make-diff-rank-input --repo <repo_root> --base <base> --mode local-patch --out <artifacts_dir>/rank_input.jsonl` for a local patch
- copy every diff row into `deep_review_input.jsonl` with `<python_command> <plugin_dir>/scripts/generate_rank_input.py copy-deep-review-input --rank-input <artifacts_dir>/rank_input.jsonl --out <artifacts_dir>/deep_review_input.jsonl`
- deep-review every file in `deep_review_input.jsonl`
- add directly supporting files only when repository evidence shows they are needed to understand the changed security behavior
- stay anchored to the changed code and directly supporting files rather than broadening into unrelated repository-wide enumeration

If discovery produces no technically plausible candidates, stop there, skip validation and attack-path analysis, complete the canonical JSON contract, and finalize the scan.

## Diff-Scoped Sibling Coverage

For PR, commit, branch, and local-patch scans, stay diff-focused but preserve repeated vulnerable instances that are created or affected by the same changed pattern.

Diff scans should:

- start from the changed files and the supporting files needed to understand the changed behavior
- expand from a changed route, handler, shared helper, guard, template pattern, query builder, serializer/deserializer, filesystem/network sink, config block, or wrapper to sibling instances that the diff also changes, newly reaches, or affects through the same modified shared dependency
- when the diff adds, removes, or reshapes a guard around an existing parser, deserializer, expression evaluator, filesystem/path helper, archive utility, or auth/authz helper, use the adjacent pre-existing sink/control as supporting context for the changed behavior; keep the candidate anchored to the changed guard or newly exposed path unless the user explicitly asks for wider instance expansion
- when a changed wrapper, guard, or API delegates to a shared parser/deserializer/path/archive/auth helper, keep both the wrapper call site and the underlying shared sink/control line addressable; do not replace the root sink/control evidence with wrapper-only evidence
- carry each vulnerable sibling instance through discovery and validation with its own affected location, source, closest control, sink, impact, and suppression evidence
- use unchanged siblings as context and negative controls, but report them only when the diff makes them newly vulnerable or changes the shared control or sink they depend on
- stop when the diff-linked pattern family is exhausted, rather than broadening into repository-wide enumeration

This keeps diff scans precise while avoiding the common failure mode where one representative route or sink hides additional vulnerable siblings introduced by the same patch.

## Diff-Mode Closure

- Goal completion for diff mode requires: every `deep_review_input.jsonl` row has a completion receipt in `work_ledger.jsonl` (or explicit `deferred`/`not_applicable`/`suppressed` closure with reason); every candidate that reached discovery has discovery, validation, and attack-path ledger receipts (or an explicit deferred reason); and the final markdown report has been written.
- Do not claim diff coverage until every `deep_review_input.jsonl` row has a completion receipt in `work_ledger.jsonl`.
- Commit scans use this same diff-mode contract because a commit is a diff-scan target type.
