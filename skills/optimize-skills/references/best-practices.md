# Best Practices for Building AI Skills

## Quick Checklist

- Skill name and folder name are kebab-case and match.
- SKILL.md exists and frontmatter includes only `name` and `description`.
- Description focuses on when to use the skill and includes realistic trigger phrases.
- SKILL.md is concise and imperative; heavy content moved to references.
- Main SKILL.md stays under 500 lines.
- References are one level deep and linked from SKILL.md.
- Scripts are used for deterministic, repeatable work and tested once.
- Skill has trigger tests (should/should-not) and functional tests.
- Package only after validation passes.

## Principles

- Concision wins: every token in SKILL.md competes with the system prompt.
- Progressive disclosure: metadata -> SKILL.md -> assets/scripts/references.
- Metadata should stay lean (around 100 tokens combined for `name` + `description`).
- Keep SKILL.md targeted (\<5000 tokens recommended) and push details to on-demand files.
- Composability: assume multiple skills can load together.
- Portability: avoid environment-specific assumptions unless required.
- Right level of freedom: prose for judgment, scripts for fragile steps.

## Description (Triggering) Guidance

- Treat the description as the trigger gate, not the workflow summary.
- Prefer trigger language: symptoms, user phrases, file types, and contexts.
- Keep it short to reduce system prompt budget and improve visibility.
- Avoid XML angle brackets and avoid first-person voice.
- If your platform expects "what + when," keep the "what" minimal and focus on when.
- Add negative triggers if the skill overfires.

## SKILL.md Body Guidance

- Use imperative/infinitive form.
- Put critical constraints early.
- For decision-heavy logic, use a small dot flowchart and link to references.
- For long references (>100 lines), include a table of contents.
- Avoid narrative case studies; focus on reusable patterns.

## Optional Directories

### `assets/`

- Use for static reusable resources (templates, examples, lookup tables, schemas).
- Store artifacts agents can consume directly instead of re-describing them in prose.

### `references/`

- Use for on-demand documentation that should not sit in main SKILL.md.
- Keep files focused and topic-scoped; prefer multiple small files over one large file.
- Common patterns include `REFERENCE.md`, `FORMS.md`, and domain-specific files.

Create resources when:

- The material exceeds ~100 lines.
- There are multiple variants (frameworks, providers, file types).
- You need a deep API or schema reference.

Keep inline when:

- The pattern fits in a few bullets or a short example.
- The information is required in most invocations.

### `scripts/`

- Use for deterministic or repetitive work agents can execute.
- Keep scripts self-contained or clearly declare dependencies.
- Return actionable errors and handle expected edge cases.

## Workflow Modeling (GraphViz)

- Use dot as a lightweight process DSL for non-obvious decision paths.
- Prefer multiple trigger-based subgraphs over a single giant flow.
- Use semantic shapes and edge labels per `graphviz-conventions.dot`.
- Keep node labels short, specific, and action-oriented.
- Use flowcharts only when decision logic or loops are easy to misapply.
- Prefer markdown lists/tables/code blocks for linear steps, reference data, and code snippets.
- Avoid placeholder labels (for example `step1`, `helper2`) that hide intent.

## Testing and Iteration

### Trigger Tests

- Should trigger on direct asks.
- Should trigger on paraphrases.
- Should not trigger on unrelated requests.

### Functional Tests

- Run at least one representative real task.
- Verify the workflow completes with minimal correction.
- Confirm error handling instructions are followed.

### Iteration Signals

- Under-triggering: add missing triggers and symptoms to the description.
- Over-triggering: add exclusions and tighten context phrases.
- Misexecution: clarify steps, add guardrails, or add scripts.

## Troubleshooting

- Skill not triggering: description too vague or too long; reduce and add trigger phrases.
- Skill ignored: description may summarize workflow; reduce to when-only triggers.
- Skill not visible: too many skills or long descriptions; shorten and consolidate.
- Instructions ignored: move critical rules to the top and tighten language.
