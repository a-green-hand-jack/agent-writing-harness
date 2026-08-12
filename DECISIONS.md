# Decisions

## DEC-0001: Evidence-first writing control plane

Decision: register contribution, claims, evidence, numbers, references, floats, notation, and release policy before treating prose as paper-facing.

Rationale: paper errors usually come from untracked factual promotion, stale numbers, citation drift, and release leakage.

## DEC-0002: Separate harness and release surfaces

Decision: `paper/` is the editing surface, release artifacts are generated under ignored `dist/`, and tracked release information lives in Markdown records under `releases/records/`.

## DEC-0003: Adopt the current paper-first template on this case branch

Decision: `case/arxiv-2505-22954` migrates to the current upstream template layout through the governed `template-adoption.py` workflow.

- Template target: `9a3db5f48c6457f045c889c2d0c81ab3ad79feaa` (main after PR #103 and #104).
- Status: adoption is `in_progress` in `.agents/template-sync.json`; no Human review has occurred, so no reviewed baseline is recorded.
- Scope of this round: template migration, Overleaf bootstrap sync, arXiv source restoration and local upload-package verification. Out of scope: venue-kit verification, arXiv upload, public release, Human review.
- The Round-1 harness control plane (`.agent/`, `.claude/`, `state/`, `lab/`, `memory/`, `human/`, `exemplars/`, `scripts/`, committed `release/`) is retired in this branch; full content remains in Git history under `case/arxiv-2505-22954` (e.g. the legacy release manifest recorded commit `8700abe611734aa4a05ed35f5260031df4062b4c`).
- The verbatim arXiv content, authorship, headline numbers, citations, figures, and tables are preserved unchanged; rendered output of the rebuilt variants must match the committed original arXiv PDF at the ordered-text level.

## DEC-0004: Reference integrity is not yet adopted

Decision: this case keeps the verbatim 195-entry `paper/refs.bib`. Reference-integrity enforcement (PUBLICATION.md policy block, activation marker, `.agents/template-sync.json.reference_integrity.adopted=true`, ledger migration) is a separate reviewed step and is not performed in this round. The Round-1 184-entry citation ledger (all `fitness_status: needs-review`) is preserved in history and noted in `EXPERIMENTS.md` and `PAPER.md` as open debt.

## DEC-0005: Overleaf and arXiv delivery policy for this round

Decision: the Overleaf project `6a7cbcb091d988c7e64e85ec` (remote `overleaf-dgm`) is a paper-only working copy synchronized with `overleaf-sync.py`. Round-1 legacy `overleaf-publish.yml` (one-way subtree push to a GitHub branch) is retired and replaced by the template tooling.

- arXiv packages are built and verified locally only; no arXiv upload is performed.
- No `Human-approved` or `release_ready` release instance is created. Overleaf web compile and arXiv platform compile remain `UNVERIFIED`.
- Bootstrap export runs from the clean protected case branch and must preserve the pre-existing Overleaf history.

## Protected evidence surface

This repository protects its current and future real-paper case branches and the corresponding case and standing verification issues: `case/arxiv-2505-22954`, `case/arxiv-2604-01658`, `case/arxiv-2605-03042`, issues #23, #24, #30, and trackers #21, #31. Never propose or perform their deletion, and never include them in routine cleanup or deletion reports.

## Recording future decisions

Append new decisions as `DEC-NNNN` sections with a decision statement and rationale; do not rewrite historical entries.
