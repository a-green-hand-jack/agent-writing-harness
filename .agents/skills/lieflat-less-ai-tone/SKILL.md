---
name: lieflat-less-ai-tone
description: Remove AI writing tells using an explicit whitelist of rules; leaves unmatched text untouched. Use for final manuscript cleanup after writing is complete. Applies only to listed patterns and must not change the article framework.
---

# Lieflat Less AI Tone (bundled)

Bundled from the writing-dna-skill (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/writing-dna-skill/skills/lieflat-less-ai-tone/SKILL.md`
- Resources: sibling `references/`, `scripts/`, `resources/`, `templates/`, and `assets/` directories under `.agents/vendor/writing-dna-skill/skills/lieflat-less-ai-tone`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Optional final whitelist pass; approved Writing DNA and scientific meaning take priority.

Only handles whitelisted patterns; any prose change that touches claims or meaning routes back through `section-writing`.

When both `ccf-humanization` and this skill would touch the same surface, `ccf-humanization`'s `references/humanization-policy.md` thresholds win (e.g., em-dash/openers/enumeration counts); this skill is an optional post-final whitelist pass and must not re-litigate counts already resolved. It applies to whitelisted patterns only and never changes article framework.

## Provenance

Source: https://github.com/larashero3-dotcom/writing-dna-skill at commit `d5145ef671be70d3439524b6b72f55fe06a869a9`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
