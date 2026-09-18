# Security Policy

## Reporting a Vulnerability

We take the security of `book2game` seriously. If you believe you have
found a security vulnerability, please do **not** open a public issue. Instead,
contact the maintainer directly at **[REDACTED]**.

We aim to respond within 48 hours and will work with you to resolve the issue
promptly and responsibly.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :white_check_mark: |

## Security Architecture Notes

- The canonical layer is **read-only** from source text. No network calls.
- All verification uses **deterministic SHA-256 hashes**.
- `unresolved-ambiguities.json` quarantines any unverifiable claims.
- The pipeline does not collect or transmit user data.

## Dependencies

- Core pipeline has **zero external dependencies** (pure Python stdlib).
- Optional packages (pandoc, pymupdf, ebooklib, python-docx) are used only
  for format parsing and are pinned via `scripts/requirements.txt`.

## Security Scanning

Run the validation gate to check for security issues in output artifacts:
```bash
python scripts/validate_output.py ./my-game
```
