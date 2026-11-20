# Test Portfolio

## Outcome

A test suite shaped to give maximum confidence at minimum cost, with the right tests at the right level of the stack.

## The Testing Pyramid

Mike Cohn introduced the testing pyramid in 2009.
Martin Fowler elaborated and popularized it.
The shape from bottom to top:

```text
        /\
       /E2E\         few — slow, brittle, expensive
      /------\
     /        \
    /Integration\    some — verify component contracts
   /------------\
  /              \
 /   Unit tests   \  many — fast, isolated, cheap
/------------------\
```

**The two core rules (Fowler):**

1. Write tests at different granularities.
2. The more high-level you get, the fewer tests you should have.

**Why the shape:** high-level tests are slow, costly to maintain, and fail for reasons unrelated to the behavior under test (timing, environment, adjacent services).
Unit tests are fast (milliseconds) and diagnosable.
The shape reflects cost-per-test rising as you move up.

**The ice-cream cone anti-pattern** is the inverted pyramid: many slow E2E tests, few unit tests.
It produces a suite that is expensive to maintain, slow to run, and fails non-deterministically.

**When the pyramid breaks down:**

> "If my high-level tests are fast, reliable, and cheap to modify — then lower-level tests aren't needed." — Fowler

The pyramid's assumptions fit monoliths with complex branching logic.
They break down for:

- **Microservices**: the service boundary is the natural unit.
  Internal logic is often simple; cross-service interaction is the primary source of bugs. → Use the honeycomb model.
- **Frontend / dynamic-language apps**: static analysis (type checking, linting) already eliminates many structural bugs. → Use the trophy model.
- **Data pipelines and pure transformations**: the input-output contract is what matters. → Integration tests at the transformation boundary.
- **Legacy code**: the code was not written to be unit-testable. → Characterization tests at whatever granularity the code will support.

## Alternative Models

### Testing Trophy (Kent C. Dodds)

Adds static analysis as a first-class layer at the base; shifts the bulk to integration tests.

```text
      /\
     /E2E\
    /------\
   /        \
  /Integration\   ← widest: most tests here
 /------------\
/    Unit      \
/--------------\
/ Static / Lint  \  ← foundation: type checking, linting
/------------------\
```

**Key claim:** integration tests have the highest ROI.
They test multiple units interacting without a real browser or network, catching the bugs that unit tests miss — where component A works alone and B works alone but they fail together.

**Mocking stance:** mock only at network/infrastructure boundaries.
"When you mock something you're removing all confidence in the integration between what you're testing and what's being mocked."

**Guiding principle:** "The more your tests resemble the way your software is used, the more confidence they can give you."

Best fit: frontend and JS/TS applications, dynamically typed languages, monoliths where static analysis is not a built-in compiler guarantee.

### Service Honeycomb (Spotify)

Designed for microservice architectures where service interaction is the primary failure mode.

```text
  [ Integrated ]   ← fewest: avoid entirely if possible
  [Integration ]   ← most: service tested with real infra
  [ Impl Detail]   ← few: only for isolated complex logic
```

- **Implementation detail tests** (bottom, few): isolated unit tests for internally complex, naturally separable logic (e.g., a parser, an algorithm).
  Standard unit tests.
- **Integration tests** (middle, most): the service is spun up with real infrastructure (real database, in-memory queue).
  The API is called directly.
  No other production services are needed.
  This is the primary layer.
- **Integrated tests** (top, fewest — ideally zero): tests whose pass/fail depends on another production service being correct.
  Defined as Rainsberger's "integrated tests": the test cannot be run independently.
  Spotify explicitly recommends eliminating these.

**The key insight:** the microservice _is_ the unit.
Treating the service as the unit and using real infrastructure gives refactoring freedom — you can restructure internals, switch database engines, or rearrange modules without changing the tests.

**Trade-off accepted:** when a test fails you follow a stack trace rather than having a single-component failure.
Spotify considers this worthwhile for the confidence and refactoring freedom gained.

## Scope Decision Guide

Match test scope to the natural behavioral unit of the code.
Answer these in order:

**1.**
**What is the natural behavioral unit?**

- Pure function, no collaborators → unit test.
- Component coordinating several tested sub-components → integration test at the component boundary.
- Service or module with a defined API boundary → service-level integration test (real or in-process infrastructure).
- User-facing workflow spanning the full stack → E2E (few, critical paths only).

**2.**
**What is the primary failure mode you're guarding against?**

- Internal logic errors (off-by-one, wrong formula) → unit tests with boundary inputs; consider property-based testing for algorithmic code.
- Integration wiring failures (wrong field name, protocol mismatch) → integration tests or contract tests.
- Cross-service communication regression → contract tests.
- Full-system user-facing degradation → E2E tests.

**3.**
**What is the cost of false isolation?**
If mocking a dependency makes the test pass even though the real dependency would behave differently, the test provides false confidence.
The higher this risk, the more the test should use real collaborators or realistic in-process substitutes.

**4.**
**What is the cost of slow feedback?**
A TDD inner loop running in seconds gets exercised dozens of times per hour.
A 10-minute suite gets run once per hour.
Protect fast-running tests for the development loop; accept slower integration tests in CI.

**5.**
**Can you state a general invariant?**
If the code is a pure function and you can specify properties that must hold over the input domain, add property-based tests alongside example-based tests (see below).

**6.**
**Is this legacy, untested code?**
First priority: introduce seams to break hard dependencies.
Second: write characterization tests at whatever granularity the code will support.
Avoid big-bang rewrites under the assumption that starting over is safer.

## Rainsberger's Collaboration + Contract Tests

J.B.
Rainsberger argues that integrated tests (tests whose result depends on the correctness of more than one non-trivial component) cause combinatorial explosion: a system with 10 layers and 3–4 branches each has 3^10–4^10 distinct integrated paths.
Teams can write 2–5% of the needed integrated tests, creating a false sense of security that grows worse as complexity increases.

His alternative — two-sided boundary testing:

For every boundary between a client (A) and a server (B):

- **Collaboration tests** on the client side: use a stub of B; assert that A sends the right messages.
- **Contract tests** on the server side: assert that B correctly handles the queries A's collaboration tests say it sends, and returns the responses A expects.

This scales linearly in component boundaries rather than exponentially in integrated paths.
It tests each boundary from both sides without wiring the components together.
Pact and Consumer-Driven Contract frameworks operationalize this pattern.

**When to apply:** multiple independently deployed services, frequent API evolution, separate teams owning client and server sides.

**Limitations:** contract tests verify structural correctness of the interface, not the correctness of side effects (e.g., that the database was updated correctly).
They complement, not replace, integration tests for a service's internal behavior.

## Multiple Write-Sites and Derived-Pair Invariants

**Multiple write-sites:** when the same contract outcome can be produced by more than one code path (canonical path, dedup shortcut, cache hit, idempotency early-return), each path needs its own test.
A test of the canonical path does not prove the shortcut is correct.

```text
// Test the canonical path
result = repo.save(record, mode=CANONICAL)
assert result.id != null

// Also test the shortcut — it may skip validation or use a different write order
result = repo.save(record, mode=DEDUP)
assert result.id != null
assert result.normalized_url == normalize(record.url)
```

**Derived-pair invariants:** when a spec asserts `field_a == f(field_b)` and the two fields are written by different producers, neither field-local tests nor per-producer tests prove the invariant holds after composition.
Write a post-composition test.

```text
// Each producer may be correct in isolation but the pair must be verified together
manifest = merge(resolver_output, fetcher_output)
assert manifest.normalized_url == normalize(manifest.source_url)
```

## Avoid Duplicate Coverage Across Levels

Push tests as far down the pyramid as they can go while still providing meaningful signal.
If a higher-level test catches a failure that no lower-level test catches, write the lower-level test — and consider simplifying the higher-level one.

```text
// A bug caught by an E2E test means:
// 1. There is a bug in production code (fix it)
// 2. There is a missing or insufficient lower-level test (write it)
```

## Property-Based Testing

Property-based testing (PBT) replaces specific example inputs with _generators_ that produce random inputs across a domain, and replaces exact expected values with _properties_ — invariants that must hold for all valid inputs.
Frameworks shrink failing inputs to the minimal counterexample.

**Good candidates for properties:**

- Round-trip symmetry: `decode(encode(x)) == x`
- Idempotence: `f(f(x)) == f(x)`
- Ordering invariants: `sort(xs).length == xs.length`, `sort(xs)[i] <= sort(xs)[i+1]`
- Range constraints: result falls within a specified domain
- Algebraic properties: commutativity, associativity, distributivity

**When PBT adds value over example-based tests:**

- Boundary and edge case discovery — generators naturally reach values humans overlook: empty collections, maximum integers, strings with unusual characters.
- Algorithmic correctness over a domain — proves the relationship holds universally rather than for a handful of chosen examples.
- Regression pinning — failing inputs found during a run can be committed as permanent example-based tests.

**Limitation:** PBT requires you to articulate a general invariant.
For code that computes a specific business result, there may be no compact property other than "re-implement the function."
When properties are not specifiable, example-based tests are the right tool.

**The complementary pattern:** start with example-based tests to establish semantic correctness for concrete cases, then add property-based tests to audit the domain.
Examples catch semantic errors; properties catch edge cases examples miss.

## Mutation Testing

Mutation testing audits assertion quality — the dimension that code coverage metrics cannot see.

**What coverage measures:** whether a line was executed during the test run.

**What coverage misses:** whether the test would have failed if the behavior changed.
A test that calls a function but asserts nothing achieves 100% coverage with zero protective value.
A test that asserts `result != null` when the function should return 42 has full coverage with a weak assertion.

**How mutation testing works:** tools introduce small syntactically valid changes to production code — _mutants_ — and re-run the test suite:

- Operator substitutions: `>` → `<`, `&&` → `||`, `+` → `-`
- Return value replacements: return `null` instead of the computed value
- Conditional flips: `if (condition)` → `if (true)` or `if (false)`

Each mutant is either **killed** (at least one test fails — the suite detected the change) or **survived** (all tests still pass — the change was undetected).

A surviving mutant indicates: a missing test case, a weak assertion, or untested code.

**Use mutation testing as a periodic diagnostic**, not a CI gate.
Running it against a fast unit suite is practical; running it against slow integration tests is not.
Use its output to guide where to add tests (missing cases) or strengthen assertions (surviving mutants in tested code).

**Mutation score vs. coverage:** high coverage → mutation score can be anywhere from 0% to 100%.
Low coverage → low mutation score.
The relationship is asymmetric; coverage is a necessary but not sufficient proxy.
