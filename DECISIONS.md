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

## DEC-0006: Bundled third-party skill suites

Decision: this case adopts the template's bundled CCFA-Skills suite
(`v0.9.0`, commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`, MIT) and
writing-dna-skill (commit `d5145ef671be70d3439524b6b72f55fe06a869a9`, MIT) as
immutable snapshots under `.agents/vendor/`, exposed through thin wrappers
under `.agents/skills/` that enforce the paper-contract boundaries. All 17
`ccf-*` skills plus `writing-dna-skill` and `lieflat-less-ai-tone` are
available; bundled skills act as sidecars and never override the local owner
skill or a Human contract.

The "complete functional suite" boundary excludes copyright-ambiguous content
and non-functional assets (third-party paper PDFs/full-text reproductions,
the 71 MB `ccf-latex-templates` corpus, demo/evaluation/plugin/CI surfaces,
runtime adapter configs). Exclusions and file hashes are recorded in
`.agents/dependencies/vendored-skills/provenance.json` and verified by
`.agents/tools/check-vendored-skills.py`.

Ownership: `section-writing` remains the local text owner and runs
`ccf-paper-writer` as its writing engine; `manuscript-consistency-review`
remains Human-triggered and findings-only with `ccf-paper-reviewer` and
`ccf-integrity-auditor` as sidecars; `style-alignment` governs approval of any
Writing DNA distilled by `writing-dna-skill`. `ccf-experiment-designer` is a
sidecar of `EXPERIMENTS.md`/`section-writing` (proposals only). The vendor tree
is never edited locally; upstream updates flow through template-sync after
review. Human-facing contracts always take precedence over bundled guidance
and exemplar defaults.

Rationale: this makes the case's Agent capability layer self-contained and
verifiable while keeping the paper contracts as the single source of truth,
and avoids redistributing third-party paper content whose redistribution
rights are unverified. Adopted via template-sync target `1f5d4f1`.

## Recording future decisions

Append new decisions as `DEC-NNNN` sections with a decision statement and rationale; do not rewrite historical entries.
