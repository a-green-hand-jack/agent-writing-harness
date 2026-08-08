# Agent Knowledge

This directory contains optional reference knowledge for Agent tasks. It is not a checklist that every session must load.

## Context hygiene

Load the smallest useful context for the current task.

- Start from `AGENTS.md` and the current Human-facing contract.
- Load one relevant skill before broad knowledge documents.
- Read only the knowledge that the selected skill names or that a concrete problem requires.
- Do not load every venue, workflow, policy, historical decision, and ledger “just in case.”
- Prefer current project decisions over generic writing advice.
- Summarize retrieved context before acting when several sources interact.

Context pollution is a correctness risk: irrelevant constraints can make an Agent over-cautious, apply the wrong venue convention, or overlook the Human's current decision.

## Knowledge classes

### Strong principles

These normally apply across tasks:

- do not invent facts, results, citations, or Human approval;
- do not turn correlation into causation;
- do not silently change a locked scientific or narrative commitment;
- keep uncertainty and negative evidence visible when they constrain a central claim;
- report unverified checks honestly.

### Heuristics

Writing and organization advice is usually conditional. A heuristic must not override `PAPER.md`, `EXPERIMENTS.md`, `DECISIONS.md`, or a current Human instruction.

`scientific-writing.md` contains section-specific drafting guidance. Load only the active section's guidance; do not use it as a reason to interrupt drafting with a manuscript-wide review.

Examples:

- a gap-first introduction can be effective;
- experimental paragraphs often benefit from question → result → interpretation;
- captions should usually be understandable without searching the body.

These are options, not universal rules.

### Venue knowledge

Load venue-specific knowledge only when venue adaptation is the active task. Distinguish stable observations about audience and style from current official requirements, which must be checked against an official source at the time of submission work.

Active venue planning facts live in `.agents/knowledge/venues/<venue>-<year>.md`. See `.agents/knowledge/venues/README.md` for the schema, freshness contract, and strict verification entry point.

## Project truth priority

When sources conflict, prefer:

1. the latest explicit Human decision;
2. current `PAPER.md` / `EXPERIMENTS.md` / `PAPER_INTERFACES.md` contracts;
3. applicable durable rationale in `DECISIONS.md`;
4. task-specific skill guidance;
5. general knowledge and heuristics;
6. Agent preference or inference.

Runtime notes and chat context do not silently become durable project truth.
