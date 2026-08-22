---
name: ccf-experiment-designer
description: Own experiment evidence semantics: decide datasets, baselines, metrics, ablations, robustness tests, chart evidence, and result-table schema. Use for experiment design, benchmark planning, supplied-result evidence structure, ablation, 设计实验, 对比实验, 结果表证据结构. Do not search literature as the main deliverable or invent results.
---

# CCF Experiment Designer (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-experiment-designer/SKILL.md`
- Resources: any existing sibling `references/`, `scripts/`, `resources/`, `templates/`, or `assets/` directories under `.agents/vendor/ccfa-skills/ccf-experiment-designer`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Governed by `EXPERIMENTS.md`; proposals only. Experiment fairness, primary metrics, baselines, and result interpretation remain Human decisions.

Also owned with `section-writing` for experiment/result-interpretation drafting; proposals only, and `EXPERIMENTS.md` semantics never change without a Human decision.

Candidate designs go to the active task and the Human decision process; never change `EXPERIMENTS.md` semantics without a Human decision.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
