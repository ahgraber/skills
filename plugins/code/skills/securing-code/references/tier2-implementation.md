# Tier 2 — Implementation Task Checklists

Select the section matching your task.
Fill in the context fields, then follow the requirements.
Tier 1 from `SKILL.md` always applies on top of these.

---

## 2.1 General Secure Feature

Use for any new feature, component, or service not covered by a more specific section.

**Establish context before writing:**

- Language / framework:
- Auth model: (JWT / session cookie / OAuth / API key / none)
- Authorization rules: (who can do what, including object-level)
- Data classification: (public / internal / confidential / regulated)
- External dependencies: (APIs, services, libraries)

**Non-negotiable requirements:**

- [ ] Validate all inputs with allowlists; reject invalid input; do not repair bad input
- [ ] Parameterize all database queries — no string concatenation
- [ ] Enforce authorization on every request including object-level checks
- [ ] Load secrets from a secret manager, not from code or config files
- [ ] Fail closed with full rollback on errors
- [ ] Log security-relevant events; never log secrets or sensitive PII
- [ ] Rate-limit all endpoints; no wildcard boundaries

**Deliver:**

1. Implementation code
2. Input validation and authorization examples
3. Unit/integration tests for authorization and input validation
4. "Security Notes" covering headers, cookie flags, CSRF settings, and required infra config

**OWASP coverage:** A01 (access control), A02 (config), A04 (crypto), A05 (injection), A09 (logging), A10 (error handling)

---

## 2.2 Secure API Endpoint

Use when building or modifying a REST or GraphQL API endpoint.

**Establish context before writing:**

- Method + path:
- Request schema: (fields, types, constraints)
- Response schema: (fields, types)
- Auth model:

**Non-negotiable requirements:**

- [ ] Validate access control on every request — object-level and function-level checks
- [ ] Validate all inputs with allowlists; reject anything that does not match
- [ ] Safe serialization; correct content type; never build JSON by string concatenation
- [ ] Apply output encoding only at HTML/JS/URL/CSS rendering points — not in API response bodies
- [ ] Parameterized queries for all database access
- [ ] Secure cookies, security headers, HTTPS; CSRF if using cookie sessions and state-changing operations
- [ ] Rate limiting and anti-brute-force controls
- [ ] Catch all exceptions; log with context; return generic error messages to callers
- [ ] Roll back and fail closed on unexpected behavior

**Deliver:**

1. Endpoint code
2. Security checklist showing where each requirement is handled in the code
3. Tests that prove authorization and input validation work correctly

**OWASP coverage:** A01, A02, A05, A07, A10

---

## 2.3 Authentication, Sessions & Access Control

Use when designing or implementing any login, session, or permissions flow.

**Establish context before writing:**

- App / service:
- Framework / identity provider:
- Auth flow type: (login, OAuth callback, API key validation, MFA enrollment)

**Non-negotiable requirements:**

- [ ] Use proven framework, product, or identity provider — do not build custom authentication
- [ ] Enforce access control on every request; include object-level checks
- [ ] Support MFA; include brute-force and credential-stuffing defenses (rate limits, lockout, monitoring)
- [ ] Secure cookies and security headers; HTTPS only
- [ ] Rotate session IDs after login; invalidate on logout and password change
- [ ] Check compromised-password lists at registration and password change (HIBP or equivalent)
- [ ] State auth assumptions before writing code

**Deliver:**

1. Threat model of the auth flow (actors, trust boundaries)
2. Recommended implementation steps with rationale
3. Code samples or pseudocode
4. Logging and alerting events to instrument

**OWASP coverage:** A01, A02, A06, A07

---

## 2.4 Secrets, Cryptography & Data Protection

Use when handling API keys, passwords, tokens, encryption, or classified data.

**Establish context before writing:**

- Service / feature:
- Fields to classify: (list each data field)

**Non-negotiable requirements:**

- [ ] No secrets in code, config files, or logs — use a secret manager (see §2.5 for scanning tooling)
- [ ] Treat any detected secret as compromised — rotate immediately; scrubbing history is not sufficient
- [ ] HTTPS everywhere; TLS 1.2 minimum, prefer TLS 1.3
- [ ] Classify data; encrypt sensitive data at rest and in transit; document sensitive data flows
- [ ] Approved algorithms only: AES-256-GCM for encryption, SHA-256/SHA-3 for hashing, Argon2id/bcrypt for passwords, Ed25519 or ECDSA P-256 for signatures
- [ ] Cryptographically secure RNG — never `Math.random()` or equivalent
- [ ] Plan for post-quantum cryptography transition by 2030 for long-lived keys

**Deliver:**

1. Data classification for each field
2. Key management approach
3. Example code for encryption and secret retrieval
4. "Do Not Do" list: hardcoding, logging secrets, weak crypto, rolling your own

**OWASP coverage:** A02, A04, A08

---

## 2.5 Supply Chain & CI/CD Hardening

Use when setting up or reviewing build pipelines, repositories, or development environments.

**Establish context before writing:**

- Repo / org / pipeline:

**Non-negotiable requirements:**

- [ ] Lock down dev environments, repo settings, CI/CD pipeline, and all tooling; validate regularly
- [ ] Pin dependency versions; keep dependencies updated and supported; remove unused ones
- [ ] Maintain an SBOM with transitive dependency tracking
- [ ] Verify integrity of downloaded packages (checksums, signing, or equivalent)
- [ ] Add SCA, SAST, and linters; treat compiler warnings as errors
- [ ] Wire secret scanning into both pre-commit hooks and CI so findings are consistent.
  Recommended tools: [gitleaks](https://github.com/gitleaks/gitleaks) or [betterleaks](https://github.com/betterleaks/betterleaks), [kingfisher](https://github.com/mongodb/kingfisher), [trufflehog](https://github.com/trufflesecurity/trufflehog), or [detect-secrets](https://github.com/Yelp/detect-secrets).
  As a last-mile manual catch, `git diff --cached | grep -iE 'password|secret|api[_-]?key|token|bearer'` flags obvious leaks before commit.
  Rotate immediately on any hit — scrubbing history is not sufficient
- [ ] Use short-lived credentials for all automation; audit service account access
- [ ] Implement separation of duties in CI/CD with MFA and signed builds

**Deliver:**

1. CI pipeline outline with stages: lint → test → SAST → dependency scan (SCA) → secret scan → build → deploy
2. Branch protection rules and required review policies
3. Build integrity steps (immutable builds or signing)
4. Developer "paved road" policy with minimum security baseline for all contributors

**OWASP coverage:** A02, A03, A08

**Triaging dependency-audit findings** (`npm audit`, `pip-audit`, `cargo audit`, `osv-scanner`, etc.):

Not every advisory is a release blocker.
Use reachability + context to prioritize:

```text
Advisory reported
├── Critical / High severity
│   ├── Reachable in a runtime code path?
│   │   ├── Yes → fix now: update, patch, or replace the dependency
│   │   └── No (dev-only, unused export, gated behind a disabled feature) → fix soon, not a blocker
│   └── No fix available?
│       └── Evaluate workaround, replacement, or temporary allowlist with a review date
├── Moderate
│   ├── Runtime → fix in the next release cycle
│   └── Dev-only → backlog
└── Low
    └── Roll into routine dependency updates
```

Key questions when assessing reachability:

- Is the vulnerable function actually called from our code or transitive call graph?
- Runtime dependency or dev/build-only?
- Is the vuln exploitable in this deployment context (e.g., a server-side gadget in a client-only bundle)?

When deferring, record the reason and a review date in the allowlist file (`.gitleaksignore`, `audit-ci.json`, `osv-scanner` config, etc.) — never silently suppress.
