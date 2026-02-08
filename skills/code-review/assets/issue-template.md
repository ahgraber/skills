# Issue Template

Use this template when raising specific issues during a code review.

## Issue Type Legend

| Emoji | Label                     |
| ----- | ------------------------- |
| 🔧    | Change request            |
| ♻️    | Refactor suggestion       |
| ❓    | Question                  |
| ⛏     | Nitpick                   |
| 💭    | Concern / thought process |
| 🌱    | Future consideration      |

## Issue Priority Legend

| Emoji | Priority |
| ----- | -------- |
| ‼️    | Critical |
| 🔴    | High     |
| 🟡    | Medium   |
| 🟢    | Low      |

## Blocking Decision

- `Blocking: yes` means this should be addressed before merge.
- `Blocking: no` means this is advisory or follow-up work.

## Suggestion Format

```md
## [priority emoji] [type emoji] Summary of the issue

- Type: [type label (text)]
- Priority: [priority label (text)]
- Blocking: [yes/no]
- Confidence: [high/medium/low]
- File: [path/to/file.ext]
- Details: [Explanation of the issue and why it matters]
- Evidence: [risk path, failing scenario, policy reference, or repro steps]
- Example / Suggested Change (if applicable):
  [code change in markdown code block or diff block]
- Impact: What improves if this is addressed
```

## Guidance

- Always include file paths.
- Sort suggestions by priority: critical, high, medium, low.
- Use blocking=yes only for correctness, reliability, security, or clear policy/style violations.
- Use confidence labels to separate hard defects from lower-confidence concerns.
- Use nitpicks sparingly; mark them clearly.
