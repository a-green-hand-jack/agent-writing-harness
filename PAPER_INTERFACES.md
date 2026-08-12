# Paper Interfaces

Paper interfaces are stable paper-facing names whose meaning must not drift silently. The interface is the shared meaning, not merely the LaTeX macro.

## Why interfaces exist

A stable interface helps Human and Agent coordinate when:

- the same title, author identity, result, term, or symbol appears in several surfaces;
- a value changes while its scientific meaning is intended to remain stable;
- a term is renamed and every old consumer must be found;
- presentation differs by publication variant without changing canonical meaning.

This case is a verbatim migration of arXiv `2604.01658v2`; interface definitions were chosen so that the rendered
output stays identical to the source text.

## Keep the implementation light

The implementation is `paper/macros.tex` plus clear comments. No schema, generator, or versioning framework exists.

## Current minimal interface catalogue

- `\PaperTODO{...}` — explicit Draft-only placeholder; Release rejects active uses. No active use in this paper.
- `\PaperTitle{}` — canonical title shared by all variants.
- `\PaperAuthors{}` — canonical visible author line; anonymous variants hide it rather than redefine it.
- `\MethodName{}` — `CORAL`; the proposed method name.
- `\CoreTerm{}` — `multi-agent evolution`; the preferred recurring term for the central concept.
- `\StateSymbol{}` — `\mathcal{M}`; the shared persistent memory symbol used by the method.
- `\MainResult{}` — `3--10x higher improvement rates`; the main result under the reported primary protocol.
- `\MainResultUncertainty{}` — `not reported in the arXiv source`; the uncertainty paired with `\MainResult` is not reported and the interface keeps that omission explicit.

Each definition records meaning, practical control boundary, and Human-review trigger in `paper/macros.tex`.
The project keeps its migrated text macros `\method`, `\rowstrut`, and `\stage` in the same file.

## Interface categories

### Identity and terminology

`\PaperTitle`, `\PaperAuthors`, `\MethodName`, `\CoreTerm`. Publication variants may hide identity but must not silently redefine it.

### Notation

`\StateSymbol` is the shared persistent memory symbol from the source method section.

### Results

`\MainResult` and `\MainResultUncertainty`, together with the source-reported conditions (fixed evolutionary search baselines, no reported uncertainty).

### Claims and wording

Stable claim wording lives in `PAPER.md`; variants never copy or reword it.

### Artifacts

Figures, tables, and algorithms keep their source responsibility; `paper/figures/README.md` records the wrapper convention.

## Flexible control

Use the collaboration cues from `PAPER.md`:

- **locked** — do not change meaning silently;
- **bounded** — maintain inside the written boundary;
- **free** — implementation details may be handled autonomously;
- **unresolved** — keep uncertainty visible and choose the next step based on risk and reversibility.

All definitions here are **locked** to render identical output to the verbatim source unless the Human approves a change.

## Change workflow

When an interface changes, the Agent should:

1. distinguish presentation changes from meaning changes;
2. retrieve every consumer across canonical and variant surfaces;
3. explain effects on claims, experiments, tables, captions, conclusions, and publication versions;
4. request Human review for high-impact meaning changes;
5. update the interface and all consumers consistently;
6. report unresolved or stale uses.

## Draft and release

Drafts may contain explicit `\PaperTODO` interfaces. Before release, required interfaces must have Human-understood meaning, no active placeholder, consistent consumers, and no silent semantic or cross-variant drift.

```bash
python3 .agents/tools/check-paper-interfaces.py
python3 .agents/tools/check-paper-contracts.py --profile release
```

This case has no Human-approved release; strict Release gates remain failing-closed by design.
