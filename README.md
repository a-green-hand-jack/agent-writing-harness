# TODO Paper Title

A paper-first repository for Human–Agent collaborative scientific writing.

The repository should feel like a normal LaTeX paper project: read the current paper contract, edit the paper, compile it, and iterate. Agent governance, detailed checks, and legacy evidence controls support the work without becoming the Human's primary interface.

## Start writing

1. Open `PAPER.md` and record what the paper is trying to be: thesis, contributions, story, style, protected decisions, and unresolved questions.
2. Open `EXPERIMENTS.md` and record the paper-facing experiment questions and the conditions that must not change silently.
3. Edit the LaTeX source under `paper/`, starting with `paper/sections/`.
4. Compile from the paper directory:

```bash
cd paper
latexmk -pdf main.tex
```

If `latexmk` is unavailable, use the TeX workflow appropriate for the target venue. Missing tools must be reported as unverified rather than treated as a successful build.

## Human-facing entry points

- `PAPER.md` — current paper positioning, thesis, claims, story, style, flexible boundaries, and unresolved decisions.
- `EXPERIMENTS.md` — what the paper needs experiments to answer and which experimental changes require Human awareness.
- `PAPER_INTERFACES.md` — stable paper-facing names such as `\MethodName` or `\MainAccuracy`, and how Human and Agent maintain their meaning.
- `DECISIONS.md` — durable rationale for important Human decisions.
- `paper/` — the actual LaTeX paper.

The collaboration cues **locked**, **bounded**, **free**, and **unresolved** are intentionally flexible. They help Human and Agent recognize important boundaries without turning the template into a rigid state machine.

## Agent collaboration

`AGENTS.md` is a thin routing entry point. Agents should begin with the Human-facing contract, load only the knowledge or skill needed for the current task, and avoid filling the context with every policy, venue, ledger, and historical file.

The Human retains final responsibility for scientific claims, story, experiment fairness, result interpretation, interface meaning, and release approval. Agents handle retrieval, alternatives, consistency, drafting, low-risk revision, impact analysis, and focused validation.

## Draft and release

Drafts may contain explicit TODO, provisional language, and unresolved choices. Uncertainty should remain visible.

Release work is stricter: important claims, experiment interpretation, stable interfaces, venue settings, and known exceptions must be reviewed; active placeholders or silent semantic changes must not enter the submission package.

## Repository internals

The existing evidence-first harness, validators, release exporters, and adapter surfaces remain available during the transition to the paper-first model. They are compatibility infrastructure, not the recommended Human orientation path.

Agent or maintainer validation currently includes:

```bash
python scripts/check-writing-harness.py
python scripts/check-capability-parity.py
python scripts/check-paper-surface.py
bash scripts/check-latex.sh --compile
bash scripts/export-tex-release.sh
python scripts/check-release-package.py
python scripts/check-release-freshness.py
python scripts/check-arxiv-portability.py
bash scripts/check-latex.sh --compile-release arxiv
```

Release directories are generated TeX-only surfaces. Edit `paper/`, not `release/`. The ongoing simplification is tracked in issue #32; the first implementation phase is issue #39.