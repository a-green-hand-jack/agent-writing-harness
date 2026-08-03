# Decisions

## DEC-0001: Paper-first two-layer repository

Decision: the repository consists of a canonical authored paper workspace and an optional Agent sidecar.

- Human intent and collaboration boundaries live in the root contracts.
- Authored LaTeX lives in `paper/` and compiles independently.
- Agent knowledge, skills, checks, and runtime coordination live in `.agents/`.

Rationale: users should start writing without learning a governance framework.

## DEC-0002: Remove the old harness and duplicate control planes

Decision: the template contains no capability registry, Bridge preflight, product-specific adapter mirror, experiment/evidence ledger, worktree governance, or duplicate Human/memory store.

Rationale: those structures duplicated Human-readable contracts and imposed a research lifecycle on the paper repository.

## DEC-0003: Flexible control cues

Decision: use `locked`, `bounded`, `free`, and `unresolved` as natural-language collaboration cues, not a rigid permission engine.

## DEC-0004: Selective Agent context

Decision: a task loads current contracts and one relevant focused skill or knowledge document. Generic knowledge never overrides an explicit current Human decision.

## DEC-0005: Stable paper-facing interfaces

Decision: recurring identity, terminology, notation, results, claims, and artifacts use lightweight Human-readable interfaces in `paper/macros.tex` and `PAPER_INTERFACES.md`.

## DEC-0006: One canonical paper with small publication overlays

Decision: `paper/` is the only canonical authored source. `paper/variants/` contains small overlays for `draft`, `anonymous`, `camera-ready`, and `arxiv`.

Variants may control author visibility, acknowledgements, appendix inclusion, and publication-facing presentation hooks. They must not copy canonical sections or silently change claims, experiment interpretation, limitations, or interface meaning.

Rationale: maintaining full paper copies or long-lived publication branches causes semantic drift and merge overhead. Small overlays make every permitted difference explicit and testable.

## DEC-0007: Variant and release instance are different concepts

Decision: a variant describes presentation rules; a release instance identifies one immutable published candidate such as `submission-r1` or `arxiv-v2` with artifacts, checks, source revision, and Human approval.

Rationale: anonymous/camera-ready/arXiv differences are not the same as revision history or delivery package format.

## Recording future decisions

Record durable, high-impact Human decisions and rationale here. Do not record every sentence edit or temporary discussion. A useful decision states what was chosen, affected paper objects, rejected alternatives when relevant, and what future change requires review.
