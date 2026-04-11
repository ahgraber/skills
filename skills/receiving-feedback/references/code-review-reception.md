# Code Review Reception

Code-specific guidance for receiving feedback on code changes.
Extends the core `receiving-feedback` skill with verification techniques, revision ordering, and conventions specific to code review.

## Verification Strategies

For code, ground truth is the codebase itself.
Use whatever tools give the most complete picture — graph tools for structural relationships, text search for string-level references, LSP for type-aware navigation, tests for behavioral verification.

- **Trace usage** — search for callers, references, and dependents of the code in question.
  Use `code-review-graph` tools (if available) for structural relationships, text search for string-level references, LSP for type-aware navigation.
- **Run tests** — if a reviewer claims something is broken, run the relevant tests before agreeing or disagreeing.
- **Check constraints** — platform, version, and compatibility requirements that may not be visible in the diff.
- **Read surrounding context** — a change that looks wrong in isolation may be correct given the broader module.
  Use structural tools to understand the neighborhood before judging.

## YAGNI Checks

When a reviewer suggests "implementing properly" or adding capabilities:

```text
1. Trace usage of the feature in question
2. IF unused → "This isn't called anywhere. Remove it (YAGNI)? Or is there usage I'm missing?"
3. IF used → implement properly
```

Do not add features, abstractions, or configurability that nothing currently needs.

## Revision Ordering for Code

Override the general revision ordering with this code-specific sequence:

1. **Clarify everything unclear FIRST** (unchanged)
2. Then fix by priority:
   - **Blocking issues** — breaks, security vulnerabilities, data loss risks
   - **Simple fixes** — typos, imports, naming, obvious corrections
   - **Complex fixes** — refactoring, logic changes, architectural adjustments
3. Test each fix individually
4. Verify no regressions after each change
