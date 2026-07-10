---
name: explain-diff
description: |-
  Use when the user wants a rich, interactive explanation of a code change — a diff, branch, commit, staged changes, or PR — as a standalone artifact rather than a quick answer in chat. Produces a dated, self-contained HTML (default) or Markdown artifact the reader can revisit and quiz themselves against, so understanding sticks instead of evaporating after one read. Triggers: "explain this diff/PR/branch", "walk me through this change", "make an interactive explanation of this commit", "help me/my team understand this PR", "onboarding doc for this change", "teach me what changed". Not for: a quick one-line summary of a diff (just answer), writing a commit message (use commit-message), or reviewing code for defects (use code-review).
---

# Explain Diff

Turn a code change into a rich, interactive learning artifact — not a passive summary.
The reader gets oriented, builds intuition, walks the code, then actively checks their understanding with a quiz.
The design is grounded in learning science; the principles are named inline where they apply, and citations are in `ATTRIBUTION.md`.

Adapted from Geoffrey Litt's `explain-diff` prompts (see `ATTRIBUTION.md`).

## Invocation Notice

- Inform the user when this skill is being invoked by name: `explain-diff`.

## When to Use

- The user wants to understand, or help others understand, a specific code change deeply — not just skim it.
- Onboarding, knowledge transfer, teaching, or a design/PR write-up where the reader will engage, not just read.
- The reader's prior knowledge is unknown, so the explanation must serve both a novice and someone already familiar.
- The user wants a durable, shareable artifact (a page or file) rather than an answer in the chat.

## When Not to Use

- A quick "what does this diff do?"
  — just answer inline; the full artifact is overkill.
- Writing the commit message for the change — use `commit-message`.
- Reviewing the change for bugs, security, or style — use `code-review` or `securing-code`.
- Explaining a whole codebase or writing sustained library docs — use `scaffold-docs`.

## Workflow

1. **Resolve the change.**
   Determine the exact diff to explain: staged changes, a commit or range (`git diff <range>`), a branch vs. its base, or a PR.
   If ambiguous, ask which.
   Read the full diff.
2. **Explore the surrounding code — broadly.**
   The diff alone is not enough context.
   Read the files it touches and their neighbors, callers, and callees so the Background is accurate.
   This exploration is load-bearing; a shallow read produces a shallow explanation.
3. **Choose the output format.**
   HTML is the default (self-contained, no dependencies, works offline).
   Use Markdown as a universal fallback — for committing to a docs/wiki, or when a browser is not the target.
   See `references/output-formats.md`.
4. **Draft the four sections** — Background, Intuition, Code, Quiz — following the Section Guide below.
   Write the prose with the clarity and flow of Martin Kleppmann: engaging, classic style, smooth transitions between sections.
5. **Build the quiz** following `references/quiz-design.md`.
   This is where the artifact becomes interactive and where quality most often slips — do not skip the item-writing rules.
6. **Save and deliver.**
   Write the artifact to a location **outside the code repository** (so it stays out of version control), with a filename starting with today's date in `YYYY-MM-DD-` format for time-sorting, e.g. `YYYY-MM-DD-explanation-<slug>.html`.
   Return the path.
   For HTML, before saving, verify every code block's CSS uses `white-space: pre` or `pre-wrap` (see Format Rules).

## Section Guide

Each section maps to a learning-science principle, named inline below; citations in `ATTRIBUTION.md`.

- **Background** — Orient the reader in the existing system this change touches (activate prior knowledge before introducing the new).
  Provide **two layers**: a _deep background for beginners_, explicitly marked as skippable, and a _narrow background_ directly relevant to the change.
  The split is deliberate: deep scaffolding helps novices but bores or hinders experts (expertise-reversal effect), so make the beginner layer easy to bypass.
- **Intuition** — Convey the _essence_ of the change, not the full detail.
  Lead with a **concrete toy example** with example data, then generalize (concreteness fading).
  Use figures and diagrams liberally — pair every idea with a visual, since words plus pictures beat words alone.
  - **Data flow / transformations.**
    When the change is a pipeline or transformation sequence, show a **flow diagram** _and_ make the **input/output shape/contract visible at each stage** — borrowing `interactive-notebook-demo`'s prove-with-real-data discipline (show the shape, don't assert it).
    Mechanics per format in `references/output-formats.md`.
- **Code** — A high-level walkthrough of the actual changes.
  **Group and order** the changes so related edits are chunked together and introduced in a sensible sequence, rather than dumped file-by-file.
  Label each group with its _purpose_ so the reader sees intent, not just lines.
- **Quiz** — Five interactive multiple-choice questions the reader answers, each with immediate feedback explaining why every option is right or wrong.
  This is retrieval practice, the single highest-leverage part of the artifact.
  Aim for medium difficulty — questions that require understanding the substance of the change, not recall gotchas.
  Full construction rules and the distractor pitfalls in `references/quiz-design.md`.

## Format Rules

Full detail per output format is in `references/output-formats.md`.
The items most easily missed:

- **Diagrams.**
  Never ASCII; embed inline so the file renders offline; put real example values on the nodes and wires; reuse a few diagram types.
  Rendering technique is yours per figure.
- **HTML code blocks.**
  Use `<pre>`, or a `div` whose CSS includes `white-space: pre` / `pre-wrap` — otherwise the browser collapses newlines.
  Scan every block before saving.
- **Quiz interactivity is required.**
  HTML: clicking an option reveals correct/incorrect plus feedback.
  Markdown: collapsible `<details>` per option.
- **Callouts** for key concepts, definitions, and important edge cases.

## Output

A single dated artifact (HTML file by default, or Markdown file) saved outside the repo, containing Background → Intuition → Code → interactive Quiz, written with Kleppmann-style clarity.
Return its path.

## Related Skills

- **code-review** — reviewing the change for defects rather than explaining it.
- **commit-message** — writing the Conventional Commit message for the change.
- **interactive-notebook-demo** — when the change is best understood by _running_ it: build a hands-on demo notebook the reader executes and pokes at, instead of (or alongside) a read-only explanation.
  Its prove-with-real-data pattern also informs the data-flow guidance.
- **mermaid** — when Mermaid is the most effective way to render a given diagram (idiomatic for Markdown output; export to inline SVG for HTML).

## References

- `references/quiz-design.md` — quiz construction: retrieval-practice rationale, feedback rules, difficulty calibration, and the multiple-choice item-writing flaws to avoid.
- `references/output-formats.md` — HTML and Markdown output contracts, diagram families, and the dated-file convention.
- `ATTRIBUTION.md` — source prompt credit and the full research bibliography.
