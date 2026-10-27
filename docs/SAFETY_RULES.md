# Safety Rules — Archivio Personale AI

These rules apply to all phases: ChatGPT acts directly through available authorized tools; Cursor may support a task only on explicit user delegation.

## Absolute prohibitions

- **No destructive operations** against the source archive.
- **No automatic move**.
- **No rename**.
- **No delete**.
- **No overwrite**.
- **No writing inside the source archive by default** — outputs go to a user-specified external path.
- **No real personal files committed to Git**.
- **No external/cloud AI API calls for personal file contents**.
- **No Google Drive API automation by default**.
- **No n8n runtime activation**.
- **No MCP/filesystem agent operations on personal files**.
- **No dependency installs unless explicitly approved**.

## Operational gate policy

If a requested step crosses a real gate (move/rename/delete, API/cloud, n8n, MCP, installs, secrets), stop and request explicit user approval.

If there is no real gate, execute only the minimum next safe step.

## Reports

Do not auto-open reports with `start`, `Invoke-Item`, or equivalents.
Commands may be documented, but execution requires explicit user request.

## Future move phase — required conditions

A controlled move phase may be introduced only if all conditions are satisfied:

1. read-only inventory and dry-run report phase complete and reviewed;
2. `proposed_moves.json` generated and manually reviewed;
3. explicit user approval for each move batch;
4. rollback plan defined before execution.

No move, rename, or delete operation shall ever be automatic or unattended.

## V1 readiness checklist

For the complete v1 readiness checklist (implemented components, stop criteria, definition of "v1 ready"), see `docs/V1_READINESS.md`.
