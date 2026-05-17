# LLMS.md — Archivio Personale AI

## Project

**Archivio Personale AI** is a lightweight, safety-first helper for organizing folders and files on the user's own computer.

Primary target: local PC/internal HDD. Future target: Google Drive only when available as a local synced/mirrored filesystem folder, not through cloud API automation.

## Roles

- **ChatGPT web**: orchestrator and advisor. It may reason on project code, commands, summaries, counts, and reports shared by the user.
- **Claude Code**: current local implementer when available.
- **Cursor Pro+**: future local/editor implementer.
- **GitHub repository**: source of truth for code and project rules only, never for personal files.
- **Local models**: preferred future AI layer for file/content classification.
- **n8n VPS**: future optional scheduler/notification layer only; not active and not connected to local files in the current phase.

## Task history

| Task | Description | Outcome |
|------|-------------|---------|
| ARCH-0001 | Improve duplicate report filtering | Closed — commit `9c421c` |
| ARCH-0002 | Local validation of filtered duplicate report | Validation-only — no commit |
| ARCH-0003 | Document safe report opening command | Closed — commit `5f09dac` |
| ARCH-0004..ARCH-0013 | Batch 1 — tracking, usability, local workflow cleanup | In progress |

## Current phase

**Dry-run inventory + rule-based classification baseline.**

Implemented:

- read-only inventory script: `scripts/inventory_readonly.py`;
- static HTML inventory report generator: `scripts/generate_inventory_report.py`;
- rule-based dry-run classifier: `scripts/classify_inventory.py`;
- static HTML classification report generator: `scripts/generate_classification_report.py`;
- context preservation policy: files already inside existing folders are marked `keep_in_place`;
- review-only action plan for root sort candidates and exact duplicate groups;
- duplicate review priority and theoretical potential reclaimable size;
- unit tests for inventory, classification, and action planning;
- lightweight project documentation.

Not implemented:

- cloud/API classification of personal file contents;
- real move/rename/delete logic;
- active n8n workflow;
- automatic folder organization.

## Operating doctrine

Keep the project simple. The goal is to help the user understand and organize folders on their own computer, not to build an over-engineered automation platform.

Batch execution rule: when a set of tasks requires no user decision, prefer task ranges (e.g. ARCH-0004..ARCH-0013) in a single implementation prompt. Use batches of up to 10 tasks. Stop only for real gates: move/rename/delete, source writes, cloud/API calls, Drive API, n8n/MCP, dependency installs, secrets exposure, or a required user decision.

Rules:

- No external AI APIs for personal file contents.
- Local models are allowed for future classification, for example via Ollama, LM Studio, llama.cpp, or similar local runtimes.
- ChatGPT web is allowed as orchestrator using project state, code, logs, counts, and user-approved summaries/reports.
- Do not upload raw personal file contents to cloud AI services unless the user makes a separate explicit decision.
- Prefer reports, review lists, and clear questions over autonomous actions.
- Default posture is `review_only` / ask before acting.
- Any future Google Drive support must treat Drive as a local folder first, not as an API automation target.
- Do not build autonomous agents, MCP pipelines, or multi-step orchestration that operates on personal files without human review at each step.

## External tools under evaluation

No external tool is integrated yet. Candidate modules:

- **ExifTool** for read-only metadata extraction from photos, videos, audio, and PDFs.
- **DocFetcher** for local full-text search without reorganizing files.
- **Paperless-ngx** only as a possible separate document/OCR workflow for administrative documents and scans.
- **Czkawka / dupeGuru / fdupes** as references for duplicate detection, review-only by default.
- **MCP / local agents** only in a future restricted read-only setup with path allowlists; no free filesystem agent.

External tools must not bypass the safety model: no destructive operation, no source-folder writes, no cloud upload of personal file contents, and no automatic move/rename/delete without explicit user approval.

## Required references

- Safety rules: `docs/SAFETY_RULES.md`.
- Workflow: `docs/WORKFLOW.md`.
- Commands: `docs/COMMANDS.md`.

## Documentation policy

Keep the LLM Wiki Lite small. Do not create duplicate Markdown files or repeat the same rule in multiple places. Each `.md` file must have a distinct purpose and reduce risk, confusion, or future token use.
