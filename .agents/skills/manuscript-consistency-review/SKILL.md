---
name: manuscript-consistency-review
description: Use when the Human identifies a completed manuscript version as ready and requests a findings-only consistency review.
---

# Manuscript Consistency Review

## Trigger

Use only after the Human identifies a manuscript version as ready for review.
Do not invoke this workflow while any section of that version is being drafted,
after completing an individual section, or merely because a file was edited or
built.

This is a consistency review, not an anonymous peer-review simulation, novelty
score, accept/reject recommendation, or mandatory gate between writing steps.

## Minimum context

Read in this order:

1. `PAPER.md`;
2. `EXPERIMENTS.md` for experimental claims, conditions, results, and maximum
   interpretations;
3. `PAPER_INTERFACES.md` and `paper/macros.tex` for recurring semantic surfaces;
4. the complete canonical source graph for that manuscript version;
5. relevant figures, tables, captions, bibliography entries, and reference
   ledger records consumed by that scope;
6. only durable decisions needed to resolve an apparent conflict.

Do not load publication variants or release records unless the Human includes
them in the review scope.

## Procedure

1. Record the reviewed version and identify incomplete or unavailable surfaces that
   limit the review. Explicit placeholders are coverage limits, not invented
   content and not automatically inconsistencies.
2. Compare section previews, enumerations, and promises with the content and
   order that the manuscript actually delivers.
3. Check recurring names, technical terms, acronyms, capitalization, and
   definitions for stable meaning and use.
4. Check notation for definition before use, symbol reuse, indices, dimensions,
   and agreement between prose, equations, algorithms, and implementation
   descriptions present in the paper.
5. Compare thesis, contribution identity, claim strength, scope, and key insight
   across the title, abstract, introduction, method, experiments, limitations,
   and conclusion.
6. Compare every recurring number, unit, metric, dataset or split, aggregation,
   uncertainty statement, experimental condition, and stated improvement.
7. Compare figures and tables with their captions, body references, values,
   terminology, visual positions, and stated takeaways. Report orphaned or
   contradictory artifacts.
8. Check citation keys, named entities, citation locations, and claim-use records
   for inconsistency. Do not infer that bibliographic identity proves claim
   support.
9. Identify logical contradictions, unsupported cross-section transitions,
   repeated explanations that disagree, conclusions that exceed reported
   evidence, and negative evidence hidden by stronger later wording.
10. Report findings only. Do not edit the manuscript or silently choose which
    conflicting statement, number, or interpretation is correct.

## Bundled review sidecars

The bundled `ccf-paper-reviewer` skill (`.agents/skills/ccf-paper-reviewer/SKILL.md`)
and `ccf-integrity-auditor` skill
(`.agents/skills/ccf-integrity-auditor/SKILL.md`) may be loaded as sidecars for
deeper assessment. They are subject to the same boundary as this skill: the
Human identifies a manuscript version as ready, the pass is findings-only by
default, and neither produces edits. Upstream scores are diagnostic feedback,
never acceptance probabilities or approved Human decisions. Where CCFA review
criteria conflict with the paper contracts, the local contracts win.

## Output contract

Order findings by severity:

- **High**: conflicts with a central claim, approved experiment interpretation,
  locked condition, stable interface, or consequential limitation.
- **Medium**: may materially confuse scientific meaning, reproducibility,
  comparison fairness, or evidence supporting a contribution.
- **Low**: a local mismatch with limited scientific impact, such as a secondary
  term, cross-reference, caption, or notation-presentation inconsistency.

Each finding must include:

<!-- paper-skill-contract: F7-MCR-001-v1 -->
- an enumeration of every conflicting or affected surface found, with exact file and line references;
- short quotations or values that demonstrate the conflict;
- the governing contract or interface when one exists;
- why the inconsistency matters;
- whether resolution requires a Human scientific decision.

Lead with findings. If no findings are identified, say so and list any review
coverage limits. Do not manufacture findings, provide replacement prose, edit
files, or begin remediation unless the Human separately requests a fix.

## Human decision

When the governing contracts do not identify which conflicting surface is
correct, preserve the uncertainty. The Human decides scientific meaning, claim
strength, experiment interpretation, consequential limitations, and stable
interface meaning before remediation.
