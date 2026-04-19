# Tier 3 — Threat Modeling

Apply during design review or when implementing auth flows, payment systems, multi-tenant features, or any security-critical component.

## STRIDE Analysis

For each component or trust boundary, step through STRIDE:

| Threat                     | Question                                                |
| -------------------------- | ------------------------------------------------------- |
| **Spoofing**               | Can attackers impersonate users or services?            |
| **Tampering**              | Can attackers modify data in transit or at rest?        |
| **Repudiation**            | Can users deny actions they performed?                  |
| **Information Disclosure** | Can sensitive data be accessed by unauthorized parties? |
| **Denial of Service**      | Can attackers disrupt availability?                     |
| **Elevation of Privilege** | Can attackers gain unauthorized access levels?          |

## For Each Identified Threat

1. Rate **likelihood** and **impact**: Critical / High / Medium / Low
2. Identify the **attack vector** and entry point
3. Recommend a **mitigation control**
4. Note whether the control **Eliminates, Reduces, Transfers, or Accepts** the risk

## Trust Boundary Analysis

Identify and document:

- **Trust boundaries** — where data crosses between trust zones (user → server, service → service, public → internal)
- **Sensitive data flows** — where PII, secrets, or regulated data is handled, stored, or transmitted
- **External dependencies** — third-party services, libraries, or APIs and their risk surface

## Deliver

1. Prioritized threat list (Critical → High → Medium → Low)
2. Recommended mitigations with implementation notes
3. Residual risks to document and accept explicitly

## Common High-Risk Patterns

Always check for these regardless of feature type:

- **Credential recovery** — security questions, weak reset flows, enumerable or short-lived tokens
- **Business logic limits** — no per-user rate limits, quantity limits, or workflow ordering enforcement
- **Race conditions** — concurrent requests to payment, inventory, or auth state transitions
- **Bot protection gaps** — scalper/automation attacks on endpoints without CAPTCHA or behavioral analysis
- **Privilege escalation paths** — parameter tampering, IDOR, JWT claim manipulation, role confusion
- **Dangerous file operations** — upload/download without authz, path traversal in file access

## Review Checklist

- [ ] STRIDE applied to each component and trust boundary in scope
- [ ] All trust boundaries identified and documented
- [ ] Sensitive data flows mapped
- [ ] External dependency risk surface assessed
- [ ] Business logic limits enforced (rate, quantity, workflow ordering)
- [ ] Race conditions addressed in critical flows
- [ ] Residual risks explicitly accepted and documented
