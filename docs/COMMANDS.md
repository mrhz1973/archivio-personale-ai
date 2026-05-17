# Commands — Archivio Personale AI

This file lists safe commands for the current phase. The source archive must remain read-only.

## Validation

```bash
python -m py_compile scripts/inventory_readonly.py scripts/generate_inventory_report.py scripts/classify_inventory.py scripts/generate_classification_report.py scripts/generate_action_plan.py scripts/generate_action_plan_report.py
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

## Review-only action plan example

```bash
python scripts/generate_action_plan.py --inventory reports/inventory.json --classifications reports/classifications.json --output reports/proposed_actions.json
```

## Action plan HTML report example

```bash
python scripts/generate_action_plan_report.py --input reports/proposed_actions.json --output reports/action_plan_report.html
```

## Open generated HTML reports on Windows

I report HTML generati sono in italiano.

Use `.\reports\...` to avoid malformed paths such as `reportsaction_plan_report.html`.

```powershell
Invoke-Item .\reports\inventory_report.html
Invoke-Item .\reports\classification_report.html
Invoke-Item .\reports\action_plan_report.html
```

Non auto-aprire i report durante la validazione. Usare `Invoke-Item .\reports\...` solo quando richiesto dall'utente. Preferire la generazione del report e la conferma che il file esiste.

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
- Verify that no unexpected GitHub commit was created and that the previous code commit remains current.

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
