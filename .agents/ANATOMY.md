# Agent Sidecar Anatomy

`.agents/` is the gradual home for Agent-facing knowledge, skills, workflows, policies, and short-lived coordination. It must support the paper project without becoming the Human's primary work surface.

## Current structure

- `knowledge/`: optional reference material. Load only what the active task needs.
- `skills/`: reusable task procedures. `paper-orientation` defines the minimal context-recovery path for a new session.
- `roles/`, `workflows/`, `tool-policies/`, and `handoffs/`: existing Codex adapter surfaces that mirror `.agent/capabilities/`; retained for compatibility during the refactor.
- `runtime/`: ignored session or worktree coordination state when present; it is not durable project truth.

## Boundary

- The Human-facing paper contract lives at the repository root and under `paper/`, not inside `.agents/`.
- Current `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and explicit Human decisions override generic knowledge or adapter defaults.
- Agents should load one relevant skill and the minimum related knowledge rather than recursively reading the sidecar.
- Normal LaTeX authoring and compilation must not require `.agents/` runtime state.
- Tool and adapter migration into this sidecar is incremental; existing `.agent/`, `.claude/`, `scripts/`, `state/`, and `lab/` paths remain until separate changes preserve current validation and release behavior.

## Context hygiene

The sidecar may contain rich knowledge, but more context is not automatically better. Venue-specific rules, release policy, experiment guidance, style knowledge, and historical rationale should be loaded only when the task makes them relevant. Irrelevant context can override the current Human decision, create false constraints, or make an Agent overly cautious.