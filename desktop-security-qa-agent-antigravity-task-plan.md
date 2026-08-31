# Desktop Website Security & QA Agent
## Antigravity-Friendly Phase and Task Plan

## Product boundary

Build a cross-platform desktop application for **authorized** website security and QA scanning. The application runs its scan engine locally, stores evidence locally by default, and may later use external AI APIs only for optional report writing.

The desktop application must never be used as an uncontrolled scanner. Every task in this plan assumes the following rules are implemented and tested:

- A user must confirm ownership or explicit authorization before a scan.
- The user must define the allowed domains, path prefixes, scan limits, and mode.
- Passive/read-only scanning is the default.
- Active or state-changing checks are excluded from the MVP.
- The app does not display untrusted target pages in a privileged Electron renderer.
- The local scanner service—not the desktop UI—uses Playwright to visit approved targets.

## Chosen technology stack

- Desktop shell: Electron + React + TypeScript.
- Desktop build tools: Vite + Electron Forge (or an equivalent maintained Electron packaging setup).
- Scanner service: Python + FastAPI.
- Browser automation: Playwright for Python.
- Local data: SQLite for MVP, accessed only by the scanner service.
- Evidence files: encrypted-on-device directory, accessed through scanner APIs.
- Contracts: versioned JSON Schema or TypeScript/Pydantic models shared between UI and scanner.
- QA/security rules: Python rule modules with deterministic tests.
- Reports: HTML templates plus a local PDF renderer; JSON and SARIF export.
- AI: optional provider adapter used only after evidence collection and deterministic rules are complete.

## Repository layout

```text
desktop-security-qa-agent/
  apps/
    desktop/                 # Electron main, preload, and React renderer
  services/
    scanner/                 # FastAPI, crawler, Playwright worker, rules
  packages/
    contracts/               # versioned API/event/findings schemas
    report-templates/        # HTML/CSS report templates
  tests/
    fixtures/                # safe local test pages and expected artifacts
    e2e/                     # desktop-to-scanner end-to-end tests
  docs/
    architecture/
    security/
  AGENTS.md
  README.md
```

## How to assign work in Antigravity

Keep each agent task narrow, independent where possible, and verifiable with a command. Do not give one agent an entire phase.

Every task brief should include:

1. **Objective:** one clear outcome.
2. **Allowed files:** exact directories/files the agent may change.
3. **Constraints:** security rules and dependencies that must remain unchanged.
4. **Acceptance checks:** commands or manual checks that prove completion.
5. **Out of scope:** what the agent must not implement.

Suggested agent roles:

- **Desktop agent:** Electron main process, preload bridge, React UI, packaging.
- **Scanner agent:** FastAPI, crawler, Playwright, SQLite, evidence handling.
- **Rules agent:** deterministic QA/security rules and their test fixtures.
- **QA agent:** unit, integration, end-to-end, and regression tests.
- **Security reviewer:** Electron IPC, scan policy, secrets, artifact redaction, abuse resistance.
- **Report agent:** report templates and optional AI report adapter; no authority to alter findings.

## Required `AGENTS.md` rules

Create these rules before delegating implementation:

- Never widen scan scope, rate limits, allowed methods, or redirect behavior without an explicit task.
- Never place target-site HTML in Electron’s privileged renderer or enable Node integration for external content.
- All UI-to-native capability calls must use a typed, allowlisted preload API.
- The Electron renderer may not access filesystem, shell, database, or scanner-process APIs directly.
- All scanner output must be schema validated before being shown in the UI.
- Do not add active vulnerability tests, payload libraries, or state-changing form submission in the MVP.
- Add/adjust tests for each behavior change.
- Do not commit credentials, browser profiles, raw sensitive artifacts, or generated scan data.

## Phase 0 — Product and safety foundation

### Task P0-01: Write rules of engagement and scan policy schema

- **Owner:** Security reviewer + scanner agent
- **Allowed files:** `docs/security/`, `packages/contracts/`
- **Objective:** Define the authorization record and scan policy payload.
- **Deliverables:** JSON/Pydantic schema for owner confirmation, approved hosts, allowed URL prefixes, maximum depth, request-per-minute limit, total request budget, scan duration, and scan mode.
- **Acceptance:** invalid/missing authorization or empty scope is rejected by schema tests.
- **Out of scope:** scanning implementation.

### Task P0-02: Define the finding and evidence contract

- **Owner:** Scanner agent + report agent
- **Allowed files:** `packages/contracts/`, `docs/architecture/`
- **Objective:** Create versioned schemas for scans, artifacts, findings, and reports.
- **Deliverables:** `Finding`, `EvidenceRef`, `ScanPolicy`, `ScanStatus`, and `Report` definitions with explicit confidence and severity fields.
- **Acceptance:** fixture JSON validates; a finding cannot exist without at least one evidence reference.
- **Out of scope:** UI and database implementation.

### Task P0-03: Create local test targets and fixtures

- **Owner:** QA agent
- **Allowed files:** `tests/fixtures/`
- **Objective:** Provide harmless, reproducible pages for crawler and rule tests.
- **Deliverables:** static pages with links, redirects within scope, broken assets, console errors, missing headers, and known expected results.
- **Acceptance:** local fixture server starts with one documented command.
- **Out of scope:** deploying an internet-accessible training target.

## Phase 1 — Repository and local runtime

### Task P1-01: Scaffold the monorepo and quality gates

- **Owner:** Desktop agent
- **Allowed files:** root config, `apps/`, `services/`, `packages/`, CI configuration
- **Objective:** Establish the directory structure, formatters, linters, test runners, and root documentation.
- **Acceptance:** one command installs dependencies; one command runs all lint/type/unit checks.
- **Out of scope:** feature UI or scanning behavior.

### Task P1-02: Create the FastAPI scanner service shell

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/`
- **Objective:** Start a local-only service with `/health` and version endpoints.
- **Constraints:** bind to loopback only; do not expose a network service to the LAN.
- **Acceptance:** service health test passes and an external-host bind is rejected by configuration tests.
- **Out of scope:** crawl logic.

### Task P1-03: Create the Electron desktop shell

- **Owner:** Desktop agent
- **Allowed files:** `apps/desktop/`
- **Objective:** Launch an Electron application with a React page and a minimal typed preload bridge.
- **Constraints:** `contextIsolation: true`, sandboxing enabled, Node integration disabled, local packaged content only.
- **Acceptance:** desktop app launches; renderer has no direct Node/filesystem access; preload API test passes.
- **Out of scope:** scanner interaction.

### Task P1-04: Define desktop-to-scanner process ownership

- **Owner:** Desktop agent + scanner agent
- **Allowed files:** `apps/desktop/`, `services/scanner/`, `docs/architecture/`
- **Objective:** Specify how Electron starts, monitors, and stops the local scanner process.
- **Deliverables:** process lifecycle design and a health-check handshake.
- **Acceptance:** starting the app starts one scanner; closing the app terminates it cleanly; crash state appears in logs.
- **Out of scope:** full scan jobs.

## Phase 2 — Safe scan control plane

### Task P2-01: Implement scan-policy validation API

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/`, `packages/contracts/`
- **Objective:** Implement create/validate policy endpoints without performing network calls.
- **Acceptance:** schema, hostname, URL-prefix, and budget validation tests pass.
- **Out of scope:** URL discovery.

### Task P2-02: Implement desktop scan setup flow

- **Owner:** Desktop agent
- **Allowed files:** `apps/desktop/`
- **Objective:** Build the scan setup form with authorization confirmation, target domains, path scope, and conservative default limits.
- **Constraints:** user must visibly acknowledge authorization; no hidden default target.
- **Acceptance:** invalid policy cannot start a scan; valid policy is sent through the typed preload bridge.
- **Out of scope:** scan results dashboard.

### Task P2-03: Implement durable scan job state

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/`
- **Objective:** Add SQLite-backed scan records and the states `draft`, `validated`, `queued`, `running`, `completed`, `failed`, `cancelled`, and `blocked`.
- **Acceptance:** state-transition tests reject invalid transitions and preserve timestamps/reason codes.
- **Out of scope:** background queue scale-out.

### Task P2-04: Add cancellation and emergency stop

- **Owner:** Scanner agent + desktop agent
- **Allowed files:** `services/scanner/`, `apps/desktop/`
- **Objective:** Stop a queued/running scan safely and visibly.
- **Acceptance:** cancellation test prevents new requests after cancellation; UI displays final stop reason.
- **Out of scope:** active testing.

## Phase 3 — Passive crawler

### Task P3-01: URL normalization and same-origin gate

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/crawler/`
- **Objective:** Normalize URLs, deduplicate them, and accept only URLs that match the approved policy.
- **Acceptance:** tests cover subdomains, ports, redirects, URL encoding, fragments, query canonicalization, and lookalike hosts.
- **Out of scope:** browser rendering.

### Task P3-02: Implement budgeted HTML link discovery

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/crawler/`
- **Objective:** Crawl seed pages and extract safe GET links within depth, duration, and request limits.
- **Acceptance:** fixture tests prove scope enforcement and report visited/skipped/blocked URLs.
- **Out of scope:** form submission and non-GET requests.

### Task P3-03: Record coverage and crawl decisions

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/`, `packages/contracts/`
- **Objective:** Persist URL discovery source, decision, status code, content type, and rejection reason.
- **Acceptance:** scan summary exposes coverage counts and blocked URLs with reasons.
- **Out of scope:** visual UI.

## Phase 4 — Playwright evidence worker

### Task P4-01: Create isolated Playwright browser contexts

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/browser/`
- **Objective:** Launch an isolated browser context per scan with timeouts, download restrictions, and no persistent profile reuse.
- **Acceptance:** browser cleanup test passes even when navigation fails.
- **Out of scope:** interactions that change target state.

### Task P4-02: Capture passive browser evidence

- **Owner:** Scanner agent
- **Allowed files:** `services/scanner/browser/`, `packages/contracts/`
- **Objective:** Capture title, final URL, screenshot, DOM snapshot, console errors, page errors, network metadata, and response headers.
- **Acceptance:** local fixture scan produces linked artifact IDs for each expected event.
- **Out of scope:** raw sensitive response retention without redaction.

### Task P4-03: Build artifact storage and redaction

- **Owner:** Scanner agent + security reviewer
- **Allowed files:** `services/scanner/storage/`, `docs/security/`
- **Objective:** Save artifacts with access controls and redact tokens, cookies, authorization headers, and obvious personal data from display copies.
- **Acceptance:** redaction test fixtures prove sensitive fields do not appear in API responses or reports.
- **Out of scope:** cloud backup.

## Phase 5 — Deterministic QA and security rules

### Task P5-01: QA rule pack

- **Owner:** Rules agent
- **Allowed files:** `services/scanner/rules/`, `tests/fixtures/`
- **Objective:** Implement broken-link, failed-asset, console-error, page-error, title, and basic accessibility-signal rules.
- **Acceptance:** every rule has positive and negative fixtures plus a structured finding output test.
- **Out of scope:** severity decisions based solely on AI.

### Task P5-02: Passive web-hardening rule pack

- **Owner:** Rules agent + security reviewer
- **Allowed files:** `services/scanner/rules/`, `docs/security/`
- **Objective:** Add passive checks for visible TLS/HTTPS behavior, security headers, cookies, CORS, public error information, and server-banner exposure.
- **Acceptance:** each rule specifies evidence requirements, remediation, confidence, limitations, and test cases.
- **Out of scope:** exploit payloads, injection attempts, account/access-control testing.

### Task P5-03: Finding deduplication and confidence policy

- **Owner:** Scanner agent + rules agent
- **Allowed files:** `services/scanner/findings/`, `packages/contracts/`
- **Objective:** Group repeated rule output and clearly separate severity from confidence.
- **Acceptance:** repeated evidence produces one grouped finding with multiple evidence references.
- **Out of scope:** LLM classification.

## Phase 6 — Desktop results experience

### Task P6-01: Scan history and progress UI

- **Owner:** Desktop agent
- **Allowed files:** `apps/desktop/`
- **Objective:** Display scan state, timing, coverage, progress messages, and cancellation controls.
- **Acceptance:** end-to-end test starts a fixture scan and displays its terminal state.
- **Out of scope:** rendering external web pages in Electron.

### Task P6-02: Findings and evidence UI

- **Owner:** Desktop agent
- **Allowed files:** `apps/desktop/`
- **Objective:** Display finding title, severity, confidence, remediation, and safely rendered evidence metadata/screenshots.
- **Constraints:** no raw arbitrary HTML injection; sanitize all displayed text.
- **Acceptance:** XSS regression test proves malicious target content cannot execute in the app UI.
- **Out of scope:** editing raw evidence.

### Task P6-03: Review-state workflow

- **Owner:** Desktop agent + scanner agent
- **Allowed files:** `apps/desktop/`, `services/scanner/`
- **Objective:** Allow users to mark a finding confirmed, false positive, accepted risk, fixed, or retest requested, with reason and timestamp.
- **Acceptance:** review history persists and appears in report exports.
- **Out of scope:** multi-user collaboration.

## Phase 7 — Report generation

### Task P7-01: Structured report builder

- **Owner:** Report agent
- **Allowed files:** `packages/report-templates/`, `services/scanner/reports/`
- **Objective:** Generate HTML from scanned findings, evidence links, policy scope, coverage, and limitations.
- **Acceptance:** snapshot tests cover no-findings, verified-finding, observation-only, and cancelled-scan reports.
- **Out of scope:** LLM writing.

### Task P7-02: PDF, JSON, and SARIF export

- **Owner:** Report agent + QA agent
- **Allowed files:** `services/scanner/reports/`, `tests/`
- **Objective:** Produce portable reports from the same structured data.
- **Acceptance:** generated PDF visual test, JSON schema validation, and SARIF validation pass.
- **Out of scope:** sending reports externally.

### Task P7-03: Desktop report-view and export flow

- **Owner:** Desktop agent
- **Allowed files:** `apps/desktop/`
- **Objective:** Let users preview reports and export them to a user-selected directory.
- **Acceptance:** path-selection and overwrite confirmation tests pass.
- **Out of scope:** auto-uploading reports.

## Phase 8 — Optional AI report assistance

### Task P8-01: Create an AI provider adapter

- **Owner:** Report agent
- **Allowed files:** `services/scanner/ai/`, `packages/contracts/`
- **Objective:** Define a provider-neutral interface for evidence-bound report summary generation.
- **Constraints:** scan rules and severity calculations must not depend on AI availability.
- **Acceptance:** a mock provider produces a validated report section; a disabled provider leaves deterministic reports functional.
- **Out of scope:** granting an AI model browser, scanner, filesystem, or policy-changing permissions.

### Task P8-02: Evidence-bounded prompts and evaluations

- **Owner:** Report agent + security reviewer
- **Allowed files:** `services/scanner/ai/`, `tests/fixtures/`
- **Objective:** Require report statements to cite finding/evidence IDs and label unknowns as unknown.
- **Acceptance:** evaluation tests fail outputs that invent an affected URL, severity, evidence, or reproduction step.
- **Out of scope:** using the model to discover vulnerabilities.

### Task P8-03: AI settings and consent UI

- **Owner:** Desktop agent
- **Allowed files:** `apps/desktop/`
- **Objective:** Clearly show provider, model, what data may be sent, cost warning, and on/off control.
- **Acceptance:** AI is opt-in and the UI states when a report was AI-assisted.
- **Out of scope:** hidden background API use.

## Phase 9 — Desktop hardening and release

### Task P9-01: Electron security hardening review

- **Owner:** Security reviewer
- **Allowed files:** `apps/desktop/`, `docs/security/`
- **Objective:** Audit renderer settings, IPC allowlists, navigation, external links, filesystem permissions, CSP, and update settings.
- **Acceptance:** a documented checklist passes; security regression tests cover hostile IPC and renderer content.
- **Out of scope:** new user-facing features.

### Task P9-02: Package, sign, and update the application

- **Owner:** Desktop agent + release engineer
- **Allowed files:** `apps/desktop/`, CI/release configuration, `docs/`
- **Objective:** Produce signed installers and a controlled update path for Windows first, then macOS/Linux as needed.
- **Acceptance:** clean-machine install/uninstall/update test and version rollback plan are documented.
- **Out of scope:** public store distribution.

### Task P9-03: End-to-end release test suite

- **Owner:** QA agent
- **Allowed files:** `tests/e2e/`, CI configuration
- **Objective:** Test app launch, policy validation, local fixture scan, evidence capture, cancellation, finding review, and report export.
- **Acceptance:** suite passes on every release candidate in a clean environment.
- **Out of scope:** scanning live third-party sites.

## Phase 10 — Controlled pilot and iteration

### Task P10-01: Pilot onboarding and telemetry

- **Owner:** Product owner + desktop agent
- **Objective:** Pilot only with authorized users and collect consented product telemetry: scan duration, crashes, rule usefulness, false positives, and report completion.
- **Acceptance:** telemetry excludes sensitive target content and can be disabled by the user.

### Task P10-02: Triage feedback into rule improvements

- **Owner:** Rules agent + security reviewer
- **Objective:** Convert reviewed false positives/negatives into regression fixtures and rule improvements.
- **Acceptance:** every production rule change has a linked regression test and version note.

### Task P10-03: Production launch review

- **Owner:** Security reviewer + release engineer
- **Objective:** Approve the release against safety, security, privacy, support, and rollback checklists.
- **Acceptance:** written sign-off plus tested emergency scan-stop and update rollback procedures.

## Antigravity task prompt template

Use this structure for each task:

```text
Task: <ID and short title>

Objective:
<one measurable result>

Allowed files:
<exact paths>

Read first:
AGENTS.md, relevant contract/schema files, and existing tests.

Constraints:
- Preserve scan policy enforcement and passive-only MVP behavior.
- Do not change unrelated files.
- Do not add external network calls, credentials, or hidden telemetry.
- Add focused tests for changed behavior.

Acceptance checks:
<commands or manual verification>

Out of scope:
<explicit exclusions>

Finish by reporting:
- changed files
- tests run and results
- decisions/assumptions
- remaining risks or follow-up tasks
```

## Recommended execution sequence

Run P0-01, P0-02, and P0-03 first. Then complete Phase 1 before allowing concurrent work on Phase 2. After Phase 2, crawler work (Phase 3) and desktop lifecycle work can proceed in parallel. Do not begin rules, AI, or report work until the artifact and finding contracts are stable.

The first usable milestone is the end of Phase 7: a signed local desktop application that runs approved passive scans, captures evidence, produces deterministic findings, and exports a report. Phase 8 is a quality enhancement, not a prerequisite for shipping.
