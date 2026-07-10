# Output formats

The artifact ships in one of two formats.
**HTML is the default** because it is self-contained, needs no external service or account, and works offline.
Choose Markdown when the user asks or the context calls for it.

| Format       | Use when                                                        | Requires                  |
| ------------ | --------------------------------------------------------------- | ------------------------- |
| **HTML**     | Default. A durable, portable, offline artifact.                 | Nothing beyond a browser. |
| **Markdown** | Committing to a docs/wiki, or when a browser is not the target. | Nothing.                  |

## Shared conventions (both formats)

- **Dated filename, outside the repo.**
  Name the file starting with today's date, `YYYY-MM-DD-explanation-<slug>.<ext>`, and save it _outside the code repository_ so it stays out of version control and sorts by date.
- **Four sections in order:** Background → Intuition → Code → Quiz.
- **Kleppmann-style prose:** engaging, classic style, smooth transitions between sections.
- **Diagram families:** pick a small number of reusable diagram types and reuse them.
  Two that recur usefully:
  - a _simplified UI view_ — a stripped-down picture of what the user sees, for explaining UI-facing changes;
  - a _system / data-flow diagram_ — components and the data moving between them, **with concrete example data shown on the wires**.
    Never use ASCII-art diagrams — embed them per each format's contract below.
- **Callouts** for key concepts, definitions, and important edge cases.

## HTML contract

- A **single self-contained `.html` file** with inline `<style>` and `<script>` — no external assets or CDN links, so it works offline and survives being moved.
  "Self-contained" is a rule about _runtime fetches_, not about authoring: you may build a diagram in any tool, then inline its output (SVG/CSS/JS) rather than linking to it.
- **One long page** with section headers and a **table of contents** at the top.
  Do _not_ use top-level tabs for structure (breaks linear reading and printing).
- **Basic responsive styling** so it reads on a phone.
- **Code blocks:** use `<pre>`.
  If you style a `div` instead, its CSS **must** include `white-space: pre` or `white-space: pre-wrap`, or the browser collapses every newline into one line.
  **Before saving, scan every code block in the source and confirm the whitespace CSS is present.**
- **Diagrams:** Build the diagram in whatever tool renders it best for the change at hand — CSS boxes-and-arrows, an exported Graphviz/Mermaid figure, etc. — the technique is yours to choose.
  Embed the result inline so the finished file displays with zero network fetches at view time: paste the SVG or markup directly, never link a CDN, font, or asset a reader would have to load.
  Skip ASCII art.
  Label every node and edge, size text to stay readable at normal zoom, and stamp concrete example values on the wires and nodes (a real request body, an actual id, a sample payload) so the reader traces the change with data rather than placeholders.
  Settle on a small vocabulary of diagram types and reuse them throughout the artifact instead of drawing each figure in a new style.
  When two approaches would render the same, take the lighter embedded one; reserve a live JS renderer for figures that genuinely need interaction.
- **Interactive data-flow / contracts** (when the change has a pipeline or transformation sequence): render the flow diagram (per the diagram guidance above), then add a small interactive stepper — clicking a stage reveals the **real input and output** at that boundary and its **shape/contract** (type, schema, or example payload).
  Vanilla JS toggling pre-rendered panels; the reader steps through the transformation and sees each shape, rather than reading that it changes.
- **Interactive quiz:** clicking an option reveals correct/incorrect state and the per-option explanation (a few lines of vanilla JS; no framework).
  Keep the correct-answer key out of trivially-scrapable inline text where reasonable, but do not over-engineer.

## Markdown contract

- A single `.md` file.
  Headings for sections, fenced code blocks for code, blockquotes for callouts.

- **Quiz interactivity via collapsible `<details>`** — one per option (GitHub/most renderers support it):

  ```markdown
  **1.**
  **Question text**

  <details><summary>Option A</summary>❌ Why A is wrong</details>
  <details><summary>Option B</summary>✅ Why B is correct</details>
  ```

- Diagrams: prefer a fenced Mermaid block (compose with the `mermaid` skill) over ASCII; include example data in the diagram.

- Data-flow / contracts: pair the Mermaid flow diagram with a before/after table or per-stage `<details>` blocks showing each stage's real input, real output, and shape/contract — Markdown cannot animate, so make the shapes visible statically.
