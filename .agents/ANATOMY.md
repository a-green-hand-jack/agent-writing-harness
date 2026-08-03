# Agent Sidecar Anatomy

`.agents/` contains optional Agent-facing knowledge, focused skills, tools, tests, and short-lived coordination. It supports the paper without becoming the Human's primary work surface.

## Structure

- `knowledge/`: conditional reference material. Current project contracts always take priority.
- `skills/`: focused procedures for orientation, control review, decision packets, style alignment, interface maintenance, publication planning, and release review.
- `tools/`:
  - `verify.sh` runs structure, Draft contract, interface, publication, release-record, and regression checks.
  - `release.sh` builds one strict immutable release instance.
  - `release.py` builds instances and writes non-overwriting release records.
  - `check-release.py` verifies manifest/artifact checksums and package boundaries.
  - `check-release-records.py` keeps tracked records Markdown-only and Human-approved where required.
  - `check-structure.py`, `check-paper-contracts.py`, `check-paper-interfaces.py`, and `check-publication.py` enforce the paper-first collaboration model.
- `tests/`: standard-library positive and negative regressions, including release immutability and checksum drift.
- `runtime/`: ignored session or worktree coordination state; never durable project truth.

## Boundary

- Human-facing intent lives in root contracts.
- Authored scientific content lives in canonical `paper/` surfaces.
- Publication variants contain only presentation switches.
- Generated release instances live in ignored `dist/` and never become authored source.
- Durable tracked release information is Markdown provenance under `releases/records/`.
- Agents load one relevant skill and minimum context rather than recursively reading the sidecar.
- `make pdf VARIANT=<name>` and a paper-only checkout do not require `.agents/`.

## Release honesty

A Draft-validation package proves the packaging mechanism, not submission readiness. Strict Release requires the Release contract to pass. Real Overleaf import, official venue upload, and arXiv platform compilation remain unverified until actually exercised.

## Context hygiene

Rich knowledge is useful only when relevant. Venue guidance, publication practices, experiment advice, and historical rationale are loaded on demand. Generic knowledge never overrides a current explicit Human decision.
