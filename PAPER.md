# Paper Contract

This file records the current Human-readable contract for the ARIS technical
report. It summarizes the authored paper and its source attribution; it does
not create new scientific claims.

The collaboration cues are flexible controls:

- **locked**: analyze or propose, but do not silently change meaning.
- **bounded**: revise only inside the stated scientific or presentation boundary.
- **free**: handle implementation or wording while preserving higher-level decisions.
- **unresolved**: keep uncertainty visible and ask before a high-impact or hard-to-reverse choice.

## Paper identity

- Working title: ARIS: Autonomous Research via Adversarial Multi-Agent Collaboration
- Authors: Ruofeng Yang, Yongcan Li, Shuai Li
- Target venue/style: ICLR 2026; current official rules and the author kit have not been independently reverified in this repository
- Paper type: method-oriented technical report
- Intended readers: researchers and engineers working on autonomous ML research systems, agent harnesses, and scientific assurance
- One-sentence positioning: ARIS is an open-source research harness that coordinates ML research workflows through a default executor/reviewer pattern with cross-model adversarial review.

Identity, attribution, and the imported source mapping are locked. Publication
metadata may change only through explicit Human review.

## What readers should believe

### Central thesis - locked

Long-horizon autonomous research is unreliable when one agent both produces and
validates the work; ARIS addresses this risk through persistent research state,
modular execution, and independent assurance under a recommended cross-family
executor/reviewer configuration.

### Contributions

1. **C1 - central, locked:** an assurance stack with separate executor and reviewer roles, a three-stage evidence-to-claim audit cascade, and manuscript-quality checks.
2. **C2 - central, locked:** a three-layer modular architecture spanning execution, orchestration, and assurance, including reusable skills, persistent research state, effort presets, reviewer routing, and a prototype outer loop.
3. **C3 - supporting, locked to observational scope:** early deployment experience across tested and adapted executor environments, including one documented overnight trajectory and explicit limitations.

C1 and C2 may not be weakened, strengthened, removed, or redefined without a
Human decision. C3 may be revised only to remain no stronger than its reported
observational evidence.

## What must not change silently

Current locked items:

- ARIS defaults to cross-family executor/reviewer separation as a recommended configuration; it does not enforce model-family separation in code.
- The system is described through the three bottlenecks and three architectural layers already used by the manuscript.
- The documented overnight run is one observational trajectory, not a controlled comparison or causal result.
- The report does not establish that cross-family review is superior to same-family review or that two reviewers are optimal.
- The limitations on correctness, novelty, scientific soundness, automation, and Human responsibility remain visible.
- Title, author identity, venue/style identity, stable interface meaning, and source attribution require Human review before semantic change.

## What may evolve

- Local sentence wording and paragraph boundaries are free when claim strength, attribution, and scientific meaning remain unchanged.
- Figure and table layout is bounded by the existing content and captions; no value or interpretation may change.
- Reference metadata repair is bounded to the same scientific object and must update `paper/refs.bib` and `references/ledger.json` together.
- Build, CI, release packaging, and Agent-sidecar implementation are free inside the paper-first boundaries in `PUBLICATION.md` and `DECISIONS.md`.
- Venue presentation may evolve only after current official rules are checked; it must not redefine the base story.

## Unresolved

- The current official ICLR 2026 submission rules, track, deadline, page limit, and author-kit identity remain unverified locally.
- Citation identity and occurrence-level claim-support reviews recorded as pending in `references/ledger.json` remain unresolved for a strict release.
- No future venue submission, revision deadline, or new controlled evaluation has been approved.

## Story and structure

### Narrative arc - locked

The manuscript proceeds from the risk of plausible unsupported success in
long-horizon research, to three operational bottlenecks, to the ARIS
architecture and assurance mechanisms, then to observational deployment
evidence, limitations, related systems, and conclusions. Reordering that changes
the argument or the role of a limitation requires Human review.

### Section responsibilities

| Section | Reader task | Must preserve | Flexible elements |
|---|---|---|---|
| Abstract | Identify ARIS, its layers, and evidence scope | default cross-model review, three layers, observational qualification | compression that preserves meaning |
| Introduction | Understand the failure mode and three bottlenecks | stringent assumption, bottleneck decomposition, three stated contributions | examples and paragraph boundaries |
| System and assurance | Understand architecture, roles, audits, skills, workflows, and tools | recommended-not-enforced cross-family distinction and implementation scope | local explanation order |
| Deployment evidence | Read ecosystem facts and the overnight run conservatively | observational and non-causal interpretation | table and paragraph presentation |
| Limitations | Understand what ARIS cannot guarantee and where Humans remain responsible | all substantive limitations | local wording only |
| Related work | Place ARIS relative to research agents, debate, review, and harness engineering | comparison meaning and citations | grouping and ordering |
| Conclusion | Retain the three-bottleneck response and limitations | no stronger claim than supported above | compression and emphasis |

## Writing style

### Current style - bounded

- Positioning and voice: direct technical-report voice; describe implemented mechanisms before broader implications.
- Explanation density: retain concrete component, workflow, and audit details needed to understand the system.
- Claim-strength discipline: use observational language for deployment outcomes and reserve causal claims for controlled evidence.
- Preferred paragraph moves: state the risk or reader question, describe the mechanism or observation, then qualify its interpretation.
- Terms to avoid: claims of guaranteed correctness, autonomous scientific validity, causal improvement, or optimal reviewer composition.
- Venue-specific overlay: the imported ICLR 2026 style may affect presentation only; official current rules remain unverified.

No Writing DNA has been activated for this paper.

## Human decisions required

The Human retains final responsibility for:

- central contributions, claims, and any claim degradation;
- main story, positioning, and audience changes;
- experiment conditions, fairness, new results, and important interpretation;
- author identity, venue choice, and stable paper-interface meaning;
- publication-variant differences and immutable release approval;
- ambiguous citation identity or version choices that could affect meaning.

Agents retrieve affected consumers, evidence, alternatives, and risks before
asking for a decision. They do not infer approval from existing prose or a
successful build.
