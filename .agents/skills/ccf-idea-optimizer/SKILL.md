---
name: ccf-idea-optimizer
description: Turn rough CCF research directions into concrete problem, gap, insight, method, novelty, and evidence plans. Use for idea optimization, fuzzy idea concretization, research direction shaping, salvage routes, 优化idea, 具象化idea, 研究思路优化. Do not rank or score multiple ideas as the main output.
---

# CCF Idea Optimizer (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-idea-optimizer/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-idea-optimizer`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Proposals only. Central thesis, contributions, and story changes require `control-review` and a Human decision packet.

Candidate idea documents go to ignored `.agents/runtime/` or the discussion; do not edit `PAPER.md` claims without Human approval.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
