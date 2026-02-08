---
name: optimize-skills
description: Use when creating or refining SKILL.md-based skills, or diagnosing weak triggering (under/over-triggering, vague descriptions, bloated context, or missing workflow guidance).
---

# Optimizing Skills

Use this skill to create, review, or improve SKILL.md-based skills so they trigger correctly, stay concise, and execute reliably.

## When to Use

- Creating a new reusable skill from repeated work patterns.
- Updating an existing skill that under-triggers, over-triggers, or misfires.
- Tightening a skill that is too long, redundant, or hard to execute.
- Converting narrative guidance into concise, imperative instructions.
- Rebalancing where content should live across `SKILL.md`, `references/`, `assets/`, and `scripts/`.

## Overview

### What is a Skill?

A **skill** is a reference guide for proven techniques, patterns, or tools, typically classed as procedural knowledge or best practices.
Skills help future Agent instances find and apply effective approaches.

**Skills are:** Reusable techniques, patterns, tools, reference guides

**Skills are NOT:** Narratives about how you solved a problem once

### When to Create a Skill

**Create when:**

- Technique wasn't intuitively obvious to you or required multiple iterations to get right.
- You'd reference this again across projects / Others would benefit from knowing this.
- Pattern applies broadly (not project-specific)
- Triggerable by specific user intents or common failure modes.

**Don't create for:**

- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions that aren't broadly applicable

## Workflow

1. Define trigger tests: list 2-3 prompts that should trigger the skill and 2 that should not.
2. Audit frontmatter: keep only `name` and `description`; make `description` when-focused, not workflow-focused.
3. Rewrite the body in imperative form: keep main instructions short, specific, and ordered by execution.
4. Move deep detail out of `SKILL.md` into `references/`, `assets/`, or `scripts/`; link to each from `SKILL.md`.
5. Validate workflow representation: use markdown for linear steps; use a small DOT flowchart only for non-obvious branching or loops.
6. Run trigger and functional checks against real prompts; iterate until both pass.

## Core Principles

- Optimize for triggering: description must emphasize when to use the skill (`references/skills-search-optimization.md`).
- Keep frontmatter metadata small (about 100 tokens combined).
- Keep main `SKILL.md` under 500 lines and focused on action.
- Use progressive disclosure: metadata -> SKILL.md -> references/scripts/assets.
- Choose the right degree of freedom: text, pseudocode, or scripts depending on fragility.
- Prefer reusable resources (scripts, templates) over repeated prose.

### Progressive Disclosure Targets

- Metadata (`name` + `description`): small startup footprint, ideally ~100 tokens.
- `SKILL.md`: keep actionable and concise, target \<5000 tokens and \<500 lines.
- `scripts/`, `references/`, `assets/`: loaded only when needed; keep files narrow so agents pull less context.

## Flowchart Guidance

```dot
digraph when_flowchart {
    "Need to show process guidance?" [shape=diamond];
    "Non-obvious decision or loop?" [shape=diamond];
    "Use markdown (list/table/code)" [shape=box];
    "Use small inline DOT flowchart" [shape=box];

    "Need to show process guidance?" -> "Non-obvious decision or loop?" [label="yes"];
    "Need to show process guidance?" -> "Use markdown (list/table/code)" [label="no"];
    "Non-obvious decision or loop?" -> "Use small inline DOT flowchart" [label="yes"];
    "Non-obvious decision or loop?" -> "Use markdown (list/table/code)" [label="no"];
}
```

- Use markdown lists/tables/code blocks by default.
- Add DOT only when decision logic or loops are easy to misapply.
- Avoid placeholder node labels; use concrete actions and conditions.
- Follow `references/graphviz-conventions.dot` for node shapes and labels.
- Keep flowcharts small and trigger-based; split large flows into focused subgraphs.

Render DOT to SVG with `scripts/render-dot.py`.
Output SVGs are written to the target skill's `assets/` directory.

```bash
scripts/render-dot.py skills/optimize-skills/references/skill-workflow.dot
scripts/render-dot.py skills/optimize-skills/SKILL.md
scripts/render-dot.py skills/optimize-skills/SKILL.md --force # overwrite existing SVGs
```

## Output

### SKILL.md Structure

```txt
skills/
  skill-name/
    SKILL.md      # Main reference (required)
    assets/       # (optional) Static reusable resources such as templates or figures
    references/   # (optional) On-demand documentation, organized by topic or variant
    scripts/      # (optional) Executable helpers for deterministic tasks;
                  # scripts should be self-contained or clearly declare dependencies,
                  # include clear errors, and handle edge cases.
```

### Rules

- SKILL.md must be named exactly `SKILL.md`.
- Folder name must be kebab-case, matching the `name` in frontmatter.
- Do not add README.md inside the skill.
- YAML frontmatter must include `name` and `description` fields.
- `name` must be kebab-case and match the folder name.
- `description` should emphasize when to use the skill and include triggers/symptoms.
- Avoid workflow summaries in the description.
- Keep descriptions short and specific.
- Refer to `assets/skill-template.md` for a suggested (but easily modified) template structure.

## Common Mistakes

- Summarizing workflow in `description` instead of stating actionable triggers and symptoms.
- Keeping workflows as one giant graph instead of splitting into trigger-based subgraphs.
- Repeating deep reference material in `SKILL.md` instead of linking to `references/`.
- Leaving scripts implicit: deterministic steps should be executable where possible.

## References

- `assets/skill-template.md` for a suggested SKILL.md structure.
- `references/best-practices.md`: checklists, structure guidance, testing, and troubleshooting patterns.
- `references/skills-search-optimization.md`: description and trigger optimization rules.
- `references/skill-workflow.dot`: canonical workflow for this skill.
- `references/graphviz-conventions.dot`: DOT style and semantics for workflow diagrams.
