# Humanize Guardrails (LLM Failure Patterns)

Use this checklist when text sounds AI-generated, over-polished, or vague.
Apply the fixes while preserving meaning and tone.
Aligned to the categories in Wikipedia:Signs of AI writing; see `skills/good-prose/ATTRIBUTION.md`.

## Process

1. Identify AI-sounding patterns.
2. Rewrite the affected lines.
3. Preserve meaning and intended tone.
4. Prefer concrete facts and plain English.
5. Read aloud once for rhythm and clarity.

## Voice and Craft

- Vary sentence length and structure.
- Prefer specific details over abstract claims.
- Keep a clear point of view without over-opining.
- Earn emphasis with evidence, not adjectives.

## Content Patterns to Remove or Recast

### 1) Significance inflation

- Watch for: pivotal, crucial, vital, testament, underscores, marks a shift, key moment, evolving landscape.
- Fix: Replace with specific facts and implications.

### 2) Notability padding

- Watch for: media name-dropping, vague "coverage" claims, social follower counts without relevance.
- Fix: Use a specific, relevant example or remove.

### 3) Superficial -ing clauses

- Watch for: "highlighting," "underscoring," "symbolizing," "showcasing".
- Fix: Split into clear sentences with direct verbs.

### 4) Promotional tone

- Watch for: vibrant, stunning, world-class, groundbreaking, must-visit, nestled.
- Fix: Replace with neutral description and concrete detail.

### 5) Vague attribution

- Watch for: "experts say," "observers note," "industry reports".
- Fix: Name a source or remove the claim.

### 6) Formulaic challenges/future sections

- Watch for: "Despite these challenges," "Future outlook" without specifics.
- Fix: Replace with concrete obstacles, dates, or actions.

## Language and Grammar Patterns

### 7) Overused AI vocabulary

- Avoid: additionally, crucial, delve, highlight (verb), tapestry, interplay, pivotal, showcase, underscore.
- Fix: Use simpler words or omit.

### 8) Copula avoidance

- Watch for: serves as, stands as, represents, features, boasts.
- Fix: Use is/are/has when accurate.

### 9) Negative parallelism

- Watch for: "Not only... but..."
  "It's not just... it's...".
- Fix: State the main point directly.

### 10) Rule of three overuse

- Watch for: stacked triples that feel forced.
- Fix: Keep the list to what is necessary.

### 11) Elegant variation

- Watch for: synonym cycling in a short span.
- Fix: Reuse the same noun when it improves clarity.

### 12) False ranges

- Watch for: "from X to Y" when X and Y are not comparable.
- Fix: List topics directly.

## Style Patterns

### 13) Em dash overuse

- Fix: Replace with commas or periods.

### 14) Boldface lists as pseudo-headings

- Fix: Use plain sentences or standard list items.

### 15) Inline-header vertical lists

- Watch for: list items that start with a bolded label and a colon.
- Fix: Convert to a normal list or a paragraph.

### 16) Title Case headings

- Fix: Use sentence case for headings.

### 17) Emojis

- Fix: Remove.

### 18) Curly quotation marks and apostrophes

- Fix: Use straight quotes.

### 19) Subject lines

- Fix: Remove subject lines from body text.

## Communication Artifacts

### 18) Chatbot phrases

- Watch for: "Hope this helps," "Of course," "Let me know," "Great question."
- Fix: Remove unless the medium requires it.

### 19) Knowledge-cutoff disclaimers

- Watch for: "As of my last update," "based on limited information."
- Fix: Remove; replace with verified facts if needed.

### 20) Phrasal templates and placeholder text

- Watch for: "This section will cover..." "[Insert example here]".
- Fix: Replace with actual content or delete.

### 21) Sycophantic tone

- Watch for: excessive praise or agreement.
- Fix: Keep neutral, factual tone.

## Filler and Hedging

### 22) Filler phrases

- Examples: "In order to," "At this point in time," "Due to the fact that."
- Fix: Use shorter equivalents.

### 23) Excessive hedging

- Watch for: "could potentially possibly."
- Fix: Reduce to one modal, or remove.

### 24) Generic positive conclusions

- Watch for: "The future looks bright" without specifics.
- Fix: End with concrete next steps or facts.

## Wikipedia-Specific Tells (Use if writing or editing Wikipedia-like text)

These reflect the Wikipedia "Signs of AI writing" list.
Include only when working on wiki pages or encyclopedia-style content.

### Content (Wikipedia context)

- **Leads that treat list or broad article titles as proper nouns** (e.g., capitalizing generic list items as if official names).
- **Vague "See also" sections** with unspecific or tangential entries.

### Style and formatting

- **Unusual use of tables** for prose or non-tabular data.
- **Subject lines** inserted into article text.

### Communication and templates

- **Phrasal templates or placeholder text** ("[Insert example here]", "This section will cover...").

### Markup and citation artifacts

- **Markdown instead of wikitext**, or broken wikitext.
- **Search-link artifacts** (links to search results rather than sources).
- **Reference markup bugs** (stray tokens like "oaicite", "contentReference", "+1").
- **Attribution or attributionIndex artifacts**.
- **Non-existent categories or templates**.
- **Citation issues** (broken links, invalid DOIs/ISBNs, outdated access dates, unrelated DOIs, missing page numbers, unused named references, or odd URL tracking params).

### Miscellaneous

- **Sudden shift in writing style** within a single article.
- **Overly verbose edit summaries** or "submission statements" in drafts.
- **Pre-placed maintenance templates** not tied to actual issues.
