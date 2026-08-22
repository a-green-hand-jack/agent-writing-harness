# Paper Interfaces

Paper interfaces are stable paper-facing names whose meaning must not drift
silently. The interface is the shared meaning, not merely the LaTeX macro.

## Keep the implementation light

The implementation is `paper/macros.tex`, Human-readable comments, and active
consumers in the canonical paper. Do not add a schema or generator until a real
recurring cost justifies one. Reviewed generated numeric macros may extend or
override result definitions through `paper/generated/results-macros.tex`.

## Interface categories

### Identity and terminology

- `\PaperTODO{...}`: explicit Draft-only placeholder. There are no active uses in the current ARIS paper; strict Release rejects any future active use.
- `\PaperTitle`: canonical title, "ARIS: Autonomous Research via Adversarial Multi-Agent Collaboration." Meaning and positioning are locked.
- `\PaperAuthors`: canonical visible author and affiliation block for Ruofeng Yang, Yongcan Li, and Shuai Li. Identity is locked; anonymous variants hide it rather than redefine it.
- `\MethodName`: approved rendered system name, `ARIS`. Renaming requires Human review and a global consumer audit.
- `\CoreTerm`: preferred central term, "research harness." Redefinition that changes scope requires Human review.

### Notation

- `\StateSymbol`: the manuscript's stable prose-level label `state` in the persistent-state bottleneck. The report does not introduce a mathematical state variable; replacing this with invented notation is prohibited.

### Results

- `\MainResult`: the reported internal reviewer-score transition `5.0 to 7.5/10` in E1. It is locked to one documented observational trajectory and is not a standardized benchmark result.
- `\MainResultUncertainty`: the paired interpretation, "a single trajectory on one paper; we do not generalize from it." It is a qualitative scope limitation because the source reports no statistical uncertainty.

The two result interfaces must remain paired. A change to the score definition,
trajectory, aggregation, evidence source, uncertainty meaning, or display value
requires Human review and updates to `EXPERIMENTS.md` and every consumer.

### Claims and artifacts

The central thesis and C1-C3 remain natural-language contracts in `PAPER.md`.
Figures and tables remain canonical under `paper/`; no duplicate artifact
registry is maintained.

## Flexible control

- **locked**: identity, scientific meaning, score conditions, and interpretation do not change silently.
- **bounded**: display formatting and local wording may change while preserving the documented meaning.
- **free**: low-risk LaTeX implementation and consumer maintenance may be handled autonomously.
- **unresolved**: a missing or disputed value remains explicit; use `\PaperTODO` in Draft rather than inventing one.

## Change workflow

1. Distinguish a presentation change from a meaning change.
2. Retrieve all canonical and variant consumers.
3. Explain effects on claims, experiments, tables, captions, conclusions, and release versions.
4. Request Human review for identity, scientific meaning, or important result-interpretation changes.
5. Update the definition, contract, and every consumer together.
6. Report unresolved or stale consumers.

## Draft and release

Draft interfaces remain compilable and explicit. Before a strict release, every
required interface must have Human-understood meaning, no active placeholder,
consistent consumers, and no cross-variant semantic drift.

```bash
python3 .agents/tools/check-paper-interfaces.py
python3 .agents/tools/check-paper-contracts.py --profile release
```
