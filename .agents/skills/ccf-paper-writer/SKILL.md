---
name: ccf-paper-writer
description: Upstream writing engine for drafting, revision, polishing, and compression; load as a sidecar of the local `section-writing` skill, which remains the text owner.
---

# CCF Paper Writer (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-paper-writer/SKILL.md`
- Resources: any existing sibling `references/`, `scripts/`, `resources/`, `templates/`, or `assets/` directories under `.agents/vendor/ccfa-skills/ccf-paper-writer`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

`section-writing` remains the local text-owner; load this skill as the upstream writing engine and route manuscript changes through the section-writing contract.

Manuscript edits go to canonical `paper/` only through the normal section-writing flow; never create second canonical copies; citations via `citation-support-review`.

`references/table-style-guide.md` applies only to content scaffolding while drafting; final table beautification/redesign of an already-specified table belongs to `ccf-visual-composer`.

Vendored `venue-guides/` corpus is fallback only; the template's `.agents/knowledge/venues/` and official checked sources win. Vendored citation-density targets (e.g., 25-40 references) are advisory and never justify a citation that fails the `citation-support-review` Draft profile.

The vendored `exemplars/index.md` and `custom-format/default-user-format.md` files contain relative paths that are one level too deep for this vendor layout; when following them, resolve from the `ccf-paper-writer/references/` base (e.g., `custom-format/default-user-format.md`, `exemplars/cards/…`), or ask the Human to provide reference PDFs. Dead pointers to `ccf-latex-templates/…` and `paper_ref/*.pdf` are excluded resources; use this repository's `paper/` tree for from-scratch LaTeX drafting.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
