# Agent Entry

The paper project is primary. Start from the current Human-facing contract and load only the context required for the active task.

## Orientation

1. Read `PAPER.md`.
2. Read `EXPERIMENTS.md` only for experiment, evidence, claim-support, or result-interpretation work.
3. Read `PAPER_INTERFACES.md` only for recurring terminology, notation, results, claims, figures, tables, or macros.
4. Read only relevant decisions in `DECISIONS.md`.
5. Inspect the active paper section and current diff.
6. Load one focused skill or knowledge document.

## Task routing

- high-impact meaning or control boundary → `.agents/skills/control-review/SKILL.md`
- focused Human choice → `.agents/skills/decision-packet/SKILL.md`
- positioning, structure, or prose style → `.agents/skills/style-alignment/SKILL.md`
- recurring semantic interface → `.agents/skills/paper-interface-maintenance/SKILL.md`
- publication or release candidate → `.agents/skills/release-review/SKILL.md`

Do not load all skills for an ordinary local edit.

## Collaboration cues

- **locked** — analyze or propose; do not silently change meaning.
- **bounded** — adjust inside the written boundary.
- **free** — handle implementation or wording while respecting higher-level decisions.
- **unresolved** — keep uncertainty visible, prefer reversible progress, and ask before a high-impact or hard-to-reverse choice.

The Human decides central claims, claim degradation, the main story, experiment fairness, important result interpretation, stable interface meaning, and final publication approval.

The Agent performs retrieval, impact analysis, alternatives, consistency maintenance, drafting, low-risk revision, and focused validation.

## Strong rules

- Do not invent contributions, facts, results, citations, or Human approval.
- Do not promote expected or unresolved results into verified evidence.
- Do not turn correlation into causal language without support.
- Do not silently change a locked claim, story decision, experiment condition, limitation, or interface meaning.
- Keep negative or inconclusive evidence visible when it constrains a central claim.
- Report missing tools or external environments honestly.
- Do not make `paper/` depend on `.agents/`.

## Handoff

Report changed files, scientific or narrative meaning affected, decisions made or unresolved, impacted interfaces or experiment contracts, and validation performed.
