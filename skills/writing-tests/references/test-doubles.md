# Test Doubles

## Outcome

Tests that replace only what must be replaced, stay honest about the collaborators they substitute, and fail for real behavioral reasons — not because a mock's expectations drifted from reality.

## Terminology

Gerard Meszaros coined the term **Test Double** (from "stunt double") as the generic name for any object that stands in for a real dependency during testing.
"Mock" is not a synonym for test double — it names one specific subtype with a specific verification style.

The **System Under Test (SUT)** is the specific unit being exercised.
The **Depended-On Component (DOC)** is anything the SUT relies on.

## The Five Types

### Dummy

Passed to the SUT but never actually used.
Satisfies a required parameter whose value is irrelevant to the test.

```text
// Dummy: the logger is required by the constructor but irrelevant to this test
service = PaymentService(gateway=real_gateway, logger=NullLogger())
result = service.charge(amount=50)
assert result.status == "success"
```

Never assert on a Dummy.
If you find yourself inspecting it, it is probably a Spy or Stub.

### Fake

A working implementation that takes a shortcut making it unsuitable for production.
Has real business logic, unlike the other four types.
The canonical example is an in-memory database.

```text
// Fake: real insert/query logic, but stores data in memory instead of disk
repo = InMemoryUserRepo()
repo.save(User(id=1, name="alice"))
assert repo.find_by_id(1).name == "alice"
```

Fakes are the most realistic doubles.
Prefer them over stubs and mocks when a simplified real implementation is feasible.
In-memory queues, fake email collectors, and in-process event buses are common examples.

**Fake drift:** a Fake with significant business logic can silently diverge from the real implementation as the system evolves.
For long-lived Fakes, add a contract test that runs both the Fake and the real implementation against the same inputs to verify they agree.

### Stub

Provides canned return values.
Does not verify how it is called.
Controls the **indirect inputs** to the SUT — values the SUT receives from a DOC.

```text
// Stub: always returns the same exchange rate regardless of call arguments
exchange_stub = ExchangeRateStub(rate=1.25)
converter = CurrencyConverter(rates=exchange_stub)

result = converter.convert(amount=100, from_currency="USD", to_currency="EUR")

assert result == 125.0
```

Stubs use **state verification**: assert on the SUT's output or final state, not on what the stub received.

### Spy

A stub that records how it was called.
Lets you make assertions about **indirect outputs** — calls the SUT made to a DOC — after the Act phase, in the Assert phase.

```text
// Spy: records all emails sent so the test can inspect them afterward
email_spy = EmailSpy()
notifier = OrderNotifier(mailer=email_spy)

notifier.confirm(order=Order(id=42, customer="alice@example.com"))

assert len(email_spy.sent) == 1
assert email_spy.sent[0].to == "alice@example.com"
assert email_spy.sent[0].subject == "Order #42 confirmed"
```

Spies assert post-hoc after the Act.
They verify that a side-effect occurred without pre-programming expectations before the Act — making them less brittle than Mocks.

### Mock

Pre-programmed with expectations about which calls it will receive, in what order, with what arguments.
Verifies those expectations during or immediately after the Act phase.
Used for **behavior verification**.

```text
// Mock: pre-programmed to expect exactly one call to send() with specific args
email_mock = MockMailer()
email_mock.expect_call("send", to="alice@example.com", subject="Order #42 confirmed")

notifier = OrderNotifier(mailer=email_mock)
notifier.confirm(order=Order(id=42, customer="alice@example.com"))

email_mock.verify()  // fails if expected call did not happen, or unexpected call did
```

**Use Mocks sparingly.**
They are structure-sensitive by design: if the SUT's internal call pattern changes — even when external behavior is preserved — the mock expectation fails.
This makes tests fragile under refactoring.

Mocks are appropriate when the _interaction itself_ is the behavior under test: audit logging that must record specific events, a payment gateway call that must not be duplicated, a circuit breaker that must open after N failures.

## State Verification vs. Behavior Verification

This is the most consequential design decision when using test doubles.

**State verification** (classical school): after exercising the SUT, assert on the observable state — return values, object properties, records in a Fake repository.
Does not care _how_ the result was produced.

```text
// State verification: did the account end up with the right balance?
account = Account(balance=100)
account.withdraw(30)
assert account.balance == 70
```

**Behavior verification** (mockist school): assert that the SUT sent the correct messages to its collaborators, with the correct arguments, in the correct order.

```text
// Behavior verification: did the SUT call the right method with the right args?
ledger_mock.expect_call("debit", account_id=account.id, amount=30)
account.withdraw(30)
ledger_mock.verify()
```

**Prefer state verification.**
Tests using state verification survive internal refactoring: the implementation can change as long as the observable outcome is the same.
Tests using behavior verification are coupled to the implementation's call graph — they break when you restructure the internals without changing behavior.

**When behavior verification is appropriate:**

- The interaction with the DOC _is_ the observable behavior: sending an email, writing to an audit log, enqueuing a message, opening a circuit breaker.
- The SUT has no state to observe after the interaction (e.g., a pure side-effect operation).
- Even in these cases, prefer a Spy (assert post-hoc) over a Mock (pre-program expectations) when possible.

## Classical vs. Mockist Schools

These two traditions draw different conclusions about when to use doubles.

### Classical (Detroit) School

Uses real collaborators wherever practical.
Test doubles are reserved for dependencies that are genuinely awkward: external services, non-determinism, destructive operations.

- **Tests are sociable**: the SUT exercises real collaborators; failures may ripple.
- **Verification**: primarily state-based.
- **Design direction**: inside-out — build the domain model first, tests emerge from it.
- **Mock policy**: use doubles only for infrastructure; use real domain collaborators.

```text
// Classical: real collaborators for domain logic, Fake only for the database
repo = InMemoryOrderRepo()
pricer = RealPricer(catalog=real_catalog)
checkout = CheckoutService(orders=repo, pricer=pricer)

order_id = checkout.place(items=[("widget", qty=2)])

assert repo.find(order_id).total == 19.98
```

### Mockist (London) School

Replaces all collaborators with mocks.
Isolates the SUT from every dependency with interesting behavior.

- **Tests are solitary**: only the SUT runs real code.
- **Verification**: primarily behavior-based.
- **Design direction**: outside-in — write the test for the outer layer first, let mock expectations define the interface for the inner layer.
- **Mock policy**: replace everything with interesting behavior.

```text
// Mockist: every collaborator is mocked
pricer_mock.expect_call("price", items=[("widget", qty=2)], returns=19.98)
repo_mock.expect_call("save", order=any_order(), returns=Order(id=99))

checkout = CheckoutService(orders=repo_mock, pricer=pricer_mock)
checkout.place(items=[("widget", qty=2)])

pricer_mock.verify()
repo_mock.verify()
```

**Which to use:** the classical school's preference for real collaborators produces tests that survive refactoring better and read as specifications rather than interaction transcripts.
The mockist school's outside-in design can be valuable when the domain model is unknown and needs to be discovered through test-driving.
Both schools agree that programmer unit tests must be supplemented by coarser integration or acceptance tests that exercise the system as a whole.

Fowler (classical): "I don't see any compelling benefits for mockist TDD, and am concerned about the consequences of coupling tests to implementation."

Beck (classical): the Test Desiderata property "structure-insensitive" — tests should not change result if code structure changes without behavior changing — is violated by mock-heavy tests.

## When to Use Each Type

| Situation                                            | Preferred double        |
| ---------------------------------------------------- | ----------------------- |
| Parameter required but irrelevant                    | Dummy                   |
| External service (database, queue, cache)            | Fake (in-memory)        |
| Network call, time, randomness, config               | Stub                    |
| Side-effect that must be verified (email, audit log) | Spy or Mock             |
| Internal domain collaborator                         | Real object (no double) |
| Slow or expensive operation that cannot be made fast | Stub or Fake            |
| Destructive operation that must not execute          | Stub                    |

## Stub at the Boundary, Not Deep Inside

Replace the dependency at the seam where your module imports or constructs it — not at the object's original definition.

```text
// Wrong: patching at the definition site affects all callers globally
patch("email_library.SmtpClient.send", ...)

// Right: patch at the usage site — the boundary your module crosses
patch("notifications.mailer.SmtpClient.send", ...)
```

Deep mock chains — where a mock returns a mock which returns a mock — mirror the internal call graph of the production code.
They are a design smell: I/O has not been decoupled from logic.
The fix is architectural: push I/O to the edges and test the pure core without doubles.

## Common Misuse Patterns

**Testing the mock:** asserting that a mock received a call without asserting on observable output.
The test proves the SUT invoked the method; it does not prove the behavior was correct.

```text
// Bad: proves the mock was called, not that the behavior was correct
mock_notifier.expect_call("notify")
service.process(order)
mock_notifier.verify()  // passes even if the wrong order was processed

// Better: assert on what the notification contained
assert notification_spy.last_call.order_id == order.id
```

**Mocking what you don't own:** mocking third-party libraries couples the test to that library's API.
When the library updates, tests break even when your code is unchanged.
Wrap external libraries in a thin adapter and mock the adapter.

**Mock signatures that don't match reality:** a stub that accepts any arguments regardless of the real method's signature passes when the production code calls it incorrectly.
Use spec-constrained doubles (whatever your framework calls them) to enforce real signatures.

**Over-specified interactions:** asserting on exact argument values, call ordering, and call counts for calls that are incidental to the behavior under test.
When the implementation is refactored, these assertions fail even though behavior is preserved.
Assert on the minimum interaction needed to verify the behavior.
