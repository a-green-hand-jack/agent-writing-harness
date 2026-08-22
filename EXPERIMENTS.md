# Experiment Contract

This technical report contains deployment observations and a future controlled
benchmark protocol. It does not contain a local experimental run ledger. Use the
same **locked**, **bounded**, **free**, and **unresolved** collaboration cues as
`PAPER.md`.

## Experiment overview

| ID | Paper question | Supports | Current state |
|---|---|---|---|
| E1 | What occurred in the documented overnight auto-review trajectory? | C3 | reported and observational |
| E2 | What implementation and deployment footprint did ARIS report in April 2026? | C2, C3 | reported snapshot |
| E3 | How could cross-family review be compared under controlled conditions? | future-work boundary | protocol only; not executed |

### E1 - Documented overnight trajectory

- Paper role: illustrate that the harness operationalized review-driven revision and claim pruning in one realistic trajectory.
- Reported conditions: one paper, approximately eight hours, four review-revise rounds, more than 20 GPU experiments, and an internal reviewer score moving from 5.0 to 7.5/10.
- Evidence source: the imported arXiv 2605.03042 report and its canonical copy/provenance under `paper/supplementary/`.
- Locked interpretation: this is one observational trajectory and cannot be causally attributed to ARIS alone.
- Maximum paper-facing interpretation: ARIS operationalized claim pruning and review-driven revision in this documented run.
- Must not support: superiority over same-family review, optimal reviewer committee size, general effectiveness, or a standardized score improvement.
- Bounded presentation: the same values may be displayed through `\MainResult` and `\MainResultUncertainty`; their metric and scope may not change.

### E2 - Deployment footprint

- Paper role: describe the implementation and ecosystem snapshot reported at the time of writing.
- Reported conditions: the counts, platforms, model bridges, backends, templates, and skills stated in the canonical paper, as of April 2026 where marked.
- Locked interpretation: these are descriptive deployment facts, not comparative performance results.
- Bounded presentation: tables and prose may be reformatted without changing counts, dates, category meaning, or attribution.

### E3 - Controlled benchmark protocol

- Paper role: mark the evidence needed to isolate cross-family review effects from researcher expertise, model choice, and task difficulty.
- Current state: future work only; no result is available or implied.
- Existing protocol: 12+ public-preprint drafts; five compute-matched conditions; issue recall, false-positive rate, actionability, revision quality, cost, and latency; three independent blinded raters with Krippendorff's alpha.
- Locked boundary: do not present the protocol as executed, preregistered, approved, or evidential.
- Human decision trigger: any execution, condition change, metric change, reported result, or claim based on this protocol requires a new explicit experiment decision.

## Result interpretation

For E1, the measured value is an internal reviewer score within one documented
trajectory. No statistical aggregation, seed distribution, confidence interval,
or standardized benchmark uncertainty was reported. `\MainResultUncertainty`
therefore carries the trajectory-level limitation rather than a fabricated
numeric uncertainty.

For E2, counts are a time-bounded descriptive snapshot. They can support system
scope and deployment-footprint statements but not performance comparisons.

E3 has no results. Negative or inconclusive evidence from any future execution
must remain visible when it constrains C1 or C2. An observational result must
never be rewritten causally without controlled support and Human approval.

The interpretation becomes stale if the canonical source, conditions, score
meaning, values, aggregation, or evidence identity changes.

## Relationship to the code repository

This repository is the canonical paper source, not the ARIS implementation or a
research-run repository. It contains no local controlled evaluation artifacts.
The paper links to the external project repository and attributes the imported
arXiv source in `paper/supplementary/source-attribution.md`.

Raw runs, checkpoints, and metric truth must remain in their owning code or
experiment repository. Any future result imported here requires a reviewed
paper-facing interpretation and stable interface; this contract must not
duplicate an external run lifecycle.
