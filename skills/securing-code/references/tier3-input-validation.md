# Tier 3 — Input Validation & Output Encoding

Apply when reviewing any code that handles input, or when implementing input handling in complex features.

## Validation Rules

1. **Validate first with a strict allowlist** — define exactly what is allowed (types, formats, ranges, patterns).
   Reject anything that does not match.
   Never "fix" or normalize bad input.
2. **Never repair bad input** — reject and return an error; do not strip, trim, or modify to make it valid.
3. **Allowlists over blocklists** — blocklists miss variants; allowlists are the only reliable defense.
4. **Validate at every trust boundary** — re-validate when data crosses service, network, or process boundaries even if it was validated upstream.

Apply to: query params, POST body, headers, cookies, file uploads, API inputs, database queries, system calls, config files, environment variables.

## Output Encoding Rules

Encode after validation passes.
Encoding is context-specific:

| Context        | Encoding required                                                   |
| -------------- | ------------------------------------------------------------------- |
| HTML body      | Encode `<`, `>`, `&`, `"`, `'`                                      |
| HTML attribute | Encode all non-alphanumeric characters                              |
| JavaScript     | Use `JSON.stringify()` or JS string escaping; never inject directly |
| URL            | Percent-encode all non-safe characters                              |
| CSS            | Avoid user input entirely; if unavoidable, strict allowlist only    |

**Rules:**

- Use framework built-in encoding: React JSX auto-escapes, Angular interpolation, Jinja2 autoescaping
- Never construct HTML by string concatenation
- Never use `dangerouslySetInnerHTML` or `innerHTML` without explicit sanitization via DOMPurify or equivalent
- Use sanitization only when escaping is not possible, via a hardened library

## Content-Security-Policy

Add CSP headers as defense in depth:

- Avoid `'unsafe-inline'` and `'unsafe-eval'`
- Use nonces or hashes for inline scripts when required
- Set `default-src 'self'` as baseline

## Review Checklist

- [ ] All inputs validated against an explicit allowlist before use
- [ ] Bad input rejected, not repaired
- [ ] Output encoded for the specific rendering context at the rendering point
- [ ] No `innerHTML`, `dangerouslySetInnerHTML`, or `document.write()` without DOMPurify
- [ ] No string concatenation to build HTML, SQL, or system commands
- [ ] CSP header present and does not include `unsafe-inline` or `unsafe-eval`
- [ ] Validation applied at all trust boundaries, not just entry points
