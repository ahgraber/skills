# Issue Template

Write each issue of a code review in this format.

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

## Suggestion Format

```md
## [priority emoji] [type emoji] Summary of the issue

- Type: [type label (text)]
- Priority: [priority label (text)]
- Blocking: [yes/no]
- Confidence: [high/medium/low]
- File: [path/to/file.ext]
- Details: [the issue and why it matters]
- Evidence: [risk path, failing scenario, policy reference, or repro steps]
- Example / Suggested Change (if applicable):
  [code change in markdown code block or diff block]
- Impact: [what improves if this is addressed]
```

## Guidance

- `Blocking: yes` means the issue should be addressed before merge; `Blocking: no` means it is advisory or follow-up work.
- Use confidence labels to separate hard defects from lower-confidence concerns.
- Always include file paths.
- Sort issues by priority: critical, high, medium, low.
- Use nitpicks sparingly, and mark them clearly.
