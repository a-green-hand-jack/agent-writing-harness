---
name: ccf-rebuttal-writer
description: Write and organize conference rebuttals, author responses, response letters, revision summaries, reviewer-comment ledgers, and conservative resubmission adaptation plans. Use for rebuttal, author response, revision ledger, resubmission, 审稿意见回复. Do not trigger for ordinary manuscript writing.
---

# CCF Rebuttal Writer (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-rebuttal-writer/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-rebuttal-writer`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Requires an active rebuttal publication context and follows `section-writing` boundaries for any manuscript-adjacent edits.

Response documents are candidates under ignored `.agents/runtime/` until Human review; do not overwrite release records.

`resubmission` mode changes the active variant/venue; `publication-planning` owns that decision and `PUBLICATION.md` gates it. This skill drafts the response/revision ledger only.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
