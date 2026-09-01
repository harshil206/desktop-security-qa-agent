# Architecture Specification: Finding, Evidence, and Report Contracts

This document defines the data contracts used across the scanner service, data layer, report generators, and desktop client.

## 1. Scan Lifecycle and Statuses

A scan job progresses through explicit states. State transitions are strictly validated.

| Status | Description |
| :--- | :--- |
| `draft` | Scan configuration is being built. |
| `scope_validated` | Authorization record and target domains/prefixes are validated. |
| `queued` | Scan job is queued for execution. |
| `running` | Crawler and Playwright browser workers are actively executing. |
| `evidence_review` | Raw artifacts are stored and undergoing evidence validation/deduplication. |
| `completed` | Scan completed successfully within budget. |
| `failed` | Scan encountered an unrecoverable worker error. |
| `cancelled` | User initiated a scan cancellation. |
| `blocked` | Emergency stop triggered (e.g. rate limit, scope breach attempt, or host request). |

---

## 2. Severity and Confidence Enums

To prevent confusing risk signals, severity (impact) and confidence (evidence strength) are strictly separated.

### Severity
- `critical`: Vulnerability leads to immediate data breach, unauthenticated RCE, or full system compromise.
- `high`: High impact issue (e.g., severe injection risk, broken access control).
- `medium`: Moderate impact (e.g., misconfigured security headers exposing sensitive information, CSRF).
- `low`: Hardening opportunity or minor security oversight.
- `info`: Non-vulnerability observation, QA issue, or technology discovery.

### Confidence
- `confirmed`: Verified by machine evidence or reproducible check.
- `high`: Strong multi-source evidence points to issue.
- `medium`: Single-source passive signal observed.
- `low`: Inconclusive observation requiring human investigation.

---

## 3. Evidence Reference Contract (`EvidenceRef`)

Every finding must link to one or more evidence references. An evidence reference points to machine-collected data.

### Fields
- `artifact_id` (str): Unique identifier of the collected artifact.
- `artifact_type` (Enum): Type of artifact (`screenshot`, `dom_snapshot`, `network_trace`, `response_header`, `console_log`, `page_error`, `http_response`).
- `location_url` (str): Target URL where the evidence was collected.
- `timestamp` (datetime): Exact collection timestamp.
- `snippet_or_description` (str): Redacted text snippet, header value, or log line describing the evidence.
- `metadata` (dict, optional): Additional structured metadata (e.g. status code, selector).

---

## 4. Finding Contract (`Finding`)

A `Finding` represents a security or QA observation. **Strict Rule:** A finding cannot exist without at least one `EvidenceRef`.

### Fields
- `finding_id` (str): Unique identifier for the finding.
- `title` (str): Short, descriptive title.
- `description` (str): Detailed explanation of the finding.
- `category` (str): Category (e.g., `security_header`, `tls_config`, `broken_link`, `console_error`).
- `affected_asset` (str): The target URL or resource affected.
- `severity` (Severity): Impact rating.
- `confidence` (Confidence): Detection confidence rating.
- `rule_id` (str): ID of the deterministic rule that triggered the finding.
- `rule_version` (str): Version of the rule module.
- `remediation` (str): Actionable guidance for fixing the issue.
- `evidence` (List[EvidenceRef]): Non-empty list of evidence references (**Required**).

---

## 5. Report Contract (`Report`)

A `Report` synthesizes scan outcomes, policy details, coverage counts, and verified findings.

### Fields
- `report_id` (str): Unique identifier of the report.
- `scan_id` (str): Associated scan job ID.
- `created_at` (datetime): Report generation timestamp.
- `policy_summary` (dict): Summary of target domains and scan limits.
- `coverage_summary` (dict): Statistics (visited URLs, skipped URLs, blocked URLs, total requests, scan duration).
- `findings` (List[Finding]): List of findings produced during the scan.
- `findings_count_by_severity` (dict): Summary breakdown by severity level.
