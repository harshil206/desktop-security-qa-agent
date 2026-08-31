# Desktop Website Security & QA Agent

A local-first Electron desktop application with a local FastAPI + Playwright scanner service for **authorised, passive** website security and QA assessments.

## Project documentation

- `skills.md` — skills roadmap.
- `website-security-qa-agent-roadmap.md` — product delivery roadmap.
- `desktop-security-qa-agent-antigravity-task-plan.md` — phase-by-phase task cards.
- `antigravity-development-workflow.md` — how to run the task cards in Antigravity.
- `AGENTS.md` — mandatory implementation and security rules.

## Current status

The repository foundation and safe local fixtures are in place. Start implementation with task `P0-01` in `desktop-security-qa-agent-antigravity-task-plan.md`.

## Planned local setup

The implementation tasks will establish the package manifests and exact automation commands. The intended local workflow is:

```powershell
# Desktop dependencies (after P1-01)
npm install

# Python scanner environment (after P1-02)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .\services\scanner[dev]

# Development app (after P1-04)
npm run dev

# Quality checks (after P1-01)
npm run lint
npm run typecheck
npm run test
```

These commands are intentionally not runnable until their corresponding task cards create the project manifests and service code. Do not add scanner features before P0-01 through P0-03 are complete.

## Local test fixtures

Use only `tests/fixtures/site/` during early development. These harmless pages provide expected links, a broken asset, a console error, and local redirects for reproducible crawler and evidence tests.

To serve the fixture site:

```powershell
python -m http.server 8080 --directory tests/fixtures/site
```

Open `http://127.0.0.1:8080/` in a normal browser to inspect it. Do not scan external websites during repository setup.

## Git workflow

- `main` is the local integration branch.
- Create one short-lived branch per task, for example `p0-01-scan-policy-schema`.
- Review test evidence before merging.
- Enable branch protection once this repository has been pushed to the chosen Git hosting provider.
