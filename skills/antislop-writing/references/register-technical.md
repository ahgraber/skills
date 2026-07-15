# Technical register

Apply alongside the core directives when the piece is technical: a design doc, RFC or ADR, API reference, tutorial, how-to, runbook, engineering explainer, or README.
The core still governs every sentence — point first, active voice, concrete verbs, lean sentences, claim-bearing headings, no engineered symmetry or AI tells.
This module lists only where technical writing diverges, plus the shapes the common genres take.

## The target

Prose an engineer would trust and act on: a well-edited design doc, a clean man page, a reference like the Stripe or Kubernetes docs, a readable RFC.
It is precise and unadorned.
It is not a tutorial-flavored blog post, a marketing page for a library, or a wall of narrated bullets.
Correctness is part of the register: a graceful sentence that is wrong fails.

## Pick the mode before the words

Technical documents serve four distinct jobs; a section that mixes them serves none (the Diátaxis split):

- **Tutorial** — teach a beginner by doing; one happy path, no digressions or alternatives.
- **How-to** — get a competent reader through one task; stated preconditions, numbered steps, a verified result.
- **Reference** — answer a lookup; exhaustive, consistent, structured, no narrative.
- **Explanation** — build understanding; prose, rationale, tradeoffs, context.

Decide which job a section does, and cut whatever belongs to another.

## Deltas from the core

Whether content becomes a table or a paragraph depends on its shape, not on the document being "technical."
Genuine lookup material — parameters, flags, config keys, fields, error codes, return values, and comparison matrices — is one fixed field-set repeated across entries, and it belongs in tables or definition lists; commands, code, and output belong in fenced blocks; ordered procedures belong in numbered steps.
Everything else is sentences, here more than anywhere.
A per-item description in a survey or design doc — what a component is, how it works, why its design matters — is explanation, not reference, even under its own heading, and it is written as flowing prose.
Apply the row test from the core: could this content be a row whose columns fit every sibling entry?
If not, it is narration; restore the verbs.
And the surface pass still runs here — no technical document legitimizes emoji, decorative arrows, bold-first bullets, or em-dash pile-ups.

Precision beats elegance, so name each thing the same way every time; elegant variation ("the endpoint," "the route," "the handler" for one thing) is a defect here, not a virtue.
Where behavior is a contract — specs, RFCs, protocol docs — the normative keywords MUST, SHOULD, and MAY (RFC 2119) carry real weight; use them deliberately, and keep them out of tutorials and explanations.

Every example is correct, runnable, and shows its output: snippets copy-paste and produce what you claim, pinned to a version where behavior depends on it, and they show the error path, not only the happy one.
A plausible example that does not run is worse than none.
Claims are verifiable and version-scoped — if a claim depends on a version, name it, and if you cannot verify it, mark it rather than assert it.

State prerequisites and scope up front, then disclose progressively: say what the reader must already have and know, and introduce each concept before the one that depends on it.
Passive voice is legitimate when the system is the actor ("the request is retried three times"); keep the active voice for what the reader does ("run `x`," "set `FOO`").
Close a section by pointing forward — the next task, the related reference, the failure to watch for — not on a flourish like "and that is the power of X."

## Common shapes

- **Design doc / RFC / ADR** — context and problem; goals and explicit non-goals; the decision; alternatives considered and why rejected; risks and open questions.
  Lead with the decision, not the history.
- **Tutorial** — prerequisites; a single end-to-end path; each step's command and its expected output; a working result at the end.
  No branches.
- **How-to** — the task and when to use it; preconditions; numbered steps; the end state and how to verify it.
- **Reference** — one entry per item, the same fields in the same order every time (name, signature, parameters, returns, errors, example).
  Alphabetical or grouped, never narrative.
- **README** — what it is in one line; install; a minimal working example; where to go next.
  The example runs.

## Worked example

Fragment-stack slop — a heading over verbless fragments describing one thing:

> #### filestash
>
> A self-hosted file-management platform and universal data-access layer. 13.9k stars. Go backend, vanilla-JS frontend.

Prose — subject-first sentences carrying the same facts:

> #### filestash
>
> Filestash is a self-hosted file-management platform and universal data-access layer with 13.9k GitHub stars, built with a Go backend and a vanilla-JavaScript frontend.
> Its core `IBackend` interface is deliberately small: any storage that implements `Ls`, `Stat`, `Cat`, `Mkdir`, `Rm`, `Mv`, and `Save` becomes a first-class backend.

Genuine lookup stays a table — N entries against the same columns:

> | Implementation | Runtime  | Read/write | Maturity |
> | -------------- | -------- | ---------- | -------- |
> | wasi-common    | Wasmtime | Read-write | Mature   |
> | fsspec memory  | CPython  | Read-write | Mature   |
