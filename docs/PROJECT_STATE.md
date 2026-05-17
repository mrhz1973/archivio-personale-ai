# Project State — Archivio Personale AI

| Field | Value |
|---|---|
| **Project name** | Archivio Personale AI |
| **Current phase** | Phase 1 — Initial safe inventory baseline |
| **Target** | Personal home files on local PC / internal HDD |
| **Date** | 2026-05-17 |

## Infrastructure

- **n8n**: exists on a VPS but is **not connected to local files** in this phase. No n8n workflow touches source archive files.
- **Claude Code**: current implementer for phase 1 scripts and documentation.
- **Cursor Pro+**: may be used in a later phase for extended development.

## What is implemented

- [x] Read-only recursive inventory scanner (`scripts/inventory_readonly.py`)
- [x] Static HTML report generator (`scripts/generate_inventory_report.py`)
- [x] Unit tests (`tests/test_inventory_readonly.py`)
- [x] Project documentation (`docs/`)

## What is NOT implemented

- [ ] AI classification of files
- [ ] `proposed_moves.json` generation
- [ ] Any move, rename, or delete operation
- [ ] n8n automation connected to local files
- [ ] Any automatic folder organization

## Next steps

1. Manual test on a folder with fake files.
2. Run inventory on a real archive subfolder (read-only).
3. Review the HTML report.
4. Decide whether to proceed to Phase 2 (AI classification).
