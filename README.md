# Archivio Personale AI

A safe, local-first helper for inventory and dry-run classification of a personal file archive on a local PC/internal HDD.

## Current status

- Phase: read-only inventory + rule-based dry-run classification + Italian HTML reports.
- Mode: dry-run / read-only / review-only.
- Forbidden operations: move, rename, delete, overwrite, or automatic folder reorganization.
- Classification reads only `reports/inventory.json` (metadata flow), not source file contents.

## Personal files

Do not commit real personal files to this repository.
The source archive must stay outside the repo (for example `C:\Archivio_Test`).

## Operational guardrails

- One active implementer at a time: Claude Code (primary) or Codex (backup).
- Before implementer switch: verify workspace clean/aligned.
- Local user environment is Windows: use PowerShell for local commands.

## First-run readiness check

Before running any other commands, verify that your environment meets minimal requirements:

```powershell
python .\scripts\run_first_time_check.py
```

This checks:
- Python version >= 3.8
- Expected scripts exist
- Expected docs exist

List planned checks without running them:

```powershell
python .\scripts\run_first_time_check.py --list
```

## v1 quickstart

Fastest path to verify the project on synthetic data (no personal files):

```powershell
python .\scripts\run_first_time_check.py       # 0. verify environment readiness
python .\scripts\run_validations.py --quick    # 1. essential checks
python .\scripts\run_synthetic_demo.py --quick # 2. quick pipeline smoke-test on synthetic data
python .\scripts\run_synthetic_demo.py         # 3. full pipeline on synthetic data
```

All commands use only synthetic data and never touch personal files or `reports/`. No file is opened automatically. See `docs/COMMANDS.md` for advanced options.

## Minimal usage

```powershell
python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
```

Do not auto-open reports with `start`, `Invoke-Item`, or equivalents unless explicitly requested by the user.

## Project structure

- `docs/` — rules, commands, workflow
- `scripts/` — Python scripts (read-only/dry-run logic)
- `tests/` — unit tests
- `reports/` — generated outputs

## Requirements

- Python 3.8+ (standard library only)

## Synthetic demo

Verify the full pipeline on synthetic data (no personal files, no `reports/` writes):

```powershell
python .\scripts\run_synthetic_demo.py --quick   # quick smoke-test
python .\scripts\run_synthetic_demo.py            # full pipeline
```

See `docs/COMMANDS.md` for all demo options including `--keep-temp`, `--quiet`, and `--no-manifest`.

## Running tests

```powershell
python -m py_compile scripts/inventory_readonly.py scripts/generate_inventory_report.py scripts/classify_inventory.py scripts/generate_classification_report.py scripts/generate_action_plan.py scripts/generate_action_plan_report.py
python -m unittest discover -s tests -v
```

## Safety

See `docs/SAFETY_RULES.md`.
