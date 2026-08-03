# TODO Paper Title

[![PR validation](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml/badge.svg?branch=main)](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml)

A paper-first repository for Human–Agent collaborative scientific writing.

## Start writing

1. Record thesis, story, style, protected decisions, and open questions in `PAPER.md`.
2. Record paper-facing experiment questions and interpretation boundaries in `EXPERIMENTS.md`.
3. Maintain recurring terminology, notation, identity, and results through `PAPER_INTERFACES.md` and `paper/macros.tex`.
4. Record publication variants and allowed differences in `PUBLICATION.md`.
5. Edit the canonical LaTeX source under `paper/`.
6. Build the daily Draft:

```bash
make pdf
```

Build another publication variant:

```bash
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

Clean generated LaTeX files with `make clean`.

## Human-facing surface

- `PAPER.md` — current positioning, claims, story, style, protected decisions, and unresolved work.
- `EXPERIMENTS.md` — paper-facing experiment questions and interpretation boundaries.
- `PAPER_INTERFACES.md` — stable semantic names shared by prose, tables, figures, notation, and variants.
- `PUBLICATION.md` — active variants, allowed differences, and Human review triggers.
- `DECISIONS.md` — durable rationale for important Human decisions.
- `paper/` — the one canonical authored LaTeX project.

The cues **locked**, **bounded**, **free**, and **unresolved** are intentionally flexible. They support collaboration without creating a rigid state machine.

## Publication variants

`paper/variants/` contains small overlays for `draft`, `anonymous`, `camera-ready`, and `arxiv`. A variant may change author visibility, acknowledgements, appendix inclusion, and publication-facing presentation hooks. It must not copy or silently diverge scientific prose, claims, result meaning, or experiment interpretation.

Variants are not long-lived branches and not separate paper copies. Immutable release instances and delivery packages are produced by the release workflow.

## Agent sidecar

`AGENTS.md` is a thin router. Agents load the current Human-facing contract, then one focused skill or knowledge document.

```bash
bash .agents/tools/verify.sh
bash .agents/tools/release.sh
```

`verify.sh` checks structure, Draft contracts, interfaces, publication variants, and regressions. `release.sh` applies the strict Release contract and compiles the canonical publication variant selected by the workflow.

## Project boundary

The repository has no capability registry, Bridge chassis, experiment ledger, product-specific adapter mirror, or duplicate Human/memory control plane. Scientific and narrative intent remains in root contracts; authored content remains in `paper/`; Agent support remains in `.agents/`.

A clean copy of `paper/` must compile all supported variants without `.agents/`. Pull requests must pass the `harness`, variant `latex` matrix, and `paper-only` Actions jobs before merge. See `CONTRIBUTING.md`.
