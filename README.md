# TODO Paper Title

A paper-first repository for Human–Agent collaborative scientific writing.

The repository behaves like a normal LaTeX paper project. Human-facing contracts explain what the paper is trying to say; Agent knowledge, checks, and release tooling stay in the `.agents/` sidecar.

## Start writing

1. Open `PAPER.md` and record the thesis, contributions, story, style, protected decisions, and unresolved questions.
2. Open `EXPERIMENTS.md` and record the paper-facing experiment questions and conditions that must not change silently.
3. Edit `paper/sections/` and the stable interfaces in `paper/macros.tex`.
4. Build the paper:

```bash
make pdf
```

Clean generated LaTeX files with:

```bash
make clean
```

The Human build uses only the normal `paper/` project. It does not load Agent runtime state, research ledgers, or release tooling.

## Human-facing entry points

- `PAPER.md` — current positioning, thesis, claims, story, style, flexible boundaries, and unresolved decisions.
- `EXPERIMENTS.md` — what experiments need to answer and which changes require Human awareness.
- `PAPER_INTERFACES.md` — stable paper-facing names and how Human and Agent maintain their meaning.
- `DECISIONS.md` — durable rationale for important Human decisions.
- `paper/` — the actual LaTeX source.

The cues **locked**, **bounded**, **free**, and **unresolved** are intentionally flexible. They help Human and Agent recognize important boundaries without turning the template into a rigid state machine.

## Agent collaboration

`AGENTS.md` is a thin router. Agents begin with the Human-facing contracts, then load one relevant skill or knowledge document rather than every policy, venue, ledger, and historical file.

Stable Agent entrypoints are:

```bash
bash .agents/tools/verify.sh
bash .agents/tools/release.sh
```

`verify.sh` runs the current deterministic checks. `release.sh` first applies the strict Release contract, then compiles, exports, validates, and independently compiles the arXiv package. The unresolved factory template is expected to fail the Release contract until a real paper is ready.

The Human retains final responsibility for scientific claims, story, experiment fairness, result interpretation, interface meaning, and release approval. Agents handle retrieval, alternatives, consistency, drafting, low-risk revision, impact analysis, and focused validation.

## Draft and release

Drafts may contain explicit TODOs, provisional language, and unresolved choices. Uncertainty should remain visible.

Release work is stricter: important claims, experiment interpretation, stable interfaces, venue settings, and known exceptions must be reviewed; active placeholders or silent semantic changes must not enter the submission package.

## Compatibility internals

`state/`, `lab/`, `.agent/`, `.claude/`, and `scripts/` remain temporarily because existing capabilities, real-paper cases, and release regressions depend on them. They are compatibility implementation, not the Human's navigation model or the default place for new paper-first features.

Release directories are generated TeX-only surfaces. Edit `paper/`, not `release/`. Pull requests are validated by deterministic checks, real TeX compilation, isolated arXiv compilation, and a paper-only build that removes the Agent and legacy control surfaces.
