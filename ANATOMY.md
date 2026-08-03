# Repository Anatomy

This repository has two primary layers: one canonical authored paper and an optional Agent sidecar.

## Human and authored surface

- `README.md`: direct starting point.
- `Makefile`: Human build commands with `VARIANT=...`.
- `PAPER.md`: positioning, thesis, claims, story, style, protected decisions, and unresolved work.
- `EXPERIMENTS.md`: paper-facing experiment questions and interpretation boundaries.
- `PAPER_INTERFACES.md`: stable identity, terminology, notation, result, claim, and artifact interfaces.
- `PUBLICATION.md`: publication variants, permitted differences, and Human review boundaries.
- `DECISIONS.md`: durable rationale for important Human decisions.
- `paper/`: canonical LaTeX source and small publication overlays.

A clean copy of `paper/` must compile every supported variant independently.

## Canonical paper and variants

`paper/main.tex`, sections, figures, tables, style, references, and semantic interfaces form the canonical paper. `paper/variants/` contains only small configurations and build drivers for `draft`, `anonymous`, `camera-ready`, and `arxiv`.

Variants may control publication-facing presentation. They do not own copied sections or separate scientific content.

## Agent sidecar

- `AGENTS.md`: thin routing entrypoint.
- `.agents/knowledge/`: optional reference knowledge loaded only when relevant.
- `.agents/skills/`: focused procedures, including publication planning.
- `.agents/tools/`: structure, contract, interface, publication, verification, and release-readiness checks.
- `.agents/tests/`: positive and negative regressions.
- `.agents/runtime/`: ignored short-lived coordination state.

## Generated outputs

LaTeX build files remain local and ignored. Immutable release instances and delivery packages are generated from a selected variant by the release workflow; generated outputs are never a second authored source.

## Dependency direction

```text
Human intent and decisions
        ↓
PAPER / EXPERIMENTS / INTERFACES / PUBLICATION / DECISIONS
        ↓
paper/ canonical source + small variant overlay
        ↓
make pdf VARIANT=<name>

Agent task
        ↓
AGENTS.md → one focused skill / knowledge document
        ↓
.agents/tools/verify.sh or release workflow
```

The paper must not import `.agents/`. Generic Agent knowledge must not override a current explicit Human decision.
