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
- unit tests for inventory and classification;
- lightweight project documentation.

Not implemented:

- AI/cloud classification;
- `proposed_moves.json`;
- move/rename/delete logic;
- active n8n workflow;
- automatic folder organization.

## Required references

- Safety rules: `docs/SAFETY_RULES.md`.
- Workflow: `docs/WORKFLOW.md`.
- Commands: `docs/COMMANDS.md`.

## Documentation policy

Keep the LLM Wiki Lite small. Do not create duplicate Markdown files or repeat the same rule in multiple places. Each `.md` file must have a distinct purpose and reduce risk, confusion, or future token use.
