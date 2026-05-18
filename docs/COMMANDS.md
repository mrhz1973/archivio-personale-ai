# Commands — Archivio Personale AI

This file lists safe commands for the current phase. The source archive must remain read-only.

## Flusso consigliato v1

Ordine operativo suggerito per un primo utilizzo sicuro:

1. **First-run check** — verifica prerequisiti locali:
   `python .\scripts\run_first_time_check.py`
2. **Validazione quick** — controlli essenziali (py_compile + validate_reports --help):
   `python .\scripts\run_validations.py --quick`
3. **Demo sintetica quick** — smoke-test pipeline su dati sintetici:
   `python .\scripts\run_synthetic_demo.py --quick`
4. **Demo sintetica full** — pipeline completa su dati sintetici:
   `python .\scripts\run_synthetic_demo.py`
5. **Inventario dry-run** — legge la sorgente, scrive solo il JSON di output:
   `python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json`
6. **Classificazione dry-run** — legge il JSON inventario, produce classificazioni review-only:
   `python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json`
7. **Piano azioni review-only** — legge inventario e classificazioni, produce piano per sola revisione manuale:
   `python scripts/generate_action_plan.py --inventory reports/inventory.json --classifications reports/classifications.json --output reports/proposed_actions.json`
8. **Validazione report** — verifica struttura HTML, lang="it", wording review-only:
   `python .\scripts\validate_reports.py`

Nessun passo esegue operazioni di spostamento, rinomina o cancellazione. Nessun report viene aperto automaticamente.

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

`run_first_time_check.py` verifica solo prerequisiti locali: Python, script richiesti e documentazione. È locale, read-only, non usa rete né servizi esterni, non legge file personali, non legge `reports/` e non modifica alcun file.

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

**Safety summary:** `run_validations.py` esegue solo validazioni locali. Non apre report né browser, non usa rete né servizi esterni, non legge file personali e non propone operazioni distruttive.

**Flag principali:**
- `--quick` — esegue solo i controlli essenziali (py_compile + validate_reports --help); salta first-run check, unittest e demo.
- `--list` — non esegue nulla: stampa solo i controlli pianificati con i relativi label di modalità ed esce con 0.
- `--no-demo` — modalità full senza demo sintetica; first-run check e unittest vengono comunque eseguiti.

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

`scripts/inventory_readonly.py` legge la cartella sorgente e scrive solo il file JSON indicato in `--output`. Non modifica, non sposta, non rinomina e non cancella i file sorgente.

```powershell
python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
```

**JSON output format:**
- `metadata` — `schema_version`, `generated_at_iso` (ISO UTC), `tool`, `mode` (`read_only`)
- `summary` — file counts, `total_size_bytes`, `total_size_human`, `directories_scanned`, `ignored_dirs_count`, `extensions_count`, `skipped_count`, `errors_count`
- `files` — list of file records sorted deterministically by `relative_path`
- `errors` — list of unreadable paths sorted by `path`

## Inventory HTML report example

`scripts/generate_inventory_report.py` legge il JSON inventario e scrive solo il file HTML in `--output`. Non modifica i file sorgente. Il report è in italiano, è review-only (non propone cancellazioni, spostamenti né rinomina) e non viene aperto automaticamente.

HTML sections: `Informazioni report` (metadata), `Riepilogo` (summary with `total_size_human`, `directories_scanned`, `ignored_dirs_count`), `Estensioni`, `File più grandi — lista di revisione`.

```powershell
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

## Dry-run classification example

`scripts/classify_inventory.py` legge solo il JSON inventario, usa i metadati e i percorsi relativi già presenti nel JSON — non legge il contenuto dei file personali. Produce classificazioni dry-run, preserva il contesto dei file in sottocartelle (`keep_in_place`) e non agisce mai sui file personali. Scrive solo il JSON in `--output`.

**JSON output format:**
- `metadata` — `schema_version`, `generated_at_iso`, `tool`, `mode` (`dry_run_classification`), `input_tool`, `input_schema_version`
- `summary` — `categories_count`, `location_policy_counts`, `confidence_buckets` (high/medium/low), `root_file_count`, `context_bound_count`, `low_confidence_count`
- `classifications` — list sorted by `relative_path`; each entry includes `dry_run_only: true`

```powershell
python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
```

## Classification HTML report example

`scripts/generate_classification_report.py` legge il JSON classificazioni e genera un report HTML statico in italiano (metadati, riepilogo con `confidence_buckets`, conteggi categorie e policy). Il report è review-only, non agisce sui file personali e non viene aperto automaticamente.

```powershell
python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
```

## Review-only action plan example

`scripts/generate_action_plan.py` legge il JSON inventario e le classificazioni, produce un piano review-only (candidati a riordino radice + gruppi duplicati) per sola revisione manuale. Non agisce mai sui file personali. Lo spazio recuperabile (`potential_reclaimable_human`) è solo teorico — nessuna cancellazione è proposta.

**JSON output format:**
- `metadata` — `schema_version`, `generated_at_iso`, `tool`, `mode` (`review_only_action_plan`), `inventory_tool`, `classifications_tool`, `inventory_schema_version`, `classifications_schema_version`
- `summary` — counts, `potential_reclaimable_bytes`, `potential_reclaimable_human`, `duplicate_priority_counts`
- `root_sort_candidates` — sorted by `relative_path`; each entry has `dry_run_only: true`
- `duplicate_groups` — sorted by reclaimable bytes desc, then sha256 for stable tie-break

```powershell
python scripts/generate_action_plan.py --inventory reports/inventory.json --classifications reports/classifications.json --output reports/proposed_actions.json
```

## Action plan HTML report example

`scripts/generate_action_plan_report.py` legge il JSON piano azioni e genera un report HTML statico in italiano (metadati, riepilogo con `potential_reclaimable_human`, candidati a riordino, gruppi duplicati con filtri interattivi). Il report è review-only, non agisce sui file personali, non propone cancellazioni e non viene aperto automaticamente. Lo spazio recuperabile è solo teorico.

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

`scripts/validate_reports.py` valida la struttura minima degli HTML generati: controlla `lang="it"`, presenza di `<!DOCTYPE html>`/`<html`/`<body>`, wording review-only obbligatorio e assenza di wording pericoloso non negato (delete, move, rename, ecc.). Non apre browser, non modifica file, non crea directory, non scrive output e non usa rete né servizi esterni.

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

Missing default report files are skipped with `[SKIP]`. Directories with no HTML print `[INFO]`. Results per file: `[OK]`, `[WARN]`, `[FAIL]`. The final summary line is always printed and reports `Checked`, `OK`, `Warnings`, `Errors`, followed by `Validation passed.` or `Validation FAILED.`.

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

`scripts/run_synthetic_demo.py` usa esclusivamente fixture sintetiche in una directory temporanea: non legge file personali, non scrive in `reports/`, non apre browser e non usa rete né servizi esterni. La directory temporanea viene eliminata automaticamente al termine (salvo `--keep-temp`). Il `demo_manifest.json` prodotto include `metadata` (schema_version, tool, mode, safety_profile) e `safety` (tutti i flag a `false`). I `generated_files` sono ordinati per `path`. Tutto è temporaneo e non va committato.

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

Esegue la pipeline completa su una directory temporanea di **file sintetici innocui** (non file personali). Tutto l'output va in una directory temporanea eliminata automaticamente al termine. Non scrive in `reports/`, non apre browser, non usa rete né servizi esterni.

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
