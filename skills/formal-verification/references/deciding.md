# Stage 1: Decide

This stage decides whether formal verification fits the purpose and, if it does, which tool and which verified object.
"Not a fit" is a complete outcome.

Gap: user:agent.
Close it by stating the question, the property kinds, and the recommended tool back to the user, and getting their agreement.

## Entry check

User requirements exist (see "Requirements source" in `alignment-file.md`), or the user agrees to state them now.
If neither, record user:spec as open before you continue, and tell the user what that means for any later result: it will describe the code or the model, not their intent.

## Procedure

1. List the requirements the purpose depends on.
2. Classify each requirement by the questions below.
   Work per requirement; one effort often has requirements in different branches.
3. Apply the tie-breakers inside the branch.
4. State the outcome to the user: the tool, the verified object, the reason, and the cheaper instrument you rejected and why.
5. Record the outcome in the Decision section.
   For "not a fit", record the recommended instrument and the reason, so that a later session does not reopen the question without new facts.

## Decision questions

1. **Would failure be expensive?**
   Expensive means data loss or corruption, a security breach, financial error, state that cannot be recovered, or costly rework.
   - No: use tests, including property-based tests and fuzzing, beyond ordinary example tests.
     Formal verification is not a fit.
2. **What does the property constrain?**
   - **A quantity over runs**: a percentile, an average, a probability, "can always", "returns the same output as".
     These compare runs, and TLA+ and most model checkers state properties of each individual run.
     Use probabilistic model checking (PRISM, Storm) for a model in their languages, differential testing for "same output as", and benchmarks, simulation, or evaluations for performance and statistical quality.
   - **Performance, user experience, or statistical quality of a learned system**: not a formal target.
     Use benchmarks and evaluations.
   - **Sequences of states under choices the author does not control** (concurrency, crashes, message loss, timing): go to question 3.
   - **Functional correctness of specific code**: go to question 5.
3. **Does a cheaper instrument cover it?**
   Examples: a serializable transaction, a concurrency testing tool for the language's memory model (loom, JCStress), or deterministic simulation.
   - Yes: use the cheaper instrument.
     Note that PlusCal and TLC assume every thread sees memory operations in one order; bugs that depend on weaker memory ordering need those language-level tools.
   - No: go to question 4.
4. **Does the bug show up in a small instance?**
   - Yes: model-check the design (TLC, Apalache, Quint, P, Alloy, Spin).
   - No: prove the design (TLAPS, Isabelle, an inductive invariant with Apalache or an IC3 engine).
   - Then ask: must the code match the model?
     If yes, stage 5 applies; choose the connection in `connecting-to-code.md` now, because it changes how the model is written.
     If no, the result is design insight; record that scope.
5. **Can the code be written or reshaped for proof?**
   Some teams rewrite the code in a verification language first, or verify a model and test the production code against it.
   - No: use bounded model checking (Kani, CBMC, ESBMC), property-based testing, or fuzzing.
   - Yes: go to question 6.
6. **Is SMT automation enough?**
   - Yes: an SMT-backed verifier (Dafny, Verus, SPARK, Frama-C WP, F\*).
     Choose the level of rigor per component; SPARK's Bronze, Silver, and Gold levels are the clearest ladder.
   - No: interactive proof (Lean, Rocq, Isabelle).

Rigor is chosen per component.
A formal specification with no proof is often the right place to stop.
State that option to the user when the purpose is design insight.

## Tie-breakers

Apply these when the branch leaves two or more candidate tools.

- **Can the approver read the statement language?**
  Stage 3 ends with a person approving each statement.
  If no approver can read the candidate languages, approval rests on the blind back-translation and the can-fail checks.
  Tell the user this before choosing, and let them decide whether that serves their purpose.
  Within a branch, prefer a language the approver can read (for example, Quint over TLA+, or Dafny over Lean, where both fit).
- **Can the statements live in files that are frozen whole?**
  The freeze is exact only when each statement and every definition it depends on sit in files of their own.
  See "Layout for the freeze" in `specifying.md`.
  If the user wants assurance, prefer a tool where that layout is possible.
- **Is the code's language supported?**
  Code-level tools are bound to a language: Verus and Kani to Rust, SPARK to Ada, Frama-C and CBMC to C, Dafny to its own language with compilation to several targets.
  Design-level tools are language-neutral and need stage 5 to say anything about code.

## Signals from a spec-driven workflow

When the repo uses SDD, its requirement shapes (guarantee, invariant, prohibition, precondition and consequence) are the forms formal properties take.
A universal claim ("never", "always", "at most once") that the change's scenarios only sample is the strongest signal that question 1 onward applies.
Phrases such as "at most one", "eventually", "lease", or "quorum" are hints to run the questions, not a rule; a requirement worded "returns the balance" can hide a concurrency property.
