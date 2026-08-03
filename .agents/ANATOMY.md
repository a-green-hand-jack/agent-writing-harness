# Agent Sidecar Anatomy

`.agents/` is the home for Agent-facing knowledge, skills, public tool entrypoints, policies, and short-lived coordination. It supports the paper project without becoming the Human's primary work surface.

## Current structure

- `knowledge/`: optional reference material loaded only when relevant.
- `skills/`: focused procedures for orientation, control review, decision packets, style alignment, interface maintenance, and release review.
- `tools/`: stable Agent-facing command surface.
  - `verify.sh` runs deterministic repository verification.
  - `release.sh` applies the strict Release contract, compiles, exports, validates, and independently compiles the arXiv package.
  - `check-paper-contracts.py` distinguishes flexible Draft checks from strict Release readiness.
  - `check-paper-state.py` enforces reciprocal claim/number links, scoped numeric exceptions, and actual configured venue use.
  - `check-paper-interfaces.py` verifies lightweight LaTeX interface definitions, documentation, active consumers, and generated-result hooks.
- `runtime/`: ignored session or worktree coordination state. Only `.gitignore` is durable.
- `roles/`, `workflows/`, `tool-policies/`, and `handoffs/`: existing adapter surfaces retained during migration.

## Boundary

- Human-facing contracts live at the repository root and under `paper/`.
- Current `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and explicit Human decisions override generic knowledge or adapter defaults.
- Agents load one relevant skill and the minimum related knowledge rather than recursively reading the sidecar.
- Normal LaTeX authoring and `make pdf` do not require `.agents/`.
- Draft checks allow visible uncertainty; Release checks reject active placeholders and unresolved current commitments.
- Semantic checkers validate identity, scope, configured use, and consumer consistency; they do not decide scientific truth.
- New Agent automation should enter through `.agents/tools/`; existing `scripts/` remain compatibility implementation until current capabilities and real cases can migrate with equivalent evidence.

## Context hygiene

Rich knowledge is useful only when relevant. Venue rules, release policy, experiment guidance, style knowledge, and historical rationale are loaded when the task requires them. Irrelevant context can override a current Human decision, create false constraints, or make an Agent unnecessarily cautious.
