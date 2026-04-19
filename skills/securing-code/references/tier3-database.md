# Tier 3 — Database Security

Apply when reviewing or implementing database access, query construction, or data storage.

## Injection Prevention (Critical)

- **Always use parameterized queries or prepared statements** — non-negotiable for SQL and NoSQL
- **Never concatenate user input** into query strings — applies to MongoDB, CouchDB, Redis, and all NoSQL equally
- **Never merge untrusted objects into queries** — use typed query APIs/ORMs, schema validation, allowlisted operators and fields
- **Explicitly block server-side JS execution features** in MongoDB and similar (e.g., `$where`, `mapReduce`, `$function`)
- **Prefer ORM query builders**; if raw SQL is required, still use parameter binding
- Stored procedures are **not** automatically safe — they remain vulnerable if they concatenate queries internally

## Access Control

- [ ] Use least-privilege database accounts — separate read and write accounts where possible
- [ ] Application accounts must not have `DROP`, `CREATE`, or `ALTER` permissions
- [ ] Never use `root`, `DBO`, `sa`, or equivalent superuser accounts for application connections
- [ ] Connection strings stored in a secret manager, never in code or config files checked into source control

## Connection Security

- [ ] Require TLS/SSL for all database connections; validate server certificates
- [ ] Credentials rotated on a schedule and immediately on suspected compromise

## Data Protection

- [ ] Encrypt sensitive columns at rest
- [ ] Hash + salt passwords with Argon2id, bcrypt, or scrypt before storage — never plaintext or reversibly encrypted
- [ ] Enable database audit logging for sensitive data access
- [ ] Classify and label sensitive data fields; document data flows

## Review Checklist

- [ ] All queries use parameterized statements or ORM query builders
- [ ] No string concatenation in any query construction path
- [ ] NoSQL queries use typed APIs; `$where` and JS execution features disabled
- [ ] Database account has minimum required privileges; no DDL permissions
- [ ] No superuser account used for application connections
- [ ] TLS enforced for database connections
- [ ] Passwords hashed with Argon2id/bcrypt (not MD5, SHA1, or unsalted hashes)
- [ ] Sensitive columns encrypted at rest
- [ ] Credentials sourced from secret manager, not code or config
