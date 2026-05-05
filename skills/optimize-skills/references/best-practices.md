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

### The Description Shortcut Trap

Descriptions that summarize workflow create a shortcut the agent takes instead of reading the skill body.
When enough process detail appears in the description, the agent treats it as authoritative and skips the full skill.

Observed failure: a description summarizing a two-stage review ("dispatches subagent per task with code review between tasks") caused agents to do one review instead of two — the shortcut bypassed the flowchart showing both stages.

```yaml
# ❌ Workflow summary — agent may follow this instead of reading the skill body
description: Use when drafting commit messages — reads staged diff, applies conventional commit rules, self-checks body

# ✅ Triggering conditions only — forces agent to read the skill for the workflow
description: Use whenever a Conventional Commit message is being drafted
```

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

## Compliance Hardening

Apply when empirical compliance on specific rules is poor.
Do not apply preemptively — it adds overhead and bulk.

### The Reference-Skip Failure Mode

Progressive disclosure assumes agents read references deeply.
Under time or context pressure, agents draft from memory and treat "using references/X" as if familiarity is sufficient.
Rules in reference files effectively don't exist when this happens.

Indicators: the same rule is violated repeatedly across invocations despite being documented in a reference file.

### Three-Layer Defense

Apply all three layers together:

| Layer                                | Technique                                                                          | What it catches                                             |
| ------------------------------------ | ---------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 1. Force the load                    | Change "Draft using X" → "Read X. Then draft applying those rules."                | Agent skips the reference file entirely                     |
| 2. Duplicate at Critical Constraints | Put the highest-violation rules in `Critical Constraints`, even at the cost of DRY | Agent reads SKILL.md but skips the reference                |
| 3. Verification gate before output   | Add a self-check step: a concrete per-line checklist applied before returning      | Agent reads the rules but fails to apply them at draft time |

### Common Rationalizations

Anticipate these and counter them explicitly in Critical Constraints or the self-check step.

| Rationalization                                               | Counter to add to skill                                                            |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| "The description covered it — no need to read the full skill" | Keep descriptions triggering-only; workflow must live in the skill body            |
| "I know this pattern well enough from context"                | Name the Read action explicitly; familiarity is not a substitute                   |
| "This is a simple case — the full workflow doesn't apply"     | Add a Critical Constraint: the workflow applies regardless of perceived complexity |
| "The draft looks correct — I'll skip the self-check"          | Self-check exists precisely because correct-looking drafts often aren't            |

### Red Flags

Signs that compliance is breaking down — add these so agents can self-check:

- Output drafted before the workflow reached the drafting step
- Skill invoked but a required Read action was skipped
- Self-check step skipped because the draft "looks fine"
- "Using references/X" treated as equivalent to having Read X

### Hardening Rule Statements

Stating a rule is not enough — agents find the path of least resistance.
Three techniques make rule statements harder to rationalize around.

**Name the specific workaround you're forbidding, not just the rule.**
"Read X before drafting" is weaker than "Read X before drafting.
Do not draft from memory.
'I know this reference well enough' is not an exception."
Specificity removes the judgment call that enables rationalization.

**State why the rule exists.**
When the failure mode is visible, rationalization requires arguing against it too.
"Self-check before returning — this is where slop is caught" is harder to skip than "Self-check before returning."

**Forbid "I followed the intent" arguments.**
For rules with no exceptions, add near the top of the skill:

> These instructions admit no exceptions. "I followed the intent" or "this case is different" do not license skipping steps.

## Troubleshooting

- Skill not triggering: description too vague or too long; reduce and add trigger phrases.
- Skill ignored: description may summarize workflow; reduce to when-only triggers.
- Skill not visible: too many skills or long descriptions; shorten and consolidate.
- Instructions ignored: apply compliance hardening — see `## Compliance Hardening` above.
