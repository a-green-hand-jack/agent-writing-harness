---
name: writing-dna-skill
description: Distill reusable writing DNA from an author, publication, or project corpus: language, article structure, topic logic, source strategy, cognitive framework, and visual style, producing Writing-DNA.md. Use for style analysis and consistent writing for Chinese or English authors, publications, brands, and accounts; in this template it is adapted for academic paper writing style.
---

# Writing DNA (bundled)

Bundled from the writing-dna-skill (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/writing-dna-skill/SKILL.md`
- Resources: any existing sibling `references/`, `scripts/`, `resources/`, `templates/`, or `assets/` directories under `.agents/vendor/writing-dna-skill`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream writing-dna-skill guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

`style-alignment` governs whether and how a distilled style is adopted; the academic adaptation rules in `.agents/knowledge/writing/README.md` apply.

Corpus lives outside Git or under ignored `.agents/runtime/writing-dna/`; the Human-reviewed Writing DNA may be promoted to `.agents/knowledge/writing/paper-writing-dna.md`, never overwriting project contracts.

## Provenance

Source: https://github.com/larashero3-dotcom/writing-dna-skill at commit `d5145ef671be70d3439524b6b72f55fe06a869a9`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
