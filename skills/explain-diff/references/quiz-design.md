# Quiz design

The quiz is the artifact's highest-leverage section (retrieval practice with feedback beats re-reading).
It is also where quality slips most easily, because a badly written multiple-choice item is guessable without understanding anything.
These rules exist to prevent that.

## What to produce

Five interactive multiple-choice questions.
Each question:

- Tests understanding of _this change_ — its purpose, mechanism, or behavior on new input — not trivia about the surrounding code.
- Has one clearly correct option and 3 plausible distractors.
- On selection, reveals whether the choice was correct **and an explanation for every option** — why the right one is right, why each wrong one is wrong.
  Bare "correct/incorrect" is not enough (Hattie & Timperley, 2007).

## Difficulty calibration

- Aim for **medium** difficulty: the reader should need to actually understand the substance of the change to answer, but the answer should be reachable from the artifact — not a gotcha, edge-case trivia, or a memory test (Bjork & Bjork, 2011).
- Target the _understand_ and _apply_ levels of Bloom's revised taxonomy (Krathwohl, 2002): "why does this change fix X?", "what would this code now do given input Y?"
  — not "what is the name of the variable on line 12?"
- Good source of distractors: **common misconceptions** about the change — the wrong mental model a reader might plausibly hold before reading carefully.

## Item-writing flaws to avoid

These are validated item-writing guidelines (Haladyna, Downing & Rodriguez, 2002).
Each is a way a savvy reader guesses the answer _without knowing the material_ — which defeats the entire purpose of retrieval practice.

- **The correct option is the longest / most detailed.**
  This is the classic tell and was a real bug reported against the source prompt: models tend to write a fully-qualified correct answer and terse distractors, so "pick the longest" wins.
  **Keep all options roughly equal in length and specificity.**
  After drafting each item, check option lengths and trim or pad to match.
- **Grammatical cueing.**
  The stem grammatically agrees with only the correct option (a/an, singular/plural, verb tense).
  Make every option fit the stem grammatically.
- **Implausible distractors.**
  A wrong option no one would pick narrows the field for free.
  Every distractor must be plausible to someone who half-understands the change.
- **"All of the above" / "None of the above."**
  Recognizing one true option (or one false one) lets the reader infer the answer.
  Avoid these.
- **Verbal association / word repetition.**
  A word from the stem echoed in only the correct option cues it.
  Avoid the giveaway repeat.
- **Convergence / answer-position patterns.**
  Do not let the correct answer cluster in one position, and do not make the correct option the "middle" numeric value by habit.
  Vary correct-answer position across the five questions.
- **Overlapping or "two are both right" options.**
  Keep options mutually exclusive so there is exactly one defensible answer.

## Self-check before finalizing the quiz

Run this pass over all five questions before saving:

1. Could someone answer this correctly _without_ having understood the change (length, grammar, elimination)?
   If yes, rewrite.
2. Is each item at understand/apply level, not recall?
3. Does every option — correct and incorrect — have an explanation tied to the change?
4. Are correct-answer positions varied across the five questions?
5. Are all options in each item comparable in length and specificity?
