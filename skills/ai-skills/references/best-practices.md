# Best Practices for Building AI Skills

## Quick Checklist

- Skill name and folder name are kebab-case and match.
- SKILL.md exists and frontmatter includes only `name` and `description`.
- Description focuses on when to use the skill and includes realistic trigger phrases.
- SKILL.md is concise and imperative; heavy content moved to references.
- References are one level deep and linked from SKILL.md.
- Scripts are used for deterministic, repeatable work and tested once.
- Skill has trigger tests (should/should-not) and functional tests.
- Package only after validation passes.

## Principles

- Concision wins: every token in SKILL.md competes with the system prompt.
- Progressive disclosure: metadata -> SKILL.md -> references/scripts/assets.
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

## When to Split into References

Create `references/` when:

- The material exceeds ~100 lines.
- There are multiple variants (frameworks, providers, file types).
- You need a deep API or schema reference.

Keep inline when:

- The pattern fits in a few bullets or a short example.
- The information is required in most invocations.

## Scripts and Assets

- Add scripts for deterministic or repetitive tasks.
- Test added scripts at least once after changes.
- Keep assets for templates or artifacts that are reused in outputs.

## Workflow Modeling (GraphViz)

- Use dot as a lightweight process DSL for non-obvious decision paths.
- Prefer multiple trigger-based subgraphs over a single giant flow.
- Use semantic shapes and edge labels per `graphviz-conventions.dot`.
- Keep node labels short, specific, and action-oriented.

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

## Packaging

- Validate and package with `scripts/package_skill.py`.
- Fix validation errors before distributing.

## Metrics (Optional)

- Trigger rate on a 10-20 query test set.
- Average tool calls vs. baseline.
- Qualitative consistency across sessions.
