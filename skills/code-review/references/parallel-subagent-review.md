# Parallel Subagent Review Path

Use this path when reviewing non-trivial changes and a subagent dispatch tool is available.
Defect discovery runs over a partition list (`references/partition-discovery.md`): one small-model explorer per domain feature, a runner that executes their distinguishing inputs, and a variant hunt on each confirmed defect.
Lens subagents (architecture when warranted, spec compliance, quality, test adversary, security) run in the same pass.
A devil's-advocate subagent then runs a challenge pass on every finding that could not be run.
The main agent keeps coordination, tiebreaks, and user dialogue.

This path's rules — model resolution, the agent set, synthesis ownership, and the challenge pass — are purpose-built for code review and take precedence over any general subagent skill (e.g. `subagent-patterns`) when reviewing code.

> **Harness note.** This document uses `Agent` as the running example name for the subagent dispatch tool, and `model` as the example name for a per-dispatch model parameter.
> Substitute your harness's equivalents as needed; the workflow is the same.

## Architecture Subagent — When to Include

The architecture critique is **conditional**, not default.
Include it when any of these apply:

- **Pre-merge / pre-PR review** — reviewing a branch against its target base.
- **User mentions "merge"** — explicit or implicit signal that this change is about to land.
- **User explicitly requests** architectural review, design feedback, or similar.
- **Main agent judgment** — the change crosses module boundaries, introduces new abstractions, modifies public APIs, or otherwise has architectural surface.
  In this case, **confirm with the user before dispatching** the architecture agent.
- **The change adds a state, variant, field, or case to a data structure that crosses a boundary** — a module's public interface, an API payload, a stored record, a queued message.
  This one overrides the pre-commit exemption below.
  A data structure is cheapest to correct in the change that first gets it wrong, and the change that gets it wrong is usually small and local.

Skip the architecture agent for pre-commit reviews of localized changes, bug fixes within a single module, or when the user has asked for a quick correctness pass.

## Availability Gate

Run this check once at the start of Step 0, after the graph gate.

1. Confirm the `Agent` tool is available in this session.
2. Assess diff size and scope from Step 0 scope detection.
3. Apply the table below; the first matching row wins.
4. If the parallel path was selected, resolve the models and the depth now (Prerequisites steps 4 and 5) — same decision point as the path choice.

| Order | Condition                                               | Path                            |
| ----- | ------------------------------------------------------- | ------------------------------- |
| 1     | `Agent` tool unavailable                                | Single-agent (skip this path)   |
| 2     | User explicitly asked for a "quick" or "sanity" check   | Single-agent                    |
| 3     | Change touches a security boundary, or a spec drives it | Parallel-subagent, at any size  |
| 4     | Single file, \<50 lines, no cross-module surface        | Single-agent (overhead too big) |
| 5     | 2+ files OR >100 lines OR cross-module                  | Parallel-subagent               |
| 6     | Ambiguous                                               | Ask the user which they prefer  |

Row 3 comes before the size rows because a one-file change to a parser or a policy check carries the most risk per line.
`references/partition-discovery.md` § 1 defines a security boundary.

## Prerequisites Before Dispatch

Subagents have no conversation history.
Gather what they need first, or dispatch is wasted.

1. **Finish Step 1 Triage, including the partition list** (`references/partition-discovery.md` § 1).
   You need the prioritized file list, risk hotspots, the ranked partitions, and (if graph is on) the blast-radius snapshot.

2. **Clarify intent with the user.**
   Ask, if not already clear:

   - What is this change trying to accomplish?
     Any non-obvious constraints?
   - Is there a spec, ticket, PRD, or design doc the implementation should match?
     If yes, where?
   - Any areas the user already knows are rough and wants (or does not want) scrutinized?

3. **Package a shared context block.**
   The review packet from Step 0 (`scripts/build_review_packet.py`) is this block — build it once and hand every subagent its `packet_path` rather than inlining the diff into each prompt.
   The packet already carries:

   - Scope refs (base branch, merge-base SHA, or staged), the branch, and the full diff.
   - The changed-file list.
   - The source of truth (intent plus any `--include`d spec/plan), when provided.

   For lens subagents, add per-dispatch only what the packet lacks: file priorities from triage and the surrounding code paths a reviewer will likely need to read.
   Partition explorers get only their template's slots (`references/partition-discovery.md` § 2).

4. **Resolve the models (if the dispatch schema exposes a model parameter).**
   The choice is the user's, not the harness default.
   Ask once, name the two roles, then apply the answer to every dispatch in this review:

   ```text
   Subagent dispatch supports a model override.
   Partition explorers and the runner work best on a small, fast model (e.g., `haiku`); triage, architecture, spec compliance, quality, the test adversary, security, the variant hunt, and the challenge pass need a strong one (e.g., `opus` or `sonnet`).
   Which models should I use for each role?
   ```

   If the user specified models earlier in the conversation, reuse them.
   Do not silently default.

5. **State the depth and the dispatch count** (`references/partition-discovery.md` § 5).
   Example: "Standard depth: 8 of 23 partitions, 5 lens subagents, 1 runner, variant hunts on critical and high findings, 1 challenge pass — about 17 dispatches."
   The user can lower the depth or the partition count.

## Step A — Breadth Pass

Dispatch the partition explorers (`references/partition-discovery.md` § 2) and the lens subagents together, at most 8 per message; batch the rest in rounds of 8.
Every subagent prompt states that the subagent must not edit code.
Include the phrase **"think hard"** in each lens prompt to engage extended thinking.
If available, include applicable `code-review-graph` instructions.

Fill only each template's slots.
Do not add prior findings, prior verdicts, edges to probe, or notes from earlier runs.

### Lens 1 — Architectural Critique (conditional)

**Focus:** module boundaries, coupling, layering, separation of concerns, abstraction quality, API shape, hidden dependencies, blast radius, consistency with surrounding architecture, premature abstraction vs. missing abstraction, and the shape of the data that crosses boundaries.

Subagents cannot invoke skills, so **you** (the orchestrator) must expand the prompt before dispatch: copy the three tests from `references/data-representation.md` into the `## Data representation` placeholder in the template.

### Lens 2 — Code Quality & Correctness

**Focus:** logic bugs, edge cases, nil/null paths, error handling, concurrency hazards, resource leaks, idiomatic usage, readability, naming, dead code, duplication, obvious performance pitfalls.
Partition explorers search by domain feature; this lens reads the diff line by line for defects that belong to no feature, such as an off-by-one, a wrong operator, or a wrong default.
Test adequacy belongs to Lens 4.

### Lens 3 — Spec Compliance

**Focus:** does the implementation do what the spec/ticket says?
Unstated behaviors added?
Required behaviors missing?
Scope creep?
Deviations from the spec's acceptance criteria?
If no spec was provided, report that the subagent was dispatched without one and focus only on stated PR intent.
When the packet reports `has_source_of_truth: false`, this is that case — proceed on stated intent and do not infer a spec from the diff; if a spec exists, the better fix is to rebuild the packet with `--intent`/`--include` rather than skip this lens.

### Lens 4 — Test Adversary

**Focus:** for the tests that cover the changed behavior, "What wrong implementation would still pass these tests?"
For each answer, the test adversary writes an input that distinguishes the wrong implementation from the right one and runs it against the real code.
A wrong result is a defect; a right result that no test checks is a test gap.
It also checks each property test that would close a partition (`references/partition-discovery.md` § 6).
It writes probe scripts only under `$TMPDIR`, runs them with the project's own runner or interpreter, and never edits a repository file.

### Lens 5 — Security Review

**Focus:** security vulnerabilities and control gaps across all OWASP Top 10:2025 categories.
Always dispatch — security is a required lens on every non-trivial review.
Security partitions (`references/partition-discovery.md` § 1) add depth on a security boundary; this lens covers the whole change, including dependency, logging, and configuration changes that no partition reaches.
Subagents cannot invoke skills, so **you** (the orchestrator) must expand the prompt before dispatch.

**Before filling in Template — Lens 5:**

1. Identify the feature domain(s) from triage.
2. For each matching domain, read the corresponding `securing-code` tier3 reference and copy its **Review Checklist** section verbatim into the `## Domain-specific checks` placeholder in the template.

If no domain matches, omit the placeholder section — the OWASP checklist is still required.

**Covers:** broken access control, injection (SQL/NoSQL/OS/XSS), cryptographic failures, insecure design, auth failures, supply chain risks, data integrity, logging gaps, exceptional condition mishandling, and security misconfiguration.

## Step B — Judge Candidates

Collect the explorer candidates and run them (`references/partition-discovery.md` § 3).
Dispatch one runner subagent, on the small model, with every runnable candidate.
Confirmed candidates become findings; refuted candidates are dropped.
Candidates that cannot be run go to Step E with the lens findings.

## Step C — Variant Hunt

For each confirmed finding the depth selects, dispatch a variant hunt (`references/partition-discovery.md` § 4).
Judge its candidates the way Step B judges explorer candidates.
Run Step A again for the new partitions only, explorers only.
Stop when a round adds no partition, or at the depth's round cap.

## Step D — Synthesize

Main agent consolidates all reports.
Do not delegate this.

1. Group findings by file/function.
2. Dedupe overlapping issues.
   When two or more subagents raised the same concern, mark it **corroborated** — higher-confidence signal.
3. Resolve contradictions where possible.
   Where unresolved, mark **disputed** and queue for Step E or self-tiebreak.
4. Sort by priority (critical > high > medium > low).
5. Flag any finding whose verdict depends on intent you're not sure about; clarify with user before Step E.

## Step E — Challenge Pass (1 subagent, devil's advocate)

Dispatch one subagent with a strong model and "think hard" in the prompt.
This agent challenges the **review itself**, not the code — it argues the author's side against the synthesized findings.
It checks every finding that a run did not confirm: architecture, quality, spec-compliance, and security findings, and candidates that could not be run.
Findings a run confirmed skip this step; the run is their evidence.
For each finding it asks: is it wrong, overconfident, or missing counter-evidence, and what is the strongest counter-argument a thoughtful author would make?
It returns challenges and a strength-of-evidence rating for each finding.
The challenge pass does not search for new defects.
It has read every finding, so its search would start from them; discovery belongs to Steps A and C, where the search starts without prior findings.

## Step F — Final Synthesis and Tiebreak

Main agent again — not a subagent.

1. For each challenge raised: accept (drop/downgrade the finding), reject with rationale (keep as-is), or mark for tiebreak.
2. For tiebreak items, do targeted verification yourself: read the specific lines, run `Grep` for callers, check tests, inspect adjacent code.
   Do not dispatch another subagent for small checks.
3. For items that hinge on unstated intent, ask the user before finalizing.
4. Produce the final, deduped, priority-sorted issue list.

## Step G — Produce Report

Use the standard Step 3 report format from `SKILL.md`, and persist the synthesized report and the review state as Step 3 describes.
Add:

- A header line noting the parallel-subagent path and the depth.
- A **Partitions** appendix: each partition explored this run, its result (`handled`, findings, or new partitions it produced), and the open partitions left for the next run.
- A short **Challenge Pass Summary** appendix listing challenges raised and how each was resolved.
- If graph was also used, include the Blast Radius and Test Coverage Gaps sections as normal.

## Agent Prompt Templates

Each subagent prompt is self-contained: it will not see this conversation.
The partition explorer and variant-hunt templates are in `references/partition-discovery.md`.

In every template below, point the `## Diff` (and `## Context` / `## Intent and Spec`) placeholders at the packet rather than inline its contents: `Start from the review packet at <packet_path> — it has the diff, changed files, and source of truth, but it is a starting point, not the whole picture. You have Read/Grep/git; pull callers, surrounding code, and any file the diff does not show whenever a finding depends on it.` Inline a snippet only when a finding needs a specific excerpt called out.

### Template — Lens 1: Architectural Critique

```text
You are a staff-level software architect reviewing a code change.
Think hard.

## Goal
Critique this change on architectural grounds only. Do NOT rewrite code; produce findings.

## Context
- Repo: <path or name>
- Scope: <pre-commit | pre-merge against {base}>
- Intent (from author/user): <short summary>
- Spec or design doc (if any): <paste or summarize>

## Diff
<full diff or pointer>

## Files of interest (from triage, priority-ordered)
<list>

## What to evaluate
- Module boundaries and layering
- Coupling and cohesion; hidden dependencies
- API shape, extensibility, and backward compatibility
- Separation of concerns
- Abstraction quality — premature? missing? wrong shape?
- Consistency with the surrounding architecture
- Blast radius of the change

## Data representation
Check the data structures that cross a boundary first: a module's public interface, an API payload, a stored record, a queued message.
For every field this change adds, ask whether it belongs to a type that already exists — a new field placed beside a type instead of inside it is how this problem usually enters.

<orchestrator: paste the tests from references/data-representation.md here>

## Constraints
- Do NOT edit code.
- Do NOT comment on style nits or formatting.
- If intent is unclear, state what you assumed.
- For data representation findings, supply the evidence the test calls for.
  A finding without it is an impression — leave it out.

## Output format
A markdown list of findings. For each finding:
- Priority: critical | high | medium | low
- File:line (or function)
- Observation (1-3 sentences)
- Why it matters
- Suggested direction (not a full patch)
End with a brief summary of the 3 most important architectural concerns.
```

### Template — Lens 2: Code Quality & Correctness

```text
You are a senior engineer doing a correctness-focused code review.
Think hard.

## Goal
Find bugs, edge cases, and quality issues. Do NOT rewrite code; produce findings.

## Context
- Repo: <...>
- Scope: <...>
- Intent (from author/user): <...>

## Diff
<full diff>

## Files of interest
<priority-ordered list>

## What to evaluate
- Logic bugs, off-by-one, wrong-operator, wrong-default
- Edge cases: nil/null/empty, boundary values, unicode, timezones, concurrency
- Error handling and propagation
- Resource handling (files, connections, goroutines/tasks)
- Idiomatic usage and readability
- Dead code, unreachable branches, duplication
- Obvious performance pitfalls (N+1, unbounded memory, sync calls in hot paths)

## Constraints
- Do NOT edit code.
- Style-only nits are non-blocking; mark them `low`.
- Reference exact file:line.

## Output format
Markdown list of findings, each with: priority, location, observation, why it matters, suggested direction. End with a summary of the top 3 correctness risks.
```

### Template — Lens 3: Spec Compliance

```text
You are a reviewer checking a code change against its spec.
Think hard.

## Goal
Determine whether the implementation matches the stated intent and spec.
Do NOT rewrite code.

## Intent and Spec
Author intent: <summary>
Spec/ticket/PRD:
<paste verbatim or summarize with pointer>

## Diff
<full diff>

## Files of interest
<list>

## What to evaluate
- Does each acceptance criterion (explicit or implied) have a corresponding implementation?
- Are there behaviors in the diff that the spec does not require? (scope creep)
- Are there behaviors the spec requires but the diff does not implement? (gaps)
- Are any deviations from the spec justified in the change itself or author intent?

## Constraints
- Do NOT edit code.
- If no spec was provided, say so and focus on stated author intent only.
- Be specific: tie each finding to a spec line/criterion where possible.

## Output format
Markdown list of compliance findings with priority, location, spec reference, observation, and suggested direction. End with a verdict: `matches spec`, `partial — {N} gaps`, `exceeds spec — {N} scope items`, or `no spec provided`.
```

### Template — Lens 4: Test Adversary

```text
You are a test adversary in a code review.
Think hard.

## Goal
Find defects and test gaps by asking what wrong implementation the tests would still accept.
Do NOT edit any repository file.

## Context
- Repo: <...>
- Scope: <...>
- Intent (from author/user): <...>

## Diff
<full diff>

## Tests in scope
<test files that cover the changed behavior>

## Property tests proposed to close partitions
<test id → partition, or "none">

## Task
1. For each test in scope, name the wrong implementations it would still accept.
2. For each, write a distinguishing input: one where the correct and the wrong implementation give different results.
3. Write each input as a probe script under $TMPDIR and run it against the real code with the project's own runner or interpreter.
4. For each proposed property test, ask the same question of its property and generator.

## Constraints
- Write files only under $TMPDIR. Never edit a repository file.
- Run only the project's own test runner or interpreter.

## Output format
For each probe: the wrong implementation it targets, the input, the expected and actual results, and the probe path.
Classify each as `defect` (actual is wrong), `test gap` (actual is right but no test checks it), or `covered`.
For each property test: `spans the partition` or the wrong implementation it would accept.
```

### Template — Runner

```text
You are the runner in a code review.
Do NOT edit any repository file.

## Candidates
<numbered list: file:line, distinguishing input, expected result>

## Review packet
<packet_path>

## Task
For each candidate, write the input as a probe script under $TMPDIR, run it against the real code with the project's own runner or interpreter, and compare the result with the expected result.

## Output format
For each candidate: `confirmed` (result differs from expected), `refuted` (result matches expected), or `not runnable` (with the reason), plus the actual result and the probe path.
```

### Template — Lens 5: Security Review

```text
You are a senior application security engineer doing a security-focused code review.
Think hard.

## Goal
Find security vulnerabilities and control gaps. Do NOT rewrite code; produce findings.

## Context
- Repo: <...>
- Scope: <pre-commit | pre-merge against {base}>
- Feature type: <API endpoint / auth flow / file handling / data processing / other>
- Intent (from author/user): <short summary>

## Diff
<full diff>

## Files of interest (from triage, priority-ordered)
<list>

## What to evaluate

Work through each OWASP Top 10:2025 category relevant to this change:

- **A01 Broken Access Control** — authorization on every request, object-level checks, deny-by-default, no IDOR
- **A02 Security Misconfiguration** — no default credentials, no unnecessary exposure, security headers, no system details in errors
- **A03 Supply Chain** — pinned deps, no suspicious packages, integrity checks on artifacts
- **A04 Cryptographic Failures** — no plaintext sensitive data, approved algorithms, no hardcoded keys, secure RNG
- **A05 Injection** — parameterized queries (SQL + NoSQL), no concatenation into queries/system calls, allowlist input validation, context-aware output encoding
- **A06 Insecure Design** — business logic limits, no race conditions in critical flows, trust boundaries enforced
- **A07 Authentication Failures** — no custom auth, MFA support, brute-force defenses, session rotation, secure cookies
- **A08 Data Integrity** — no unsafe deserialization, signatures on updates/plugins, signed CI/CD builds
- **A09 Logging Failures** — security events logged, no secrets/PII in logs, required fields present
- **A10 Exceptional Conditions** — fail closed, full rollback on error, no internal details to users, resource limits

Additional checks:
- Rate limiting present; no wildcard boundaries
- CSRF protection on state-changing cookie-session operations
- No user input to eval, system calls, or deserialization
- Not running as root; variables initialized; warnings as errors
- Language-specific anti-patterns (eval, innerHTML, pickle, BinaryFormatter, etc.)

## Domain-specific checks
<orchestrator: paste the Review Checklist from the matching tier3 reference(s) here, or omit this section if no domain matched>

## Constraints
- Do NOT edit code.
- Do NOT comment on style or non-security quality issues — those belong to Lens 2.
- Reference exact file:line for every finding.

## Output format
Markdown list of findings, each with: priority (critical/high/medium/low), OWASP category, file:line, observation, impact, suggested direction.
End with a summary of the top 3 security risks and any OWASP categories that are clean.
```

### Template — Challenge Pass (Devil's Advocate)

```text
You are a senior engineer acting as devil's advocate against a code review.
Your target is the review itself, not the code — argue the author's side.
Think hard.

## Goal
Try to invalidate the findings below. Where are they wrong, overconfident, missing
counter-evidence, or misdiagnosing the real issue?

## Original diff
<full diff>

## Context and intent
<same shared context block>

## Findings to challenge
<numbered list: synthesized findings not confirmed by a run>

## What to produce
For each numbered finding: one of
- `confirm` — evidence is sound
- `challenge` — reason it may be wrong or overstated, with citation
- `downgrade` — finding is real but priority is too high, with reason
- `escalate` — finding is real and priority is too low, with reason

Do not report new defects.
Finish with a one-paragraph meta-critique: where does the overall review lean too hard, or too soft?
```

## Dispatch Call Shape

This is an example - you may have a different API surface.
Defer to the subagent tool schema available in the current runtime/harness.

```text
Agent({
  description: "Explore partition P3: here-documents feeding a pipeline",
  subagent_type: "general-purpose",
  model: "<small_model>",
  prompt: "<partition explorer template filled in>",
})
Agent({
  description: "Architectural critique",
  subagent_type: "general-purpose",
  model: "<strong_model>",
  prompt: "<template — lens 1 filled in>",
})
Agent({
  description: "Code quality and correctness review",
  subagent_type: "general-purpose",
  model: "<strong_model>",
  prompt: "<template — lens 2 filled in>",
})
Agent({
  description: "Spec compliance check",
  subagent_type: "general-purpose",
  model: "<strong_model>",
  prompt: "<template — lens 3 filled in>",
})
Agent({
  description: "Test adversary",
  subagent_type: "general-purpose",
  model: "<strong_model>",
  prompt: "<template — lens 4 filled in>",
})
Agent({
  description: "Security review",
  subagent_type: "general-purpose",
  model: "<strong_model>",
  prompt: "<template — lens 5 filled in>",
})
```

Send the explorers and lenses for one round in a **single message**, at most 8 calls; batch the rest in rounds of 8.
Omit Lens 1 unless the "When to Include" criteria apply.
Lenses 2 through 5 are always dispatched.
The runner (small model) dispatches after the breadth pass, each variant hunt (strong model) after its finding is confirmed, and the challenge pass (strong model) after Step D completes.

## Common Mistakes

- **Skipping intent clarification.**
  Subagents cannot ask the user; missing intent = guesswork at best, wasted dispatch at worst.
- **Letting subagents edit code.**
  They critique only; the test adversary and the runner write only under `$TMPDIR`.
- **Seeding the partition list from the last review's findings.**
  Partitions come from the domain, the implementation's tables, the spec, and the diff's constructs (`references/partition-discovery.md` § 1).
- **Adding prior findings, edge lists, or notes to an explorer prompt.**
  The explorer then searches near the last defect, and each review finds one more class instead of all of them.
- **Running the variant hunt on unjudged candidates.**
  A false positive then adds partitions that every later review explores.
- **Ending the loop because explorers found nothing.**
  The loop ends when a round adds no partition; the partition list, not the findings, sets the search.
- **Dispatching on a tiny diff that touches no security boundary.**
  Overhead is not worth it for \<50-line single-file changes; row 3 of the gate overrides this for security and spec-driven changes.
- **Exceeding 8 subagents in one message.**
  Batch in rounds of 8.
- **Dispatching the architecture agent by default.**
  It's conditional — see "When to Include" above.
- **Dispatching without resolving the models.**
  If the harness exposes model selection, silent defaulting hides a cost/quality decision from the user.
  Ask once, reuse across all dispatches.
- **Skipping the security lens.**
  Lens 5 is always dispatched alongside Lenses 2 through 4; security partitions do not replace it.
- **Asking the challenge pass for missed issues.**
  The challenge pass has read every finding, so its search would start from them; discovery belongs to the breadth pass.
- **Treating the challenge pass as authoritative.**
  It's one more perspective; main agent arbitrates.
- **Delegating synthesis.**
  Synthesis and tiebreak belong to the main agent — that's where coordination context lives.
- **Forgetting "think hard".**
  The phrase engages extended thinking; omitting it leaves quality on the table.
