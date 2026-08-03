# Agent Sidecar Anatomy

`.agents/` contains optional Agent-facing knowledge, focused skills, tools, tests, and short-lived coordination. It supports the paper without becoming the Human's primary work surface.

## Structure

- `knowledge/`: conditional reference material. Current project contracts always take priority.
- `skills/`: focused procedures for orientation, control review, decision packets, style alignment, interface maintenance, and release review.
- `tools/`:
  - `verify.sh` runs paper-first structure, Draft contract, interface, and regression checks.
  - `release.sh` applies the strict Release contract and compiles the canonical paper.
  - `check-structure.py` enforces the two-layer repository boundary and paper source structure.
  - `check-paper-contracts.py` distinguishes flexible Draft work from strict Release readiness.
  - `check-paper-interfaces.py` verifies stable interface definitions, documentation, and active consumers.
- `tests/`: standard-library positive and negative regressions for the tool surface.
- `runtime/`: ignored session or worktree coordination state; it is never durable project truth.

## Boundary

- Human-facing intent lives in the root contracts.
- Authored content lives in `paper/`.
- Agent automation and checks live in `.agents/`.
- The sidecar contains no capability registry, Bridge contract, experiment ledger, product adapter mirror, or duplicate Human/memory store.
- Agents load one relevant skill and minimum context rather than recursively reading the sidecar.
- `make pdf` and a paper-only checkout must not require `.agents/`.

## Context hygiene

Rich knowledge is useful only when relevant. Venue guidance, release practices, experiment advice, and historical rationale are loaded on demand. Generic knowledge never overrides a current explicit Human decision.
