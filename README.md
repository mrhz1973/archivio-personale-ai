# Archivio Personale AI

## Cos'è Archivio Personale AI

Un helper locale, sicuro e review-only per l'inventario e la classificazione dry-run di un archivio di file personali su PC locale o HDD interno.

- **Local-first**: tutto gira sul tuo PC, nessun dato inviato all'esterno.
- **Review-only**: i report sono per revisione manuale; nessuna azione automatica sui file.
- **Safety-first**: nessuna operazione di spostamento, rinomina o cancellazione.
- **Nessuna azione automatica sui file personali**: gli script leggono metadati e percorsi, non i contenuti dei file personali.

## Cosa non fa

- Non sposta file.
- Non rinomina file.
- Non cancella file.
- Non usa cloud o servizi esterni sui contenuti personali.
- Non apre report automaticamente.

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

## v1 quickstart

Ordine consigliato per verificare l'ambiente e la pipeline su dati sintetici (nessun file personale):

```powershell
# 1. verifica prerequisiti locali
python .\scripts\run_first_time_check.py

# 2. controlli essenziali (py_compile + validate_reports --help)
python .\scripts\run_validations.py --quick

# 3. demo sintetica rapida (inventory → classify → report su dati sintetici)
python .\scripts\run_synthetic_demo.py --quick
```

Tutti i comandi usano solo dati sintetici e non toccano file personali né `reports/`. Nessun file viene aperto automaticamente. Vedi `docs/COMMANDS.md` per le opzioni avanzate.

### Demo sintetica

La demo sintetica usa esclusivamente file temporanei innocui generati al momento: non legge file personali, non scrive in `reports/`, non apre browser, non usa rete o servizi esterni. La directory temporanea viene eliminata automaticamente al termine.

```powershell
python .\scripts\run_synthetic_demo.py --quick  # smoke-test rapido
python .\scripts\run_synthetic_demo.py          # pipeline completa su dati sintetici
```

### Report HTML

I report HTML generati (inventario, classificazione, piano azioni) sono in italiano e sono strumenti di **revisione manuale**. Non costituiscono istruzioni operative automatiche e non propongono alcuna cancellazione. Devono essere aperti esplicitamente dall'utente.

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

## Running tests

```powershell
python -m py_compile scripts/inventory_readonly.py scripts/generate_inventory_report.py scripts/classify_inventory.py scripts/generate_classification_report.py scripts/generate_action_plan.py scripts/generate_action_plan_report.py
python -m unittest discover -s tests -v
```

## V1 readiness

`docs/V1_READINESS.md` è il riferimento per capire se la v1 è pronta all'uso locale: contiene la checklist dei componenti implementati, i criteri di stop, la definizione di "v1 pronta" e i limiti intenzionali del progetto.

## Safety

See `docs/SAFETY_RULES.md`.
