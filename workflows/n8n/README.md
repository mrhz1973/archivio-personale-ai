# n8n Workflows — Archivio Personale AI

## Current status: NOT ACTIVE

No n8n workflow is active in Phase 1. The n8n instance on the VPS is not connected to local files.

## Rules for future n8n integration

- n8n may be introduced only **after** the inventory and report baseline is working and reviewed.
- **No n8n workflow may move, rename, or delete files in Phase 1.**
- Any n8n workflow based on AI file organization (e.g. a "monitor folder → ask AI → move file" pattern) must be converted to **dry-run / report-only** mode before it is imported or activated in this project.
- All proposed actions must be written to a report file for human review before any execution.

## Reference — prior inspiration

A prior n8n workflow was used as inspiration. It monitored a folder, asked an AI where to place each file, and then moved them automatically. **That behavior is explicitly prohibited in Phase 1** of this project. It will only be considered in a future controlled phase after dry-run validation and explicit user approval.
