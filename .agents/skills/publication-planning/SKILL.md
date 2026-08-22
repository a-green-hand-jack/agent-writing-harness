---
name: publication-planning
description: Use when adding, changing, comparing, or preparing a publication variant such as `anonymous`, `camera-ready`, or `arxiv`; rebuttal drafting is handled by `ccf-rebuttal-writer`.
---

# Publication Planning

## Trigger

Use when adding, changing, comparing, or preparing a publication variant such as `anonymous`, `camera-ready`, or `arxiv`; rebuttal drafting is handled by `ccf-rebuttal-writer`.

## Minimum context

- `PUBLICATION.md`;
- `PAPER.md` and relevant decisions;
- `PAPER_INTERFACES.md` when a result, term, notation, claim, or artifact could differ;
- `.agents/knowledge/venues/README.md` and the active `<venue>-<year>.md` file when venue planning, deadlines, page budget, or official submission rules are involved;
- the affected variant config and canonical paper surface.

Do not load unrelated venue knowledge until a concrete venue is active.

## Procedure

1. Identify whether the request changes the canonical paper, a publication-facing overlay, or a future package target.
2. If a venue is active, load its venue knowledge file and verify the official sources and `last_checked` before treating deadlines, page limits, anonymity, or operational rules as current constraints.
3. Keep scientific and narrative changes in the canonical paper; use variants only for approved presentation differences.
4. List every difference from the canonical paper and classify it as allowed, Human-review required, or forbidden.
5. Treat official venue deadlines and limits as hard constraints. Derive internal writing, experiment, review, and approval buffers without labeling them official deadlines.
6. For template, page-limit, or anonymity compliance, load `.agents/skills/ccf-submission-checker/SKILL.md` as the compliance sidecar; official current venue rules still prevail over any checker verdict.
7. Prefer a small switch/config change over copied sections or long-lived branches.
8. Build every affected variant and inspect anonymity, author, acknowledgement, appendix, and interface behavior.
9. Update `PUBLICATION.md`, venue knowledge, the checker, tests, and CI matrix when the set of variants or active venue facts changes.
10. Report external venue or platform behavior as unverified unless actually exercised.

## Human decision

The Human approves active variants, permitted differences, scientific exceptions, and publication of an immutable release instance.
