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

## Validation

```powershell
python -m py_compile scripts/inventory_readonly.py scripts/generate_inventory_report.py scripts/classify_inventory.py scripts/generate_classification_report.py scripts/generate_action_plan.py scripts/generate_action_plan_report.py
python -m unittest discover -s tests -v
```

## Inventory example

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

```powershell
python scripts/validate_reports.py
```

Optional: pass explicit paths to override defaults.

```powershell
python scripts/validate_reports.py reports/inventory_report.html reports/classification_report.html reports/action_plan_report.html
```

Missing report files are skipped with `[SKIP]`. Structural failures are reported with `[FAIL]`.

## Troubleshooting: blank duplicate table in action report

If the action plan report shows the summary and filters but no duplicate rows, open the browser Console (F12) for JavaScript errors, then regenerate the report:

```powershell
python scripts/generate_action_plan_report.py --input reports/proposed_actions.json --output reports/action_plan_report.html
```

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
