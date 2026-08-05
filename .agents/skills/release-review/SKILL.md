---
name: release-review
description: Use when preparing an immutable submission, arXiv version, camera-ready version, or other Human-approved release instance.
---

# Release Review

## Trigger

Use when preparing an immutable submission, arXiv version, camera-ready version, or other Human-approved release instance.

## Minimum context

- `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and `PUBLICATION.md`;
- current applicable decisions;
- selected variant and canonical paper diff;
- release-instance record or candidate manifest;
- `.agents/knowledge/venues/<venue>-<year>.md` and its current official-source freshness when a venue is active;
- venue rules only from current official sources when a venue is involved.

Do not load historical alternatives unless a current conflict requires them.

## Procedure

1. Confirm the selected variant and permitted differences from the canonical paper.
2. If a venue is active, run `python3 .agents/tools/check-venue-knowledge.py --strict` and recheck official venue facts before relying on deadlines, page limits, anonymity, or operational rules.
3. Run the Draft and Release contract checks; do not suppress unresolved or placeholder failures.
4. List high-impact changes since the last Human review.
5. Check claim strength, experiment interpretation, stable interfaces, limitations, negative evidence, anonymity, author/acknowledgement behavior, appendix inclusion, reference-ledger Release status, claim evidence, figures, tables, and compilation.
6. Build the exact release candidate and verify its manifest and artifact checksums.
7. Mark unavailable external environments as unverified, not successful.
8. Produce a short release summary with blockers, accepted exceptions, residual risks, and an Agent recommendation.

## Human decision

Only the Human approves a release instance and accepts explicit residual risk or exceptions. Bind approval to the reviewed source revision, variant, manifest, and artifacts.
