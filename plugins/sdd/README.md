# sdd

Spec-driven development: explore, propose, apply, verify, sync, and archive changes against versioned specs, with formal verification where a design needs proof.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `formal-verification`: Use when the user asks for formal verification or formal methods: writing or checking a design model (TLA+, Alloy, P, Quint), proving code against contracts (Dafny, Verus, SPARK, Frama-C, Lean, Rocq), model checking, invariants, liveness, vacuous passes, or counterexamples; deciding whether a design or requirement warrants formal verification; or keeping existing formal specs and proofs current.
- `sdd`: Use when the user wants any spec-driven development action — exploring before speccing, deriving specs from code or translating specs from another system, proposing a change, applying or implementing, verifying, syncing delta specs, or archiving.
- `sdd-apply`: Use when implementing tasks from a change's tasks.md.
- `sdd-archive`: Use when completing and archiving a change after all tasks are done and specs are synced.
- `sdd-derive`: Use when deriving SDD specs from existing code or retroactively documenting implemented behavior.
- `sdd-explore`: Use when the user wants to think through ideas, investigate problems, or clarify requirements before or during any SDD path.
- `sdd-propose`: Use when creating a new change with all SDD artifacts — proposal, delta specs, design, and tasks — or completing a partial change.
- `sdd-sync`: Use when merging delta specs from a change into the main baseline specs.
- `sdd-translate`: Use when translating or migrating existing specs from another tool or format (Spec Kit, Kiro, ADRs, Jira, Confluence, Word docs, or custom markdown requirements) into SDD spec format.
- `sdd-verify`: Use when verifying that an implementation matches a change's SDD artifacts.

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install sdd@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add sdd@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install sdd@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
