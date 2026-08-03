# Repository Anatomy

This repository is a paper-first Human–Agent collaboration project with an Agent sidecar and a retained compatibility harness.

## Primary Human-facing surface

- `README.md`: direct starting point.
- `Makefile`: simple `make pdf` and `make clean` interface.
- `PAPER.md`: positioning, thesis, claims, story, style, protected decisions, and unresolved questions.
- `EXPERIMENTS.md`: paper-facing experiment questions, boundaries, and interpretation responsibilities.
- `PAPER_INTERFACES.md`: stable semantic names used across prose, tables, figures, notation, and LaTeX macros.
- `DECISIONS.md`: durable rationale for important Human decisions.
- `paper/`: authored LaTeX source and primary editing surface.

The Human build depends only on the normal LaTeX project. A clean copy of `paper/` must compile without `.agents/`, `state/`, `lab/`, or `scripts/`.

## Agent sidecar

- `AGENTS.md`: thin discovery and routing entry point.
- `.agents/knowledge/`: optional reference knowledge loaded only when relevant.
- `.agents/skills/`: focused task procedures.
- `.agents/tools/verify.sh`: stable deterministic verification entrypoint.
- `.agents/tools/release.sh`: strict Release contract, compilation, export, package checks, and isolated arXiv compilation.
- `.agents/tools/check-*.py`: focused Human–Agent contract and paper-state checks.
- `.agents/runtime/`: ignored short-lived coordination state.
- `.agents/roles/`, `.agents/workflows/`, `.agents/tool-policies/`, `.agents/handoffs/`: existing adapter surfaces retained during migration.

Current Human-facing contracts outrank generic knowledge and old adapter guidance. New Agent-facing orchestration belongs behind `.agents/tools/` or a focused skill rather than adding more Human commands.

## Compatibility implementation

- `.agent/`: existing doctrine and capability registry.
- `.claude/`: existing Claude adapter surface.
- `state/`: legacy writing control plane required by current capabilities and real-paper cases.
- `lab/`: legacy claim, evidence, result, citation, and artifact ledgers.
- `human/`: legacy briefs, reviews, decisions, and inbox surfaces.
- `memory/`: legacy status, handoff, worktree, and change-control surfaces.
- `scripts/`: deterministic implementation used by the stable `.agents/tools/` entrypoints.
- `release/`: generated TeX-only export surfaces.
- `exemplars/`: rhetorical move maps.

These paths remain while existing capabilities and real cases depend on them. They are not the Human navigation model and are not the default growth surface for new paper-first features. Deletion or migration requires equivalent CI and case evidence.

## Dependency direction

```text
Human intent and decisions
        ↓
PAPER.md / EXPERIMENTS.md / PAPER_INTERFACES.md
        ↓
paper/ authored source ── make pdf ──> paper/main.pdf
        ↓
release/ generated surfaces

Agent runtime
        ↓ reads selectively
AGENTS.md → focused skill / knowledge
        ↓ invokes stable interfaces
.agents/tools/verify.sh or .agents/tools/release.sh
        ↓ compatibility implementation
scripts/ + current state/lab surfaces
```

Release surfaces must not expose control-plane or Agent-sidecar paths. CI independently proves the full harness, real release builds, and paper-only compilation.