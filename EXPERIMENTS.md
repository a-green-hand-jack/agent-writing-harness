# Experiment Contract

This file records what the paper needs experiments to establish and which choices require Human awareness.
It is not a run ledger, scheduler, or second source of truth for raw research results.

Use the same flexible collaboration cues as `PAPER.md`: **locked**, **bounded**, **free**, and **unresolved**.

## Experiment overview

| ID | Paper question | Supports | Current state |
|---|---|---|---|
| E1 | Does autonomous multi-agent evolution beat fixed evolutionary search baselines across tasks? | C1 | **unresolved** — evidence is the published arXiv source, not a local run |
| E2 | Do co-evolving agents improve the Anthropic kernel engineering score? | C2 | **unresolved** — evidence is the published arXiv source, not a local run |
| E3 | Do mechanistic analyses explain the gains (knowledge reuse, exploration, communication)? | C3 | **unresolved** — evidence is the published arXiv source, not a local run |
| E4 | Does CORAL improve evolution rate/speed on the Erdos Minimum Overlap problem? | C4 | **unresolved** — evidence is the published arXiv source, not a local run |

This repository is an external case-replay of a published paper. No local experiment plan exists; the evidence is the published source itself.

## E1 — Primary comparison

### Paper role

- Supports: C1
- Reader question: does CORAL improve over fixed evolutionary search baselines?
- Maximum paper-facing interpretation: the source abstract reports 3-10x higher improvement rates with far fewer evaluations across tasks.

### Locked

- The verbatim numbers and benchmark names in the migrated text.
- No local experiment run may substitute for the published evidence.

### Bounded

- Reproduction or re-verification attempts must record conditions explicitly and must not overwrite the published numbers.

### Free

- Provenance and fidelity documentation of the migrated content.

### Unresolved

- Whether the reported numbers come with uncertainty, and whether "higher improvement rates" is the strongest defensible wording.
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

- what was measured: improvement rates and task scores across mathematical, algorithmic, and systems optimization tasks, plus the kernel engineering cycles;
- under which approved conditions: those reported verbatim in the arXiv source;
- what the result can support: only what the source text claims;
- what it cannot support: nothing beyond the source wording;
- what would make the interpretation stale: a Human-approved re-interpretation or a verified correction of the source numbers.

## Relationship to the code repository

The Round-1 legacy control plane kept experiment surfaces under `lab/` (now retired). The paper's code repository is
external (`https://github.com/Human-Agent-Society/CORAL` per the source abstract). This repository only maintains the
paper-facing experimental contract; it does not duplicate the code repository's run lifecycle or raw metric truth.
Legacy `lab/` content is preserved in Git history (branch `case/arxiv-2604-01658`) and summarized in `DECISIONS.md`.
