# Parallel run

Use this for more than about 30 docstrings, after calibration with the user.

## Writers

- Use a model that reads code well enough to judge a contract, such as Sonnet.
  A rewrite fails most often on accuracy: a condition stated wrongly, or a rule that the code does not apply.
- Give each writer one module, or about 10 docstrings, so that it stays under half of its context.
- Give each writer a brief that holds:
  - the shape and the register (`shape.md`, `register.md`), and the calibrated examples (`examples.md`);
  - the renderer findings that affect format (`renderer-probe.md`);
  - its file list and the level of each docstring in it;
  - the instruction to verify every fact against the body or the tests, and to add a missing contract fact;
  - the instruction to move rationale that guards against a wrong fix to a body comment, and to delete other rationale;
  - what to return: the edited files, and a list of facts it could not verify.
- Keep the brief in a scratch location for the run, and delete it afterward, unless the user asks to keep it.

## Review sweeps

Run each sweep as a separate agent over the writers' output.
Send findings back to the writer, or fix them in a final pass; do not let a reviewer edit.

1. Accuracy: each statement is true against the code.
   This reviewer reads the bodies and the tests.
2. Shape: each docstring has the summary line, the sections in order, and the entry formats the renderer parses.
   This sweep works from the text and can use a smaller model.
3. Plain language: no metaphor for a mechanism, no narration, no announcements, no restated signature, no history.
   This sweep works from the text and can use a smaller model.

## Finish

1. Run the test suite: doctests and documentation tests can execute docstrings.
2. Rebuild the site and check a sample of pages at each level.
3. Report the facts no writer could verify.
