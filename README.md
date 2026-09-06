# Desktop Website Security & QA Agent

A local-first Electron desktop application with a local FastAPI + Playwright scanner service for **authorised, passive** website security and QA assessments.

## Project documentation

- `skills.md` — skills roadmap.
- `website-security-qa-agent-roadmap.md` — product delivery roadmap.
- `desktop-security-qa-agent-antigravity-task-plan.md` — phase-by-phase task cards.
- `antigravity-development-workflow.md` — how to run the task cards in Antigravity.
- `AGENTS.md` — mandatory implementation and security rules.

## Current status

Phase 0 is complete: rules of engagement and the scan policy schema (`P0-01`), the finding/evidence/report contracts (`P0-02`), and the local fixture site (`P0-03`). Task `P1-01` has established the monorepo layout and the local quality gates. Continue with task `P1-02` in `desktop-security-qa-agent-antigravity-task-plan.md`.

## Local setup

Requires Node.js 20.11+ and Python 3.10+ on `PATH`. One command installs both toolchains:

```powershell
npm run setup
```

One command runs every gate — lint, format check, type check, and unit tests across both stacks:

```powershell
npm run check
```

Individual gates are available if you need to narrow a failure:

```powershell
npm run lint          # eslint + ruff + prettier --check
npm run typecheck     # tsc + mypy
npm run test          # vitest + pytest
npm run format        # rewrite formatting (prettier)
```

The scanner service dependencies (FastAPI, Playwright) arrive with task `P1-02`, and `npm run dev` arrives with task `P1-04`.


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
