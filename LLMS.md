# LLMS.md — Archivio Personale AI

## Project

**Archivio Personale AI** is a lightweight, safety-first helper for organizing folders and files on the user's own computer.

Primary target: local PC/internal HDD. Future target: Google Drive only when available as a local synced/mirrored filesystem folder, not through cloud API automation.

## Roles

- **ChatGPT web**: orchestrator and advisor.
- **Claude Code**: primary local implementer when available.
- **Codex web**: backup implementer when Claude has finished tokens.
- **GitHub repository**: source of truth for code and project rules only, never for personal files.

## Task history

| Task | Description | Outcome |
|------|-------------|---------|
| ARCH-0001 | Improve duplicate report filtering | Closed — commit `9c421c` |
| ARCH-0002 | Local validation of filtered duplicate report | Validation-only — no commit |
| ARCH-0003 | Document safe report opening command | Closed — commit `5f09dac` |
| ARCH-0004..ARCH-0013 | Batch 1 — tracking, usability, local workflow cleanup | Closed — commit `f97050f` |
| ARCH-0014..ARCH-0023 | Batch 2 — Italian HTML reports | Closed — commit `65a14e5` |
| ARCH-0024..ARCH-0033 | Batch 3 — operational guardrails | Closed — commit `23f59ae` |
| ARCH-0034..ARCH-0044 | Batch 4 — action report rendering and orchestration rules | Closed — commit `1348ef1` |
| ARCH-0045..ARCH-0054 | Batch 5 — tracking and report verification hardening | Closed — commit `4287ff1` |
| ARCH-0055..ARCH-0064 | Batch 6 — auto-push policy and report validation tooling | Closed — commit `429592e` |
| ARCH-0065..ARCH-0074 | Batch 7 — harden report validator | Closed — commit `63ad275` |
| ARCH-0075..ARCH-0084 | Batch 8 — tracking cleanup and validator integration | Closed — commit `2c087ee` |
| ARCH-0085..ARCH-0094 | Batch 9 — validator CLI polish and tracking fix | Closed — commit `e073a64` |
| ARCH-0095..ARCH-0104 | Batch 10 — report generator regression tests | Closed — commit `1566ea8` |
| ARCH-0105..ARCH-0114 | Batch 11 — CLI smoke tests and docs consistency | Closed — commit `1eada61` |
| ARCH-0115..ARCH-0124 | Batch 12 — test hygiene and safety assertions | Closed — commit `0bd1304` |
| ARCH-0125..ARCH-0134 | Batch 13 — docs smoke alignment and tracking fix | Closed — commit `f363aeb` |
| ARCH-0135..ARCH-0144 | Batch 14 — local validation runner | Closed — commit `9f9a52a` |
| ARCH-0145..ARCH-0164 | Batch 15 — validation runner polish and invariants | Closed — commit `9a6b237` |
| ARCH-0165..ARCH-0184 | Batch 16 — CLI help consistency and validation coverage | Closed — commit `47f4b42` |
| ARCH-0185..ARCH-0204 | Batch 17 — synthetic fixture consolidation and validation stability | Closed — commit `cdf28ec` |
| ARCH-0205..ARCH-0224 | Batch 18 — synthetic end-to-end demo workflow | Closed — commit `9acf5bf` |
| ARCH-0225..ARCH-0259 | Batch 19 — synthetic demo polish and full validation integration | Closed — commit `812da45` |
| ARCH-0260..ARCH-0294 | Batch 20 — synthetic demo manifest and user-facing quickstart | Closed — commit `2763017` |
| ARCH-0295..ARCH-0334 | Batch 21 — v1 quickstart and validation summaries | Closed — commit `49ac2d8` |
| ARCH-0335..ARCH-0344 | Batch 22A — first-run readiness check | Closed — commit `37cf1a7` |
| ARCH-0345..ARCH-0354 | Batch 22B — first-run check tests and docs | Closed — commit `0f18d3c` |
| ARCH-0355..ARCH-0364 | Batch 22C — first-run check CLI polish | Closed — commit `8fc098a` |
| ARCH-0365..ARCH-0374 | Batch 23A — integrate first-run check in validation runner | Closed — commit `0596a98` |
| ARCH-0375..ARCH-0384 | Batch 23B — first-run validation safety and docs alignment | Closed — commit `1a91b3d` |
| ARCH-0385..ARCH-0394 | Batch 23C — validation runner help and full-only clarity | Closed — commit `77a10bf` |
| ARCH-0395..ARCH-0404 | Batch 24A — inventory read-only safety and CLI clarity | Closed — commit `6cedf2b` |
| ARCH-0405..ARCH-0429 | Batch 24B — inventory JSON metadata and deterministic output | Closed — commit `c1a3f45` |
| ARCH-0430..ARCH-0464 | Batch 24C — inventory HTML report metadata and safety alignment | Closed — commit `93ab4b6` |
| ARCH-0465..ARCH-0489 | Batch 25A — classification metadata deterministic dry-run output | Closed — commit `550cf06` |

## Current phase

**Dry-run inventory + rule-based classification baseline.**

Implemented:

- read-only inventory script: `scripts/inventory_readonly.py`;
- static HTML inventory report generator: `scripts/generate_inventory_report.py`;
- rule-based dry-run classifier: `scripts/classify_inventory.py`;
- static HTML classification report generator: `scripts/generate_classification_report.py`;
- context preservation policy: files already inside existing folders are marked `keep_in_place`;
- review-only action plan for root sort candidates and exact duplicate groups.

Not implemented:

- cloud/API classification of personal file contents;
- real move/rename/delete logic;
- active n8n runtime workflow;
- Google Drive API automation;
- MCP/filesystem agent operations on personal files.

## ChatGPT Priority Gate (silent checklist)

Before each operational reply, ChatGPT checks silently:

1. one operational step only;
2. latest output/screenshot has been read;
3. wait for output before continuing;
4. only one active implementer (Claude or Codex);
5. repo clean/aligned or explicitly to verify;
6. only authorized files/areas;
7. real gates: move, rename, delete, API, cloud, n8n, MCP, installs, secrets;
8. if a real gate exists: stop and ask;
9. if no real gate exists: provide only the next minimum step.

Do not print “priorità controllate” (or equivalent checklist confirmations) to the user.

## Implementer switch policy (Claude/Codex)

- Only one implementer active at a time.
- Prefer Claude Code as primary implementer.
- Use Codex web only as backup when Claude is unavailable/out of tokens.
- Before switching implementer, verify workspace clean/aligned.

## Codex guardrails

Codex must follow the same safety model as Claude:

- work only on authorized repository code/docs;
- never touch personal files;
- no cloud API processing for personal content;
- no n8n runtime activation;
- no MCP/filesystem agent workflows;
- no dependency installs unless explicitly approved.

Codex may use temporary work branches, but the base must be a verified remote commit.

## Windows local execution policy

User local environment is Windows. Local command examples and operator instructions must use **PowerShell**.

Do not mix Bash syntax with PowerShell constructs (`Test-Path`, `if (...) {}`, Windows paths, local Git checks, report regeneration).

## Report language policy

All generated user-facing HTML reports must be in Italian (`lang="it"`). Visible UI text must be in Italian. Python identifiers, JSON keys, filenames, and machine-readable fields stay in English.

## Operating doctrine

Keep the project simple, local-first, review-only, and safety-first.

Rules:

- No destructive operations.
- No automatic move/rename/delete.
- No external AI APIs for personal file contents.
- Prefer reports, review lists, and explicit user decisions.
- Default posture is `review_only` / ask before acting.

## Required references

- Safety rules: `docs/SAFETY_RULES.md`.
- Workflow: `docs/WORKFLOW.md`.
- Commands: `docs/COMMANDS.md`.

## No-confirmation-next-task rule

If no real decision gate, safety check, or explicit user confirmation is needed, proceed directly to the next operational step without asking for confirmation.

Real gates (must stop and ask): move/rename/delete on personal files, cloud/API use, dependency installs, secrets, implementer switch, dirty/misaligned workspace, merge/push to remote.

Non-gates (proceed directly): documentation updates, test additions, code fixes, validation runs, commits of authorized files.

## Documentation preservation rule

When updating existing documents, preserve all useful operational content already present: usage examples, safety conditions, workflow steps, notes on future phases, and operational sections.

Do not remove or overwrite existing content unless explicitly requested. Prefer targeted edits over broad rewrites. If a section appears duplicated, note it in the task summary instead of deleting it.

## Claude Code settings checklist (orchestrator)

Before giving an operational prompt to Claude Code, ChatGPT orchestrator should state, when relevant:

- Active implementer: Claude Code; Codex stopped.
- Mode: Code (modifying files) or Plan (analysis/planning only, no edits).
- Claude model selected, if visible in the interface.
- Effort / thinking / reasoning level, if visible.
- Expected branch and repo state (branch name, HEAD commit).
- Workspace: clean/aligned or verify first.
- Authorized files and forbidden files for the task.
- Whether the task requires a commit or is validation-only.
- Whether real gates exist.

If a setting is not visible or not controllable, do not invent it — declare only what is actually known. If the task is implementation, prefer Code mode. If the task is analysis or audit without changes, prefer Plan mode.

## Post-push verification rule

After a push or merge, ChatGPT should verify the result on GitHub directly when available before asking the user for extra local status commands. Ask the user for local commands only when GitHub cannot answer the question or when local workspace state is genuinely needed.

## Orchestrator prompt compactness rule

When preparing prompts for Claude Code, ChatGPT orchestrator must not repeat rules already versioned in `LLMS.md`, `docs/COMMANDS.md`, or `README.md`.

The prompt should tell Claude Code to read and follow those files, then include only:
- task-specific objective;
- task IDs;
- authorized/forbidden files if not already obvious;
- validation commands;
- commit/push instruction when applicable;
- new temporary constraints needed for that batch.

If a new rule should become permanent, ChatGPT orchestrator must tell the user that it should be added to the repository and must get user authorization before asking Claude Code to add it.

Keep prompts compact. Avoid bureaucratic restatements of rules already stored in the repo.

## Implementation prompt requirements

Prompts to Claude Code must include: preflight commands, explicit file scope, validation commands, git diff/status checks, and commit instructions. This ensures the user does not need to run routine commands manually.

## Auto-push authorization

Claude Code may run `git push origin main` automatically after:
- tests pass;
- commit succeeds;
- branch is main;
- workspace is clean post-commit;
- only authorized files are included;
- no reports/ artifacts committed.

Claude Code must stop before push on any blocker: dirty or misaligned workspace, branch not main, failed tests, push rejection or conflict, personal files, secrets, install, cloud/API, move/rename/delete.

## Division of labor: real gates vs. routine work

Routine commit and push can be handled by Claude Code under standing authorization. User intervention is required for: merge PRs, conflicts, installs, secrets, API/cloud, personal files, destructive operations, implementer switch, or dirty workspace.

## Final output requirement for pushed batches

Claude Code final output after an implementation batch must include:
- preflight result;
- validation result;
- files changed;
- commit hash;
- push result;
- final `git status --short --branch`;
- confirmation that reports/ and personal files were not committed.

## Task ID uniqueness rule

New tasks must use IDs not already present in the task history. If an ID is accidentally reused, correct only the tracking entry in LLMS.md — no rebase, no force-push, no history rewrite.

Tracking note: commit `a6bfade` (message: `ARCH-0065 add orchestrator prompt compactness rule`) is a micro-commit that reused the ARCH-0065 label after Batch 7 was already closed. It was committed outside the batch on the same topic. The Git history is not rewritten; it is recorded here as an out-of-band micro-commit.

## Documentation policy

Keep documentation compact. Avoid duplicate Markdown files and duplicated rules across files.
