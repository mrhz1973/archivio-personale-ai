# LLMS.md — Archivio Personale AI

## Project

**Archivio Personale AI** is a lightweight, safety-first project for inventorying and later classifying personal home files stored on a local PC or internal HDD.

## Roles

- **ChatGPT**: orchestrator.
- **Claude Code**: current implementer.
- **Cursor Pro+**: future implementer.
- **GitHub repository**: source of truth.
- **n8n VPS**: future automation layer; not active and not connected to local files in the current phase.

## Current phase

**Safe inventory baseline.**

Target: personal home files on the user's local PC/internal HDD.

Implemented:

- read-only inventory script: `scripts/inventory_readonly.py`;
- static HTML report generator: `scripts/generate_inventory_report.py`;
- unit tests: `tests/test_inventory_readonly.py`;
- lightweight project documentation.

Not implemented:

- AI classification;
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
