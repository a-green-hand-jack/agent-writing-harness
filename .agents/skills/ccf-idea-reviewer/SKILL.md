---
name: ccf-idea-reviewer
description: Strictly score, rank, compare, and triage early research ideas with prior-art awareness and venue-fit risk. Use only for explicit idea scoring, ranking, triage, 选题评分, 选题排名. Do not polish manuscripts or develop a fuzzy idea unless scoring is explicit.
---

# CCF Idea Reviewer (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-idea-reviewer/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-idea-reviewer`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Scoring is diagnostic feedback only; a score is never an acceptance probability or an approved Human decision.

Reports go to ignored `.agents/runtime/`; do not promote scores into `PAPER.md` or `DECISIONS.md` without Human review.

Ranking/selection is only performed on explicit Human request; scores are diagnostic feedback, never acceptance probabilities. A chosen direction is a Human decision via `decision-packet`.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
