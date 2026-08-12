# Paper Contract

This file is the short, Human-readable source of truth for what the paper is trying to be.
Keep it useful during discussion and revision; do not turn it into a complete research ledger.

The control words below are collaboration cues, not a rigid permission system:

- **locked** — an Agent may analyze or propose a change, but must not silently change the meaning.
- **bounded** — an Agent may adjust the item inside the written boundary.
- **free** — an Agent may handle the implementation or wording while respecting higher-level decisions.
- **unresolved** — Human and Agent have not settled the matter; proceed flexibly, keep uncertainty visible, and ask before making a high-impact or hard-to-reverse choice.

## Paper identity

- Working title: Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents
- Case: `case/arxiv-2505-22954`; migration source: arXiv `2505.22954v3` (latest)
- Authors (from the migrated source): Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune
- Paper type: method
- Venue context: the migrated source uses the official ICLR 2026 style files; venue-kit work is out of scope for this round and remains **unresolved**
- Intended readers: **unresolved** (not recorded in the migrated source)
- One-sentence positioning: a self-improving agent system that iteratively modifies its own code, empirically validates changes, and grows an open-ended archive of discovered coding agents (from the source abstract)

## What readers should believe

### Central thesis — recorded from the source, not agent-verified

The Darwin Gödel Machine (DGM) realizes open-ended self-improvement: agents self-modify, empirically validate each change, and accumulate an archive of stepping stones. This external case-replay preserves the published paper; this repository does not re-derive the claims.

### Contributions

1. **C1 — recorded:** DGM improves its coding capabilities on SWE-bench from 20.0% to 50.0% (source abstract).
2. **C2 — recorded:** DGM improves Polyglot performance from 14.2% to 30.7% (source abstract).
3. **C3 — recorded:** DGM outperforms baselines without self-improvement or open-ended exploration (source abstract).
4. **C4 — recorded:** transfer experiments are reported in the source paper; no claim text is invented here.

All contributions are **unresolved** for any purpose beyond faithful reproduction: the Agent must not re-interpret, strengthen, or weaken them without Human review.

## What must not change silently

Use this section only for high-impact commitments:

- the verbatim scientific content of the migrated sections;
- the author list and title;
- headline numbers (20.0%, 50.0%, 14.2%, 30.7%) and the benchmarks they belong to;
- the limitation and safety statements in the source paper;
- the meaning of the stable paper interfaces (see `PAPER_INTERFACES.md`).

Current locked items:

- All prose, numbers, citations, figures, and tables in `paper/sections/` and `paper/supplementary/` are migrated verbatim from arXiv `2505.22954v3`; changes require Human review.
- Negative or inconclusive evidence in the source stays visible.

## What may evolve

- Presentation machinery only: publication variants, LaTeX macros, build targets, CI jobs.
- Documentation of provenance (source attribution, migration debt) may be corrected when facts are wrong.
- **bounded** — interface definitions may change wording only while the rendered output stays identical to the source.

## Unresolved

This is a working queue, not a failure list.

- Human review of this contract and the other four contracts.
- Whether any active venue/author-kit work (ICLR 2026 rules) is ever in scope.
- Reference identity: 195 bibliography entries migrated verbatim; 184-entry legacy citation ledger stayed at `fitness_status: needs-review` in Round 1 and has not been re-reviewed.
- Numeric-ledger debt recorded in Round 1 (date-exception masking gap P15).
- Release approval, Overleaf web compile, and arXiv platform compile: all remain `UNVERIFIED`.
- Target audience, track, deadline, and page limit were `TODO` in the legacy metadata and remain unresolved.

## Story and structure

### Narrative arc — recorded from the source structure

Problem (fixed architectures cannot improve themselves) → Gödel machine theory and its impractical proof requirement → DGM (empirical validation + open-ended archive) → experiments (SWE-bench, Polyglot, ablations, transfer) → safety discussion → conclusion and limitations.

### Section responsibilities

| Section | Reader task | Must preserve | Flexible elements |
|---|---|---|---|
| Abstract | headline claims and result numbers | verbatim claims and numbers | none (verbatim migration) |
| Introduction | motivation and DGM idea | framing and claims | none (verbatim migration) |
| Related work | position against prior art | citations and comparisons | none (verbatim migration) |
| Method | DGM algorithm | algorithm, archive, selection | none (verbatim migration) |
| Experiments | evidence for C1-C4 | conditions and results | none (verbatim migration) |
| Conclusion + limitations | takeaway and honesty | limitations | none (verbatim migration) |
| Appendix | details, agents, prompts | all appendix content | none (verbatim migration) |

## Writing style

### Current style — recorded, not invented

- The paper text is a verbatim migration of the arXiv source; no rewriting is authorized in this round.
- Positioning and voice: that of the source paper.
- Claim-strength discipline: preserve the source's exact wording; do not convert correlation into causal language.
- Terms or expressions: `Darwin Gödel Machine`, `DGM`, `archive`, `self-improving`, `open-ended`.
- Venue-specific overlay: ICLR 2026 style files exist in the tree; current-year official rules remain unverified.

## Human decisions required

The Human retains final responsibility for:

- central contributions and claims;
- whether a claim may degrade, be removed, or require more experiments;
- the main story and paper positioning;
- primary metrics, baselines, evaluation fairness, and result interpretation;
- changes to the meaning of stable paper interfaces;
- final release approval.

Agents should retrieve the relevant context, affected sections, alternatives, and risks before asking the Human to decide.
