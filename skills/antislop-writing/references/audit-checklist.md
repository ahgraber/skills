# Audit checklist

Run this in the audit pass, after a draft exists, reading as an editor who did not write it.
These checks operate at the word, sentence, and paragraph level; the structural work (spine, claims outline, fragment stacks, headings) belongs to the compose pass and its gate, and the tell catalog is `ai-tells.md`.
The output of an audit is named changes, not a pass/fail feeling.

## Diction (word choice)

- **Prefer plain words**: familiar words over ornate synonyms — "use," not "utilize."
  The test is precision lost, not syllable count: the AI-vocabulary tell is a fancy word vaguer than the plain one; a rare word that is the most exact word for the meaning stays, especially in a human-authored draft where it was chosen on purpose.
- **Be specific**: replace vague adjectives with facts, numbers, or examples.
- **Use is/are/has when accurate**: avoid "serves as," "stands as," "represents," "boasts."
- **Use concrete verbs**: dissolve nominalizations, so "implementation of improvements" becomes "we improved X."
- **Cut empty intensifiers**: "very," "highly," "extremely," unless load-bearing.
- **Reuse the exact term**: do not cycle synonyms for one thing; repetition beats elegant variation when it aids clarity.
- **Choose neutral reporting verbs**: "said" is neutral, while "claimed," "admitted," "revealed," and "insisted" import doubt, fault, concealment, or stubbornness — use them only where that reading is the point.
- **Cut decorative figuration**: a vivid word swapped for a plain one that carries the same meaning ("shape" for structure, "rung" for level) is ornament, not precision, and one instance is enough to fix — but a figure that genuinely clarifies stays, even in technical prose.
  The test is whether the image does work the plain word cannot (see "Dead metaphor" in `ai-tells.md`).

## Syntax (sentences)

- **Prefer the active voice**: passive when the actor is unknown or irrelevant, or when it keeps the topic in subject position (see "Old before new" under Cohesion).
- **Keep sentences lean**: cut filler, hedging, and throat-clearing.
- **Emphasize by position**: put the most important words at the end.
- **Keep parallel structure**: align lists and paired clauses grammatically.
- **Avoid dangling modifiers; keep subject and verb close**: no long interruptions between them.
- **Vary sentence length**: mix lengths and let a short sentence land — except in instructions, where short and uniform is the genre's shape.
- **Lead an instruction with its condition**: "if the build fails, run X," so the reader learns the gate before the imperative.
- **Name the actor; do not let an abstraction or the text act**: rewrite "verification licenses the edit" or "the data demands a rethink" to name who does the work — the writer, the reader, you, the system.
- **Rewrite a maxim as an instruction**: in explanatory or instructional prose, a line that could be an epigraph ("Refactor changes the shape of working code and nothing else") should state the directive it stands for; editorial writing may earn one.

## Cohesion (local flow)

- **Old before new**: open a sentence with known information; close it with what is new.
- **One idea per paragraph**: open with a topic sentence.
- **Connect by topic, not filler**: link sentences through shared subjects, not "it's worth noting."

## Mechanics

- **Comma before a coordinating conjunction** joining two independent clauses; no comma splices.
- **Oxford comma** in a series of three or more.
- **Possessive singular with 's,** including names ending in s.
- **Straight quotes, sentence-case headings, no emoji.**
- **Fragments only for deliberate emphasis.**
- **Match the document's existing conventions**: spelling dialect, date format, and terminology follow the draft you were handed — do not Americanize a British document.
  The scope is those three: the fixed rules above still apply, so a draft's dropped serial commas or curly quotes are corrections to make, not conventions to keep.
