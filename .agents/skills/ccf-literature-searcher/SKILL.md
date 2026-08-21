---
name: ccf-literature-searcher
description: Search and screen external literature, related work, datasets, benchmarks, citation candidates, and research opportunity maps. Use when external retrieval is the requested deliverable: literature search, related work, prior art, benchmark search, 文献检索, 相关工作. Do not own manuscript writing or full review.
---

# CCF Literature Searcher (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-literature-searcher/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-literature-searcher`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Broad discovery support; known manuscript claim support stays with `citation-support-review`.

Candidate references enter `REFERENCES.md` and the ledger only through the citation-support workflow.

Reports observed facts only (clusters, coverage, quality scores, benchmark candidates). Gap, differentiation, and rescue-route recommendations belong to `ccf-idea-optimizer`; a 'stop / pivot' verdict is a direction decision for the Human, not this skill. Citation candidates are leads only; insertion requires `citation-support-review`.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
