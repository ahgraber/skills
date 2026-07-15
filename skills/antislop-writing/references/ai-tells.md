# AI Writing Tells

A single de-duplicated catalog of the patterns that mark text as machine-generated.
Every tell is a symptom of one reflex: engineered symmetry and promotional polish, the default voice a model reaches for when left alone.
Entries are organized by linguistic level and tagged by how to fix them.

- **[strip]** — a surface tic removable without touching meaning (a token, a mark, a formatting habit).
  A checklist or find-replace pass handles it.
- **[rewrite]** — a structural or rhetorical reflex that encodes a move, not a token.
  You cannot find-replace it; return to what the passage is actually asserting and re-draft.

Stripping tics while the reflex still runs is a losing game: surface-laundered text — em-dashes and "delve" removed — still reads as machine-made, because the structure is the signal.
Fix the [rewrite] tells first; the [strip] pass is cleanup.

Any one of these used once may be fine.
The tell is density: several together in a stretch, or one repeated down the page.

## Contents

1. [Lexical](#1-lexical-word-choice) — word and phrase choice
2. [Syntactic](#2-syntactic-sentence-patterns) — sentence-level constructions
3. [Discourse and structure](#3-discourse-and-structure) — paragraph and document shape
4. [Rhetorical stance](#4-rhetorical-stance-the-ai-voice) — the "AI voice" and its posture toward the reader
5. [Formatting and markup](#5-formatting-and-markup) — marks, decoration, artifacts

---

## 1. Lexical (word choice)

Mostly \[strip\]: swap the word, keep the sentence.
Watch for clusters — one "leverage" is noise, five style-words in a paragraph is the fingerprint.

### Magic adverbs — [strip]

Adverbs that inflate a mundane observation into false significance: "quietly," "deeply," "fundamentally," "remarkably," "arguably."
Avoid: "quietly orchestrating workflows," "the one that quietly suffocates everything else."
Fix: delete the adverb, or state the significance with a fact.

### "Delve" and the AI vocabulary — [strip]

A family of over-reached words: delve, utilize, leverage (verb), robust, streamline, harness, certainly, additionally, moreover.
Empirically the strongest lexical signal — the post-2023 shift in published prose is a shift in style words, not content.
Avoid: "Let's delve into the details," "leverage these robust frameworks."
Fix: plainer word or omit — "look at," "use."

### "Tapestry," "landscape," and ornate nouns — [strip]

Grandiose nouns where a plain one would do: tapestry (anything interconnected), landscape (any field), plus paradigm, synergy, ecosystem, realm, interplay.
Avoid: "the rich tapestry of human experience," "navigating the complex landscape of modern AI."
Fix: name the actual thing.

### Copula avoidance ("serves as") — [strip]

Replacing "is/are/has" with pompous alternatives — serves as, stands as, marks, represents, features, boasts.
The repetition penalty pushes models off the plain copula toward fancier verbs.
Avoid: "The building serves as a reminder of the city's heritage."
Fix: use is/are/has when accurate — "The building is a reminder..."

### Empty intensifiers — [strip]

"very," "highly," "extremely," "incredibly" propping up a weak adjective.
Fix: cut the intensifier, or replace the pair with a stronger single word or a fact.

### Filler transitions — [strip]

Connectives that signal a turn without making one: "it's worth noting," "it bears mentioning," "importantly," "interestingly," "notably."
Avoid: "It's worth noting that this approach has limitations."
Fix: delete the transition and state the point, or make the real connection explicit.

### Invented concept labels — [rewrite]

Abstract compound labels that sound analytical without being grounded: a domain word plus paradox / trap / creep / divide / vacuum / inversion — "the supervision paradox," "the acceleration trap," "workload creep."
They name a thing to skip the argument.
Multiple in one piece is a strong slop signal.
Fix: make the argument, or use the established term if one exists.
The earned exception: a coined label that substitutes for the argument — "the supervision paradox," asserted and never shown — fails, while a label that names a result the passage has already proven — a "verification tax" coined after the mechanism is argued — is craft.
The test is payment order: the argument buys the label before the label appears.

---

## 2. Syntactic (sentence patterns)

Mostly \[rewrite\]: the construction is the tell, so you must recast the sentence, not swap a word.

### Negative parallelism — [rewrite]

"It's not X — it's Y." The single most-identified AI tell.
Manufactures false profundity by framing everything as a surprising reframe.
Includes the causal variant "not because X, but because Y." One can sharpen a point; three in a piece insults the reader.
Avoid: "It's not bold.
It's backwards." / "Half the bugs you chase aren't in your code.
They're in your head."
Fix: state the main point directly — "Memory is a navigable workspace with structure," not "Memory is not a flat index; it is a navigable workspace."
Keep at most one contrast per stretch.
The move survives syntax swaps: "X rather than Y," "X instead of Y," and "X, not Y" are the same device as "It's not X — it's Y," and banning one surface form inflates the others — revision passes that cut the em-dash form to zero have been measured raising total contrast density above the original.
Count the move, not the token: keep a contrast only where the reader would otherwise believe Y, about one per page, none in headings.

### "Not X. Not Y. Just Z." countdown — [rewrite]

Negating two or more things to build tension before the reveal, faking a narrowing toward truth.
Avoid: "Not a bug.
Not a feature.
A fundamental design flaw."
Fix: lead with Z and support it.

### Self-answered rhetorical question ("The X? A Y.") — [rewrite]

Posing a question nobody asked, then answering it in the next clause for drama.
Avoid: "The result?
Devastating." / "The scary part?
This attack vector is perfect for developers."
Fix: make the assertion directly — "The result was devastating."

### Anaphora abuse — [rewrite]

Repeating a sentence opening several times in quick succession.
Avoid: "They assume users will pay.
They assume developers will build.
They assume ecosystems will emerge."
Fix: consolidate into one sentence, or vary the openings and keep only what earns its place.

### Tricolon abuse — [rewrite]

The rule-of-three run into the ground, often stacked or extended to four and five.
One tricolon is elegant; three back-to-back is a pattern-matching failure.
Avoid: "Products solve problems; platforms create worlds.
Products scale linearly; platforms scale exponentially. ..."
Fix: keep the list to what is real — two items if there are two, five if there are five.

### Superficial "-ing" tails — [rewrite]

A present-participle phrase tacked onto a sentence to inject significance that says nothing: "highlighting its importance," "reflecting broader trends," "underscoring its role as a dynamic hub."
Avoid: "...contributing to the region's rich cultural heritage."
Fix: delete the tail, or split into a sentence with a direct verb and a real claim.

### False ranges ("from X to Y") — [rewrite]

"From X to Y" implies a spectrum with a meaningful middle; the model uses it to list two loosely related things.
Avoid: "From innovation to cultural transformation" — nothing is in between.
Fix: list the items plainly, or name the actual spectrum.

### Gerund fragment litany — [rewrite]

After a claim, a stream of verbless fragments illustrating it: "Fixing small bugs.
Writing straightforward features.
Implementing well-defined tickets."
The first sentence already said everything; the fragments add cadence and word count.
Fix: cut the fragments, or fold one concrete example into the sentence.

---

## 3. Discourse and structure

All \[rewrite\]: these operate above the sentence and survive a token-level pass untouched.
Audit structure before polishing clauses.

### Short punchy fragment paragraphs — [rewrite]

Very short sentences or fragments set as standalone paragraphs for manufactured emphasis.
Avoid: "He published this.
Openly.
In a book.
As a priest."
Fix: rejoin into sentences that carry the thought; reserve a lone short sentence for one genuine beat.

### Listicle in a trench coat — [rewrite]

A listicle disguised as prose by opening each item with "The first...
The second...
The third..."
Often what a model does after being told to stop making lists.
Avoid: "The first wall is...
The second wall is...
The third wall is..."
Fix: write real paragraphs with topic sentences, or an honest list if the items are short and parallel.

### Fragment-stack catalog entries — [rewrite]

A heading or bold label followed by verbless noun-phrase fragments and ad-hoc bullets describing one item: "A self-hosted file-management platform. 13.9k stars.
Go backend, vanilla-JS frontend."
Endemic in tool surveys, landscape docs, and design docs, and routinely rationalized as "reference structure."
It is neither prose nor reference — a reference entry is N items sharing one fixed field-set, while this is one thing narrated with the verbs deleted.
Fix: write the entry as sentences with a subject ("Filestash is..."); keep a genuine comparison matrix (N items against the same columns) as a table.

### Bookmark headings — [rewrite]

A heading that names its topic or promises "why/what/how" without carrying the answer.
Avoid: `## What the catalog measures` / `### The provider, and why it is the constrained role`.
Fix: assert the section's claim — `## Three roles, one contract each` / `### Search: the index must commit inside the metadata transaction`.
A label with an appended promise ("The thesis, in one line") that then runs for paragraphs breaks its own promise.

### Obvious-instruction sentences — [rewrite]

Sentences that tell the reader to do what reading already implies, or that restate the previous sentence.
Avoid: after "The three roles are the metadata store, the blob store, and the search provider," cutting "Read each candidate against all three."
Fix: delete; open with the substantive claim instead.

### Empty "not one thing" openers — [rewrite]

A nondescript subject plus a setup device: "A backend is not one thing," "X is more than just Y."
Fix: lead with the concrete claim and an informative subject — "A backend plays up to three roles, each with its own contract."

### Fractal summaries — [rewrite]

"Tell them what you'll say; say it; tell them what you said" applied at every level — every subsection, section, and the document each get a summary.
Avoid: "In this section we'll explore...
[3000 words] ...as we've seen in this section."
Fix: cut the throat-clearing and the recap; let the content stand.

### Signposted conclusion — [rewrite]

Announcing the ending with "In conclusion," "To sum up," "In summary."
Competent writing does not need to declare that it is concluding.
Fix: end on the substantive last point; delete the signpost.

### One-point dilution — [rewrite]

A single argument restated ten ways across thousands of words to feel comprehensive — the same thesis with new metaphors and framings, adding nothing.
Fix: make the point once, support it, and stop; cut the circular restatement.

### Content duplication — [rewrite]

Whole sections or paragraphs repeated near-verbatim, a sign of a model losing track in a long piece.
Fix: delete the duplicate; keep the stronger instance.

### Register drift — [rewrite]

A sudden shift in voice, formality, or vocabulary partway through a piece — a crisp technical section that lapses into marketing, or a formal memo that turns chatty — often the seam between a human passage and a generated one.
Fix: choose the target register and hold it end to end; smooth the seam.

### Dead metaphor — [rewrite]

Latching onto one metaphor and repeating it five to ten times across the piece.
Avoid: "walls and doors" used thirty times; "the ecosystem needs ecosystems to build ecosystem value."
Fix: introduce a metaphor once, use it, and move on.

### Historical-analogy stacking — [rewrite]

Rapid-fire listing of companies or tech eras to build false authority — especially common in technical writing.
Avoid: "Apple didn't build Uber.
Facebook didn't build Spotify.
Stripe didn't build Shopify."
Fix: keep the one analogy that earns its place and develop it.

### "Despite its challenges" formula — [rewrite]

Acknowledging problems only to dismiss them on a fixed beat: "Despite its [positives], [subject] faces challenges...
Despite these challenges, [optimistic close]."
Fix: state the real obstacle and what follows from it, or cut the gesture.

### Engineered symmetry — [rewrite]

The governing reflex, above the paragraph: the default "smart-take" voice, balanced and tidy because that is the cheap default.
It survives a token pass because no single word is wrong.
Spot it by structure — antithesis on a loop, forced triads, convergence scaffolding ("three teams independently converged... this is not accidental"), sweeping closers ("won the first fifty years; it will win the next ten").
Fix: rewrite toward prose a person would sign; keep at most one contrast per stretch, list what is real, state findings without the drumroll, and close on a concrete claim.

---

## 4. Rhetorical stance (the "AI voice")

All \[rewrite\]: these are a posture toward the reader and the material, not a phrase.

### Significance and stakes inflation — [rewrite]

Everything is world-historical; a post about API pricing becomes a meditation on civilization.
Watch for: pivotal, crucial, vital, testament, "marks a shift," "will define the next era," "reshape how we think about everything."
Fix: state the specific consequence at its actual scale.

### Promotional tone — [rewrite]

Marketing adjectives in place of description: vibrant, stunning, world-class, groundbreaking, must-visit, nestled, seamless.
Fix: neutral description plus a concrete detail.

### Notability padding — [rewrite]

Name-dropping media, vague "coverage" claims, follower counts with no relevance.
Fix: one specific, relevant example, or cut it.

### Vague attribution — [rewrite]

Claims pinned to unnamed authorities — "experts say," "observers note," "industry reports," "some critics argue" — often inflating one source into many.
If you can't name the source, you don't have one.
Fix: name a source or remove the claim.

### Fabricated or broken citations — [rewrite]

Sources shaped like rigor with nothing behind them: broken links, invalid DOIs or ISBNs, page numbers that do not exist, search-result links used as sources, or references to sections, tables, works, or "see also" entries that are tangential, point nowhere, or were never written.
The encyclopedic cousin of vague attribution.
Fix: verify every link and identifier, cite the specific source or cut the claim, and remove cross-references that do not land.

### "Here's the kicker" false suspense — [rewrite]

Transitions promising a revelation before an unremarkable point: "here's the thing," "here's where it gets interesting," "here's what most people miss."
Fix: deliver the point without the drumroll.

### "Think of it as" patronizing analogy — [rewrite]

Reflexively reaching for "think of it as..." or "it's like a...," assuming the reader needs a metaphor for everything — often one less clear than the concept.
Avoid: "Think of it like a highway system for data."
Fix: explain the thing directly; add an analogy only when it genuinely clarifies.

### "Imagine a world where" futurism — [rewrite]

Selling an argument by opening with "imagine" and a list of wonderful consequences of agreeing.
Fix: make the case from evidence, not a guided daydream.

### False vulnerability — [rewrite]

Performed self-awareness — breaking the fourth wall or "admitting" a bias in a polished, risk-free way.
Avoid: "And yes, I'm openly in love with the platform model." / "This is not a rant; it's a diagnosis."
Fix: cut it, or make the admission specific and consequential.

### "The truth is simple" — [rewrite]

Asserting that a point is obvious, clear, or simple instead of proving it.
If you have to say it's clear, it probably isn't.
Avoid: "History is unambiguous on this point." / "The reality is simpler and less flattering."
Fix: show the point; delete the claim of obviousness.

### "Let's break this down" pedagogy — [rewrite]

The teacher-student voice imposed on expert readers: "let's unpack this," "let's explore," "let's dive in."
Fix: just present the material.

### Preamble and self-narration — [rewrite]

Text that narrates the work instead of doing it: a paragraph restating the task before answering, an overlong recap of what changed, "in this piece I will argue," or a draft's leftover process notes.
Fix: cut it and open on the substance; the work shows itself.

### Sycophancy and chatbot leakage — [strip]

Excessive praise or agreement, and assistant-to-user phrases bleeding into the text: "Great question," "Of course," "Hope this helps," "Let me know."
Fix: remove, unless the medium is genuinely a message where the courtesy is normal (see the correspondence register).

### Generic positive conclusions — [rewrite]

Ending on unearned optimism with no specifics: "the future looks bright," "the possibilities are endless."
Fix: close on a concrete next step, fact, or open question.

### Formulaic challenges/future sections — [rewrite]

A boilerplate "Challenges" or "Future outlook" section with no specific obstacles or dates.
Fix: name the concrete obstacle, date, or action, or drop the section.

---

## 5. Formatting and markup

Mostly \[strip\]: mechanical habits and artifacts.
Real writers typing in an editor produce straight quotes and plain lists.

### Em-dash overuse — [strip]

Compulsive em-dashes for dramatic pauses and asides; a human might use two or three in a piece, a model twenty.
Fix: replace most with commas, parentheses, or periods.

### Bold-first bullets — [strip]

Every list item opening with a bolded keyword or label — a hallmark of model markdown.
Fix: in body prose, dissolve into sentences; in a genuine list, drop the bold unless it is a true term being defined.

### Inline-header vertical lists — [strip]

List items that each begin with a bold label and a colon, standing in for paragraphs.
Fix: convert to normal prose or a clean list.

### Unicode decoration — [strip]

Arrows (→, ⇒), and smart/curly quotes and apostrophes where a typist would produce straight quotes and `->`.
Fix: straighten quotes; replace arrows with words or `->`.

### Emojis — [strip]

Decorative emoji in headings, bullets, or prose.
Fix: remove.

### Title-case headings — [strip]

Headings in Title Case where the house style is sentence case.
Fix: sentence-case them.

### Subject lines in body text — [strip]

An email-style "Subject:" line embedded in prose.
Fix: remove.

### Knowledge-cutoff disclaimers — [strip]

"As of my last update," "based on the information available to me."
Fix: remove; supply a verified fact if one is needed.

### Placeholder and phrasal templates — [strip]

Scaffolding left in the text: "This section will cover...," "[Insert example here]."
Fix: replace with real content or delete.

### Generator and markup artifacts — [strip]

Stray tokens and breakage left by a model or a paste: generator markers like "oaicite," "contentReference," or a trailing "+1"; broken or mismatched markup; generic terms capitalized as if proper nouns; a stray "Subject:" line; a table used to hold prose rather than rows.
Fix: delete the artifact, lowercase the generic term, and repair the markup.
