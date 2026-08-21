---
name: ccf-pipeline-orchestrator
description: Plan and coordinate paper-project stages, goals, constraints, success criteria, gates, artifacts, and handoffs across the CCFA family. Use for workflow planning, task decomposition, stage gates, next-skill routing, 任务拆解, 流程规划. Does not itself write, review, search, or design.
---

# CCF Pipeline Orchestrator (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-pipeline-orchestrator/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/ccfa-skills/ccf-pipeline-orchestrator`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Orchestrator only; it cannot bypass any local owner skill or Human gate.

Plans must route work through the template's owner skills; do not treat `ccfa.yaml` as project state.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
