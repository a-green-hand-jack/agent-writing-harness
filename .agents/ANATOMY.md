# Agent Sidecar Anatomy

`.agents/` contains optional Agent-facing knowledge, focused skills, tools, tests, and short-lived coordination. It supports the paper without becoming the Human's primary work surface.

## Structure

- `knowledge/`: conditional reference material. Current project contracts always take priority.
- `skills/`: focused procedures for orientation, control review, decision packets, style alignment, interface maintenance, publication planning, and release review.
- `tools/`:
  - `verify.sh` runs structure, Draft contract, interface, publication, and regression checks.
  - `release.sh` applies the strict Release contract and validates the selected canonical variant before release packaging.
  - `check-structure.py` enforces the two-layer repository boundary and canonical paper structure.
  - `check-paper-contracts.py` distinguishes flexible Draft work from strict Release readiness.
  - `check-paper-interfaces.py` verifies stable interface definitions, documentation, and active consumers.
  - `check-publication.py` verifies variants remain small, declared, safe overlays.
- `tests/`: standard-library positive and negative regressions.
- `runtime/`: ignored session or worktree coordination state; it is never durable project truth.

## Boundary

- Human-facing intent lives in root contracts.
- Authored scientific content lives in canonical `paper/` surfaces.
- Publication variants live in `paper/variants/` and contain only presentation switches.
- Agent automation and checks live in `.agents/`.
- Agents load one relevant skill and minimum context rather than recursively reading the sidecar.
- `make pdf VARIANT=<name>` and a paper-only checkout must not require `.agents/`.

## Context hygiene

Rich knowledge is useful only when relevant. Venue guidance, publication practices, experiment advice, and historical rationale are loaded on demand. Generic knowledge never overrides a current explicit Human decision.
