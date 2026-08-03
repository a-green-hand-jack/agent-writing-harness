# Repository Anatomy

This repository is transitioning to a paper-first Human–Agent collaboration model while retaining the existing evidence and release harness for compatibility.

## Primary Human-facing surface

- `README.md`: direct starting point for writing and compiling the paper.
- `PAPER.md`: current paper positioning, thesis, claims, story, style, protected decisions, and unresolved questions.
- `EXPERIMENTS.md`: paper-facing experiment questions, boundaries, and result-interpretation responsibilities.
- `PAPER_INTERFACES.md`: stable semantic names used across prose, tables, figures, notation, and LaTeX macros.
- `DECISIONS.md`: durable rationale for important Human decisions.
- `paper/`: authored LaTeX source and the primary editing surface.

These files are intentionally Human-readable. They use flexible natural-language cues such as `locked`, `bounded`, `free`, and `unresolved` rather than a rigid project state machine.

## Agent sidecar

- `AGENTS.md`: thin discovery and routing entry point.
- `.agents/knowledge/`: optional reference knowledge loaded only when relevant.
- `.agents/skills/`: task-oriented procedures, beginning with paper orientation.
- `.agents/runtime/`: ignored short-lived coordination state when present.
- `.agents/roles/`, `.agents/workflows/`, `.agents/tool-policies/`, `.agents/handoffs/`: existing Codex adapter surfaces retained during migration.

Rich Agent knowledge is useful only when context is selected carefully. Current Human-facing contracts outrank generic knowledge and old adapter guidance.

## Existing compatibility harness

- `.agent/`: product-neutral doctrine, capability registry, checklists, and templates from the existing harness.
- `.claude/`: Claude Code adapter surface generated from capability semantics.
- `state/`: existing writing control plane.
- `lab/`: existing claim, evidence, result, citation, and artifact ledgers; research-lifecycle responsibilities are planned for later simplification.
- `human/`: existing briefs, reviews, decisions, and inbox surfaces.
- `memory/`: existing status, handoffs, worktree notes, and change control.
- `scripts/`: deterministic checks, exporters, and sync helpers.
- `release/`: generated TeX-only export surfaces.
- `exemplars/`: rhetorical move maps.

These paths still support current validators and release workflows. They are not the recommended starting point for a Human writing a new paper.

## Dependency direction

```text
Human decisions and paper intent
        ↓
PAPER.md / EXPERIMENTS.md / PAPER_INTERFACES.md
        ↓
paper/ authored source
        ↓
release/ generated surfaces

Agent runtime
        ↓ reads selectively
AGENTS.md → relevant .agents skill / knowledge
        ↓ operates within Human decisions
paper project and compatibility harness
```

Normal LaTeX authoring must not require Agent runtime state. Release surfaces must not expose control-plane or Agent-sidecar paths.