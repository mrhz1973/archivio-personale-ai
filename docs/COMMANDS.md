# Commands — Archivio Personale AI

This file lists safe commands for the current phase. The source archive must remain read-only.

## Local shell policy (Windows)

For user-local execution, use **PowerShell** syntax and examples.
Do not mix Bash syntax with PowerShell-only constructs.

## Implementer preflight (before any edit)

```powershell
git branch --show-current
git log -1 --oneline
git status --short
```

Manual preflight checks (compact):
- confirm only authorized files/areas are in scope;
- declare whether real gates exist (move/rename/delete, API/cloud, n8n, MCP, installs, secrets).

## First-run readiness check

Before running other commands, verify environment readiness:

```powershell
python .\scripts\run_first_time_check.py
```

Checks:
- Python >= 3.8
- Expected scripts exist: `run_validations.py`, `run_synthetic_demo.py`
- Expected docs exist: `docs/COMMANDS.md`, `README.md`

| Mode | Command | What it does |
|------|---------|--------------|
| full | `python .\scripts\run_first_time_check.py` | runs all checks; exit 0 if all pass, 1 if any fail |
| list | `python .\scripts\run_first_time_check.py --list` | prints check labels without running; always exits 0 |
| quiet | `python .\scripts\run_first_time_check.py --quiet` | suppresses [OK] lines; keeps [FAIL] and summary |

Exit codes: `0` all checks passed (or `--list`), `1` one or more checks failed.

## Validation

```powershell
python -m py_compile scripts/inventory_readonly.py scripts/generate_inventory_report.py scripts/classify_inventory.py scripts/generate_classification_report.py scripts/generate_action_plan.py scripts/generate_action_plan_report.py
python -m unittest discover -s tests -v
```

Run the full test suite (compact form):

```powershell
python -m unittest discover
```

Tests use synthetic data and temporary directories only. Do not reference `reports/` or personal files inside tests.

## Local validation runner

`scripts/run_validations.py` — stdlib only, no network, no report opening, no personal files.

| Mode | Command | What runs |
|------|---------|-----------|
| full | `python .\scripts\run_validations.py` | first-run check + py_compile + unittest discover + validate_reports --help + synthetic demo |
| quick | `python .\scripts\run_validations.py --quick` | py_compile + validate_reports --help (skips all full-only steps: first-run check, unittest, demo) |
| list | `python .\scripts\run_validations.py --list` | prints planned checks, exits 0, no subprocess |
| quiet | `python .\scripts\run_validations.py --quiet` | any mode; suppresses [RUN]/[OK], keeps summary and errors |
| no-demo | `python .\scripts\run_validations.py --no-demo` | full mode, skips synthetic demo (useful for debug) |

```powershell
# full run
python .\scripts\run_validations.py

# quick essentials only
python .\scripts\run_validations.py --quick

# list planned checks without running
python .\scripts\run_validations.py --list
```

Exit codes: `0` all checks passed (or `--list`), `1` one or more checks failed.

**Mode summary:**
- `full` — runs all steps including full-only (first-run check, unittest, demo).
- `--quick` — runs only essential steps (py_compile + validate_reports --help); skips all full-only steps.
- `--list` — prints planned checks with mode labels, no subprocess, exit 0.
- `--no-demo` — full mode minus synthetic demo; first-run check and unittest still run.

## Inventory example

`scripts/inventory_readonly.py` reads the source folder and writes only the JSON file at `--output`. It never modifies, moves, renames, or deletes source files.

```powershell
python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
```

## Inventory HTML report example

```powershell
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

## Dry-run classification example

```powershell
python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
```

## Classification HTML report example

```powershell
python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
```

## Review-only action plan example

```powershell
python scripts/generate_action_plan.py --inventory reports/inventory.json --classifications reports/classifications.json --output reports/proposed_actions.json
```

## Action plan HTML report example

```powershell
python scripts/generate_action_plan_report.py --input reports/proposed_actions.json --output reports/action_plan_report.html
```

## Open generated HTML reports on Windows (only on explicit user request)

I report HTML generati sono in italiano.

Use `./reports/...` to avoid malformed paths.

```powershell
Invoke-Item ./reports/inventory_report.html
Invoke-Item ./reports/classification_report.html
Invoke-Item ./reports/action_plan_report.html
```

Never auto-open reports during validation. Do not use `start`, `Invoke-Item`, or equivalents unless the user explicitly asks.

## Report validation (structural, no browser)

Validate generated HTML reports structurally without opening them. Does not modify source archive files.
Exit codes: `0` no errors, `1` validation errors, `2` invalid path or CLI usage.

```powershell
# default: check reports/inventory_report.html, classification_report.html, action_plan_report.html
python .\scripts\validate_reports.py

# all *.html in a directory (recursive, deterministic order)
python .\scripts\validate_reports.py .\reports

# explicit file
python .\scripts\validate_reports.py .\reports\inventory_report.html

# show help and exit codes
python .\scripts\validate_reports.py --help
```

Missing default report files are skipped with `[SKIP]`. Directories with no HTML print `[INFO]`. Results per file: `[OK]`, `[WARN]`, `[FAIL]`.

## Troubleshooting: blank duplicate table in action report

If the action plan report shows the summary and filters but no duplicate rows, open the browser Console (F12) for JavaScript errors, then regenerate the report:

```powershell
python scripts/generate_action_plan_report.py --input reports/proposed_actions.json --output reports/action_plan_report.html
```

## Percorso consigliato

| Scenario | Comando | Cosa fa |
|----------|---------|---------|
| Validazione rapida | `python .\scripts\run_validations.py --quick` | py_compile + validate_reports --help |
| Demo rapido | `python .\scripts\run_synthetic_demo.py --quick` | inventory → classify → report (dati sintetici) |
| Demo completo | `python .\scripts\run_synthetic_demo.py` | tutte le 7 fasi della pipeline su dati sintetici |
| Ispezione manuale | `python .\scripts\run_synthetic_demo.py --keep-temp` | demo completo, stampa temp dir e manifest path, nessuna apertura automatica |

Tutti i comandi usano solo dati sintetici e non toccano file personali o `reports/`. Nessun file viene aperto automaticamente. `demo_manifest.json` è temporaneo e non va committato.

## Synthetic demo — quickstart

Fastest way to verify the full pipeline without personal files:

```powershell
# 1. quick smoke-test (inventory → classify → inventory report)
python .\scripts\run_validations.py --quick

# 2. minimal end-to-end pipeline on synthetic data
python .\scripts\run_synthetic_demo.py --quick

# 3. full pipeline on synthetic data
python .\scripts\run_synthetic_demo.py

# 4. keep temp dir for manual inspection (prints paths, no auto-open)
python .\scripts\run_synthetic_demo.py --keep-temp
```

## Synthetic end-to-end demo

Runs the full pipeline on a temporary directory of **synthetic, innocuous files** (not personal files).
All output goes to a temporary directory that is deleted automatically on exit.
Never writes to `reports/`, never opens a browser, never uses network or API.

| Mode | Command | What runs |
|------|---------|-----------|
| full | `python .\scripts\run_synthetic_demo.py` | all 7 pipeline steps |
| quick | `python .\scripts\run_synthetic_demo.py --quick` | inventory → classify → inventory report |
| list | `python .\scripts\run_synthetic_demo.py --list` | prints planned steps, exits 0, no subprocess |
| keep | `python .\scripts\run_synthetic_demo.py --keep-temp` | full run, temp dir kept, paths printed |
| quiet | `python .\scripts\run_synthetic_demo.py --quiet` | full run, suppresses OK lines, prints summary |
| no-manifest | `python .\scripts\run_synthetic_demo.py --no-manifest` | full run, skips manifest (debug) |

```powershell
# full run
python .\scripts\run_synthetic_demo.py

# minimal end-to-end (inventory → classify → inventory report)
python .\scripts\run_synthetic_demo.py --quick

# list planned steps without running
python .\scripts\run_synthetic_demo.py --list

# keep the temporary directory for manual inspection (prints path and manifest path, no auto-open)
python .\scripts\run_synthetic_demo.py --keep-temp
```

`--keep-temp` prints the temp directory path and the `demo_manifest.json` path for manual inspection only. It does not open any report automatically.
All demo files are synthetic and temporary; they are not personal files and are not written to `reports/`.

Exit codes: `0` all steps passed (or `--list`), `1` one or more steps failed.

### demo_manifest.json

After each run a `demo_manifest.json` is written **inside the temp directory** (not in `reports/`).
It is purely **temporary and synthetic**:

- contains: mode, temp_dir basename, timestamps, exit_code, per-step results, generated file list;
- does **not** contain absolute paths, personal file paths, or credentials;
- is deleted automatically with the temp dir (unless `--keep-temp`);
- must **not** be committed to the repository;
- use `--no-manifest` to skip writing it (e.g. for debug runs).

## Implementer post-task verification

```powershell
git status --short
git diff --stat
```

Post-task checks (compact):
- run Python/unittest validation only if scripts/ or tests/ were touched;
- verify no committable reports were created;
- verify commit message format is correct;
- verify no personal files are included.

## Commit message format

Single-task commits:

```
ARCH-000X subject
```

Batch commits (multiple tasks, no user decision gates):

```
ARCH-000X..ARCH-000Y subject
```

The commit body or the LLMS.md task history must list what was included when a batch covers multiple logical items.

## Validation-only tasks

A task is validation-only when it verifies existing behavior without changing code or docs.

- Validation-only tasks may end with no commit.
- Correct validation-only outcome: no new commit, clean workspace, verified behavior.
- Verify that no unexpected GitHub commit was created and that the previous code commit remains current.

## Git rules

Allowed:

```powershell
git status --short
git diff --stat
git add <explicit-paths-only>
git commit -m "message"
git push origin main
```

Forbidden unless explicitly ordered by the user:

```powershell
git add .
git reset
git clean
git push --force
```

Do not install dependencies unless explicitly requested. Do not run commands that move, rename, delete, overwrite, or reorganize source archive files.
