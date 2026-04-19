# Tier 3 — File Upload Security

Apply when reviewing or implementing any file upload or download functionality.

## Validation

- [ ] Allowlist permitted file extensions
- [ ] Verify magic bytes (file signature) — extension alone is insufficient
- [ ] Enforce maximum file size limit
- [ ] Reject filenames containing path traversal characters (`../`, `\`, null bytes)
- [ ] Virus/malware scanning if applicable (mandatory for regulated environments)

**Block by default:** `.exe`, `.dll`, `.bat`, `.cmd`, `.sh`, `.js`, `.vbs`, `.ps1`, `.php`, `.asp`, `.jsp`, `.py`

**Archives (`.zip`, `.rar`, `.tar`, `.gz`):** Block by default.
If archives must be supported:

- Unpack in a sandbox
- Enforce total uncompressed size limits (zip bomb prevention)
- Prevent path traversal on extraction
- Scan extracted contents before making available

## Storage

- [ ] Store outside the web root — never in a directory served directly by the web server
- [ ] Generate a unique, unpredictable filename (UUID or equivalent); store the original name separately in the database
- [ ] Set restrictive file permissions (no execute bit)
- [ ] Use a separate domain or storage service (e.g., S3, GCS, Azure Blob) for user-uploaded content
- [ ] Never execute uploaded files

## Retrieval

- [ ] Verify user authorization before serving any file
- [ ] Set `Content-Type` explicitly based on allowlisted type; never trust the uploaded MIME type
- [ ] Set `Content-Disposition: attachment` for untrusted file types
- [ ] Apply rate limiting on both upload and download endpoints
- [ ] Serve files as read-only

## Review Checklist

- [ ] Magic bytes checked, not just file extension
- [ ] Dangerous file types blocked
- [ ] Path traversal characters rejected from filenames
- [ ] Files stored outside web root with unpredictable names
- [ ] Authorization checked before serving files
- [ ] `Content-Disposition: attachment` set for untrusted types
- [ ] Rate limiting applied to upload and download
- [ ] No uploaded files executed or run through an interpreter
