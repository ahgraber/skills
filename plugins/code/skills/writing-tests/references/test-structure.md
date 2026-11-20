# Test Structure

## Outcome

Tests that are readable at a glance, communicate intent through name and structure, and fail with a clear signal about what went wrong.

## Arrange / Act / Assert

Bill Wake observed and named the AAA pattern in 2001.
It is also expressed as Given/When/Then (BDD origin, Dan North) and Setup/Exercise/Verify/Teardown (Meszaros).
All three describe the same structure.

**The three phases:**

**Arrange** — bring the system under test (SUT) and its dependencies to the required state.
Construct collaborators, configure stubs, populate fixtures.
Declare expected values here, before the Act, so the reader sees inputs and expected output together.

**Act** — invoke the behavior under test.
Keep this to a single call or a single logical operation.
If the Act spans multiple calls, the test likely covers multiple behaviors.

**Assert** — verify the outcome: return value, state change on the SUT, or a recorded side-effect on a spy.
Each assertion should produce a distinguishable failure message.

Separate the three phases with a blank line.
Blank lines are the minimum required structure.
Section-label comments (`// Arrange`, `// Act`, `// Assert`) are not required; this document uses them in examples as a teaching aid.
In production tests they are acceptable when the team finds them helpful — not mandatory.

```text
// Arrange
account = Account(balance=100)
expected_balance = 70

// Act
account.withdraw(30)

// Assert
assert account.balance == expected_balance
```

**Teardown** (Meszaros's fourth phase) is required when the test acquires real resources — files, connections, server ports.
Prefer framework `after_each` / `teardown` hooks over manual teardown inside the test body.
A test that cleans up in the Assert phase will leave resources open on failure.

### The Assert-First technique

Before writing Arrange or Act, write the Assert first: "If the code worked correctly, how would I know?"
This focuses the test on what matters before getting lost in setup mechanics.
Useful when the assertion is obvious but the setup is not.

### When AAA breaks down

A test with multiple Act/Assert cycles is a run-on test — it covers more than one behavior.
Split it.

```text
// Bad: run-on test
user = create_user("alice")
assert user.is_active          // first behavior
user.deactivate()
assert not user.is_active      // second behavior — split into own test
```

A test with no Assert tests only that the code does not crash.
"Testing that nothing crashes" is not testing behavior.
Add an assertion.

A test with a Giant Arrange that buries the Act signals Irrelevant Information — fixture details the reader must wade through to find what matters.
Extract a named Creation Method that sets meaningful defaults and exposes only the values relevant to the test.

```text
// Before: irrelevant detail noise
user = User(name="alice", email="alice@example.com", role="admin",
            created_at=datetime(2024, 1, 1), locale="en-US", timezone="UTC")

// After: Creation Method hides irrelevant defaults, names the meaningful variant
user = make_admin_user()
```

## DAMP vs. DRY in Test Code

DRY (Don't Repeat Yourself) applied to tests often hurts readability.
Extracting shared setup into helpers can hide the cause-effect relationship between inputs and expected output, forcing readers to jump between files to understand what a test does.

**DAMP — Descriptive and Meaningful Phrases** — is the test-code counterpart: prefer readable duplication over abstraction that reduces glanceability.

**When duplication is acceptable:**

- Repeated inline fixture setup that makes each test self-contained.
- Literal values that make the cause-effect relationship visible.
- The full AAA structure repeated across parametrically similar tests.

**When extraction is appropriate:**

- A Creation Method that constructs a complex object and names it meaningfully — this removes Irrelevant Information without hiding intent.
- A Custom Assertion that names a multi-step verification — this gives the assertion a specification-level name without hiding what is being verified.
- A shared `before_each` / `setUp` for fixture that is truly identical across all tests in a class, with the understanding that readers must look in two places.

The rule of thumb: extract when the extraction _names something_ and makes the test more expressive.
Do not extract purely to reduce line count.

## Naming Conventions

The test name is the first thing a reader sees on a failure.
It must communicate the scenario and expected outcome without requiring the reader to enter the test body.

### Three-part form (Osherove)

`<UnitOrBehavior>_<Condition>_<ExpectedOutcome>`

Each segment names something meaningful:

- **Unit/Behavior**: the entry point being exercised.
  Can be a method name, a feature, or a workflow — whatever level makes failures diagnosable.
- **Condition**: the meaningful precondition or input configuration.
  Names a scenario, not a type (`insufficientFunds`, not `negativeInt`).
- **ExpectedOutcome**: what the test asserts — the observable result.

Casing and separators are a language convention, not a quality rule.
Use snake_case where your language/community does, camelCase where it doesn't.
Double underscores (`__`) are sometimes used as segment separators within a snake_case name.

```text
// snake_case (Python, Ruby)
withdraw_money__insufficient_funds__raises_error
cart_with_no_items__total_is_zero
parse__empty_string__returns_none

// camelCase segments (Java, C#, JavaScript)
withdrawMoney_insufficientFunds_raisesError
cartWithNoItems_totalIsZero
login_withExpiredToken_redirectsToLoginPage

// Go: TestFunctionName (PascalCase, Test prefix required for discovery)
TestWithdrawMoney_InsufficientFunds_ReturnsError
TestCartWithNoItems_TotalIsZero
```

### Behavioral statement form

Omits the method name; names the behavior the system should exhibit.
Survives renaming and refactoring that preserves behavior.

```text
should_rejectTransfer_when_balanceIsNegative
returns_empty_list_for_unknown_category
raises_on_missing_required_field
```

### BDD / Given-When-Then form

Most verbose; best for acceptance and system-level tests where the audience includes non-developers.

```text
given_authenticatedUser_when_requestsAdminPage_then_returns403
```

### What to avoid

| Pattern                                      | Problem                                                                                                                               |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `test2`, `testOrder2`                        | Numbered suffix; tells nothing about scenario or expected outcome                                                                     |
| `testWithdraw`                               | States only the entry point; no condition, no expected outcome                                                                        |
| `withdraw_negativeAmount`                    | States input but not expected outcome                                                                                                 |
| `it_works`                                   | Meaningless                                                                                                                           |
| `test_withdraw` with no condition or outcome | Framework discovery prefix is not a substitute for a descriptive name — `test_withdraw__insufficient_funds__raises_error` is the goal |

### Variable naming inside tests

Variable names should express the role the value plays, not its type.
`EMPTY_INPUT`, `ADMIN_USER`, `PAST_EXPIRY_DATE` communicate intent.
`arg1`, `input`, `result2` do not.
A good check: if the Assert line reads like a requirement statement, the naming is working.

## Given/When/Then vs. Arrange/Act/Assert

Both patterns describe the same three-phase structure.
The difference is framing, not mechanics.

|                   | AAA                                 | GWT                                       |
| ----------------- | ----------------------------------- | ----------------------------------------- |
| Origin            | Bill Wake, 2001 (XP)                | Dan North / Chris Matts, BDD              |
| Frame             | Test mechanics                      | Behavior being specified                  |
| Natural audience  | Developers                          | Developers + stakeholders                 |
| Coupling tendency | Can drift toward internal mechanics | Nudges toward treating SUT as a black box |

GWT originated in acceptance testing contexts and BDD frameworks (Cucumber, Gherkin, Behave) where scenarios are authored collaboratively.
AAA is the more common vocabulary in developer-facing unit and integration tests.
Either vocabulary is appropriate at any test level — the underlying structure is identical.

In practice: use whichever vocabulary helps the team reason about behavior.
Apply either consistently.

## Comments in Tests

A well-named, well-structured test should not need inline comments.
If a comment is required to explain what the test does, the test has a naming or structure problem; fix the test rather than adding the comment.

**When a comment is warranted:**

1. A non-obvious business rule drives an assertion and the test name cannot carry the full context:

   ```text
   // Regulatory requirement: transfers initiated after 17:00 local time post on the next business day
   assert settlement_date == next_business_day(initiated_at)
   ```

2. A deliberate deviation from convention would otherwise look like a mistake:

   ```text
   // Intentionally omit teardown — this test verifies cleanup happens automatically on scope exit
   ```

3. The test encodes a hard-won non-obvious invariant:

   ```text
   // Dedup path skips validation; we must assert normalized_url even though the canonical path test already does
   ```

**What not to comment:**

- What the test does — the name says that.
- Why the test exists — the name says that too.
- Section labels (`// Arrange`, `// Act`) — blank lines handle that.
- Caller context or task references — those belong in the commit message or PR description, not the test.
