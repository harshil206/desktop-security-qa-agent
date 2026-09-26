# Evidence Redaction and Artifact Storage Security Policy

## Overview
This document specifies the security controls and automated data redaction rules implemented by the Desktop Security & QA Scanner agent (`services/scanner/storage/redactor.py` and `services/scanner/storage/artifact_store.py`).

The primary objective is to guarantee that sensitive credentials, authentication tokens, session cookies, and personally identifiable information (PII) captured during passive scans are automatically sanitized before user-facing display, API responses, or report export.

---

## 1. Redaction Data Categories

### A. HTTP Headers
The following HTTP request and response header values are automatically replaced with `"[REDACTED]"`:
- `Authorization` (Bearer tokens, Basic auth credentials)
- `Cookie` / `Set-Cookie` (values masked while keeping cookie keys visible, e.g. `session=[REDACTED]`)
- `X-API-Key` / `API-Key`
- `Proxy-Authorization`
- `X-Auth-Token` / `X-CSRF-Token`
- `Sec-WebSocket-Key`

### B. URL Query Parameters
URL query strings containing credentials or sensitive parameters are masked prior to inclusion in `EvidenceRef` locations or summaries:
- Keywords: `token`, `access_token`, `api_key`, `apikey`, `password`, `passwd`, `secret`, `auth`, `session`, `sessionid`, `jwt`, `key`
- Example: `https://example.com/api?token=secret123&user=admin` -> `https://example.com/api?token=[REDACTED]&user=admin`

### C. Tokens & Credentials in Text/HTML Snippets
Unstructured text snippets (such as DOM HTML previews, console log messages, and HTTP response bodies) are scanned with pattern regexes:
- **JWT Tokens:** `eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*`
- **Bearer Tokens:** `Bearer [A-Za-z0-9\-._~+/=]+`
- **Basic Auth:** `Basic [A-Za-z0-9+/=]+`
- **Email Addresses:** `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+`

---

## 2. Artifact Storage Security Controls

- **Local Isolation:** Artifacts are stored under scan-isolated output directories (`outputs/scans/{scan_id}/artifacts/`).
- **Separation of Raw vs Display Evidence:** Raw artifact files remain restricted to local scanner process access, while display copies and `EvidenceRef` objects exposed to the Electron UI or PDF/SARIF report exports are strictly sanitized.
- **No Cloud Backup:** Artifact storage is strictly local and never transmitted to external servers.
