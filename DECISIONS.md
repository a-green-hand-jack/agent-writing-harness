# Decisions

## DEC-0001: Paper-first two-layer repository

Decision: the repository consists of a canonical authored paper workspace and an optional Agent sidecar.

- Human intent and current collaboration boundaries live in `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and `DECISIONS.md`.
- Authored LaTeX lives in `paper/` and compiles independently.
- Agent knowledge, skills, checks, and short-lived coordination live in `.agents/`.

Rationale: users should be able to start writing immediately without learning a governance framework.

## DEC-0002: Remove the old harness and duplicate control planes

Decision: delete capability registries, Bridge preflight, product-specific adapter mirrors, experiment/evidence ledgers, worktree governance, and duplicate Human/memory stores from this template.

Rationale: those structures duplicate the Human-readable contracts, impose a research lifecycle on the paper repository, and create context and maintenance overhead. The paper repository does not own code-repository experiment truth.

This decision supersedes the former evidence-first control-plane, Bridge-preflight, and compatibility-infrastructure decisions.

## DEC-0003: Flexible control cues

Decision: use `locked`, `bounded`, `free`, and `unresolved` as natural-language collaboration cues, not a rigid permission engine.

Rationale: high-impact boundaries must be visible without turning every paper object into structured state.

## DEC-0004: Selective Agent context

Decision: Agent knowledge and skills may be rich, but a task loads only the current contracts and one relevant focused skill or knowledge document.

Rationale: irrelevant context can override current Human intent, apply the wrong venue convention, or make the Agent unnecessarily cautious.

## DEC-0005: Stable paper-facing interfaces

Decision: recurring identity, terminology, notation, results, claims, and artifacts use lightweight Human-readable interfaces, primarily in `paper/macros.tex` and `PAPER_INTERFACES.md`.

Rationale: the Agent can retrieve consumers and maintain consistency while the Human retains responsibility for scientific meaning.

## Recording future decisions

Record durable, high-impact Human decisions and rationale here. Do not record every sentence edit or temporary discussion. A useful decision states what was chosen, affected paper objects, rejected alternatives when relevant, and what future change requires review.
