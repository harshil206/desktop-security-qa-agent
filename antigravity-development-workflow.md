# Developing the Desktop Security & QA Agent with Antigravity

This guide explains how to use `desktop-security-qa-agent-antigravity-task-plan.md` as the operating plan for development in Antigravity.

## Principle: you own the architecture; agents execute small verified changes

Use Antigravity as a capable implementation partner, not as an autonomous product owner. Keep architecture, security boundaries, product scope, authorization rules, and release approval under human control.

The most reliable loop is:

```text
Choose one task card
      ↓
Give the agent its exact scope and acceptance checks
      ↓
Agent inspects, plans, implements, and tests
      ↓
You inspect the diff and evidence
      ↓
Accept, request corrections, or revert
      ↓
Move to the next dependent task
```

## 1. Prepare the project once

Before asking Antigravity to write features:

1. Create the repository using the layout in the task plan.
2. Put these documents in the repository root or `docs/` directory:
   - `skills.md`
   - `website-security-qa-agent-roadmap.md`
   - `desktop-security-qa-agent-antigravity-task-plan.md`
   - `antigravity-development-workflow.md`
3. Create `AGENTS.md` at the repository root with the mandatory safety rules from the task plan.
4. Add a small `README.md` containing the exact local setup, test, lint, type-check, and app-start commands.
5. Configure a protected main branch and work on one short-lived branch per task.
6. Build local fixture sites before any real-world scan implementation.

Do not begin with a broad instruction such as “build the whole application.” The task plan deliberately breaks the work into small pieces because agent quality falls when scope, context, and acceptance criteria are vague.

## 2. Configure Antigravity for this project

Create project-level instructions in `AGENTS.md`. Antigravity can use repository instructions, skills, and tool configurations, so this file should be the non-negotiable source of truth for every task.

Keep available tools minimal:

- Editor and repository search: allowed.
- Terminal: allowed for project commands only.
- Browser: initially restricted to localhost test fixtures and documentation; do not authorize it to scan public sites during development.
- Network access: only when a task explicitly needs a dependency install or approved documentation lookup.
- Secrets: no automatic access. Use local environment variables only when required, never paste secrets into prompts.

For this product, do not enable “always approve” behavior for terminal, filesystem, browser, or tool calls. Scan targets and evidence are untrusted input; a malicious web page or artifact can attempt to manipulate an agent through its text.

## 3. How to execute each phase

Follow the dependency order in the task plan.

### Phase 0: define contracts before code

Run P0-01, P0-02, and P0-03 sequentially.

- Review the policy and evidence schemas manually.
- Ensure every finding requires evidence references.
- Confirm test fixtures are local and harmless.

Do not start Electron, crawling, security rules, or AI work until these definitions are accepted.

### Phase 1: establish a runnable local skeleton

Run P1-01, P1-02, and P1-03 as separate tasks. Run P1-04 after both the desktop shell and scanner shell exist.

At this stage, your only goal is a desktop window starting a local-only scanner service and showing its health status. No scanning is needed yet.

### Phase 2: build the authorization and scan lifecycle

Implement P2-01 through P2-04 one at a time. This is the most important safety boundary in the product. Review all input validation, IPC calls, state transitions, cancellation behavior, and audit records before proceeding.

### Phase 3–5: build the scanner in layers

Implement URL scope gates before crawling. Implement crawling before browser evidence. Implement browser evidence before security rules.

Run each feature against local fixtures. If an agent proposes adding active payloads, posting forms, or probing public targets, reject that change for the MVP.

### Phase 6–7: make evidence understandable

Build the desktop results experience and deterministic reports after data contracts and scanner output are stable. Use screenshot and report fixtures for visual regression tests.

### Phase 8: add AI only as an optional writing layer

First make the template-based report good enough to ship. Then add the AI provider adapter and prove that disabling it has no effect on scanner operation, finding validation, or deterministic reporting.

### Phase 9–10: harden, package, and pilot

Complete desktop-security review, signing, clean-machine installation tests, and end-to-end tests before a pilot. Run the pilot only against sites whose owners have authorized testing.

## 4. A good Antigravity task prompt

Use this prompt pattern, replacing the task ID and details each time:

```text
Implement task P2-03, “Implement durable scan job state”, from
docs/desktop-security-qa-agent-antigravity-task-plan.md.

Read first:
- AGENTS.md
- docs/desktop-security-qa-agent-antigravity-task-plan.md
- packages/contracts/
- existing scanner tests

Allowed files:
- services/scanner/
- packages/contracts/
- tests/ relevant to this task

Do not change Electron UI, crawler behavior, scan-policy rules, or unrelated
files. Do not make network requests or add active testing.

Implement only the stated objective and tests. Before editing, state a concise
plan. After editing, run the documented lint, type-check, and focused test
commands.

Finish with:
1. changed files;
2. tests and results;
3. assumptions;
4. known limitations or follow-up work.
```

Give only one task card to a single agent run. Use a follow-up on the same task only for corrections discovered in review.

## 5. Review checklist after every agent run

Before merging, inspect the changes yourself or run a separate review agent with read-only instructions.

Check:

- Does the code change only the permitted files?
- Does it satisfy the specific task card rather than adding a larger redesign?
- Are the policy defaults conservative?
- Can a target URL, redirect, page title, HTML body, or evidence text influence privileged desktop/terminal actions?
- Are renderer-to-main-process IPC messages typed and allowlisted?
- Is untrusted HTML rendered as text/sanitized content rather than executable markup?
- Does every new rule include positive and negative tests?
- Can the feature be tested with local fixtures?
- Were generated artifacts, secret values, node modules, or local databases kept out of version control?
- Do tests actually pass, rather than merely being written?

Require the agent to show its test results. Do not accept “tests should pass” as evidence.

## 6. Safe parallelism

Antigravity can run multiple agent conversations, but parallel work must be isolated by ownership.

Good parallel work after contracts are stable:

- Desktop agent: Electron shell and UI components.
- Scanner agent: FastAPI lifecycle and SQLite persistence.
- QA agent: local fixtures and test utilities.
- Documentation agent: architecture and setup documentation.

Avoid parallel work when agents would change the same contracts, configuration, or core scanner files. In particular, do not run parallel agents on:

- `AGENTS.md`
- shared schemas under `packages/contracts/`
- Electron preload/IPC definitions
- scan policy enforcement
- database migrations
- root build configuration

Finish and merge prerequisite tasks before launching agents for dependent tasks.

## 7. Common malpractice / anti-patterns

### “Build the complete app” prompts

Why it fails: the agent makes unreviewable architectural decisions, creates inconsistent code, and skips critical tests.

Better: assign one task card with a clear acceptance test.

### Giving the agent uncontrolled browser or shell access

Why it fails: targets and artifacts are untrusted; prompt injection or a malicious URL can cause unintended actions.

Better: restrict browser use to local fixtures during development, confirm dangerous tool calls manually, and allow only documented commands.

### Letting the UI directly control filesystem, shell, or scanner logic

Why it fails: a renderer compromise becomes a local-code-execution risk.

Better: Electron renderer → typed preload bridge → allowlisted IPC → main process → local scanner service.

### Using an LLM as the security decision-maker

Why it fails: models can hallucinate a finding, severity, evidence, or reproduction step.

Better: use deterministic rules and captured artifacts for findings; use AI only to explain already-verified output.

### Starting active testing too early

Why it fails: it increases legal, safety, false-positive, and product-risk exposure before policy controls exist.

Better: ship a passive, evidence-rich MVP first; active testing is a separately approved future feature.

### Allowing agents to edit broad sets of files

Why it fails: it leads to accidental architecture drift and hard-to-review changes.

Better: list allowed directories for each task and reject unrelated edits.

### Trusting an agent’s claimed test result

Why it fails: agents can misread output, skip commands, or test the wrong path.

Better: inspect the command output, reproduce critical tests, and use a separate read-only review pass for security-sensitive changes.

### Storing raw scan artifacts indiscriminately

Why it fails: pages and network logs can contain cookies, tokens, personal data, or proprietary content.

Better: define retention, redaction, local encryption, user consent, and safe export behavior before browser evidence collection.

### Adding AI APIs before the evidence pipeline

Why it fails: a well-written but unsupported report creates more risk than a basic deterministic report.

Better: first produce a report entirely from structured findings and evidence; add AI as a replaceable optional enhancement.

## 8. Daily development cadence

Use a simple cadence:

1. Select one task that has all dependencies complete.
2. Create a branch named after the task, such as `p3-01-url-scope-gate`.
3. Start one Antigravity task using the standard prompt template.
4. Review its plan before it edits if the task affects security boundaries.
5. Review the final diff and test evidence.
6. Run an independent review for policy, Electron IPC, crawler, evidence-redaction, or release changes.
7. Merge only when acceptance criteria are met.
8. Record decisions, trade-offs, and follow-up tasks in the project documentation.

## 9. First five Antigravity runs

Start with this exact sequence:

1. P0-01 — Rules of engagement and scan-policy schema.
2. P0-02 — Finding and evidence contract.
3. P0-03 — Local fixture pages and expected outputs.
4. P1-01 — Repository scaffold and quality gates.
5. P1-02 — Local-only FastAPI scanner health service.

After these five runs, stop and review the foundations before creating the Electron shell. This prevents the user interface from dictating insecure scanner behavior.

## 10. Definition of healthy agent-assisted development

You are using Antigravity well when:

- Each merged change can be traced to a task ID.
- Every task has a focused test result.
- Security-critical design choices receive human review.
- Agent permissions are least-privilege and temporary.
- The system remains functional when the AI/report provider is unavailable.
- The team can explain why every security finding exists using collected evidence.
