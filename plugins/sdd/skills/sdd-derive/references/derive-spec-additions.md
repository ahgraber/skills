# Derive-Specific Spec Additions

Two spec-format additions specific to `sdd-derive` output (do not apply to `sdd-propose`).
They reflect derive's "snapshot lift" philosophy: derived specs document a specific commit's behavior with honest gaps.

## As-of anchor

Record the commit each derived spec was lifted from.
This anchor is the canonical reference for re-derivation — future runs diff against newer commits and re-lift the delta.

### Format

Include the as-of commit SHA in the generation note at the top of each generated spec:

```markdown
> Generated from code analysis on 2026-04-29, as-of commit a1b2c3d4e5f6
```

- Use the full or short Git commit hash from repo HEAD at derivation time.
- Short hashes (7-12 chars) are acceptable; full hashes preferred for unambiguous re-derivation.
- Commit SHA + capability name reproduces the exact file set (discovery is deterministic given the same commit).
- Do NOT include a `Source files: {list}` line — file lists age poorly across renames.

## `## Uncertainties` section

Append this section when the lifter cannot lift confidently.
**Omit entirely when empty** — a spec with no uncertainties has no section at all.

For when to emit and per-tag rules, see `lifter.md` § Uncertainty discipline.

### Format

```markdown
## Uncertainties

- **<brief anchor>** (Req #N | file:line | phrase): <reason>.
  Resolve: <suggestion>.
```

Each entry has three components, fitting on 2-3 lines:

1. **Anchor** — what the uncertainty attaches to.
   Free-form parens content.
   Examples:
   - `(Req #5)` — a specific requirement
   - `(Scenario in Req #7)` — a scenario within a requirement
   - `(during verification of src/search/scoring.py:80)` — Observer Gaps
   - `(custom tag: foo_bar)` — unknown tag rules
2. **Reason** — one sentence or fragment explaining why the lifter couldn't lift cleanly.
3. **Resolution suggestion** — brief; what the user can do.

### Worked examples

```markdown
## Uncertainties

- **Search ranking strategy** (Req #5): TF-IDF with threshold 0.3 used for ranking.
  Strategy ownership unclear.
  Resolve: confirm if TF-IDF is intended strategy (preserve verbatim) or replaceable internal optimization (lift "ranked by relevance" only).

- **Verified gap in `src/search/scoring.py:80`**: Found `boost_recent` modifier during verification, not described in observations.
  Resolve: re-derive with observation covering recency boost, or accept as out-of-scope.

- **Retry behavior** (Req #7): Two plausible properties — "retry idempotently" vs "retry only on timeout."
  Resolve: pick one or add observation distinguishing the cases.

- **Custom tag `pii_handling`** (Req #11): Lifter has no rule for this tag.
  Resolve: define the rule in evidence-class-taxonomy.md and re-derive, or remove the tag.
```

### Resolution lifecycle

1. Lifter emits the section (only when items exist).
2. Validate counts and surfaces entries.
3. User resolves manually by either:
   - Editing the spec to integrate the chosen resolution and removing the entry, or
   - Re-deriving (for Observer Gap or custom tag cases).
4. Remove the section once no entries remain.

No programmatic "resolve" tool exists — resolve uncertainties by editing the spec.

## Placement in spec file

Order sections in a derived spec (delta or baseline) as:

1. Generation note blockquote (with as-of commit SHA)
2. `## Purpose` (baseline only)
3. ADDED/MODIFIED/REMOVED sections (delta) OR Requirements (baseline)
4. `## Uncertainties` (only when present)

`## Uncertainties` always comes last for easy scan-and-resolve in isolation.
