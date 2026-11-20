# Tier 3 — Memory Safety (C, C++, Embedded Systems)

Apply when reviewing or implementing code in C, C++, or memory-unsafe languages.

## Language Choice

Prefer memory-safe languages (Rust, Go, Java, C#, Python) over C/C++.
If C/C++ is required, apply **all** of the following.

## Buffer Overflow Prevention

- [ ] Use safe string functions: `snprintf`, `strlcpy`, `strlcat`
- [ ] Never use: `gets()`, `sprintf()`, `strcpy()`, `strcat()`
- [ ] Always check buffer bounds before writing
- [ ] Validate array indices before access

**Required compiler/linker flags:**

- Stack protector: `-fstack-protector-strong`
- Position Independent Executable: `-fPIE -pie`
- RELRO: `-Wl,-z,relro,-z,now`
- Fortify Source: `-D_FORTIFY_SOURCE=2`
- Warnings as errors: `-Werror`
- Sanitizers in CI: `-fsanitize=address,undefined`

**Runtime/OS requirements:**

- ASLR enabled on target OS
- DEP/NX enabled

## Integer Safety

- [ ] Check for overflow before arithmetic operations
- [ ] Use safe integer libraries where available
- [ ] Enable `-Woverflow` and treat as error

## Memory Management

- [ ] Initialize all variables at declaration
- [ ] Check return values of `malloc`/`calloc`; never assume success
- [ ] Free memory exactly once; set pointers to `NULL` after free
- [ ] In C++: use smart pointers (`unique_ptr`, `shared_ptr`); use RAII; prefer `std::vector` and `std::string` over raw arrays and `char*`; use `std::span` for bounds-checked access

## Testing

- [ ] AddressSanitizer enabled in test builds
- [ ] UndefinedBehaviorSanitizer enabled in test builds
- [ ] Fuzz input-handling functions with libFuzzer or AFL

## Review Checklist

- [ ] No `gets()`, `sprintf()`, `strcpy()`, `strcat()` present
- [ ] All buffer writes bounds-checked
- [ ] Compiler flags include stack protector, PIE, RELRO, Fortify
- [ ] Integer arithmetic checked for overflow
- [ ] `malloc`/`calloc` return values checked; not assumed to succeed
- [ ] No double-free; pointers set to NULL after free
- [ ] C++ code uses smart pointers; no raw `new`/`delete` outside RAII wrappers
- [ ] Sanitizers enabled in CI
