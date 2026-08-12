# Paper Contract

This file is the short, Human-readable source of truth for what the paper is trying to be.
Keep it useful during discussion and revision; do not turn it into a complete research ledger.

The control words below are collaboration cues, not a rigid permission system:

- **locked** — an Agent may analyze or propose a change, but must not silently change the meaning.
- **bounded** — an Agent may adjust the item inside the written boundary.
- **free** — an Agent may handle the implementation or wording while respecting higher-level decisions.
- **unresolved** — Human and Agent have not settled the matter; proceed flexibly, keep uncertainty visible, and ask before making a high-impact or hard-to-reverse choice.

## Paper identity

- Working title: CORAL: Towards Autonomous Multi-Agent Evolution for Open-Ended Discovery
- Case: `case/arxiv-2604-01658`; migration source: arXiv `2604.01658v2` (latest)
- Authors (from the migrated source): Ao Qu, Han Zheng, Zijian Zhou, Yihao Yan, Yihong Tang, Shao Yong Ong, Fenglu Hong, Kaichen Zhou, Chonghe Jiang, Minwei Kong, Jiacheng Zhu, Xuan Jiang, Sirui Li, Cathy Wu, Bryan Kian Hsiang Low, Jinhua Zhao, Paul Pu Liang
- Paper type: method
- Venue context: the migrated source uses the official COLM 2026 style files (`[preprint]` option); venue-kit work is out of scope for this round and remains **unresolved**
- Intended readers: **unresolved** (not recorded in the migrated source)
- One-sentence positioning: a framework for autonomous multi-agent evolution on open-ended problems, replacing fixed heuristics with long-running agents that explore, reflect, and collaborate through shared persistent memory (from the source abstract)

## What readers should believe

### Central thesis — recorded from the source, not agent-verified

CORAL is the first framework for autonomous multi-agent evolution on open-ended problems: greater agent autonomy and multi-agent evolution can substantially improve open-ended discovery. This external case-replay preserves the published paper; this repository does not re-derive the claims.

### Contributions

1. **C1 — recorded:** CORAL sets new state-of-the-art results on 10 tasks with 3-10x higher improvement rates and far fewer evaluations than fixed evolutionary search baselines (source abstract).
2. **C2 — recorded:** on Anthropic's kernel engineering task, four co-evolving agents improve the best known score from 1363 to 1103 cycles (source abstract).
3. **C3 — recorded:** mechanistic analyses show gains arise from knowledge reuse and multi-agent exploration/communication (source abstract).
4. **C4 — recorded:** on the Erdos Minimum Overlap problem, CORAL achieves 2.5x higher improvement rate and 10x faster evolution using the same model (source abstract, commented draft retained).

All contributions are **unresolved** for any purpose beyond faithful reproduction: the Agent must not re-interpret, strengthen, or weaken them without Human review.

## What must not change silently

Use this section only for high-impact commitments:

- the verbatim scientific content of the migrated sections (including the fully commented-out `07_limitations.tex` slot, kept for source-order fidelity);
- the author list and title;
- headline numbers (3-10x improvement rates, 1363 to 1103 cycles, 2.5x, 10x) and the benchmarks they belong to;
- the limitation statements in the source appendix;
- the meaning of the stable paper interfaces (see `PAPER_INTERFACES.md`).

Current locked items:

- All prose, numbers, citations, figures, and tables in `paper/sections/` are migrated verbatim from arXiv `2604.01658v2`; changes require Human review.
- Negative or inconclusive evidence in the source stays visible.

## What may evolve

- Presentation machinery only: publication variants, LaTeX macros, build targets, CI jobs.
- Documentation of provenance (source attribution, migration debt) may be corrected when facts are wrong.
- **bounded** — interface definitions may change wording only while the rendered output stays identical to the source.

## Unresolved

This is a working queue, not a failure list.

- Human review of this contract and the other four contracts.
- Whether any active venue/author-kit work (COLM 2026 rules) is ever in scope.
- Reference identity: 50 bibliography entries migrated verbatim; citation fitness stays unreviewed.
- Release approval, Overleaf web compile, and arXiv platform compile: all remain `UNVERIFIED`.
- Target audience, track, deadline, and page limit were `TODO` in the legacy metadata and remain unresolved.

## Story and structure

### Narrative arc — recorded from the source structure

Problem (fixed heuristics limit LLM-agent autonomy) → CORAL framework (long-running agents, shared persistent memory, asynchronous multi-agent execution, heartbeat interventions, safeguards) → experiments (mathematical/algorithmic/systems tasks, kernel engineering) → mechanistic analyses → limitations (kept in the appendix per source) → conclusion.

### Section responsibilities

| Section | Reader task | Must preserve | Flexible elements |
|---|---|---|---|
| Abstract | headline claims and result numbers | verbatim claims and numbers | none (verbatim migration) |
| Introduction | motivation and paradigm comparison | framing and claims | none (verbatim migration) |
| Related work | position against prior art | citations and comparisons | none (verbatim migration) |
| Method | CORAL framework | memory, agents, safeguards | none (verbatim migration) |
| Experiments | evidence for C1-C4 | conditions and results | none (verbatim migration) |
| Limitations | source keeps this commented out; appendix carries the real section | commented-out state | none (verbatim migration) |
| Conclusion | takeaway | claims | none (verbatim migration) |
| Appendix | details and future directions | all appendix content | none (verbatim migration) |

## Writing style

### Current style — recorded, not invented

- The paper text is a verbatim migration of the arXiv source; no rewriting is authorized in this round.
- Positioning and voice: that of the source paper.
- Claim-strength discipline: preserve the source's exact wording; do not convert correlation into causal language.
- Terms or expressions: `CORAL`, `multi-agent evolution`, `shared persistent memory`, `open-ended discovery`.
- Venue-specific overlay: COLM 2026 style files exist in the tree with the `[preprint]` option; current-year official rules remain unverified.

## Human decisions required

The Human retains final responsibility for:

- central contributions and claims;
- whether a claim may degrade, be removed, or require more experiments;
- the main story and paper positioning;
- primary metrics, baselines, evaluation fairness, and result interpretation;
- changes to the meaning of stable paper interfaces;
- final release approval.

Agents should retrieve the relevant context, affected sections, alternatives, and risks before asking the Human to decide.
