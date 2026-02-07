# Handoff Template

Use this exact structure for chat output.
Assume the receiver can only see this handoff and nothing else.

```md
## Handoff: [Short topic]

- Date: YYYY-MM-DD
- Project/Repo: [name]
- Goal: [what success looks like]

### Current State

- Status: [in progress | blocked | ready for handoff]
- Completed:
  - [concrete completed item]
- Pending:
  - [concrete pending item]

### Decisions and Rationale

- [Decision]: [Reason, tradeoff, or constraint]

### Changes Made

- Files touched:
  - `[path/to/file]`: [what changed and why]
- Commits/PRs:
  - `[hash-or-link]`: [summary]
- Commands run:
  - `[command]` -> [important result]

### Validation

- Checks run:
  - `[test/lint/check]`: [pass/fail + key detail]
- Not run:
  - [what was skipped and why]

### Blockers and Risks

- Blockers:
  - [blocker + owner/dependency + impact]
- Risks:
  - [risk + likely impact + mitigation]

### Next Steps (ordered)

1. [first action to execute now]
2. [second action]
3. [third action or follow-up]

### Open Questions

- [question + information needed to resolve]

### Startup Prompt for Next Conversation

Continue this work using only this handoff.
Assume no access to prior chat history.
Start with: [first action from Next Steps].
```
