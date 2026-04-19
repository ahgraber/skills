# Tier 3 — Language-Specific Secure Patterns

Quick-reference forbidden patterns and safe alternatives.
Apply during implementation or review.

---

## Python

**Never use:**

| Forbidden                                        | Risk                         |
| ------------------------------------------------ | ---------------------------- |
| `eval()`, `exec()`                               | Code injection               |
| `pickle.loads()` on untrusted data               | Arbitrary code execution     |
| `os.system()`, `subprocess` with `shell=True`    | Command injection            |
| `yaml.load()`                                    | Arbitrary code execution     |
| `hashlib.md5()` / `hashlib.sha1()` for passwords | Weak; use `argon2`           |
| `random` for security tokens                     | Not cryptographically secure |

**Use instead:**

- `ast.literal_eval()` for safe expression evaluation
- `subprocess.run(["cmd", "arg"], shell=False)` with list args
- `yaml.safe_load()` for YAML parsing
- `secrets` module for cryptographic tokens
- `cryptography` library (not `pycrypto`)
- `argon2-cffi` for password hashing

**Validation and auth:**

- Validation: `pydantic` or `marshmallow`
- Django: ORM + built-in auth
- Flask: `flask-wtf` for CSRF, `flask-login` for auth

---

## JavaScript / Node.js

**Never use:**

| Forbidden                            | Risk                               |
| ------------------------------------ | ---------------------------------- |
| `eval()`, `Function()` constructor   | Code injection                     |
| `innerHTML`, `document.write()`      | XSS                                |
| `Math.random()` for security tokens  | Not cryptographically secure       |
| String concatenation for HTML or SQL | XSS / injection                    |
| `var`                                | Scope confusion; use `const`/`let` |

**Use instead:**

- `JSON.parse()` for JSON
- `textContent` for DOM text insertion
- `DOMPurify.sanitize()` when HTML rendering is required
- `crypto.randomBytes()` or `crypto.getRandomValues()` for tokens
- `===` strict equality throughout

**Libraries:**

- Security headers: `helmet`
- Rate limiting: `express-rate-limit`
- Validation: `zod`, `joi`, or `yup`
- Use TypeScript for type safety

---

## Java

**Never use:**

| Forbidden                                       | Risk                                      |
| ----------------------------------------------- | ----------------------------------------- |
| `Runtime.exec()` with user input                | Command injection                         |
| `new ObjectInputStream()` on untrusted data     | Unsafe deserialization                    |
| JNDI lookups from user input                    | Remote code execution (Log4Shell pattern) |
| XML parsing without disabling external entities | XXE                                       |
| `Statement` for SQL                             | SQL injection                             |

**Use instead:**

- `PreparedStatement` always
- Spring Security for auth/authz
- `SecureRandom` for token generation
- OWASP Java Encoder for output encoding

**XXE prevention:**

```java
factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
```

---

## C# / .NET

**Never use:**

| Forbidden                         | Risk                   |
| --------------------------------- | ---------------------- |
| `BinaryFormatter`                 | Unsafe deserialization |
| SQL string concatenation          | SQL injection          |
| `Process.Start()` with user input | Command injection      |

**Use instead:**

- Entity Framework or `SqlCommand` with `SqlParameter`
- ASP.NET Core Identity for auth
- `System.Security.Cryptography` for all crypto
- Secret Manager (dev) / Azure Key Vault (prod) for secrets

**Framework settings:**

- Enable request validation
- Use `[Authorize]` attribute and Data Annotations
- Enable HTTPS redirection middleware
- Use `AntiForgeryToken` for CSRF protection

---

## Review Checklist

- [ ] No language-specific forbidden patterns present (see tables above)
- [ ] Safe alternatives used for all dangerous operations
- [ ] Framework auth/session features used; no custom implementations
- [ ] Cryptographically secure RNG used for all token generation
- [ ] Shell commands use list args with `shell=False` / equivalent
