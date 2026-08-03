# Repository Anatomy

This repository has two primary layers: the authored paper workspace and an optional Agent sidecar.

## Human and authored surface

- `README.md`: direct starting point.
- `Makefile`: simple Human build commands.
- `PAPER.md`: positioning, thesis, claims, story, style, protected decisions, and unresolved work.
- `EXPERIMENTS.md`: paper-facing experiment questions and interpretation boundaries.
- `PAPER_INTERFACES.md`: stable terminology, notation, result, claim, and artifact interfaces.
- `DECISIONS.md`: durable rationale for important Human decisions.
- `paper/`: canonical LaTeX source.

A clean copy of `paper/` must compile independently.

## Agent sidecar

- `AGENTS.md`: thin routing entrypoint.
- `.agents/knowledge/`: optional reference knowledge loaded only when relevant.
- `.agents/skills/`: focused task procedures.
- `.agents/tools/`: verification, release-readiness, structure, contract, and interface checks.
- `.agents/tests/`: positive and negative regression tests for the Agent-facing tools.
- `.agents/runtime/`: ignored short-lived coordination state.

There is no separate capability registry, experiment ledger, Bridge layer, product-specific adapter mirror, or duplicate Human/memory control plane.

## Generated outputs

- LaTeX build files remain local and ignored.
- Publication variants and release instances are generated from the canonical paper through the publication workflow.
- Generated output is never a second authored source.

## Dependency direction

```text
Human intent and decisions
        ↓
PAPER.md / EXPERIMENTS.md / PAPER_INTERFACES.md / DECISIONS.md
        ↓
paper/ canonical authored source ── make pdf ──> paper/main.pdf

Agent task
        ↓
AGENTS.md → one focused skill / knowledge document
        ↓
.agents/tools/verify.sh or .agents/tools/release.sh
```

The paper must not import files from `.agents/`. Agent knowledge must not override a current explicit Human decision.
