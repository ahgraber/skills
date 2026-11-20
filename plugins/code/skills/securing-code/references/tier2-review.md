# Tier 2 — Code Review Workflow

Use for all security code reviews.
Load Tier 1 from `SKILL.md` and all `tier3-*.md` files alongside this.

## Review Stance

Act as a strict AppSec reviewer: thorough, impact-first, specific.
Reference exact code locations.
Never omit a HIGH finding to avoid conflict.

## Step 1 — Scope

Determine what is being reviewed:

- Staged diff, branch diff, or specific file/function?
- Feature type: API?
  Auth?
  File handling?
  Data processing?
- Known context: auth model, data classification, framework?

Ask for missing context before reviewing if it would change the findings.

## Step 2 — Checklist

Work through each category.
For each: state findings or explicitly confirm clean.

### Access Control (OWASP A01)

- [ ] Authorization enforced on every endpoint, AJAX call, and resource request
- [ ] Object-level checks present (user owns or has rights to the specific resource)
- [ ] No client-side-only access control
- [ ] Deny-by-default for non-public resources
- [ ] No IDOR via predictable IDs or parameter tampering

### Security Misconfiguration (OWASP A02)

- [ ] No default credentials or unused accounts
- [ ] No unnecessary services, features, or ports exposed
- [ ] Error messages do not reveal stack traces, DB errors, file paths, or framework versions
- [ ] Security headers set (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy)
- [ ] Dev/staging configs not present in production paths

### Supply Chain (OWASP A03)

- [ ] Dependencies pinned to specific versions
- [ ] No use of unverified, suspicious, or abandoned packages
- [ ] Integrity checks present on downloaded artifacts (checksums or signatures)
- [ ] No removed or bypassed SBOM/SCA tooling

### Cryptographic Failures (OWASP A04)

- [ ] No plaintext sensitive data in transit or at rest
- [ ] Approved algorithms only (AES-256-GCM, SHA-256+, Argon2id — not MD5, SHA1, ECB, CBC)
- [ ] No hardcoded keys, tokens, or passwords
- [ ] Cryptographically secure RNG for tokens and IVs
- [ ] TLS 1.2+ enforced; no deprecated ciphers

### Injection (OWASP A05)

- [ ] Parameterized queries for all DB access (SQL + NoSQL)
- [ ] No user input concatenated into queries, system calls, or file paths
- [ ] Input validated with allowlists before use
- [ ] Output encoded for the correct context (HTML/JS/URL/CSS) at the rendering point

### Insecure Design (OWASP A06)

- [ ] Business logic limits enforced (rate limits, quantity limits, workflow ordering)
- [ ] No race conditions in critical flows (payment, inventory, auth state transitions)
- [ ] Trust boundaries clearly defined and enforced
- [ ] No dangerous defaults (open file uploads, unrestricted admin access, no bot protection)

### Authentication Failures (OWASP A07)

- [ ] No custom authentication implementation
- [ ] MFA supported for sensitive operations
- [ ] Brute-force and credential-stuffing defenses present (rate limiting, lockout)
- [ ] Session IDs rotated after login; invalidated on logout and password change
- [ ] Secure cookie flags set (`Secure`, `HttpOnly`, `SameSite`)
- [ ] Consistent error messaging prevents account enumeration

### Data Integrity (OWASP A08)

- [ ] No unsafe deserialization of untrusted data
- [ ] Auto-update or plugin mechanisms verify signatures before executing
- [ ] CI/CD pipeline uses signed builds and restricted access
- [ ] No classes or objects instantiated from untrusted input

### Logging Failures (OWASP A09)

- [ ] Auth events, authz failures, and critical operations are logged
- [ ] No secrets or PII in logs
- [ ] Log entries include: timestamp (UTC), user ID, source IP, action, result, request ID
- [ ] Log storage is append-only and access-restricted

### Exceptional Conditions (OWASP A10)

- [ ] All exceptions caught; transactions fail closed with full rollback
- [ ] No stack traces or internal details exposed to users
- [ ] Resource limits enforced to prevent exhaustion (memory, file handles, connections)
- [ ] Generic error messages returned to callers; details logged internally

### Additional Checks

- [ ] Rate limiting on all endpoints; no wildcard boundaries
- [ ] CSRF protection enabled for state-changing operations using cookie sessions
- [ ] No user input passed to `eval`, system calls, or deserialization
- [ ] Not running as root; variables initialized; warnings treated as errors
- [ ] Dependency manifest changes assessed for supply-chain risk and compatibility
- [ ] Behavior changes have corresponding security regression tests

## Step 3 — Output Format

Report findings in this order:

### HIGH Risk Findings

For each: description, exact code location, impact, concrete patch (code), regression test to add.

### MEDIUM / LOW Findings

For each: description, location, recommended fix.

### Security Notes

- What the code does correctly
- Environment configuration still needed (headers, secrets, IAM, logging)
- Regression tests to add

### Clean Areas

Explicitly list categories with no findings — confirms coverage, not just silence.
