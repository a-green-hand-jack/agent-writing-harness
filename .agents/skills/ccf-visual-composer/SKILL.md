---
name: ccf-visual-composer
description: Own rendered visuals and visual redesign from supplied content or values: plot, beautify, lay out, generate, reconstruct, and QA paper figures, visual tables, diagrams, icons, palettes, and editable SVG/PDF/PPTX. Use for result-table layout, 绘图美化, 排版, architecture diagrams. Do not choose datasets/baselines or invent content.
---

# CCF Visual Composer (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-visual-composer/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-visual-composer`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Candidate output first; promotion into `paper/figures/` follows the paper-interface and manuscript ownership rules.

Generated figures are candidates under ignored `.agents/runtime/` until Human review; captions and interface names come from `PAPER_INTERFACES.md`.

Table beautification/redesign of an already-specified result table is this skill's deliverable (not ccf-paper-writer's table-style-guide, which is drafting-only). Caption wording after layout is this skill's; caption facts/claims must come from supplied values (`ccf-experiment-designer` semantics), never invented.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
