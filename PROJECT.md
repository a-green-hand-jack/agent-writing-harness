# Project

- Paper slug: `ccfa-paper-template`
- Title: TODO Paper Title
- Short title: TODO Paper
- Owner: TODO
- Venue: ICLR 2027
- Track: TODO
- Paper type: method
- Deadline: TODO
- Repo mode: standalone

## Goal

Provide a paper-first workspace where a Human and an Agent can begin writing immediately, maintain a small shared contract for claims, story, style, experiments, and stable paper interfaces, and prepare a reliable submission without allowing the Agent to silently change scientific meaning.

The Human-facing source of current intent is `PAPER.md`, with paper-facing experiment boundaries in `EXPERIMENTS.md` and stable semantic names described in `PAPER_INTERFACES.md`. The LaTeX paper remains under `paper/`.

Existing evidence-first validators and release machinery remain compatibility infrastructure during the migration. Agent knowledge and skills should be loaded selectively so that rich guidance does not pollute every task context.

## Collaboration model

- Human owns central claims, story, experiment fairness, important result interpretation, interface meaning, and release approval.
- Agent owns retrieval, alternatives, drafting, consistency maintenance, impact analysis, low-risk revision, and focused validation.
- `locked`, `bounded`, `free`, and `unresolved` are flexible collaboration cues expressed in natural language, not a rigid schema.
- Draft work may remain explicitly unresolved; release work must surface and resolve important uncertainty.

## Non-Goals

- This repo does not invent contributions or scientific results.
- This repo does not replace Human judgment with validators or workflow state.
- This repo does not verify current-year venue rules without an official source check.
- This repo does not host complex research code or a duplicate experiment lifecycle by default.
- This phase does not define the code-repository-to-paper-repository data interface.
- Bridge integration is outside the current paper-first refactor.