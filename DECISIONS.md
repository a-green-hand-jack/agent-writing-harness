# Decisions

## DEC-0001: Evidence-first writing control plane

Decision: register contribution, claims, evidence, numbers, references, floats, notation, and release policy before treating prose as paper-facing.

Rationale: paper errors usually come from untracked factual promotion, stale numbers, citation drift, and release leakage.

## DEC-0002: Separate harness and release surfaces

Decision: `paper/` is the editing surface, release artifacts are generated under ignored `dist/`, and tracked release information lives in Markdown records under `releases/records/`.

## DEC-0003: Writing-side Bridge chassis adoption-readiness preflight (issue #6)

Decision: declare `profile: writing` and record Writing-side adoption pins for the `research-writing-bridge` chassis/protocol contracts in `state/bridge-chassis.yaml` (with `state/ccfa.yaml` as the profile/pin pointer). This was a Writing-side adoption-readiness preflight, **not** upstream Bridge conformance: the Bridge chassis-spec, protocol schemas, and golden fixtures were not vendored or pinned here, and Bridge issues #3/#6/#7 remain open.

Rationale: Writing prepared to consume the Bridge chassis-spec without silently drifting from Research, kept its own implementation and paper-specific capabilities, and offered only the declarative-registry+parity pattern upstream as a governance-gated candidate. The Round-2 template adoption retired the legacy `state/` control plane; the preflight pins are preserved in Git history under `case/arxiv-2604-01658`.

## DEC-0004: Adopt the current paper-first template on this case branch

Decision: `case/arxiv-2604-01658` migrates to the current upstream template layout through the governed `template-adoption.py` workflow.

- Template target: `f7d1a37287f045913cca435738ac7e4b4d2888d0` (main after PR #103-#105).
- Status: adoption is `in_progress` in `.agents/template-sync.json`; no Human review has occurred, so no reviewed baseline is recorded.
- Scope of this round: template migration, Overleaf bootstrap sync, arXiv source restoration and local upload-package verification. Out of scope: venue-kit verification, arXiv upload, public release, Human review.
- The Round-1 harness control plane (`.agent/`, `.claude/`, `state/`, `lab/`, `memory/`, `human/`, `exemplars/`, `scripts/`, committed `release/`) is retired in this branch; full content remains in Git history under `case/arxiv-2604-01658` (legacy release manifest at commit `4a522e9549a9bdc51796d7d014e5bb8b9fff1096`).
- The verbatim arXiv content, authorship, headline numbers, citations, figures, and tables are preserved unchanged.

## DEC-0005: arXiv version identity corrected to v2

Decision: the Round-1 `paper/supplementary/source-attribution.md` and `state/ccfa.yaml` recorded arXiv `2604.01658v1`, but the recorded archive SHA-256 matches v2. This round corrects the attribution to `2604.01658v2` (latest). The committed original PDF SHA also matches v2. The v1 wording is preserved in Git history.

## DEC-0006: Reference integrity is not yet adopted

Decision: this case keeps the verbatim 50-entry `paper/refs.bib`. Reference-integrity enforcement (PUBLICATION.md policy block, activation marker, `.agents/template-sync.json.reference_integrity.adopted=true`, ledger migration) is a separate reviewed step and is not performed in this round. Round-1 citation-fitness debt stays visible.

## DEC-0007: Overleaf and arXiv delivery policy for this round

Decision: the Overleaf project `6a7cbcd4e3f0643e25365911` (remote `overleaf-coral`) is a paper-only working copy synchronized with `overleaf-sync.py`. The Round-1 legacy `overleaf-publish.yml` is retired and replaced by the template tooling.

- arXiv packages are built and verified locally only; no arXiv upload is performed.
- No `Human-approved` or `release_ready` release instance is created. Overleaf web compile and arXiv platform compile remain `UNVERIFIED`.
- Bootstrap export runs from the clean protected case branch and must preserve the pre-existing Overleaf history.

## Protected evidence surface

This repository protects its current and future real-paper case branches and the corresponding case and standing verification issues: `case/arxiv-2505-22954`, `case/arxiv-2604-01658`, `case/arxiv-2605-03042`, issues #23, #24, #30, and trackers #21, #31. Never propose or perform their deletion, and never include them in routine cleanup or deletion reports.

## Recording future decisions

Append new decisions as `DEC-NNNN` sections with a decision statement and rationale; do not rewrite historical entries.
