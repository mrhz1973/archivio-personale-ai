# Commands — Archivio Personale AI

This file lists safe commands for the current phase. The source archive must remain read-only.

## Validation

```bash
python -m py_compile scripts/inventory_readonly.py scripts/generate_inventory_report.py scripts/classify_inventory.py scripts/generate_classification_report.py
python -m unittest discover -s tests -v
```

## Inventory example

```bash
python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
```

## Inventory HTML report example

```bash
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

## Dry-run classification example

```bash
python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
```

## Classification HTML report example

```bash
python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
```

## Git rules

Allowed:

```bash
git status --short
git diff --stat
git add <explicit-paths-only>
git commit -m "message"
git push origin main
```

Forbidden unless explicitly ordered by the user:

```bash
git add .
git reset
git clean
git push --force
```

Do not install dependencies unless explicitly requested. Do not run commands that move, rename, delete, overwrite, or reorganize source archive files.
