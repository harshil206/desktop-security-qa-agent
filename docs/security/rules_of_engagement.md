# Rules of Engagement and Scan Policy Specification

This document defines the safety boundaries, authorization protocols, and scan budgets for the Desktop Website Security & QA Agent.

## 1. Safety-First Principle

The agent is designed as a safety-first scanning utility. It operates strictly within the limits established by the user's explicit authorization. To prevent abuse and accidental scanning of third-party domains, the system enforces the following boundaries:

1. **Explicit Authorization:** No scan request may be initiated without a validated `AuthorizationRecord`.
2. **Strict Scoping:** All requested scan targets (domains and allowed URL prefixes) must be a subset of the domains defined in the `AuthorizationRecord`.
3. **Passive-Only MVP:** The scanner defaults to read-only passive analysis. It does not perform form submissions (POST/PUT/DELETE), active exploit payloads, or state-altering requests.
4. **Conservative Budgets:** Rate limits, request limits, recursion depth, and scan duration have strict hard maximum constraints built into the validation layer.

---

## 2. Authorization Record Schema

Every scan must be accompanied by an authorization record confirming target ownership or explicitly granted testing rights.

| Field | Type | Description | Validation Rule |
| :--- | :--- | :--- | :--- |
| `contact_email` | String | Email address of the authorizing contact. | Must match standard email format. |
| `authorized_by` | String | Name of the person or entity providing authorization. | Non-empty string. |
| `owner_confirmed` | Boolean | Confirmation that the operator owns the target or has permission. | Must be strictly `True`. |
| `valid_from` | DateTime | Timestamp when the authorization window starts. | Must be a valid datetime. |
| `valid_until` | DateTime | Timestamp when the authorization window expires. | Must be a valid datetime after `valid_from`. |
| `target_domains` | List[String] | The list of hostnames/domains permitted to be scanned. | Must be non-empty. Each entry must be a valid hostname (no schemes/paths). |

---

## 3. Scan Policy Schema

The scan policy governs the behavior, speed, depth, and limits of the local crawler.

| Field | Type | Description | Validation Rule |
| :--- | :--- | :--- | :--- |
| `authorization` | Object | The referenced `AuthorizationRecord`. | Must be present and valid. |
| `target_domains` | List[String] | The list of hostnames to scan. | Must be a non-empty subset of the authorization record's `target_domains`. |
| `allowed_url_prefixes` | List[String] | List of absolute URL prefixes permitted for scanning. | Must be non-empty. Every URL must map to one of the scoped `target_domains`. |
| `max_depth` | Integer | Max recursion depth of the web crawler. | Range: `1` to `5`. Default: `3`. |
| `requests_per_minute` | Integer | Rate limiting budget. | Range: `1` to `120`. Default: `60`. |
| `total_request_budget` | Integer | Maximum total requests allowed for the scan job. | Range: `1` to `1000`. Default: `500`. |
| `max_duration_seconds` | Integer | Maximum duration of the scan job. | Range: `1` to `3600` (1 hour). Default: `1800` (30 mins). |
| `scan_mode` | String | Scan execution mode (passive vs. active). | Enforced strictly as `"passive"`. |
| `allowed_http_methods` | List[String] | HTTP methods the crawler is allowed to use. | Must contain only safe read-only methods (`GET`, `HEAD`). |

---

## 4. Operational Controls

- **Emergency Stop:** If any target returns a request to stop or rate-limits are violated, the local scan service will transition the job to a `blocked` or `failed` state.
- **Redirection Validation:** Any HTTP redirect followed during a crawl must have its destination URL re-validated against the `allowed_url_prefixes` and `target_domains`. Any redirect destination out-of-scope will be logged as skipped and NOT fetched.
