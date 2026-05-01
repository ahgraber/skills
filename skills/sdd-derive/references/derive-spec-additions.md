# Derive-Specific Spec Additions

Two additions to spec format that are specific to `sdd-derive`'s output and do not apply to specs authored from intent (`sdd-propose`).

These additions live in this reference rather than the shared `sdd-spec-formats.md` because they reflect derive's "snapshot lift" philosophy — derived specs document a specific commit's behavior with honest gaps.

## As-of anchor

Every derived spec records the commit it was lifted from.
This anchor is the canonical reference for re-derivation: future runs against newer commits diff and re-lift the delta.

### Format

The generation note at the top of each generated spec includes the as-of commit SHA:

```markdown
> Generated from code analysis on 2026-04-29, as-of commit a1b2c3d4e5f6
```

The SHA is the full or short Git commit hash from the repository head at derivation time.
Short hashes (7-12 characters) are acceptable; full hashes are preferred for unambiguous re-derivation.

### Why no source file list

Earlier sdd-derive versions included a `Source files: {list}` line.
This was dropped because:

- The list ages poorly (files move/rename across commits)
- The capability scope is determined by discovery; given the same commit, discovery is deterministic and reproduces the file set
- Provenance (when configured ON) provides per-scenario file:line references, which is more useful than a flat list at the spec top

The commit SHA + capability name is sufficient to reproduce the exact file set.

## `## Uncertainties` section

When the lifter cannot lift confidently, it appends an `## Uncertainties` section to the spec.
The section is **omitted entirely when empty** — a spec with no uncertainties has no section at all.

### Format

```markdown
## Uncertainties

- **<brief anchor>** (Req #N | file:line | phrase): <reason>.
  Resolve: <suggestion>.
```

Each entry has three components:

1. **Anchor** — what the uncertainty attaches to.
   Free-form parens content.
   Examples:
   - `(Req #5)` — a specific requirement
   - `(Scenario in Req #7)` — a scenario within a requirement
   - `(during verification of src/search/scoring.py:80)` — for Observer Gaps
   - `(custom tag: foo_bar)` — for unknown tag rules
2. **Reason** — brief explanation of why the lifter couldn't lift cleanly.
   One sentence or fragment.
3. **Resolution suggestion** — brief; what the user can do.

Brevity discipline: each entry should fit on 2-3 lines.

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

### When to emit

The lifter emits an Uncertainty when:

- The `algorithmic` tag is set on an observation (always — the strategy check requires human resolution)
- An observation has multiple plausible properties and the lifter cannot disambiguate
- A criticality-tag rule cannot be satisfied from inputs (e.g., security strong-specificity unachievable from a vague observation)
- An observation has a custom tag the lifter has no rule for
- Verification revealed an Observer Gap (behavior in source not in observations)
- An observation is genuinely ambiguous

Uncertainty is **the exception, not the default.**
With observer + user refinement upstream, the lifter should lift confidently most of the time.
A spec with zero uncertainties is the typical, healthy outcome.

### Resolution lifecycle

1. Lifter emits the section (only when items exist).
2. Validate counts and surfaces them in its report.
3. User resolves manually:
   - Edit the spec to integrate the chosen resolution
   - Remove the corresponding uncertainty entry
   - Or re-derive (for Observer Gap or custom tag cases)
4. The section is removed from the spec when no entries remain.

There is no programmatic "resolve" tool — uncertainties are resolved by editing the spec.

## Placement in spec file

Order of sections in a derived spec (delta or baseline):

1. Generation note blockquote (with as-of commit SHA)
2. `## Purpose` (baseline only)
3. ADDED/MODIFIED/REMOVED sections (delta) OR Requirements (baseline)
4. `## Uncertainties` (only when present)

The `## Uncertainties` section always comes last so it's easy to scan and resolve in isolation.
