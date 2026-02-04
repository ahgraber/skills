---
name: ai-skills
description: Best practices for designing, writing, testing, and packaging AI skills (SKILL.md-based). Use when creating new skills, reviewing or updating existing skills, or troubleshooting triggering quality (under/over-triggering, vague descriptions, bloated context, or missing workflows).
---

# AI Skills Best Practices

Use this skill to build, review, or improve SKILL.md-based skills with strong triggering, clear workflows, and efficient context use.

## Workflow

- Use the workflow graph in `references/skill-workflow.dot` as the canonical flow.
- Follow `references/graphviz-conventions.dot` for node shapes, labels, and edge styles.
- Keep workflows trigger-based and split into focused subgraphs rather than one giant flow.
- Render graphs with `scripts/render_dot.py` when you need a visual check.

## Core Principles

- Keep SKILL.md concise; move heavy reference material into `references/`.
- Optimize for triggering: description should emphasize when to use the skill.
- Use progressive disclosure: metadata -> SKILL.md -> references/scripts/assets.
- Choose the right degree of freedom: text, pseudocode, or scripts depending on fragility.
- Prefer reusable resources (scripts, templates) over repeated prose.

## Build Workflow (Overview)

1. Define 2-3 concrete use cases and the phrases that should trigger the skill.
2. Identify reusable resources (scripts, references, assets).
3. Initialize the skill (if new) with `scripts/init_skill.py`.
4. Draft SKILL.md with tight frontmatter and imperative instructions.
5. Add resources; keep SKILL.md lean and link to references.
6. Test triggering and functional behavior; capture failures and iterate.
7. Package with `scripts/package_skill.py` once validated.

## Frontmatter Rules

- `name`: kebab-case, matches folder name.
- `description`: emphasize when to use the skill; include triggers and symptoms.
- Avoid workflow summaries in the description.
  Keep it short and specific.
- Do not include XML angle brackets.

## File Structure Rules

- SKILL.md must be named exactly `SKILL.md`.
- Folder name must be kebab-case.
- Do not add README.md inside the skill.

## Detailed Guidance

Read `references/best-practices.md` for:

- Triggering and description writing patterns
- Testing and iteration checklists
- Troubleshooting under/over-triggering
- When to split content into references or scripts
- Token and context budget guidance
