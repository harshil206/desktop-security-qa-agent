# Website Security & QA Agent: End-to-End Build Roadmap

## 1. Product definition

Build an AI-assisted Website Security & QA platform that assesses only websites the customer owns or is explicitly authorized to test. It works without user credentials by default, discovers publicly reachable application behavior, gathers reproducible evidence, performs safe rule-based checks, and produces useful engineering reports.

### Non-negotiable product rules

- Every scan requires an approved target, owner/authorization record, and explicit scope.
- Passive, read-only scanning is the default.
- Do not submit forms, create accounts, make purchases, change data, or probe third-party domains unless an authorized engagement explicitly permits it.
- Enforce domain/path allowlists, request budgets, time limits, concurrency caps, and redirect re-validation in code.
- Security findings require collected evidence; an LLM can explain findings but cannot invent or verify them.

## 2. Target architecture

```text
Web dashboard / API
        |
Scan policy service (authorization, scope, budgets)
        |
Job queue ----> Browser worker (Playwright) ----> evidence artifacts
        |              |
        |              +--> crawler + network/API discovery
        |
        +-----------> rule engine -----------> verified findings
                                                  |
                              evidence store <---+
                                                  |
                                 AI analysis / report service
                                                  |
                                 HTML, PDF, JSON, SARIF reports
```

Suggested implementation stack:

- Backend: Python + FastAPI.
- Browser automation: Playwright.
- Queue: Redis + Celery, RQ, or Temporal.
- Database: PostgreSQL.
- Evidence artifact storage: S3-compatible object storage.
- Frontend: React + TypeScript.
- Reports: HTML templates, PDF rendering, JSON/SARIF export.
- AI: a provider adapter so models can be changed without rewriting scan logic.
- Deployment: Docker first; managed containers or Kubernetes later.

## 3. Delivery phases

## Phase 0 — Scope, safety, and success measures

**Goal:** Define exactly what the product is allowed to do before writing scanner code.

Build:

- A rules-of-engagement template: target owner, approved domains/subdomains, allowed paths, time window, allowed test modes, contact, and emergency stop procedure.
- A scan policy schema covering allowed hosts, URL prefixes, max depth, requests per minute, total requests, scan duration, and allowed HTTP methods.
- A risk classification policy: verified finding, likely finding, observation, informational, and not reproducible.
- A short list of measurable v1 outcomes: coverage, scan duration, false-positive rate, percentage of findings with evidence, and report usefulness.

Exit criteria:

- You can reject an unauthorised or out-of-scope scan before any network request is sent.
- The team agrees which checks are passive-only and which need a separate active-testing approval.

## Phase 1 — Development foundation

**Goal:** Create a safe, repeatable local development environment.

Build:

- A monorepo or clearly separated backend, frontend, worker, and infrastructure directories.
- Docker-based local services for the API, database, queue, and object storage emulator.
- Configuration handling through environment variables and a secrets manager approach; never commit API keys or test credentials.
- CI checks for formatting, type checking, tests, dependency scanning, and secret scanning.
- An intentionally vulnerable training application or an application you own for test scans.

Exit criteria:

- A new developer can run the complete environment locally from documented steps.
- Automated tests run in CI and no production targets are required for development.

## Phase 2 — Scan policy and job lifecycle

**Goal:** Establish the control plane before implementing crawling.

Build:

- API endpoints to create targets, upload authorization information, define scope, and start/cancel scans.
- A durable job state machine: `draft → scope validated → queued → running → evidence review → completed/failed/blocked`.
- Server-side validation for domains, IP ranges, URL prefixes, allowed methods, and redirect destinations.
- Audit logs for scan creation, policy decisions, worker actions, cancellations, and report downloads.
- A global emergency-stop control and per-scan cancellation.

Exit criteria:

- Workers receive an immutable, validated policy with every scan.
- Any redirect or newly discovered URL outside policy is blocked and recorded.

## Phase 3 — Passive crawler and coverage engine

**Goal:** Safely discover public application surface area.

Build:

- URL normalization and deduplication.
- Seed URL support, optional sitemap discovery, internal-link extraction, and safe redirect following.
- Breadth/depth limits, same-origin enforcement, rate limiting, timeouts, retry policy, and total request budget.
- A URL risk classifier to avoid interactions with endpoints likely to cause side effects.
- Coverage records: visited URLs, skipped URLs, blocked URLs, status codes, content types, and discovery source.

Exit criteria:

- The crawler cannot leave the approved scope.
- A completed scan shows what was visited, skipped, and blocked—and why.

## Phase 4 — Browser automation and QA evidence

**Goal:** Handle modern JavaScript applications and capture reliable artifacts.

Build:

- Playwright navigation with stable waits, timeouts, clean browser contexts, and one isolated profile per scan.
- Collection of page title, DOM snapshot, screenshots, console errors, page errors, network requests/responses, response headers, and client-side routes.
- Passive UI checks: broken links, failed assets, JavaScript errors, HTTP errors, basic form metadata, viewport rendering, and accessibility signals.
- Browser traces for failed or high-value flows.
- Redaction of sensitive data in artifacts and logs.

Exit criteria:

- Every QA observation links to a timestamped screenshot, trace, console record, or request/response artifact.
- The worker performs no state-changing interaction in default mode.

## Phase 5 — Deterministic security checks

**Goal:** Implement a small, high-confidence passive security ruleset.

Start with checks such as:

- HTTPS/TLS configuration observations.
- Missing or unsafe security-header configurations.
- Cookie flags and session-cookie properties visible in public responses.
- CORS response configuration.
- Information exposed through error pages, debug headers, public metadata files, and server banners.
- Open redirects only when safe to identify passively from observed behavior or authorised low-impact tests.
- Outdated client-side library identification, clearly labelled as an observation until a vulnerable version is corroborated.

For every rule, define:

- Rule ID and version.
- Preconditions and scope limitations.
- Exact evidence fields required.
- Severity guidance and confidence calculation.
- Remediation text and references.
- Regression tests for both positive and negative cases.

Exit criteria:

- Rules produce structured findings with evidence links and no AI dependency.
- Findings have a test suite that prevents known false positives from returning.

## Phase 6 — Evidence, finding, and review workflow

**Goal:** Make results auditable and useful to security engineers.

Build:

- A finding data model containing title, category, asset, evidence references, severity, confidence, status, remediation, and rule version.
- Immutable source artifacts plus a derived, redacted display representation.
- Finding grouping and deduplication.
- Human review states: new, confirmed, needs review, accepted risk, false positive, fixed, and retest requested.
- Re-scan comparison and a way to prove a finding was remediated.

Exit criteria:

- A reviewer can open any finding and reproduce why it was generated.
- A report can separate verified issues from hardening observations and inconclusive signals.

## Phase 7 — AI assistance, introduced safely

**Goal:** Improve understanding and report quality without putting AI in control of scanning.

Build:

- A provider-agnostic AI service with an interface such as `summarize_finding`, `draft_remediation`, and `create_executive_summary`.
- Schema-constrained input: only structured findings and approved, redacted evidence excerpts are sent to the model.
- Schema-constrained output with citations to evidence IDs.
- A prompt/evaluation suite that checks for invented findings, unsupported impact claims, and missing caveats.
- Separate roles: report writer is read-only; evidence analyst cannot initiate crawling; policy service has no LLM dependency.
- Cost, token, latency, model-version, and output-quality observability.

Exit criteria:

- Turning off the AI service does not stop scanning or remove verified findings.
- Every AI-generated statement can be traced to a rule result or evidence artifact.

## Phase 8 — Dashboard and report outputs

**Goal:** Deliver findings in formats different audiences can use.

Build:

- Scan setup page showing authorization, scope, limits, and scan mode.
- Scan-progress page showing coverage, queue status, and blocked actions.
- Findings pages with clear severity/confidence separation and evidence viewers.
- Engineering report with reproducible evidence and precise remediation.
- Executive report with risk summary, trends, coverage limitations, and remediation priorities.
- HTML, PDF, JSON, and SARIF export; visually test PDF layout before release.

Exit criteria:

- Engineers can fix an issue using the report without asking what the scanner saw.
- Security teams can export structured findings into their existing workflow.

## Phase 9 — Controlled active testing (optional, later)

**Goal:** Add carefully bounded active checks only after passive scanning is stable and the organisation has a formal authorization process.

Build:

- A separate active-test authorization switch that requires an engagement-specific approval.
- A distinct allowlist of endpoints, methods, payload classes, request caps, and test windows.
- Side-effect detection, a kill switch, detailed request audit records, and human review gates.
- Dedicated training environments for developing and evaluating active checks.

Exit criteria:

- Active mode is technically impossible to enable without explicit authorization.
- No active check is released without test-environment evidence, rollback guidance, and false-positive evaluation.

## Phase 10 — Production readiness and scale

**Goal:** Operate reliably across authorized customer environments.

Build:

- Tenant isolation, role-based access control, SSO, encryption, retention policies, and evidence access controls.
- Isolated, short-lived browser workers with restricted network egress.
- Per-customer quotas and fair-use limits.
- Metrics, tracing, alerting, backups, disaster recovery, and incident response runbooks.
- Dependency patching, container scanning, threat modeling, penetration testing of the platform itself, and external security review.
- Release management with canary deployments and rule/model versioning.

Exit criteria:

- The platform has documented operational ownership, monitored service-level objectives, and tested recovery procedures.
- A security review confirms that the scanner cannot be easily abused as an uncontrolled scanning service.

## 4. Recommended build order for a small team

1. Phase 0–2: product owner, security lead, backend engineer.
2. Phase 3–5: backend engineer plus browser/security engineer.
3. Phase 6 and 8: full-stack engineer and security analyst.
4. Phase 7: AI engineer after evidence quality is stable.
5. Phase 9–10: security lead, DevOps engineer, and independent reviewer.

Do not start with the LLM, a dashboard, or active testing. Build policy enforcement, evidence collection, and deterministic checks first.

## 5. Minimum viable product

An MVP should:

- Scan a single approved domain with strict same-origin scope.
- Crawl public pages within small request and time budgets.
- Capture screenshots, headers, network metadata, and console errors.
- Run a small passive ruleset.
- Store evidence and create an HTML report.
- Allow a reviewer to mark findings confirmed, false positive, or fixed.

Only after the MVP has a reliable evidence trail should you add AI report writing, a richer dashboard, multi-tenant support, and authorized active testing.

## 6. Definition of done

The product is ready for a controlled production launch when it can:

- Prove authorization and enforce scan scope for every job.
- Collect reliable evidence from dynamic web applications without uncontrolled interactions.
- Produce low-noise findings with clear confidence and reproducible proof.
- Generate reports useful to both developers and security leaders.
- Keep AI outputs evidence-bound, auditable, optional, and non-authoritative.
- Operate in isolated infrastructure with access controls, logging, monitoring, retention controls, and an incident-response process.
