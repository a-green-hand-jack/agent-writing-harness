# Agent Entry

The paper project is primary. Start from the current Human-facing contract and load only the context required for the active task.

## Orientation

1. Read `PAPER.md`.
2. Read `EXPERIMENTS.md` only for experiment, evidence, claim-support, or result-interpretation work.
3. Read `PAPER_INTERFACES.md` only for recurring identity, terminology, notation, results, claims, figures, tables, or macros.
4. Read `PUBLICATION.md` only for variants, delivery targets, or release instances.
5. Read only relevant decisions in `DECISIONS.md` and release records.
6. Inspect the active paper section and current diff.
7. Load one focused skill or knowledge document.

## Task routing

- high-impact meaning or control boundary → `.agents/skills/control-review/SKILL.md`
- focused Human choice → `.agents/skills/decision-packet/SKILL.md`
- positioning, structure, or prose style → `.agents/skills/style-alignment/SKILL.md`
- recurring semantic interface → `.agents/skills/paper-interface-maintenance/SKILL.md`
- publication variant or allowed difference → `.agents/skills/publication-planning/SKILL.md`
- immutable release candidate → `.agents/skills/release-review/SKILL.md`
- synchronize a downstream paper repository with the upstream template → `.agents/skills/template-sync/SKILL.md`

Do not load all skills for an ordinary local edit.

## Collaboration cues

- **locked** — analyze or propose; do not silently change meaning.
- **bounded** — adjust inside the written boundary.
- **free** — handle implementation or wording while respecting higher-level decisions.
- **unresolved** — keep uncertainty visible, prefer reversible progress, and ask before a high-impact or hard-to-reverse choice.

The Human decides central claims, claim degradation, the main story, experiment fairness, important result interpretation, stable interface meaning, active variants, permitted cross-version differences, release approval, and external publication.

The Agent performs retrieval, impact analysis, alternatives, consistency maintenance, drafting, low-risk revision, variant checks, release construction, template-sync planning, and focused validation.

## Strong rules

- Do not invent contributions, facts, results, citations, identity, approval, or external-platform success.
- Do not promote expected or unresolved results into verified evidence.
- Do not turn correlation into causal language without support.
- Do not silently change a locked claim, story decision, experiment condition, limitation, or interface meaning.
- Do not copy canonical scientific content into publication variants.
- Do not overwrite an existing release instance or release record.
- Keep generated artifacts under ignored `dist/`; never recreate a committed generated `release/` tree.
- Keep negative or inconclusive evidence visible when it constrains a central claim.
- Do not make `paper/` depend on `.agents/`, `dist/`, or `releases/`.
- Do not merge unrelated upstream-template history into a downstream paper repository.
- Do not apply template updates on the default branch, overwrite protected paper content, or record a new sync baseline before manual review and validation.

## Handoff

Report changed files, scientific or narrative meaning affected, decisions made or unresolved, impacted interfaces, variants or experiment contracts, generated release ID and manifest when relevant, template baseline/target and conflict set when syncing, and validation performed.
