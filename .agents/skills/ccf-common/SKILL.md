---
name: ccf-common
description: Shared governance for the CCFA family: routing, trigger registry, task modes, handoff modes, source registry, privacy/evidence policy, and artifact contracts. Use only when maintaining or auditing CCFA skills; not for ordinary research tasks.
---

# CCF Common (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-common/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-common`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Support package for the bundled CCFA skills; it is not a primary task skill and must not be auto-loaded for ordinary paper work.

Read-only within the template. If an upstream CCFA workflow would write a ccfa.yaml or second project state, do not create it; the template's root contracts are the single source of truth.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
