# Publication Planning

## Trigger

Use when adding, changing, comparing, or preparing a publication variant such as anonymous submission, camera-ready, arXiv, supplement, or rebuttal.

## Minimum context

- `PUBLICATION.md`;
- `PAPER.md` and relevant decisions;
- `PAPER_INTERFACES.md` when a result, term, notation, claim, or artifact could differ;
- the affected variant config and canonical paper surface.

Do not load unrelated venue knowledge until a concrete venue is active.

## Procedure

1. Identify whether the request changes the canonical paper, a publication-facing overlay, or a future package target.
2. Keep scientific and narrative changes in the canonical paper; use variants only for approved presentation differences.
3. List every difference from the canonical paper and classify it as allowed, Human-review required, or forbidden.
4. Prefer a small switch/config change over copied sections or long-lived branches.
5. Build every affected variant and inspect anonymity, author, acknowledgement, appendix, and interface behavior.
6. Update `PUBLICATION.md`, the checker, tests, and CI matrix when the set of variants changes.
7. Report external venue or platform behavior as unverified unless actually exercised.

## Human decision

The Human approves active variants, permitted differences, scientific exceptions, and publication of an immutable release instance.
