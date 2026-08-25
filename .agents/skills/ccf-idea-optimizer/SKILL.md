---
name: ccf-idea-optimizer
description: "Turn rough CCF research directions into concrete problem, gap, insight, method, novelty, and evidence plans. Use for idea optimization, fuzzy idea concretization, research direction shaping, salvage routes, 优化idea, 具象化idea, 研究思路优化. Binding local protocol: whenever an output contains more than one candidate, route, or concretization, including from one Human seed, conflicting upstream selection and output instructions are disabled even when upstream is read. Emit neutral peer candidates only, using the exact same fields and comparable depth for every candidate. With multiple candidates, primary, lead, focus, default, fallback, recommendation, pivot, recommended-next, preferred ordering, asymmetric expansion, and route selection are unconditionally forbidden; comparison/select requests route to ccf-idea-reviewer and never authorize optimizer selection, with final choice in a Human decision-packet."
---

# CCF Idea Optimizer (bundled)

## Mandatory local override (before canonical content)

This is a binding local contract, not advisory guidance. It is active before canonical content is loaded and remains authoritative if upstream content is read. Conflicting upstream selection and output instructions are disabled, including the strongest-route core text, workflow selection and pivot steps, the multi-idea selection output (`Best development candidate`, `Why it is the best current route`, and `Recommended next iteration`), and the selection instructions in `references/idea-intake.md`, `references/frontier-ideation.md`, and `references/literature-grounded-evolution.md`. Those references are inactive reference material for facts and mechanisms only; reapply this local protocol before drafting.

The protocol activates whenever the output contains more than one candidate, route, or concretization, even when they came from one Human seed. With multiple candidates, the following terms and behaviors are unconditionally forbidden: primary, lead, focus, default, fallback, pivot, recommendation, recommended-next, preferred ordering, asymmetric expansion, strongest-route selection, comparison, ranking, or optimizer selection. Do not evade this rule with renamed equivalents such as `Lead Route`, `Primary Development Route`, or `Structurally Different Fallback`.

### Complete local workflow

1. Count candidate, route, and concretization outputs. If the count is greater than one, activate the peer protocol.
2. Normalize the seed into the shared candidate fields below without prioritizing or selecting a route.
3. Develop every candidate independently with the exact same fields and comparable depth.
4. Mark novelty, evidence, assumptions, and missing inputs per candidate; include only candidate-specific tradeoffs and a discriminating evidence sketch.
5. Run the peer-parity audit: no candidate may receive a thesis, method blueprint, innovation boundary, evidence package, or action plan that peers do not receive.
6. Run the pre-return forbidden-output audit and remove any selection-bearing label, ordering, recommendation, pivot, or asymmetric expansion.
7. End with the neutral handoff below and stop.

### Exact peer-candidate output schema

For each candidate, emit exactly these fields in this order, at comparable depth:

```text
Candidate ID:
Parent seed and operation:
Target problem:
Gap and root challenge:
Core insight:
Method mechanism:
Innovation type and boundary:
Discriminating evidence sketch:
Novelty and closest-work status:
Assumptions, limitations, and missing inputs:
Candidate-specific tradeoffs:
```

Do not add a thesis, method blueprint, innovation boundary, evidence package, action plan, or any other expansion to only one candidate. The neutral handoff must state: comparison and selection are deferred to `ccf-idea-reviewer` on explicit Human request; that request never authorizes the optimizer to compare or select; and final choice remains the Human decision through `decision-packet`.

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-idea-optimizer/SKILL.md`
- Resources: any existing sibling `references/`, `scripts/`, `resources/`, `templates/`, or `assets/` directories under `.agents/vendor/ccfa-skills/ccf-idea-optimizer`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

Proposals only. Central thesis, contributions, and story changes require `control-review` and a Human decision packet.

Candidate idea documents go to ignored `.agents/runtime/` or the discussion; do not edit `PAPER.md` claims without Human approval.

The vendored mandatory experiment-plan checklist is narrowed here to a minimum viable evidence sketch (which claim needs which discriminating test); dataset/baseline/metric/ablation selection and result-table schema belong to `ccf-experiment-designer`. The mandatory local override above is binding: the optimizer develops neutral peer candidates and never selects among them. An explicit Human request to compare or select routes triggers `ccf-idea-reviewer`; it never authorizes optimizer selection, and final choice remains a Human `decision-packet` decision.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
