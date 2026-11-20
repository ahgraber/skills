# Standard Review

A standard review is the default review (`SKILL.md`, Step 0).
The lenses and the test adversary read the change and write claims, one consolidator groups them, a challenger argues against each claim, and the synthesizer writes the report.
It takes about seven dispatches with one component; each further component, up to three, adds a quality lens and a test adversary, and each further twelve records to judge add a challenger.

It does not use the partition list, and it does not dispatch a list builder, keeper, inspector, runner, hunter, or forms checker; `dispatch` refuses those roles.
It checks the inputs near the existing tests, through the test adversary, but it does not check every kind of input the domain allows.
That is what a deep review adds (`deep-review.md`).

`review-dispatch.md` holds the details this file points to: how to dispatch a role, what to gather first, each role, and the report.
Read it before the first dispatch.

## Steps

From step 3 on, after each step, run `review_state.py dispatch --review <review_id>` with no role, dispatch each entry it prints, and do what `next` says; the steps below are the order `next` follows.
Steps 1 and 2 come first because `dispatch` with no role registers the lenses for the whole change.

1. **Prepare and start the review** (`review-dispatch.md`, "Prerequisites Before Dispatch").
   Clarify the intent, find how the project runs its tests, decide on the architecture section, start the review with `start-review --depth standard`, and resolve the models.
   Tell the user the packet's size (`packet_tokens` from the packet script).
   Do not offer another depth: the review type is the user's call.
2. **Decide the components** (`review-dispatch.md`, "Components").
   Keep the change as one component unless it has parts that do not depend on each other.
   With more than one, register each component's quality lens with `dispatch quality-lens --component <name> --paths <file>...` before the first `dispatch` with no role.
3. **Dispatch the lenses and the test adversary**, all at the same time (`review-dispatch.md`, "Lenses and Test Adversary"): the quality lens, the security lens, the spec lens when there is a spec, and the test adversary.
4. **Dispatch the consolidator** (`review-dispatch.md`, "Consolidator").
   It drops duplicates and groups the records into failure modes.
5. **Dispatch the challenger** (`review-dispatch.md`, "Challenger").
   It judges every record that does not have a run.
   The test adversary ran its own probes, so its records already have verdicts; the challenger gets only those whose probe could not run or whose expected result does not cite a source.
6. **Ask the user to rule on each disputed record of critical or high priority**, when `next` names any (`review-dispatch.md`, "Challenger").
7. **Dispatch the synthesizer and present the report** (`review-dispatch.md`, "Synthesis" and "Report").

## Going Deeper

To turn a standard review into a deep one, run `update-review --review <review_id> --depth deep`.
`next` then names the list builders, and the review goes on from Step A of `deep-review.md`; the records it already has are kept.
A record the challenger already judged keeps its verdict, and a runner does not run it.
Do this only when the user asks for it.

## Without a Subagent Tool

Run each role yourself in the order of the steps above (`review-dispatch.md`, "Without a Subagent Tool").
