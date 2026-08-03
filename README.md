# TODO Paper Title

[![PR validation](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml/badge.svg?branch=main)](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml)

A paper-first repository for Human–Agent collaborative scientific writing.

## Start writing

1. Record the paper thesis, story, style, protected decisions, and open questions in `PAPER.md`.
2. Record paper-facing experiment questions and interpretation boundaries in `EXPERIMENTS.md`.
3. Maintain recurring terminology, notation, and results through `PAPER_INTERFACES.md` and `paper/macros.tex`.
4. Edit the LaTeX source under `paper/`.
5. Build with:

```bash
make pdf
```

Clean generated LaTeX files with `make clean`.

## Human-facing surface

- `PAPER.md` — current positioning, claims, story, style, protected decisions, and unresolved work.
- `EXPERIMENTS.md` — paper-facing experiment questions and interpretation boundaries.
- `PAPER_INTERFACES.md` — stable semantic names shared by prose, tables, figures, and notation.
- `DECISIONS.md` — durable rationale for important Human decisions.
- `paper/` — the authored LaTeX project.

The cues **locked**, **bounded**, **free**, and **unresolved** are intentionally flexible. They support collaboration without creating a rigid state machine.

## Agent sidecar

`AGENTS.md` is a thin router. Agents load the current Human-facing contract, then one focused skill or knowledge document.

Stable Agent entrypoints:

```bash
bash .agents/tools/verify.sh
bash .agents/tools/release.sh
```

`verify.sh` checks the paper-first structure, Draft contract, stable interfaces, and Agent-side regressions. `release.sh` applies the strict Release contract and compiles the canonical paper; publication variants and immutable release packages are managed by the dedicated publication workflow.

## Project boundary

The repository has no capability registry, Bridge chassis, experiment ledger, product-specific adapter mirror, or duplicate Human/memory control plane. Scientific and narrative intent remains in the root contracts; authored content remains in `paper/`; Agent support remains in `.agents/`.

A clean copy of `paper/` must compile without `.agents/` or any repository tooling. Pull requests must pass the `harness`, `latex`, and `paper-only` Actions jobs before merge. See `CONTRIBUTING.md`.
