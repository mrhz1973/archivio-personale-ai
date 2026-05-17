# Workflow — Archivio Personale AI

This document describes the intended pipeline from initial safe inventory to an eventual optional controlled move phase.

---

## Step 1 — Create an external test folder

Create a folder **outside** the repository (e.g. `D:\Archivio_Test`) with a small set of fake or disposable files. Never use the real archive for first tests.

## Step 2 — Run the read-only inventory scan

```bash
python scripts/inventory_readonly.py --source "D:\Archivio_Test" --output reports/inventory.json
```

The script recursively scans the source folder in read-only mode and writes a JSON file to the output path. The source folder is never modified.

## Step 3 — Review the JSON inventory

Open `reports/inventory.json` and check:
- total file count
- total size
- extension distribution
- any errors or skipped files

## Step 4 — Generate a static HTML report

```bash
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

Open `reports/inventory_report.html` in a browser for a human-readable summary.

---

## Future phases (not yet implemented)

### Phase 2 — AI classification

An AI model will analyze file names, paths, and metadata from the inventory and suggest a classification (e.g. suggested folder, category, tags). Output: a `classifications.json` file. No files are moved.

### Phase 3 — Proposed moves

Based on AI classification, the system will generate a `proposed_moves.json` describing suggested moves. The user reviews this file manually before any action is taken.

### Phase 4 — Optional controlled move (explicit approval required)

Only after:
- the user has reviewed and approved the proposed moves,
- a rollback plan is in place,

will a controlled move script be executed. Each batch must be explicitly approved. This phase is opt-in and never automatic.
