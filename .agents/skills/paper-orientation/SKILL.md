---
name: paper-orientation
description: Use at the start of a new session or when paper context is unclear to recover minimum context without loading the repository.
---

# Paper Orientation Skill

Use this skill at the start of a new session or when paper context is unclear. Recover the minimum context needed for the current task; do not load the entire repository.

## Repository role and lifecycle gate

Before choosing a downstream-repository workflow, inspect the repository root,
current branch, worktree status, origin remote, and initialization marker:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
python3 .agents/tools/paper-init.py status
```

Classify the observed state before editing or running initialization commands:

- `upstream_template`: origin is exactly `a-green-hand-jack/ccfa-writing-paper-template` and the initialization marker is absent. A new paper must use the template-create mode of `ccf-project-scaffolder`; do not write paper content here.
- uninitialized template-created downstream: `.agents/template-origin.json` is a valid repository-bound attestation verified through GitHub's `template_repository` field, its origin is not the upstream template, and the initialization marker is absent. Run downstream initialization before paper work.
- initialized downstream: the provenance attestation and initialization marker are valid, and `.agents/template-sync.json` identifies the configured upstream template. Use ordinary paper workflows; use `template-sync` for later upstream infrastructure updates.
- adoption in progress: `.agents/template-sync.json` exists with `adoption.status: in_progress`. Resume `template-adoption`; do not route to ordinary writing or `template-sync` until reviewed finalization.
- unrelated or ambiguous existing paper repository: there is no positive GitHub Template provenance or reviewed adoption state. Use `template-adoption`, not template creation or ordinary sync.

If the remote, marker, and repository contents disagree, stop and report the
exact conflict. `paper-init.py status` reporting `downstream` is not positive
evidence that the repository came from this GitHub Template. Never infer a
writing-repository identity from the directory name, branch name, copied
template files, a non-upstream origin, or a marker without matching provenance;
an initialized state additionally requires template-sync metadata. The three downstream lifecycle
variants share this gate but own different transitions:

- `ccf-project-scaffolder` in template-create mode creates and initializes a new writing repository;
- `template-adoption` maps an unrelated existing paper repository and records its first reviewed baseline;
- `template-sync` applies reviewed upstream changes after initialization or adoption.

## First-session packet

For a new writing repository, collect only the material needed to begin paper
work. Repository identity, GitHub ownership, visibility, destination, and
initialization facts are operational inputs; the Human's paper packet is:

```text
Research seed: problem, setting, and proposed idea or insight
Evidence available: code, data, results, figures, prior draft, references, or "none yet"
Target: venue/year/track and deadline, or "unresolved"
Authors and identity: author list plus anonymity or disclosure constraints
First deliverable: idea clarification, evidence plan, outline, or a named section draft
Constraints: language, length, compute/data limits, style examples, and locked decisions
```

With no evidence, limit work to initialization, clarification, an evidence plan,
or an outline. A section draft requires supplied or Human-approved claims and
evidence for that section. Never invent a method, result, contribution,
citation, authorship, venue choice, or approval state.

## Reading order

1. Read `PAPER.md`.
2. Read `EXPERIMENTS.md` only when the task touches experiments, evidence, result interpretation, or claim support.
3. Read `PAPER_INTERFACES.md` only when the task changes recurring identity, terminology, notation, results, claims, figures, tables, or macros.
4. Read `PUBLICATION.md` only when the task touches variants, venues, delivery targets, or release instances.
5. Read only relevant decisions in `DECISIONS.md`.
6. Inspect the active paper section and current Git diff.
7. Load one primary owner skill plus any explicitly permitted sidecar skills (for example a bundled CCFA wrapper); never load the whole family.

## Before a high-impact edit

Identify:

- the affected claim, story, experiment, style choice, interface, or publication variant;
- whether it is locked, bounded, free, or unresolved;
- whether the change is low-risk and easy to reverse;
- whether scientific meaning, claim strength, experiment fairness, interface meaning, or cross-version consistency may change;
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

Report changes, high-impact semantic effects, decisions made or unresolved, affected interfaces, variants or experiment contracts, focused validation, and the next Human decision when one remains.
