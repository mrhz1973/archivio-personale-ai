# Workflow — Archivio Personale AI

Safe pipeline: read-only inventory to dry-run classification. No destructive actions.

## Operational guardrails

- One active implementer only: Claude Code (primary) or Codex (backup).
- Before switching implementer: verify workspace clean/aligned.
- User local environment is Windows: local command syntax is PowerShell.
- Never auto-open reports with `start`, `Invoke-Item`, or equivalents unless explicitly requested.

## Preflight (before edits)

```powershell
git branch --show-current
git log -1 --oneline
git status --short
```

Then confirm:
- authorized files/areas only;
- whether real gates exist (move/rename/delete, API/cloud, n8n, MCP, installs, secrets).

If a real gate exists, stop and ask.

## Step 1 — Create an external test folder

Create a folder **outside** the repository, for example `C:\Archivio_Test`, with fake files or disposable copies.

## Step 2 — Run the read-only inventory scan

```powershell
python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
```

The source folder is scanned in read-only mode and is never modified.

## Step 3 — Generate the inventory HTML report

```powershell
python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
```

## Step 4 — Run dry-run rule-based classification

```powershell
python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
```

`classify_inventory` reads only `inventory.json` metadata and does not read source file contents.

- Files already inside existing folders are marked `keep_in_place`.
- Files in the root of the scanned folder are marked `classify_only` (suggestion only).

## Step 5 — Generate the classification HTML report

```powershell
python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
```

Review reports manually in browser. Do not auto-open during validation.

## Review outputs and future phases

- `reports/proposed_actions.json` is review-only (no execution).
- `proposed_moves.json` is allowed only in a future controlled move phase.
- Future local AI classification is allowed only without cloud API use for personal contents.
- Optional controlled move is allowed only with explicit user approval per batch and a rollback plan.

## Post-task verification

```powershell
git status --short
git diff --stat
```

- Run Python/unittest only if scripts/ or tests/ changed.
- Verify no committable report artifacts were created.
- Verify commit message format.
- Verify no personal files were included.

## Validation-only behavior

Validation-only tasks may end without a commit. Correct outcome: no new commit, clean workspace, verified behavior.
