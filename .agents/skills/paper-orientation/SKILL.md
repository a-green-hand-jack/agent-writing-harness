# Paper Orientation Skill

Use this skill at the start of a new session or when the paper context is unclear. The goal is to recover the minimum context needed for the current task, not to load the entire repository.

## Reading order

1. Read `PAPER.md`.
2. Read `EXPERIMENTS.md` only when the task touches experiments, evidence, result interpretation, or claim support.
3. Read `PAPER_INTERFACES.md` only when the task changes recurring terminology, notation, results, claims, figures, tables, or macros.
4. Read only the relevant decisions in `DECISIONS.md`.
5. Inspect the active paper section and current Git diff.
6. Load one task-specific knowledge document or workflow.
7. Consult legacy `state/`, `lab/`, `.agent/`, `.claude/`, or adapter files only when a current validator or task requires them.

## Before a high-impact edit

Identify:

- the affected claim, story, experiment, style choice, or interface;
- whether it is locked, bounded, free, or unresolved;
- whether the change is low-risk and easy to reverse;
- whether scientific meaning, claim strength, experiment fairness, or interface meaning may change;
- whether a Human decision is needed before editing.

These control words are flexible collaboration cues. Do not turn them into a rigid state machine or use them to block ordinary low-risk work.

## Unresolved work

Unresolved is a valid working state.

- Prefer low-risk and reversible progress.
- Keep uncertainty visible.
- Offer concrete alternatives when that helps discussion.
- Ask before a high-impact or hard-to-reverse choice.
- Do not record an Agent preference as an approved Human decision.

## Human decision requests

Retrieve the context first. A useful request contains:

- the current state;
- why a decision is needed now;
- relevant constraints or previous decisions;
- concrete options when alternatives exist;
- affected claims, sections, experiments, or interfaces;
- the Agent recommendation and tradeoff.

The Human should answer a focused question rather than search the repository for context.

## Context hygiene

- Current Human-facing contracts take priority over generic knowledge.
- Load venue knowledge only for an active venue task.
- Do not read every historical file for completeness.
- Summarize applicable guidance instead of copying large policy documents into the working context.
- Surface conflicting sources rather than silently choosing one.

## Handoff

Report what changed, any high-impact semantic effect, decisions made or still unresolved, affected interfaces or experiment contracts, focused validation, and the next Human decision if one remains.