# OWASP Top 10:2025 — Reference and Control Mapping

---

## A01 — Broken Access Control

**Description:** Systems fail to enforce user permissions, allowing users to act beyond their intended authorization scope.

**Key risks:** IDOR, parameter tampering, URL manipulation, missing API access controls, JWT/cookie manipulation, CORS misconfiguration, forced browsing.

**Prevention:** Deny by default; enforce access controls server-side only; enforce record ownership; rate-limit APIs; log and alert on failures; include access control tests.

**Skill coverage:** Tier 1 rule 3, Tier 2 §2.1 §2.2 §2.3, `tier2-review.md` A01 section

---

## A02 — Security Misconfiguration

**Description:** Incorrect configuration of systems, applications, or cloud services creates exploitable vulnerabilities.

**Key risks:** Default credentials, unnecessary services/ports/features enabled, verbose error messages, insecure headers, overly permissive cloud storage.

**Prevention:** Repeatable hardening processes; minimize platform footprint; automate config verification; identical configs across dev/QA/prod with environment-specific credentials.

**Skill coverage:** Tier 1 rules 11 13, Tier 2 §2.5, `tier2-review.md` A02 section

---

## A03 — Software Supply Chain Failures

**Description:** Breakdowns in building, distributing, or updating software caused by vulnerabilities or malicious changes in third-party code and dependencies.

**Key risks:** Untracked versions, outdated dependencies, compromised vendors, self-propagating malware via package ecosystems, weak CI/CD access controls.

**Prevention:** SBOM with transitive tracking; monitor CVE/NVD/OSV continuously; official sources over secure links; remove unused dependencies; separation of duties in CI/CD with MFA and signed builds; staged rollouts.

**Skill coverage:** Tier 2 §2.5, `tier2-review.md` A03 section

---

## A04 — Cryptographic Failures

**Description:** Failures in cryptographic implementation including absent/weak encryption, compromised keys, and deprecated algorithms.

**Key risks:** Plaintext data in transit or at rest, weak password hashing, hardcoded keys, deprecated algorithms (MD5, SHA1, ECB, CBC), insufficient RNG entropy.

**Prevention:** Classify sensitive data; encrypt at rest with AES-256-GCM; TLS 1.2+ with forward secrecy; Argon2/scrypt for passwords; proper key management via HSM or cloud KMS; secure RNG; plan for post-quantum transition by 2030.

**Skill coverage:** Tier 1 rule 5, Tier 2 §2.4, `tier2-review.md` A04 section

---

## A05 — Injection

**Description:** Untrusted user input reaches an interpreter without proper validation, causing it to execute malicious commands.
Includes SQL, NoSQL, OS command, LDAP, and XPath injection.

**Key risks:** Unauthorized data access/modification/deletion, arbitrary code execution, auth bypass.

**Prevention:** Parameterized APIs or ORMs; positive server-side allowlist validation; interpreter-specific escaping for residual dynamic queries; SAST/DAST in CI/CD.

**Skill coverage:** Tier 1 rule 1, Tier 2 §2.1 §2.2, `tier3-input-validation.md`, `tier3-database.md`

---

## A06 — Insecure Design

**Description:** Missing or ineffective control design at the architectural level — flaws present from inception that correct implementation alone cannot fix.

**Key risks:** Business logic flaws, no rate/quantity limits, race conditions in critical flows, weak credential recovery, no bot protection, trust boundary violations.

**Prevention:** Secure development lifecycle with AppSec involvement; threat modeling for critical functions; paved-road components; unit/integration tests validating threat resistance; segregated layers and tenants.

**Skill coverage:** Tier 1 design principles, Tier 2 §2.3, `tier3-threat-modeling.md`

---

## A07 — Authentication Failures

**Description:** Weak or missing authentication controls allow attackers to gain unauthorized access.

**Key risks:** Credential stuffing, brute force, default or weak passwords, inadequate MFA, session management failures, poor credential recovery.

**Prevention:** Enforce MFA; prohibit default credentials; check HIBP at registration; NIST 800-63b password policies; high-entropy server-side session IDs in secure cookies; login throttling with consistent error messages; invalidate sessions on logout.

**Skill coverage:** Tier 1 rule 2, Tier 2 §2.3, `tier2-review.md` A07 section

---

## A08 — Software or Data Integrity Failures

**Description:** Failing to verify the integrity of software, code, and data — treating untrusted updates or serialized objects as legitimate.

**Key risks:** Untrusted plugins/libraries, auto-update without signature verification, insecure CI/CD, unsafe deserialization enabling object manipulation.

**Prevention:** Digital signatures for software and data; restrict dependencies to vetted repositories; code review for all pipeline changes; CI/CD access controls; reject unsigned serialized data from untrusted sources.

**Skill coverage:** Tier 1 rule 9, Tier 2 §2.5, `tier2-review.md` A08 section, `tier3-language-specific.md`

---

## A09 — Security Logging & Alerting Failures

**Description:** Lack of adequate logging, monitoring, and alerting — attackers exploit the gap to operate undetected.

**Key risks:** Breaches undetected for extended periods, no forensic trail, sensitive data in logs, log tampering.

**Prevention:** Log all auth attempts, access control failures, and high-value transactions; protect log integrity with append-only storage; encode log data; clear alerting thresholds; centralized log management.

**Skill coverage:** Tier 1 rule 7, `tier3-error-handling.md`, `tier2-review.md` A09 section

---

## A10 — Mishandling of Exceptional Conditions

**Description:** New in 2025.
Applications fail to prevent, detect, or appropriately respond to abnormal conditions, leaving systems in unpredictable states.

**Key risks:** Resource exhaustion, sensitive data exposure via error messages, state corruption in multi-step transactions, logic bugs from unhandled edge cases.

**Prevention:** Centralized exception handling; fail closed with complete rollback; strict input validation; rate limiting and resource quotas; generic error messages to users; detailed internal logging; threat modeling and penetration testing.

**Skill coverage:** Tier 1 rules 7 8, `tier3-error-handling.md`, `tier2-review.md` A10 section
