# Agent Sidecar Anatomy

`.agents/` is the gradual home for Agent-facing knowledge, skills, tools, workflows, policies, and short-lived coordination. It supports the paper project without becoming the Human's primary work surface.

## Current structure

- `knowledge/`: optional reference material. Load only what the active task needs.
- `skills/`: reusable focused procedures. Orientation, control review, decision packets, style alignment, interface maintenance, and release review each declare a trigger and minimum context.
- `tools/`: Agent-facing checks and helpers. `check-paper-contracts.py` distinguishes flexible Draft checks from strict Release readiness without turning the contracts into a schema.
- `runtime/`: ignored session or worktree coordination state. Only `.gitignore` is durable; runtime notes are not project truth.
- `roles/`, `workflows/`, `tool-policies/`, and `handoffs/`: existing Codex adapter surfaces that mirror `.agent/capabilities/`; retained for compatibility during the refactor.

## Boundary

- The Human-facing paper contract lives at the repository root and under `paper/`, not inside `.agents/`.
- Current `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and explicit Human decisions override generic knowledge or adapter defaults.
- Agents load one relevant skill and the minimum related knowledge rather than recursively reading the sidecar.
- Normal LaTeX authoring and compilation do not require `.agents/` runtime state.
- Draft checks allow visible uncertainty; Release checks reject active placeholders and unresolved current commitments.
- Tool and adapter migration into this sidecar is incremental; existing `.agent/`, `.claude/`, `scripts/`, `state/`, and `lab/` paths remain until separate changes preserve current validation and release behavior.

## Context hygiene

Rich knowledge is useful only when relevant. Venue rules, release policy, experiment guidance, style knowledge, and historical rationale are loaded when the current task requires them. Irrelevant context can override a current Human decision, create false constraints, or make an Agent unnecessarily cautious.
