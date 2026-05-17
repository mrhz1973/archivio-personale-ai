# Workflow — Archivio Personale AI

This document describes the safe pipeline from read-only inventory to dry-run classification and, only in a future explicitly approved phase, controlled moves.

---

## Step 1 — Create an external test folder

Create a folder **outside** the repository, for example `C:\Archivio_Test`, with fake files or disposable copies.

## Step 2 — Run the read-only inventory scan

```bash
python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
```

The script recursively scans the source folder in read-only mode and writes a JSON file to the output path. The source folder is never modified.

## Step 3 — Generate the inventory HTML report

```bash
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

Open `reports/inventory_report.html` in a browser for a human-readable summary.

## Step 4 — Run dry-run rule-based classification

```bash
python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
```

This step reads only `inventory.json`. It classifies files from metadata such as relative path, filename, extension, and size. It does not read source file contents and does not move, rename, delete, overwrite, or reorganize files.

Files already inside existing folders are treated as context-bound and marked `keep_in_place`. This preserves project folders where a PDF, spreadsheet, image, note, or other file belongs to the folder context.

Files in the root of the scanned folder are marked `classify_only`; this is a classification suggestion, not a move instruction.

## Step 5 — Generate the classification HTML report

```bash
python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
```

Open `reports/classification_report.html` in a browser and review the categories, location policies, and low-confidence items.

---

## Future phases (not yet implemented)

### AI/cloud classification

A future AI model may improve classification quality, but personal file contents must not be uploaded to cloud/API services without explicit approval.

### Proposed moves

A future `proposed_moves.json` may describe suggested moves for manual review. It must not execute moves. Existing project/context folders must remain protected unless the user explicitly overrides that rule.

### Optional controlled move

Only after explicit user approval and a rollback plan may a controlled move phase be considered. Each batch must be explicitly approved. This phase is opt-in and never automatic.
