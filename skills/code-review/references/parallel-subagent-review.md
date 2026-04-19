# Parallel Subagent Review Path

Use this path when reviewing non-trivial changes and a subagent dispatch tool is available.
Fan out critique across specialist subagents — always quality and spec compliance, plus architecture when warranted — then synthesize and have a devil's-advocate subagent stress-test the synthesis.
Keeps the main agent's context free for coordination, tiebreaks, and user dialogue.

> **Harness note.** This document uses `Agent` as the running example name for the subagent dispatch tool, and `model` as the example name for a per-dispatch model parameter.
> Substitute your harness's equivalents as needed; the workflow is the same.

## Architecture Subagent — When to Include

The architecture critique (Agent 1) is **conditional**, not default.
Include it when any of these apply:

- **Pre-merge / pre-PR review** — reviewing a branch against its target base.
- **User mentions "merge"** — explicit or implicit signal that this change is about to land.
- **User explicitly requests** architectural review, design feedback, or similar.
- **Main agent judgment** — the change crosses module boundaries, introduces new abstractions, modifies public APIs, or otherwise has architectural surface.
  In this case, **confirm with the user before dispatching** the architecture agent.

Skip the architecture agent for pre-commit reviews of localized changes, bug fixes within a single module, or when the user has asked for a quick correctness pass.

## Availability Gate

Run this check once at the start of Step 0, after the graph gate.

1. Confirm the `Agent` tool is available in this session.
2. Assess diff size and scope from Step 0 scope detection.
3. Decide using the table below.
4. If the parallel path was selected and the dispatch schema exposes a model parameter, surface the model question now (see Prerequisites step 4) — same decision point as the path choice.

| Condition                                             | Path                            |
| ----------------------------------------------------- | ------------------------------- |
| `Agent` tool unavailable                              | Single-agent (skip this path)   |
| Single file, \<50 lines, no cross-module surface      | Single-agent (overhead too big) |
| User explicitly asked for a "quick" or "sanity" check | Single-agent                    |
| 2+ files OR >100 lines OR cross-module OR spec-driven | Parallel-subagent               |
| Ambiguous                                             | Ask the user which they prefer  |

## Prerequisites Before Dispatch

Subagents have no conversation history.
Gather what they need first, or dispatch is wasted.

1. **Finish Step 1 Triage.**
   You need the prioritized file list, risk hotspots, and (if graph is on) the blast-radius snapshot to brief each subagent.
2. **Clarify intent with the user.**
   Ask, if not already clear:
   - What is this change trying to accomplish?
     Any non-obvious constraints?
   - Is there a spec, ticket, PRD, or design doc the implementation should match?
     If yes, where?
   - Any areas the user already knows are rough and wants (or does not want) scrutinized?
3. **Package a shared context block.**
   Build once, reuse across all four dispatches:
   - Scope refs (base branch, merge-base SHA, or staged).
   - The full diff (or pointer to it).
   - File list with priorities from triage.
   - Relevant surrounding code paths the reviewer will likely need to read.
   - Spec/intent summary from the user, verbatim where possible.
4. **Resolve the model (if the dispatch schema exposes one).**
   When the dispatch schema has a model parameter, the choice is the user's, not the harness default.
   - If the user specified a model earlier in the conversation, reuse it across every dispatch in this review.

   - Otherwise, ask once before dispatching, then record the answer and apply it uniformly to Agents 1–4.
     Suggested phrasing:

     ```text
     Subagent dispatch supports a model override (e.g., `opus`, `sonnet`, `haiku`).
     Which should I use for this review? I'll reuse it across all critique agents and the challenge pass.
     ```

   - Do not silently default.

## Step A — Parallel Critique

Dispatch all active subagents in a **single message** with multiple `Agent` tool calls so they run concurrently.
Always dispatch Agents 2, 3, and 4 (quality, spec compliance, security).
Include Agent 1 (architecture) only when the "When to Include" criteria above are met.
If the dispatch schema exposes a model parameter, the model MUST be resolved before dispatch — either from an explicit user specification earlier in the conversation, or by asking the user (see Prerequisites step 4).
Do not silently fall back to the runtime default; that choice belongs to the user.
Include the phrase **"think hard"** in the prompt to engage extended thinking.
Subagents must have explicit instructions to critique only — no code edits.
If available, include applicable `code-review-graph` instructions.

Use the prompt templates in the next section.

### Agent 1 — Architectural Critique

**Focus:** module boundaries, coupling, layering, separation of concerns, abstraction quality, API shape, hidden dependencies, blast radius, consistency with surrounding architecture, premature abstraction vs. missing abstraction.

### Agent 2 — Code Quality & Correctness

**Focus:** logic bugs, edge cases, nil/null paths, error handling, concurrency hazards, resource leaks, idiomatic usage, readability, naming, dead code, test adequacy for behavior changes, obvious performance pitfalls.

### Agent 3 — Spec Compliance

**Focus:** does the implementation do what the spec/ticket says?
Unstated behaviors added?
Required behaviors missing?
Scope creep?
Deviations from the spec's acceptance criteria?
If no spec was provided, report that the subagent was dispatched without one and focus only on stated PR intent.

### Agent 4 — Security Review

**Focus:** security vulnerabilities and control gaps across all OWASP Top 10:2025 categories.
Always dispatch — security is a required lens on every non-trivial review.
Subagents cannot invoke skills, so **you** (the orchestrator) must expand the prompt before dispatch.

**Before filling in Template — Agent 4:**

1. Identify the feature domain(s) from triage.
2. For each matching domain, read the corresponding `securing-code` tier3 reference and copy its **Review Checklist** section verbatim into the `## Domain-specific checks` placeholder in the template.

If no domain matches, omit the placeholder section — the OWASP checklist is still required.

**Covers:** broken access control, injection (SQL/NoSQL/OS/XSS), cryptographic failures, insecure design, auth failures, supply chain risks, data integrity, logging gaps, exceptional condition mishandling, and security misconfiguration.

## Step B — Synthesize

Main agent consolidates the three reports.
Do not delegate this.

1. Group findings by file/function.
2. Dedupe overlapping issues.
   When two or more agents raised the same concern, mark it **corroborated** — higher-confidence signal.
3. Resolve contradictions where possible.
   Where unresolved, mark **disputed** and queue for challenge pass or self-tiebreak.
4. Sort by priority (critical > high > medium > low).
5. Flag any finding whose verdict depends on intent you're not sure about; clarify with user before Step C.

## Step C — Challenge Pass (1 subagent, devil's advocate)

Dispatch one subagent (Agent 5) using the runtime's available schema and "think hard" in the prompt.
This agent challenges the **review itself**, not the code — it argues the author's side against the synthesized findings.
Give it:

- The synthesized findings from Step B.
- The original diff and shared context block.
- Instruction to attempt to **invalidate** the findings: which are wrong, overconfident, or missing counter-evidence?
  What issues were missed entirely?
  What are the strongest counter-arguments a thoughtful author would make?

The devil's-advocate subagent returns its own structured report: challenges, missed issues, and strength-of-evidence ratings.

## Step D — Final Synthesis and Tiebreak

Main agent again — not a subagent.

1. For each challenge raised: accept (drop/downgrade the finding), reject with rationale (keep as-is), or mark for tiebreak.
2. For tiebreak items, do targeted verification yourself: read the specific lines, run `Grep` for callers, check tests, inspect adjacent code.
   Do not dispatch another subagent for small checks.
3. For items that hinge on unstated intent, ask the user before finalizing.
4. Produce the final, deduped, priority-sorted issue list.

## Step E — Produce Report

Use the standard Step 3 report format from `SKILL.md`.
Add:

- A header line noting the parallel-subagent path was used.
- A short **Challenge Pass Summary** appendix listing challenges raised and how each was resolved.
- If graph was also used, include the Blast Radius and Test Coverage Gaps sections as normal.

## Agent Prompt Templates

Each subagent prompt should be self-contained: it will not see this conversation.

### Template — Agent 1: Architectural Critique

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

## Constraints
- Do NOT edit code.
- Do NOT comment on style nits or formatting.
- If intent is unclear, state what you assumed.

## Output format
A markdown list of findings. For each finding:
- Priority: critical | high | medium | low
- File:line (or function)
- Observation (1-3 sentences)
- Why it matters
- Suggested direction (not a full patch)
End with a brief summary of the 3 most important architectural concerns.
```

### Template — Agent 2: Code Quality & Correctness

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
- Dead code, unreachable branches
- Tests: are behavior changes covered? Are new tests meaningful?
- Obvious performance pitfalls (N+1, unbounded memory)

## Constraints
- Do NOT edit code.
- Style-only nits are non-blocking; mark them `low`.
- Reference exact file:line.

## Output format
Markdown list of findings, each with: priority, location, observation, why it matters, suggested direction. End with a summary of the top 3 correctness risks.
```

### Template — Agent 3: Spec Compliance

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

### Template — Agent 4: Security Review

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
- Do NOT comment on style or non-security quality issues — those belong to Agent 2.
- Reference exact file:line for every finding.

## Output format
Markdown list of findings, each with: priority (critical/high/medium/low), OWASP category, file:line, observation, impact, suggested direction.
End with a summary of the top 3 security risks and any OWASP categories that are clean.
```

### Template — Agent 5: Devil's Advocate (Challenge Pass)

```text
You are a senior engineer acting as devil's advocate against a code review.
Your target is the review itself, not the code — argue the author's side.
Think hard.

## Goal
Try to invalidate the findings below. Where are they wrong, overconfident, missing
counter-evidence, or misdiagnosing the real issue? What issues did the reviewers
miss entirely?

## Original diff
<full diff>

## Context and intent
<same shared context block>

## Findings to challenge
<synthesized findings from Step B, as a numbered list>

## What to produce
For each numbered finding: one of
- `confirm` — evidence is sound
- `challenge` — reason it may be wrong or overstated, with citation
- `downgrade` — finding is real but priority is too high, with reason
- `escalate` — finding is real and priority is too low, with reason

Then a section `missed issues` listing problems the four reviewers did not raise,
each with priority, location, observation, and why it matters.

Finish with a one-paragraph meta-critique: where does the overall review lean too hard, or too soft?
```

## Dispatch Call Shape

This is an example - you may have a different API surface.
Defer to the subagent tool schema available in the current runtime/harness.

```text
Agent({
  description: "Architectural critique",
  subagent_type: "general-purpose",
  model: "<specified_model>",
  prompt: "<template 1 filled in>",
})
Agent({
  description: "Code quality and correctness review",
  subagent_type: "general-purpose",
  model: "<specified_model>",
  prompt: "<template 2 filled in>",
})
Agent({
  description: "Spec compliance check",
  subagent_type: "general-purpose",
  model: "<specified_model>",
  prompt: "<template 3 filled in>",
})
Agent({
  description: "Security review",
  subagent_type: "general-purpose",
  model: "<specified_model>",
  prompt: "<template 4 filled in>",
})
```

All active subagent calls must be in a **single message** to run concurrently.
Omit Agent 1 unless the "When to Include" criteria apply.
Agents 2, 3, and 4 are always dispatched.
Challenge pass (Agent 5, devil's advocate) dispatches separately after Step B completes.

## Common Mistakes

- **Skipping intent clarification.**
  Subagents cannot ask the user; missing intent = guesswork at best, wasted dispatch at worst.
- **Letting subagents edit code.**
  They critique only.
  The main agent (or a later explicit request) handles edits.
- **Dispatching on a tiny diff.**
  Overhead is not worth it for \<50-line single-file changes.
- **Dispatching subagents sequentially.**
  Always fan out active critique agents in one message.
- **Dispatching the architecture agent by default.**
  It's conditional — see "When to Include" above.
- **Skipping the security agent.**
  Agent 4 is always dispatched alongside Agents 2 and 3 — not optional.
- **Dispatching without confirming the model.**
  If the harness exposes model selection, silent defaulting hides a cost/quality decision from the user.
  Ask once, reuse across all dispatches.
- **Treating the challenge pass as authoritative.**
  It's one more perspective; main agent arbitrates.
- **Delegating synthesis.**
  Synthesis and tiebreak belong to the main agent — that's where coordination context lives.
- **Forgetting "think hard".**
  The phrase engages extended thinking; omitting it leaves quality on the table.
