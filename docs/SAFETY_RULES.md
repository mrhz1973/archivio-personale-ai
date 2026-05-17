# Safety Rules — Archivio Personale AI

These rules apply to all phases of this project. They must never be relaxed without explicit, deliberate review.

## Absolute prohibitions

- **No destructive operations** of any kind against the source archive.
- **No automatic move** — files are never moved without explicit human approval.
- **No rename** — filenames in the source archive are never changed by this system.
- **No delete** — files are never deleted by this system.
- **No overwrite** — source files are never overwritten.
- **No writing inside the source archive by default** — all outputs go to a user-specified external path.
- **No real personal files committed to Git** — the repository contains only code, documentation, tests, and example placeholder files.

## Future move phase — conditions required

A controlled move phase may only be introduced when ALL of the following are satisfied:

1. The read-only inventory and dry-run report phase is complete and reviewed.
2. A `proposed_moves.json` has been generated and manually reviewed by the user.
3. The user gives explicit approval for each batch of moves.
4. A rollback plan is in place before any move executes.

No move, rename, or delete operation shall ever be automatic or unattended.
