# Paper Orientation Skill

Use this skill at the start of a new session or when paper context is unclear. Recover the minimum context needed for the current task; do not load the entire repository.

## Reading order

1. Read `PAPER.md`.
2. Read `EXPERIMENTS.md` only when the task touches experiments, evidence, result interpretation, or claim support.
3. Read `PAPER_INTERFACES.md` only when the task changes recurring terminology, notation, results, claims, figures, tables, or macros.
4. Read only relevant decisions in `DECISIONS.md`.
5. Inspect the active paper section and current Git diff.
6. Load one task-specific skill or knowledge document.

## Before a high-impact edit

Identify:

- the affected claim, story, experiment, style choice, or interface;
- whether it is locked, bounded, free, or unresolved;
- whether the change is low-risk and easy to reverse;
- whether scientific meaning, claim strength, experiment fairness, or interface meaning may change;
- whether a Human decision is needed before editing.

The control words are collaboration cues, not a rigid state machine.

## Unresolved work

- Prefer low-risk and reversible progress.
- Keep uncertainty visible.
- Offer concrete alternatives when useful.
- Ask before a high-impact or hard-to-reverse choice.
- Never record an Agent preference as approved Human intent.

## Human decision requests

Retrieve context first. A useful request contains the current state, why a decision is needed, relevant constraints, concrete options, affected surfaces, and the Agent recommendation with tradeoffs.

The Human should answer a focused question rather than search the repository.

## Context hygiene

- Current Human-facing contracts take priority over generic knowledge.
- Load venue knowledge only for an active venue task.
- Do not read every historical file for completeness.
- Summarize applicable guidance instead of copying large documents into working context.
- Surface conflicting sources rather than silently choosing one.

## Handoff

Report changes, high-impact semantic effects, decisions made or unresolved, affected interfaces or experiment contracts, focused validation, and the next Human decision when one remains.
