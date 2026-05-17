# Archivio Personale AI

A safe, read-only inventory and classification system for a personal home file archive stored on a local PC or internal HDD.

## Phase 1 — Read-Only Inventory (current)

**Phase 1 is strictly read-only and dry-run only.**

This phase does **not**:
- move files
- rename files
- delete files
- reorganize folders
- apply any automatic operation to the source archive

All outputs are written to a user-specified output path — never inside the source archive by default.

## Real personal files

**Do not commit real personal files to this repository.**
The source archive must remain outside the repository (e.g. `D:\Archivio_Test` or your actual archive folder).

## Requirements

- Python 3.8+ (standard library only — no external packages required)

## Usage

### 1. Run a read-only inventory scan

```bash
python scripts/inventory_readonly.py --source "D:\Archivio_Test" --output reports/inventory.json
```

### 2. Generate a static HTML report

```bash
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

Open `reports/inventory_report.html` in a browser to review results.

> **Warning:** Test first on a folder with fake files or disposable copies before running on your real archive.

## Project structure

```
docs/           — project documentation and safety rules
scripts/        — Python scripts (read-only scanner, report generator)
tests/          — unit tests (use only temporary directories)
reports/        — output reports (not committed; examples/ contains .gitkeep)
workflows/n8n/  — future n8n integration notes
```

## Running tests

```bash
python -m unittest discover -s tests
```

## Safety

See [docs/SAFETY_RULES.md](docs/SAFETY_RULES.md) for the full list of rules.
