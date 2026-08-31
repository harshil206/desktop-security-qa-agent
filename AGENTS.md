# Project Rules

## Product boundary

This project is a desktop application for authorised Website Security and QA scans. It must not become an uncontrolled vulnerability scanner.

## Mandatory safety rules

- Require explicit authorization and a validated scan policy before any target request.
- Default to passive, read-only scanning. Do not submit forms, create accounts, change data, or add active payload tests unless a future task explicitly adds an approved active mode.
- Enforce domain/path allowlists, redirect re-validation, rate limits, request budgets, and time limits in scanner code.
- Never load target-site content in a privileged Electron renderer.
- Electron renderers must have Node integration disabled, context isolation enabled, and sandboxing enabled.
- The renderer may access native capabilities only through a typed, allowlisted preload/IPC API.
- Do not expose filesystem, shell, database, scanner-process, or secrets access directly to the renderer.
- Treat target HTML, URLs, responses, logs, screenshots, and any downloaded data as untrusted input.
- Every finding requires one or more structured evidence references. AI may explain evidence, but must not create, verify, or set severity for a finding by itself.
- Redact sensitive headers, cookies, tokens, and obvious personal data from user-visible artifacts and reports.
- Do not commit credentials, local databases, scan artifacts, browser profiles, dependency caches, or generated reports.

## Working rules

- Read the relevant task card in `desktop-security-qa-agent-antigravity-task-plan.md` before editing.
- Keep changes limited to the task’s allowed files; do not refactor unrelated code.
- Add focused positive and negative tests for every behavior change.
- Run the documented checks and report their actual results.
- Ask for direction when a task needs external scans, new credentials, production deployment, or a policy change.
