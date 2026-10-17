# Shape

## Function and method docstrings

1. A summary line.
   One line, ending with a period, that makes sense alone.
   The site's index lists each object with this line.
2. Contract paragraphs, without a label.
   What the call does, and the meaning of any argument whose type does not say it.
3. Labeled sections, in this order, each only when it has content:

| Label       | Holds                                                                 |
| ----------- | --------------------------------------------------------------------- |
| `Raises:`   | Each error a caller can handle, and the condition that raises it      |
| `Notes:`    | Ordering, cost, limits, and scaling caveats a caller must plan around |
| `See also:` | The neighbor to use instead, or the page that explains the concept    |
| `Examples:` | A short fenced code block of the common call                          |

Write a label as the word and a colon, with its content indented four spaces below.
Do not underline a label.
Do not add `Parameters` or `Returns` sections; the type hints and the contract paragraphs cover them.
Add `Returns:` only when the return value has meaning the type does not show, such as `None` against an empty list.

Format each entry so the renderer can parse it (`renderer-probe.md`):

- `Raises:` entries are `ErrorName: condition.`
- `See also:` entries are `name: what it is for.`, one per line, with no role markup.
- `Examples:` holds a fenced ```` ```python ```` block, not `>>>` lines, unless the project runs doctests.

## Class docstrings

What the object represents, how a caller gets one, its lifecycle (for example, call `close()` when done), and its invariants.
Do not list the methods; the page lists them.
A class that is an entry point to the package is a landing page: write it as orientation (below).

## Module docstrings and landing pages

These are orientation for a reader new to the project.
State, in order:

1. What the module or package is for, in one line.
2. The concepts it owns, explained once in short paragraphs, so other docstrings link here instead of repeating them.
3. Where to start: the class or function a reader uses first.
4. `Notes:` for caveats and limits, `See also:` for neighboring modules, and `Examples:` for a minimal working setup.

The higher the page, the more it orients and the less it specifies.
Leave call conventions, such as argument order, to the method pages.
Move internals (architecture, how a mechanism works, mapping tables) to body comments, or delete them.

## Private code

A docstring on an object that does not render has a maintainer for its reader.
Keep it short.
Implementation detail is allowed; line-by-line narration is not.
