# Skills Roadmap: Website Security & QA / Authorized Red-Team AI Agent

## Purpose and operating boundary

This roadmap is for building an AI-assisted website security and QA agent that can inspect publicly reachable applications **without user credentials**. It must operate only against targets the operator owns or is explicitly authorized to assess.

Design it as a safety-first system:

- Enforce an approved domain and URL scope before every scan.
- Default to passive, read-only collection; gate active checks behind explicit authorization.
- Respect rate limits, request budgets, and `robots.txt` where appropriate to the engagement.
- Do not test third-party domains, make purchases, create accounts, submit forms, or alter data unless those actions are explicitly in scope.
- Treat a finding as a hypothesis until it has reproducible, machine-collected evidence.

## Core skills

| Skill area | Importance | Why it matters |
|---|---:|---|
| Web security and authorized red teaming | Critical | Defines safe test design, threat models, and valid vulnerability evidence. |
| Web fundamentals | Critical | Provides fluency in HTTP, browsers, sessions, APIs, and modern web architecture. |
| AI/LLM engineering | Critical | Enables reliable orchestration, tool use, structured findings, and evidence-aware reasoning. |
| Browser automation | Critical | Discovers JavaScript-rendered behavior, captures network activity, and supports QA flows. |
| Backend development | High | Powers the scan API, job execution, policy enforcement, and integrations. |
| Web crawling | High | Finds reachable pages, endpoints, forms, and assets while maintaining strict scope. |
| False-positive and evidence validation | High | Keeps reports useful, defensible, and safe to act on. |
| Data engineering | Medium | Stores scan state, traces, screenshots, evidence, and trend data efficiently. |
| Frontend/UI | Medium | Makes findings, scan status, evidence, and remediation clear to users. |
| Report generation | Medium | Produces actionable HTML, PDF, and machine-readable output. |
| DevOps and cloud | Medium | Runs isolated workers reliably and securely at scale. |

## Web security and authorized red teaming

Learn the OWASP Top 10 and OWASP Web Security Testing Guide as the foundation. Focus on how issues appear in real systems, what reliable proof looks like, and how to assess them without causing harm.

Key topics:

- Authentication, authorization, sessions, cookies, and access-control failures such as IDOR.
- Input handling and safe detection patterns for injection classes, including XSS and SQL injection.
- CSRF, SSRF, insecure redirects, file handling, and security misconfiguration.
- API risks across REST and GraphQL, including undocumented endpoints and weak object authorization.
- Security headers, TLS, CORS, CSP, dependency exposure, error handling, and information disclosure.
- Threat modeling, scope definition, rules of engagement, severity assessment, and responsible disclosure.

For a credential-free agent, prioritize passive signals and non-invasive checks. Active proof-of-concept behavior should be limited to an explicitly authorized mode with safeguards, low-impact test cases, and a clear audit trail.

## Web fundamentals

Build a strong working model of how browsers and servers communicate:

- HTTP methods, status codes, redirects, caching, content types, headers, and TLS.
- URLs, DNS, origins, same-origin policy, CORS, CSP, and browser storage.
- DOM, JavaScript execution, single-page applications, iframes, service workers, and web workers.
- Cookies, sessions, JWTs, OAuth/OIDC concepts, and authentication boundaries.
- REST, GraphQL, WebSockets, request bodies, pagination, and error formats.

These fundamentals help the agent distinguish a real application behavior from a crawler artifact or a harmless framework default.

## AI/LLM engineering

Use the model as an evidence-aware coordinator and analyst—not as an unconstrained scanner.

- Tool calling with narrow, policy-enforced tools for crawling, browsing, analysis, and reporting.
- Structured outputs (for example, JSON schemas) for scan plans, findings, evidence, and remediation guidance.
- Retrieval over collected artifacts: headers, HTML, DOM snapshots, network records, console logs, screenshots, and known rules.
- Prompt design that requires citations to collected evidence and permits an "insufficient evidence" outcome.
- Deterministic guardrails outside the model for scope, rate limits, allowed methods, and action approval.
- Evaluation datasets with known-safe sites, deliberately vulnerable training apps, expected findings, and false-positive cases.
- Observability for model decisions, tool calls, cost, latency, and policy denials.

## Browser automation / Playwright

Playwright is a strong default because it handles Chromium, Firefox, and WebKit with first-class network, console, trace, and screenshot support.

Develop skill in:

- Navigating pages, waiting for stable UI state, and handling SPA routing.
- Capturing requests, responses, headers, cookies, console messages, and page errors.
- Extracting links, forms, buttons, accessible names, and client-side routes.
- Taking screenshots, videos, and traces as reproducible QA/security evidence.
- Running controlled interaction flows with strict timeouts and no side-effecting actions by default.
- Isolating browser contexts, clearing state, and enforcing target-domain allowlists.

## Backend development

Python or TypeScript are both practical choices. The backend should separate policy enforcement from scan logic.

- Build APIs with FastAPI (Python) or NestJS/Express (TypeScript).
- Use a job queue for long-running scans and retries.
- Create a scan state machine: requested, scope-validated, running, evidence-review, complete, failed, or blocked.
- Implement tenant isolation, authorization records, audit logs, request budgets, and secure secret handling.
- Version scan rules and report schemas so results remain interpretable over time.
- Add automated tests for scope escapes, redirects, subdomains, rate limits, and unsafe-action blocks.

## Web crawling

The crawler should discover coverage without becoming an uncontrolled spider.

- Normalize and deduplicate URLs; handle fragments, query parameters, canonical URLs, and redirects.
- Start from approved seeds, sitemaps, and public robots directives as appropriate to the engagement.
- Maintain domain, host, path, and scheme allowlists; re-check scope after every redirect.
- Use breadth/depth limits, concurrency caps, per-host rate limits, and total request/time budgets.
- Discover static links, forms, JavaScript routes, API calls observed in the browser, and common public metadata files.
- Classify URLs by risk so read-only pages are visited before potentially state-changing endpoints.

## Data engineering

Store evidence so every reported conclusion can be audited and reproduced.

- Relational data: scan configuration, targets, URLs, findings, remediation status, and audit events.
- Object storage: HTML/DOM captures, screenshots, browser traces, response bodies, and report artifacts.
- Search/indexing: extracted text, URLs, headers, endpoints, technology fingerprints, and error signatures.
- Retention rules, encryption, access control, and redaction for cookies, tokens, personal data, and sensitive responses.
- Data lineage linking each finding to the exact scan, tool action, timestamp, and source artifact.

## Frontend / UI

The product UI should make risk and uncertainty obvious rather than overwhelming users.

- Scan setup with visible proof of authorization, scope, rate limits, and passive/active mode.
- Live scan progress, coverage metrics, blocked URLs, and policy-denied actions.
- A findings view showing severity, confidence, affected URLs, evidence, impact, and recommended remediation.
- Evidence viewers for request/response metadata, DOM excerpts, screenshots, console logs, and traces.
- Filtering, deduplication, suppression with justification, remediation workflow, and historical comparison.
- Accessible design and clear language appropriate for both engineering and security audiences.

## Report generation

Reports should be concise, reproducible, and useful to the person fixing the issue.

- Produce HTML for interactive review, PDF for sharing, and JSON/SARIF for integrations.
- For each finding include: title, severity, confidence, affected asset, evidence, reproduction steps, impact, remediation, and references.
- Separate verified findings from observations, hardening opportunities, and inconclusive signals.
- Include scan scope, authorization reference, time window, tooling version, limitations, and coverage summary.
- Ensure PDFs preserve layout and links; render and visually verify templates in automated tests.

## DevOps / cloud

Security scanning workloads should be isolated, observable, and inexpensive to operate.

- Containerize the API, worker, browser runtime, and report renderer.
- Run browser/scanner workers in sandboxed, short-lived environments with restricted egress.
- Use least-privilege IAM, encrypted storage, managed secrets, and network policies.
- Add metrics, logs, traces, alerting, backups, and a dead-letter queue for failed jobs.
- Use infrastructure as code (Terraform or Pulumi) and CI/CD with dependency, secret, and container scanning.
- Plan for worker autoscaling, browser resource limits, and quotas per customer or engagement.

## False-positive and evidence validation

This is a product-defining capability. A finding should be reported only when evidence supports the stated claim.

- Use deterministic checks where possible, and record the rule version that generated the observation.
- Require evidence references for every finding; no model-only claims.
- Separate detection confidence from severity: a high-severity hypothesis with weak evidence is still unverified.
- Corroborate signals across independent sources—for example, headers plus browser behavior plus a safe response pattern.
- Re-run stable checks and compare results before escalating a finding.
- Deduplicate related observations and preserve the most specific proof.
- Label uncertainty clearly: verified, likely, needs review, informational, or not reproducible.
- Build regression tests from prior false positives and user dismissals.

## Recommended learning order

1. Learn web fundamentals: HTTP, browser security boundaries, DOM/JavaScript, cookies, sessions, and APIs.
2. Study OWASP Top 10, secure design, threat modeling, and authorized-testing ethics.
3. Build small Playwright projects that crawl a local demo site, collect network evidence, and produce screenshots.
4. Learn backend fundamentals: API design, databases, queues, testing, and structured logging.
5. Implement a scope-enforced crawler with strict budgets and a passive-only mode.
6. Add deterministic security/QA checks and an evidence store before introducing an LLM.
7. Add LLM orchestration with schemas, citations to evidence, and policy-gated tools.
8. Build the dashboard and report formats; test them with engineers who need to remediate findings.
9. Containerize and isolate workers, then add monitoring, CI/CD, and cloud deployment.
10. Continuously evaluate precision, recall, scan cost, safety-policy compliance, and remediation usefulness.

## Suggested technology stack

| Layer | Suggested choices | Role |
|---|---|---|
| Backend API | Python + FastAPI, or TypeScript + NestJS | Scan management, policy enforcement, and integrations. |
| Agent orchestration | OpenAI API with structured outputs and tool calling | Evidence-aware planning, analysis, and report drafting. |
| Browser automation | Playwright | Rendered-page discovery, network capture, screenshots, and traces. |
| Crawler | Custom async crawler using HTTPX/aiohttp, plus Playwright discovery | Controlled URL collection and browser-assisted coverage. |
| Task execution | Celery/RQ + Redis, or Temporal | Durable, rate-limited background scan workflows. |
| Primary database | PostgreSQL | Scan metadata, scope, findings, audit logs, and workflow state. |
| Artifact storage | S3-compatible object storage | Screenshots, traces, response artifacts, and generated reports. |
| Search and analytics | PostgreSQL full-text search initially; OpenSearch later if needed | Fast investigation across evidence and findings. |
| Frontend | React + TypeScript + a component library | Scan configuration, dashboards, evidence review, and remediation workflow. |
| Reports | HTML templates + Playwright/PDF renderer; JSON and SARIF exports | Shareable reports and CI/security-tool integrations. |
| Infrastructure | Docker, Terraform, Kubernetes or managed container workers | Repeatable, isolated deployment and horizontal scaling. |
| Observability | OpenTelemetry + Prometheus/Grafana + centralized logs | Performance, reliability, security events, and model/tool auditability. |
| Security controls | Network egress controls, secrets manager, KMS, WAF/rate limiting | Worker isolation, secret protection, and abuse prevention. |

## Practical first milestone

Build a local-only, passive prototype against an intentionally vulnerable training application or an application you own. Give it one approved seed URL, enforce same-origin crawling, capture browser and HTTP evidence, run a small set of deterministic checks, and generate an HTML report that distinguishes verified findings from observations. Add the LLM only after that evidence pipeline is reliable.
