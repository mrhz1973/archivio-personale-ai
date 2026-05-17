# LLMS.md — Archivio Personale AI

## Project

**Archivio Personale AI** is a lightweight, safety-first project for inventorying and classifying personal home files stored on a local PC or internal HDD.

## Roles

- **ChatGPT**: orchestrator.
- **Claude Code**: current implementer.
- **Cursor Pro+**: future implementer.
- **GitHub repository**: source of truth.
- **n8n VPS**: future automation layer; not active and not connected to local files in the current phase.

## Current phase

**Dry-run inventory + rule-based classification baseline.**

Target: personal home files on the user's local PC/internal HDD.

Implemented:

- read-only inventory script: `scripts/inventory_readonly.py`;
- static HTML inventory report generator: `scripts/generate_inventory_report.py`;
- rule-based dry-run classifier: `scripts/classify_inventory.py`;
- static HTML classification report generator: `scripts/generate_classification_report.py`;
- context preservation policy: files already inside existing folders are marked `keep_in_place`;
- review-only action plan for root sort candidates and exact duplicate groups;
- unit tests for inventory, classification, and action planning;
- lightweight project documentation.

Not implemented:

- AI/cloud classification;
- real move/rename/delete logic;
- active n8n workflow;
- automatic folder organization.

## External tools under evaluation

No external tool is integrated yet. Candidate modules:

- **ExifTool** for read-only metadata extraction from photos, videos, audio, and PDFs.
- **DocFetcher** for local full-text search without reorganizing files.
- **Paperless-ngx** for a future document/OCR workflow limited to administrative documents and scans.
- **Czkawka / dupeGuru / fdupes** as references for duplicate detection, review-only by default.
- **MCP / local agents** only in a future restricted read-only setup with path allowlists.

External tools must not bypass the safety model: no destructive operation, no source-folder writes, no cloud upload of personal file contents, and no automatic move/rename/delete without explicit user approval.

## Required references

- Safety rules: `docs/SAFETY_RULES.md`.
- Workflow: `docs/WORKFLOW.md`.
- Commands: `docs/COMMANDS.md`.

## Documentation policy

Keep the LLM Wiki Lite small. Do not create duplicate Markdown files or repeat the same rule in multiple places. Each `.md` file must have a distinct purpose and reduce risk, confusion, or future token use.
