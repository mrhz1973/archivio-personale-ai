# Archivio Personale AI

A safe, dry-run inventory and classification system for a personal home file archive stored on a local PC or internal HDD.

## Current phase — Dry-run inventory and rule-based classification

**Status:** local-first, review-only. Report HTML in italiano. The duplicate report has path, priority, context-bound, reclaimable, cross-folder, and same-filename filters. No automatic move, rename, or delete is proposed or implemented.

The current phase is strictly read-only and dry-run only.

This project does **not**:
- move files
- rename files
- delete files
- reorganize folders
- apply any automatic operation to the source archive

The classification step reads only `reports/inventory.json`; it does not read source file contents.

All outputs are written to a user-specified output path — never inside the source archive by default.

## Real personal files

**Do not commit real personal files to this repository.**
The source archive must remain outside the repository, for example `C:\Archivio_Test` or your actual archive folder.

## Requirements

- Python 3.8+ (standard library only — no external packages required)

## Usage

### 1. Run a read-only inventory scan

```bash
python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
```

### 2. Generate the inventory HTML report

```bash
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

### 3. Run dry-run classification

```bash
python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
```

### 4. Generate the classification HTML report

```bash
python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
```

Open the generated HTML reports in a browser to review results.

> **Warning:** Test first on a folder with fake files or disposable copies before running on your real archive.

## Project structure

```
docs/           — project documentation and safety rules
scripts/        — Python scripts
tests/          — unit tests (use only temporary directories or in-memory data)
reports/        — output reports (not committed; examples/ contains .gitkeep)
workflows/n8n/  — future n8n integration notes
```

## Running tests

```bash
python -m py_compile scripts/inventory_readonly.py scripts/generate_inventory_report.py scripts/classify_inventory.py scripts/generate_classification_report.py
python -m unittest discover -s tests -v
```

## Safety

See [docs/SAFETY_RULES.md](docs/SAFETY_RULES.md) for the full list of rules.
