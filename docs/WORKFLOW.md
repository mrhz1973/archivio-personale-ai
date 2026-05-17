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

### Future local AI classification

A future local AI model (e.g. Ollama, LM Studio, llama.cpp) may improve classification quality by reasoning from metadata summaries. Personal file contents must never be sent to cloud or external API services. ChatGPT web may reason only from user-approved summaries, reports, or logs — not from raw private file uploads unless explicitly approved by the user.

### proposed_actions.json vs proposed_moves.json

**Current phase:** `reports/proposed_actions.json` is review-only. It may include duplicate groups, root sort candidates, review priority, and theoretical potential reclaimable size. It does not execute anything.

**Future controlled move phase (not yet implemented):** `proposed_moves.json` may exist only if the user explicitly approves a real move phase. It must be manually reviewed, require batch approval and a rollback plan, and must never be triggered automatically.

### Proposed moves (future)

### Optional controlled move

Only after explicit user approval and a rollback plan may a controlled move phase be considered. Each batch must be explicitly approved. This phase is opt-in and never automatic.
