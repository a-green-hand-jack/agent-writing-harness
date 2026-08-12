# Experiment Contract

This file records what the paper needs experiments to establish and which choices require Human awareness.
It is not a run ledger, scheduler, or second source of truth for raw research results.

Use the same flexible collaboration cues as `PAPER.md`: **locked**, **bounded**, **free**, and **unresolved**.

## Experiment overview

| ID | Paper question | Supports | Current state |
|---|---|---|---|
| E1 | Does DGM improve coding performance on SWE-bench? | C1 | **unresolved** — evidence is the published arXiv source, not a local run |
| E2 | Does DGM improve Polyglot performance? | C2 | **unresolved** — evidence is the published arXiv source, not a local run |
| E3 | Do ablations without self-improvement or open-ended exploration underperform DGM? | C3 | **unresolved** — evidence is the published arXiv source, not a local run |
| E4 | Do transfer experiments support the reported transfer claims? | C4 | **unresolved** — evidence is the published arXiv source, not a local run |

This repository is an external case-replay of a published paper. The Round-1 claim-experiment plan recorded four claim ids
(`claim-swe-improve`, `claim-polyglot-improve`, `claim-ablation`, `claim-transfer`) with the explicit note that no local
experiment plan is needed because the evidence is the published source itself.

## E1 — Primary comparison (SWE-bench)

### Paper role

- Supports: C1
- Reader question: does DGM improve coding capabilities on SWE-bench?
- Maximum paper-facing interpretation: the source abstract reports performance increasing from 20.0% to 50.0% on SWE-bench.

### Locked

- The verbatim numbers and benchmark names in the migrated text.
- No local experiment run may substitute for the published evidence.

### Bounded

- Reproduction or re-verification attempts must record conditions explicitly and must not overwrite the published numbers.

### Free

- Provenance and fidelity documentation of the migrated content.

### Unresolved

- Whether the reported numbers come with uncertainty, and whether "improves" is the strongest defensible wording.
- Human confirmation of any result interpretation.

### Human decision triggers

The Agent must prepare context and request a Human decision before:

- changing a recorded number or benchmark attribution;
- removing an ablation or baseline comparison;
- hiding a negative or inconclusive result that constrains a core claim;
- weakening, strengthening, or replacing any recorded claim.

## E2-E4 — remaining experiments

Same boundary as E1: recorded verbatim from the source; **unresolved** pending Human review; no local re-derivation.

## Result interpretation

- what was measured: coding performance on SWE-bench and Polyglot, ablations, and transfer experiments;
- under which approved conditions: those reported verbatim in the arXiv source;
- what the result can support: only what the source text claims;
- what it cannot support: nothing beyond the source wording;
- what would make the interpretation stale: a Human-approved re-interpretation or a verified correction of the source numbers.

## Relationship to the code repository

The Round-1 legacy control plane kept experiment surfaces under `lab/` (now retired). The paper's code repository is
external (`https://github.com/jennyzzt/dgm` per the source abstract). This repository only maintains the paper-facing
experimental contract; it does not duplicate the code repository's run lifecycle or raw metric truth. Legacy `lab/`
content is preserved in Git history (branch `case/arxiv-2505-22954`) and summarized in `DECISIONS.md`.
