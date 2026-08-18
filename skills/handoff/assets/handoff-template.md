# Handoff Template

Use this exact structure for chat output.
Assume the receiver can only see this handoff and nothing else.
Sections marked `(repo-only)` apply to repository work; omit them when no repository is involved or repo state is irrelevant.
Sections marked `(only-if-established)` record only what the session actually produced; omit them rather than invent content.
Markers like `(repo-only)` and `(only-if-established)` are template annotations — do not include them in the output.
Write `None` in a section that has no items; write `Unknown` only when the information is missing.
Keep command results on one line with inline code; do not nest fenced code blocks inside the outer fence.

```md
## Handoff: [Short topic]

- Date: YYYY-MM-DD
- Context: [project, repo, document, or topic]
- Goal: [what success looks like]

### Current State

- Status: [in progress | blocked | ready for handoff]
- Repo (repo-only): [branch] @ [short-hash]; [clean | uncommitted changes in path/a, path/b]
- Completed:
  - [concrete completed item]
- Pending:
  - [concrete pending item]

### Decisions and Rationale

- [Decision]: [Reason, tradeoff, or constraint]

### References (only-if-established)

- `[path, URL, or artifact]`: [what it holds + why the recipient needs it]

### Changes Made (repo-only)

- Files touched:
  - `[path/to/file]`: [what changed and why]
- Commits/PRs:
  - `[hash-or-link]`: [summary]
- Commands run:
  - `[command]` -> [important result]

### Validation (repo-only)

- Checks run:
  - `[test/lint/check]`: [pass/fail + key detail]
- Not run:
  - [what was skipped and why]

### Blockers and Risks

- Blockers:
  - [blocker + owner/dependency + impact]
- Risks:
  - [risk + likely impact + mitigation]

### Continuation (only-if-established)

1. [direction the user gave, or the remainder of requested work — executable now]
2. [second established item]

### Open Questions (only-if-established)

- [question actually raised in the session + information needed to resolve]

### Startup Prompt for Next Conversation

Continue this work using only this handoff.
Assume no access to prior chat history.
Start with: [first Continuation item | "read Current State and confirm direction with the user"].
```
