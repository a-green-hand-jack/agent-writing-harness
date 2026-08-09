---
name: decision-packet
description: Use when a Human must choose among high-impact alternatives or approve a change outside a bounded area.
---

# Decision Packet

## Trigger

Use when a Human must choose among high-impact alternatives or approve a change outside a bounded area.

## Minimum context

- the current contract entry;
- the latest applicable decision in `DECISIONS.md`;
- directly affected paper sections, experiments, and interfaces;
- concrete evidence or constraints needed for this decision.

Do not include exhaustive search logs or unrelated history.

## Procedure

Prepare one focused packet:

- **Question** — the single decision needed now.
- **Why now** — the blocker or opportunity.
- **Current state** — what is presently approved or unresolved.
- **Options** — genuinely different choices and their consequences.
- **Affected surfaces** — claims, sections, experiments, interfaces, limitations, release.
- **Recommendation** — a neutral recommendation grounded in stated criteria, evidence, and tradeoffs; do not present Agent preference as approval.
- **Unchanged scope** — what this decision will not alter.

<!-- paper-skill-contract: F7-DP-001-v1 -->
Do not bundle independent semantic choices into one approval gate. Prepare a separate focused packet and use a separate Human approval gate for each.

After the Human answers, update the current contract and durable rationale; do not leave the decision only in chat or runtime notes.

## Human decision

The Human decides scientific commitments, story direction, experiment fairness, result interpretation, claim degradation, and release acceptance.
