# Renderer probe

Check what the documentation renderer does with the shape before you rewrite many docstrings.
A wrong assumption here breaks every page at once.

## What to find out

1. Which objects get pages: exported names only, or also submodules and private objects.
2. Which docstring parser the site uses, and which labels it turns into sections.
3. How cross-reference roles render, in body text and in `See also:`.
4. How examples render.
5. Whether a module listed in the site configuration gets a page built from its docstring.

## How to probe

1. Parse a sample docstring with the parser library the renderer uses, for each candidate parser.
   For griffe-based renderers (great-docs, quartodoc, mkdocstrings): `griffe.Docstring(text, lineno=1, parser="google").parsed` lists the sections it found.
2. Build the site for a throwaway package that holds one function and one submodule with sample docstrings.
   Read the generated page source (`.qmd` or `.md`); a later render step can fail in a sandbox without affecting it.
3. Read the real site after a full build for anything the source does not show, such as whether a role became a link.

## Findings for great-docs with the google parser

These held for great-docs with griffe in October 2026.
Probe again before relying on them.

- The `sphinx` parser reads labeled sections as plain text; the `google` parser turns them into sections.
- `Raises:` renders as a list of error type and condition.
- `Notes:` renders as a heading with prose.
- `See also:` renders as links only when each entry is `name: description`.
  An entry that starts with a role such as `` :func:`name`  `` loses its colon and renders as text.
- `Examples:` (plural) is a section; `Example:` (singular) is a plain box.
  A fenced ```` ```python ```` block renders cleanly; `>>>` lines leak their indentation and split the output from the code.
- A role with a plain name (`` :meth:`list`  ``) becomes a link.
  A role with a `~` path (`` :class:`~pkg.errors.Error`  ``) renders as literal code with no link, even when the target has a page.
- Only exported names get pages unless the `reference:` configuration lists more.
  A module listed in `reference:` gets a page with its summary line, text, sections, and a table of the classes it defines.
- The site index shows each object with its summary line.
