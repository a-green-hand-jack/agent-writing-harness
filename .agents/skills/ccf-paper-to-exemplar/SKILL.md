---
name: ccf-paper-to-exemplar
description: Convert user-provided conference paper PDFs into distilled writing exemplar cards for the ccf-paper-writer skill. Extracts full text, analyzes writing patterns by venue, and produces ready-to-use exemplar cards. Use for PDF to writing exemplar, custom writing exemplars, reusable writing templates. Do not render figures.
---

# CCF Paper To Exemplar (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-paper-to-exemplar/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-paper-to-exemplar`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Writes candidate cards outside the immutable vendor tree; no full-text source copying into Git.

Source PDFs live outside Git or under ignored `.agents/runtime/writing-dna/`; cards are candidates until Human review.

The vendored save-path steps do not apply: write candidate cards to ignored `.agents/runtime/writing-dna/cards/` and register them in a local index there; the `ccf-paper-writer` wrapper loads local cards before vendor defaults. Never write into `.agents/vendor/`.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
