---
name: ccf-integrity-auditor
description: Audit paper integrity: numeric and terminology consistency, result-to-claim numeric agreement, and figure/table-to-text consistency. Use for evidence audit, numeric audit, consistency check, 数字一致性. Do not perform full scientific review or citation audit.
---

# CCF Integrity Auditor (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-integrity-auditor/SKILL.md`
- Resources: any existing sibling `references/`, `scripts/`, `resources/`, `templates/`, or `assets/` directories under `.agents/vendor/ccfa-skills/ccf-integrity-auditor`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Routes citation issues to `citation-support-review` and `reference-repair`; manuscript-wide use remains Human-triggered.

Findings only by default; repair happens through the local reference-ledger contracts, never by silently editing `paper/refs.bib`.

Vendor modes `citation-audit` and the claim-support portion of `claim-audit` are disabled in this template: claim-support verdicts belong to `citation-support-review` (and the `references/ledger.json` Human-confirmation gate), BibTeX metadata/duplicate repair belongs to `reference-repair`. Run this skill for `numeric-audit` and result-to-claim numeric consistency only.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
