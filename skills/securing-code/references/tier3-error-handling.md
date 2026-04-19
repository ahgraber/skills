# Tier 3 — Error Handling & Security Logging

Apply when reviewing or implementing exception handling, logging, or monitoring.

## Secure Error Handling

- [ ] Catch all exceptions — never let them propagate raw to the user
- [ ] **Fail closed** — on transaction error, roll back completely; never attempt partial recovery
- [ ] User-facing messages: generic only — never expose stack traces, DB errors, file paths, framework versions, or internal system details
- [ ] Assign a unique error ID in logs; surface to users only when a support channel can act on it
- [ ] Use correct HTTP status codes:
  - `400` — bad input
  - `401` — unauthenticated
  - `403` — unauthorized (or `404` to prevent enumeration — log as authz failure either way)
  - `404` — not found
  - `429` — rate limited
- [ ] Always enforce authorization first, then choose response shaping (403 vs 404) as a secondary decision

## Security Event Logging — What to Log

Log ALL of the following:

- Authentication events: success, failure, logout, MFA enrollment, MFA bypass attempt
- Authorization failures
- Input validation failures (especially repeated patterns from the same source)
- Critical business operations and admin actions
- Sensitive data access
- Configuration changes
- Rate limit triggers

**Each log entry must include:** timestamp (ISO 8601, UTC), user identifier, source IP, user agent, action attempted, result (success/failure), resource accessed, unique request ID.

## Security Event Logging — What Never to Log

Never log: passwords, session tokens, API keys, credit card numbers, SSNs, crypto keys, PII, or any secret material.

**Log injection prevention:** validate and escape any user-controlled data before writing to logs.

## Log Security

- [ ] Append-only storage; restricted access
- [ ] Encrypted at rest
- [ ] Protected against log injection (escape user-controlled content before logging)
- [ ] Backed up and integrity-protected
- [ ] Alerts configured for high-frequency auth failures, repeated validation failures, and unusual access patterns

## Review Checklist

- [ ] All exceptions caught; none propagate raw to users
- [ ] Transactions fail closed with complete rollback on error
- [ ] No stack traces or internal details in user-facing error responses
- [ ] All OWASP A09 events (auth, authz, validation failures, critical ops) logged with required fields
- [ ] No secrets or PII in logs
- [ ] Log entries escaped against injection
- [ ] Correct HTTP status codes used; authz failures always logged regardless of 403 vs 404 choice
