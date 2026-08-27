# Experiment Contract

This file records what the paper needs experiments to establish and which choices require Human awareness.
It is not a run ledger, scheduler, or second source of truth for raw research results.

Use the same flexible collaboration cues as `PAPER.md`: **locked**, **bounded**, **free**, and **unresolved**.

## Experiment overview

Evidence and materials supplied by the Human are inventoried in `BRIEF.md`;
this file records only paper-facing evidence questions and their interpretation
boundaries.

| ID | Paper question | Supports | Current state |
|---|---|---|---|
| — | No paper-facing evidence question recorded yet | — | unresolved |

## Evidence-question template

Copy this structure only when a real paper-facing question exists, then assign
the next available ID. Do not assume that the question is a comparison.

- ID: E<N>
- Paper question: TODO

### Paper role

- Supports: TODO: approved claim or decision, if any
- Reader question: TODO
- Maximum paper-facing interpretation: unresolved

### Locked

Record conditions that an Agent must not silently change, for example:

- dataset and split;
- primary metric;
- baseline set required for a fair comparison;
- checkpoint-selection rule;
- evaluation protocol;
- exclusions that materially affect the conclusion.

Current locked conditions:

- TODO

### Bounded

Record adjustments an Agent may propose or make within a concrete range, for example:

- number of seeds, with a minimum and preferred value;
- secondary metrics;
- search budget;
- plot layout;
- ordering of reported analyses.

Current bounded adjustments:

- TODO

### Free

Implementation or presentation choices that do not change the scientific question:

- low-risk plotting and table formatting;
- file organization;
- wording changes within the approved interpretation;
- TODO

### Unresolved

- TODO: statistical summary
- TODO: whether the result supports “improves,” “consistently improves,” or a more conservative statement

### Human decision triggers

The Agent must prepare context and request a Human decision before:

- changing a locked condition;
- removing an agreed baseline;
- changing the primary metric or split;
- interpreting an observational result causally;
- hiding a negative or inconclusive result that constrains a core claim;
- weakening, strengthening, or replacing the paper claim supported by this experiment.

## Additional experiments

Add one section per real paper-facing question, copying this structure only
when that question exists. Do not assume that every paper needs an ablation,
mechanism study, robustness test, or a fixed number of experiments.

## Result interpretation

For each paper-facing result, keep the following clear in natural language:

- what was measured;
- under which approved conditions;
- what aggregation or uncertainty means;
- what the result can support;
- what it cannot support;
- what would make the current interpretation stale.

The Human must understand the important configuration and interpretation. The Agent should retrieve details, compare alternatives, surface inconsistencies, and prepare concise decision packets rather than asking the Human to search the repository.

## Relationship to the code repository

The code-to-paper data interface is intentionally out of scope for this phase. Until a dedicated interface is designed, use this file only to maintain the paper-facing experimental contract and do not duplicate the code repository's run lifecycle or raw metric truth.
