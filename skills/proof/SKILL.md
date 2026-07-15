---
name: proof
description: |-
  Use when the user asks for proofreading or light copy editing while preserving original wording, tone, and order. Triggers: 'proofread', 'fix typos', 'grammar only', 'copy edit only', 'SPAG pass'. Not for rewrites, tone shifts, structural edits, or style upgrades; use antislop-writing for those requests.
---

# Proof

Proofread and lightly copy edit text while preserving wording, order, tone, and meaning.

## Invocation Notice

- Inform the user when this skill is being invoked by name: `proof`.

## Critical Constraints

- Apply only spelling, punctuation, capitalization, agreement, and minor grammar fixes.
- Do not rewrite, rephrase, reorder, add content, or change tone.
- If a fix requires substantive rewriting for clarity or logic, leave the source text unchanged and flag it with a suggested revision.
- Preserve author voice, formatting, and regional conventions unless the user asks otherwise.
- Edits to a file (rather than to text pasted into the user's message) must land in the file via available file-editing tools.
  Never reply with the corrected file contents inline as a substitute for editing the file.

## Routing: `proof` vs `antislop-writing`

Use `proof` when the request is about correctness without stylistic change.

- "proofread this"
- "fix typos/grammar only"
- "copy edit lightly"
- "do not rewrite"

Use `antislop-writing` when the request asks for writing-quality changes or substantial edits.

- Rewrite, tighten, polish, or improve flow/clarity.
- Adjust tone for audience (more formal, friendlier, firmer).
- Restructure paragraphs, argument order, or narrative arc.
- Significantly shorten or expand content.

If intent is ambiguous:

1. Start with a proof-only pass.
2. Flag issues that need substantive rewriting.
3. Ask whether to proceed with a `antislop-writing` rewrite.

## Target Selection

Before editing, identify what to proofread, in this order:

1. Inline text included in the user's message → reply with revised text in chat.
2. Explicit file path or filename ("proofread TODO.md") → edit the file in place.
3. No explicit target, but IDE context is attached:
   - `<ide_selection>` tag with content → treat the selection as the target.
     If the selection is from a file, edit the file at those lines; otherwise reply inline.
   - Else `<ide_opened_file>` tag is present → treat the opened file as the target.
     State the inferred file in your first message (e.g., "Proofreading TODO.md — the file open in your IDE.") and proceed.
4. None of the above → ask what to proofread before editing anything.

## Workflow

1. Read the full text once to preserve meaning and tone.
2. Apply mechanical fixes only: spelling, punctuation, capitalization, subject-verb agreement, pronouns/articles/prepositions, and obvious minor grammar.
3. Apply organization agreement consistently:
   - Use plural verbs when referring to actions by people within the organization (example: "OpenAI are developing new models").
   - Use singular verbs when referring to the organization as a legal entity, owner, or brand (example: "OpenAI is valued at billions").
4. Identify major unresolved issues (clarity gaps, logical breaks, grammar that cannot be fixed without rewriting) and do not apply those edits directly.
5. Add a short flagged-issues section when major issues remain.

## Output

- File target: modify the file in place, then reply with a brief summary naming the file edited and either `No major rewrite-needed issues found.` or a `Flagged issues` list.
- Inline text target: reply with revised text first, then either `No major rewrite-needed issues found.` or a `Flagged issues` list.
- `Flagged issues` format: original snippet, reason it was not directly edited, and suggested revision.
