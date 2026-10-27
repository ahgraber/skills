# Partition Discovery

Defect discovery in `code-review` runs over a **partition list**: the features of the domain that the changed code handles.
The list is built before anyone looks for defects, so the search covers the domain instead of the neighborhood of the last defect found.
Each review explores the open partitions, follows every confirmed defect to its siblings, and saves the list so the next review starts where this one stopped.

## 1. Build the Partition List (triage)

The orchestrator builds the list during Step 1 triage, with a strong model.
A partition is one feature of the domain, stated in the domain's own terms: "here-documents feeding a pipeline", "options that change what `cd` resolves", "URLs with an IPv6 literal host".
A partition never names a file, a line, a defect, or an example input.

Take partitions from these sources, in this order:

1. **The domain's reference.**
   Name the domain the changed code models: a language, a protocol, a file format, a program's command line.
   List the reference's own sections or features (a language manual's grammar sections, a protocol's message types, a format's field kinds).
   For each feature, add a partition when the changed code reads, produces, or decides on input of that kind.
2. **The implementation's own tables.**
   For each allowlist, switch table, option parser, or registry the change adds or reads, add a partition per entry class.
   Example: for each allowlisted program, "arguments that make it read or run another file".
3. **The spec's input spaces.**
   For each universal requirement in the source of truth, add a partition per input-space partition (`sdd-spec-formats.md` § 1.6 in the `sdd` skill, when the project uses it).
4. **Generic constructs in the diff.**
   Error and exception paths, concurrency and shared state, resource lifetimes, boundary values, and data-structure invariants: add one partition for each construct the diff uses.
5. **Security, when the change touches a security boundary.**
   A change touches a security boundary when it parses or classifies untrusted input, makes an authorization, sandbox, or policy decision, or handles secrets or credentials.
   Add partitions from the trust-boundary and STRIDE sections of `securing-code` `references/tier3-threat-modeling.md`, from the OWASP Top 10:2025 categories that apply (`references/owasp-2025.md`), and from the matching tier3 domain checklists.
   Copy the checklist items a partition comes from into that partition's explorer prompt as its feature description; subagents cannot invoke skills.

On a later review, load the saved list first (§ 6), then add partitions for code the earlier list does not reach.
Do not rewrite or merge saved partitions to fit a new reading of them.

**Rank** the open partitions by risk: security boundary first, then partitions touched by the diff, then the rest.
Depth (§ 5) decides how many run.

## 2. Breadth Pass

Dispatch one **partition explorer** per open partition, on a small, fast model.
Give each explorer only the fields in the template below.
Do not add prior findings, prior verdicts, example inputs, edges to probe, or notes.
Prior content steers an explorer toward known defects and lowers what it finds elsewhere.
A small scope per explorer raises its hit rate, so list only the files that handle the partition.

```text
You are a partition explorer in a code review.
Do not edit any file.

## Partition
<one sentence: the domain feature>

## Files in scope
<the files that handle this feature>

## Review packet
<packet_path> — the diff and the source of truth. Read callers and tests as needed.

## Task
1. Decide whether the implementation handles this feature as the domain defines it.
2. For each way it does not, give one distinguishing input and the expected result.
   An input distinguishes when the correct implementation and this one give different results.
3. If the implementation handles the feature, say so and name the code that handles it.

## Output
For each candidate: file:line, the distinguishing input, the expected result, the result you predict this implementation gives, and one sentence on why.
Then one line: `handled` or `candidates: <N>`.
```

The architecture, spec-compliance, quality, test-adversary, and security subagents run in the same pass (see `parallel-subagent-review.md`).
Send at most 8 subagents in one message; batch the rest in rounds of 8.

## 3. Judge Candidates

A candidate is not a finding until it is judged.

1. **Run what can be run.**
   Dispatch one **runner** subagent with every runnable candidate.
   The runner writes each distinguishing input as a probe script under `$TMPDIR`, runs it with the project's own runner or interpreter, and compares the result with the expected result.
   It never edits a repository file.
   A candidate whose run gives the wrong result is a **confirmed finding**.
   A candidate whose run gives the expected result is refuted; drop it.
2. **Challenge what cannot be run.**
   Candidates that need a service, a race, or a design judgment go to the challenge pass (`parallel-subagent-review.md`, Step E) with the other lens findings.

Judge before the variant hunt.
A false positive that reaches the variant hunt adds partitions that later reviews explore again and again.

## 4. Variant Hunt

Run the variant hunt on confirmed findings only, with a strong model.
At standard depth, hunt only critical and high findings; at deep, hunt every confirmed finding.

```text
You are running variant analysis on a confirmed defect.
Do not edit any file.

## Defect
<file:line, the distinguishing input, the expected and actual results>

## Review packet
<packet_path>

## Task
1. List every plausible contributing cause.
   A defect often has more than one; do not commit to one reading.
2. State each cause as a domain feature the implementation does not handle, in one sentence.
   Make it more specific than "validate input" and less specific than one line of code.
3. For each cause, search vertically (every path that reaches the same code) and horizontally (sibling sites that handle the same feature).
4. Report each new instance as a candidate: file:line, distinguishing input, expected result.

## Output
The causes, each marked `new partition` or `already listed: <partition>`, then the candidates.
```

Add each `new partition` to the list, judge the new candidates (§ 3), and run a breadth pass on the new partitions only.
The loop ends when a round adds no partition, or when the depth's round cap is reached.
When the cap ends the loop, leave the unexplored partitions open; the next review explores them first.

## 5. Depth

State the depth and the number of subagents before dispatch, so the user can lower either.

| Depth    | Partitions explored                                      | Variant hunt                         | Rounds                        |
| -------- | -------------------------------------------------------- | ------------------------------------ | ----------------------------- |
| quick    | single-agent path; the reviewer checks partitions itself | none                                 | 1                             |
| standard | the 8 highest-ranked open partitions                     | critical and high confirmed findings | 2 (one variant round)         |
| deep     | every partition, closed ones included                    | every confirmed finding              | until no new partition, max 3 |

Default to standard.
Use quick when the user asks for a quick or sanity check, and deep when the user asks for a deep or exhaustive review.
To cut cost, explore fewer partitions; do not widen the files per explorer.

## 6. Closing Partitions and Review State

A partition **closes** when a property-based or differential test covers it: the test's generator spans the feature, or the test compares results with an oracle over generated inputs.
An example test does not close a partition.
Before a partition closes, the test adversary checks its property test the same way it checks any test: "What wrong implementation would still pass this property?"

A review explores open partitions, plus closed partitions whose files changed since they were last explored.
`build_review_packet.py` reports those as `stale_closed_partitions`.
A deep review explores every partition.

Save the list to the `state_path` that `build_review_packet.py` prints, as JSON:

```json
{
  "version": 1,
  "repo": "<repo name>",
  "branch": "<branch>",
  "base": "<base ref>",
  "partitions": [
    {
      "id": "P1",
      "feature": "here-documents feeding a pipeline",
      "source": "domain-reference | implementation-table | spec-input-space | generic-construct | security | variant of F3",
      "paths": [
        "src/lexer.py"
      ],
      "status": "open | closed",
      "closed_by": "tests/test_lexer.py::test_heredoc_pipeline_matches_bash",
      "explored": [
        {
          "head": "<sha>",
          "depth": "standard",
          "date": "<ISO date>"
        }
      ]
    }
  ],
  "runs": [
    {
      "head": "<sha>",
      "depth": "standard",
      "date": "<ISO date>",
      "report": "<report path>"
    }
  ]
}
```

- `paths` lists the files the partition's explorer read; the script compares them with the last explored head.
- Append to `explored` each time a partition runs.
- Record findings in the report, never in the state file.
  The state file feeds triage, and triage must not see prior findings.

## 7. Relation to `security-deep-scan`

The two skills prevent different failures.
Partitions prevent "nobody looked there": each feature of the domain gets its own explorer.
`security-deep-scan` runs repeated passes with the same brief and forbids themed lanes, to reduce "someone looked and missed it by chance".
When a change touches a security boundary and the user needs more than a review, offer `security-scan` or `security-deep-scan`.
