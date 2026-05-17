# LLMS.md — Archivio Personale AI

## Project

**Archivio Personale AI** is a lightweight, safety-first helper for organizing folders and files on the user's own computer.

Primary target: local PC/internal HDD. Future target: Google Drive only when available as a local synced/mirrored filesystem folder, not through cloud API automation.

## Roles

- **ChatGPT web**: orchestrator and advisor.
- **Claude Code**: primary local implementer when available.
- **Codex web**: backup implementer when Claude has finished tokens.
- **GitHub repository**: source of truth for code and project rules only, never for personal files.

## Task history

| Task | Description | Outcome |
|------|-------------|---------|
| ARCH-0001 | Improve duplicate report filtering | Closed — commit `9c421c` |
| ARCH-0002 | Local validation of filtered duplicate report | Validation-only — no commit |
| ARCH-0003 | Document safe report opening command | Closed — commit `5f09dac` |
| ARCH-0004..ARCH-0013 | Batch 1 — tracking, usability, local workflow cleanup | Closed — commit `f97050f` |
| ARCH-0014..ARCH-0023 | Batch 2 — Italian HTML reports | Closed — commit `65a14e5` |
| ARCH-0024..ARCH-0033 | Batch 3 — operational guardrails | Closed — commit `23f59ae` |

## Current phase

**Dry-run inventory + rule-based classification baseline.**

Implemented:

- read-only inventory script: `scripts/inventory_readonly.py`;
- static HTML inventory report generator: `scripts/generate_inventory_report.py`;
- rule-based dry-run classifier: `scripts/classify_inventory.py`;
- static HTML classification report generator: `scripts/generate_classification_report.py`;
- context preservation policy: files already inside existing folders are marked `keep_in_place`;
- review-only action plan for root sort candidates and exact duplicate groups.

Not implemented:

- cloud/API classification of personal file contents;
- real move/rename/delete logic;
- active n8n runtime workflow;
- Google Drive API automation;
- MCP/filesystem agent operations on personal files.

## ChatGPT Priority Gate (silent checklist)

Before each operational reply, ChatGPT checks silently:

1. one operational step only;
2. latest output/screenshot has been read;
3. wait for output before continuing;
4. only one active implementer (Claude or Codex);
5. repo clean/aligned or explicitly to verify;
6. only authorized files/areas;
7. real gates: move, rename, delete, API, cloud, n8n, MCP, installs, secrets;
8. if a real gate exists: stop and ask;
9. if no real gate exists: provide only the next minimum step.

Do not print “priorità controllate” (or equivalent checklist confirmations) to the user.

## Implementer switch policy (Claude/Codex)

- Only one implementer active at a time.
- Prefer Claude Code as primary implementer.
- Use Codex web only as backup when Claude is unavailable/out of tokens.
- Before switching implementer, verify workspace clean/aligned.

## Codex guardrails

Codex must follow the same safety model as Claude:

- work only on authorized repository code/docs;
- never touch personal files;
- no cloud API processing for personal content;
- no n8n runtime activation;
- no MCP/filesystem agent workflows;
- no dependency installs unless explicitly approved.

Codex may use temporary work branches, but the base must be a verified remote commit.

## Windows local execution policy

User local environment is Windows. Local command examples and operator instructions must use **PowerShell**.

Do not mix Bash syntax with PowerShell constructs (`Test-Path`, `if (...) {}`, Windows paths, local Git checks, report regeneration).

## Report language policy

All generated user-facing HTML reports must be in Italian (`lang="it"`). Visible UI text must be in Italian. Python identifiers, JSON keys, filenames, and machine-readable fields stay in English.

## Operating doctrine

Keep the project simple, local-first, review-only, and safety-first.

Rules:

- No destructive operations.
- No automatic move/rename/delete.
- No external AI APIs for personal file contents.
- Prefer reports, review lists, and explicit user decisions.
- Default posture is `review_only` / ask before acting.

## Required references

- Safety rules: `docs/SAFETY_RULES.md`.
- Workflow: `docs/WORKFLOW.md`.
- Commands: `docs/COMMANDS.md`.

## Documentation policy

Keep documentation compact. Avoid duplicate Markdown files and duplicated rules across files.
