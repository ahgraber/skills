# Tool facts

Per-tool commands for the can-fail checks (stage 3) and the gates (stage 4).
This file does not cover installation.

Items marked † come from general knowledge of the tool, not from the research behind this skill.
Confirm them against the documentation of the installed version before relying on them.
Escape-hatch lists are not complete; the freeze and the assumption listing are the gates, and the lists are for review.

## Design models

### TLA+ (TLC, Apalache, TLAPS)

- Vacuity and reachability: add the negation of a reachability claim as an invariant and expect a counterexample; write witness invariants that force deep states.
  TLC's `_POSSIBLE` conditions fail a run when a listed state or action is never reached, but the feature is provisional: it exists only in the 1.8.0 prerelease, and its documentation says it may be renamed or removed.
  Use it only when that version is installed, and keep the manual method as the default.
- Reachability does not catch an implication whose condition never holds; check conditions separately.
- Bounds: record the constants and the model's size; TLC results hold only within them.
- Gate: none exists in any tool or wrapper.
  Freeze the spec file and the `.cfg` file (properties, invariants, `CONSTRAINT`, `ACTION_CONSTRAINT` †, fairness, constants).
- Escape hatches: removed or weakened properties, added state constraints that exclude bad behavior, broadened fairness, reduced constants.
  All are changes to frozen files.
- Liveness: fairness per action; a separate model with smaller constants.
- Memory model: TLC and PlusCal assume a single order of memory operations.
- Apalache is bounded with an SMT search; it can also check an inductive invariant.
- TLAPS has had no stable release since 2022.

### Quint

- Vacuity: run with the negation of a reachability claim as the invariant (`--invariant` with `not(...)`) and expect a violation.
- Quint compiles to TLA+; the TLA+ notes on bounds and fairness apply.

### Alloy

- Scenarios: `run ... expect 1` confirms the model admits a required scenario.
- Bounds: the default scope and step count can be too small; size them for a full protocol cycle plus margin.
- Alloy is strong for exploring instances with no property stated.

### P

- P pairs design-time model checking with PObserve, which checks production logs against the same model.
- Vacuity checks for P were not covered by the research; use the negation method.

## Code-level tools

### Dafny

- Vacuity: `--warn-contradictory-assumptions`.
- Assumption listing: `dafny audit`.
- Escape hatches: `assume`, `{:axiom}` †, bodiless functions or lemmas †.
- Layout: specification in an abstract module, implementation in a refining module.
- Spec mutation exists only as a research prototype (IronSpec).

### Verus

- Escape hatches: `assume`, `admit`, `#[verifier::external_body]` †.
- Gate: no built-in gate.
  A syntax-tree comparison against a frozen contract exists as a research tool.
  No layout separates the statements, so the freeze is the user's review of the contract diff.
- Mentioning a cheat check in the prompt reduced escape-hatch use in one study, not to zero.

### SPARK

- Assumption listing: `gnatprove --assumptions`.
- Escape hatches: `pragma Assume`, `SPARK_Mode => Off` on a unit, justification annotations †.
  An agent blocked from `pragma Assume` has switched verification off instead.
- Levels: Bronze, Silver, Gold; the tool run is the same, the objectives differ.
- Failure triage: the user guide lists six causes (code bug, wrong assertion, wrong specification, modeling limit, timeout, prover limit).
- Layout: contracts in `.ads`, bodies in `.adb`.

### Frama-C (WP, EVA)

- Vacuity: WP smoke tests.
- Escape hatches: axioms in `axiomatic` blocks, `admit` annotations † (confirm the annotation kinds in the installed version).
- Layout: ACSL contracts in headers.

### Bounded model checkers for code (CBMC, ESBMC, Kani)

- Bounds: results hold up to the unwinding bound.
  Use CBMC's `--unwinding-assertions` † to confirm the bound covers the loops.
- Reachability: cover checks (`kani::cover!` †, CBMC `--cover` †); an assertion under an unreachable condition passes trivially.
- Escape hatches: `kani::assume` and `__CPROVER_assume` † that over-constrain inputs.

## Interactive provers

### Lean 4

- Assumption listing: `#print axioms <theorem>` (transitive).
  Allowlist the standard axioms the user approves.
- Gates: `lean4checker --fresh` re-checks the environment; Comparator compares the elaborated theorem statement against a trusted statement file.
- Escape hatches: `sorry`, new `axiom` declarations, `native_decide` † (adds an axiom that `#print axioms` shows), redefined definitions or notation that change what an unchanged statement means.
  Comparator does not catch definitions left open for the agent to fill; freeze the definitions the statements use.
- Program proofs in Lean are harder for agents than proofs in Dafny or Verus on the one benchmark that compares them.

### Rocq

- Assumption listing: `Print Assumptions <theorem>`.
- Gate: rocq-mcp's `rocq_verify` restates the original theorem outside the proof module and checks assumptions against an allowlist.
  Its fallback path on timeout is weaker and allows axiom-name spoofing.
- Escape hatches: `Admitted`, `admit`, `Axiom`, `Parameter` †, redefined types.

### Isabelle

- Escape hatches: `sorry`, `oops` †.
- Gate: build the session without quick-and-dirty mode †, which rejects `sorry`.
