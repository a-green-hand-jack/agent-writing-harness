# Agent Entry

The paper project is primary. Start from the current Human-facing contract and load only the context required for the active task.

## First session in a downstream repository

If this repository is not the upstream template and `.agents/init-state.json` does not exist, run:

```bash
python3 .agents/tools/paper-init.py clean --commit
```

This removes template-specific governance IDs, resets downstream-local metadata, writes an initialization marker, and commits the cleanup before paper work begins. A downstream paper must not keep the upstream template's case-branch or issue IDs.

## Orientation

1. Read `PAPER.md`.
2. Read `EXPERIMENTS.md` only for experiment, evidence, claim-support, or result-interpretation work.
3. Read `PAPER_INTERFACES.md` only for recurring identity, terminology, notation, results, claims, figures, tables, or macros.
4. Read `PUBLICATION.md` only for variants, delivery targets, or release instances.
5. Read only relevant decisions in `DECISIONS.md` and release records.
6. Inspect the active paper section and current diff.
7. Load one primary owner skill plus any explicitly permitted sidecar skills; never load the whole family.

## Task routing

- unclear paper context or new session → `.agents/skills/paper-orientation/SKILL.md`
- high-impact meaning or control boundary → `.agents/skills/control-review/SKILL.md`
- focused Human choice → `.agents/skills/decision-packet/SKILL.md`
- drafting or substantially revising a specific paper section → `.agents/skills/section-writing/SKILL.md`
- setting or changing positioning, narrative architecture, section responsibility, or writing policy → `.agents/skills/style-alignment/SKILL.md`
- Human-requested consistency review after a manuscript version is ready → `.agents/skills/manuscript-consistency-review/SKILL.md`
- recurring semantic interface → `.agents/skills/paper-interface-maintenance/SKILL.md`
- bibliography identity, metadata, duplicate, or version repair → `.agents/skills/reference-repair/SKILL.md`
- citation discovery, claim-support assessment, or evidence-passage retrieval → `.agents/skills/citation-support-review/SKILL.md`
- publication variant or allowed difference → `.agents/skills/publication-planning/SKILL.md`
- venue planning, deadlines, page budget, or official submission rules → `.agents/skills/publication-planning/SKILL.md` and `.agents/knowledge/venues/README.md`
- immutable release candidate → `.agents/skills/release-review/SKILL.md`
- adapt an existing paper repository to this template → `.agents/skills/template-adoption/SKILL.md`
- synchronize an adopted downstream repository with the upstream template → `.agents/skills/template-sync/SKILL.md`

### Bundled CCFA skills

The template ships the CCFA-Skills suite and writing-dna-skill as immutable snapshots under `.agents/vendor/` (see `.agents/vendor/README.md` and `.agents/dependencies/vendored-skills/provenance.json`). Wrappers below route to those snapshots and enforce the paper-contract boundaries. Load one as a sidecar of the matching owner skill, never as a substitute for the owner:

- shared CCFA governance → `.agents/skills/ccf-common/SKILL.md`
- experiment design, ablations, result-table semantics → `.agents/skills/ccf-experiment-designer/SKILL.md`
- manuscript-facing humanization preflight → `.agents/skills/ccf-humanization/SKILL.md`
- idea optimization and research-direction shaping → `.agents/skills/ccf-idea-optimizer/SKILL.md`
- idea scoring, ranking, triage → `.agents/skills/ccf-idea-reviewer/SKILL.md`
- claim/evidence/citation integrity audit → `.agents/skills/ccf-integrity-auditor/SKILL.md`
- arXiv/OpenReview novelty and competitor monitoring → `.agents/skills/ccf-literature-monitor/SKILL.md`
- external literature and related-work search → `.agents/skills/ccf-literature-searcher/SKILL.md`
- assessment-only manuscript review and scoring → `.agents/skills/ccf-paper-reviewer/SKILL.md`
- paper PDF → writing exemplar cards → `.agents/skills/ccf-paper-to-exemplar/SKILL.md`
- drafting, revision, polishing, compression → `.agents/skills/ccf-paper-writer/SKILL.md`
- full-project stage planning and routing → `.agents/skills/ccf-pipeline-orchestrator/SKILL.md`
- external project scaffolding → `.agents/skills/ccf-project-scaffolder/SKILL.md`
- rebuttal and reviewer-response drafting → `.agents/skills/ccf-rebuttal-writer/SKILL.md`
- skill maintenance and auditing → `.agents/skills/ccf-skill-forger/SKILL.md`
- submission-readiness checking → `.agents/skills/ccf-submission-checker/SKILL.md`
- figure/table/diagram visual composition → `.agents/skills/ccf-visual-composer/SKILL.md`
- writing-style distillation from an approved corpus → `.agents/skills/writing-dna-skill/SKILL.md`
- whitelist cleanup of AI writing tells → `.agents/skills/lieflat-less-ai-tone/SKILL.md`

Do not load all skills for an ordinary local edit.
Do not inject manuscript-wide reviewer passes into section drafting. Version-level consistency review is explicit, starts only after the Human marks a manuscript version ready, and is findings-only by default.

## Collaboration cues

- **locked** — analyze or propose; do not silently change meaning.
- **bounded** — adjust inside the written boundary.
- **free** — handle implementation or wording while respecting higher-level decisions.
- **unresolved** — keep uncertainty visible, prefer reversible progress, and ask before a high-impact or hard-to-reverse choice.

The Human decides central claims, claim degradation, the main story, experiment fairness, important result interpretation, ambiguous citation identity/version choices that affect meaning, stable interface meaning, active variants, permitted cross-version differences, release approval, and external publication.

The Agent performs retrieval, evidence-backed BibTeX and ledger repair, impact analysis, alternatives, consistency maintenance, drafting, low-risk revision, variant checks, release construction, template-adoption inspection and mapping, template-sync planning, and focused validation.

## Strong rules

- Do not invent contributions, facts, results, citations, identity, approval, or external-platform success.
- Do not promote expected or unresolved results into verified evidence.
- Do not turn correlation into causal language without support.
- Do not silently change a locked claim, story decision, experiment condition, limitation, or interface meaning.
- Do not copy canonical scientific content into publication variants.
- Do not overwrite an existing release instance or release record.
- Never propose or perform deletion of the protected case branches (`case/arxiv-2505-22954`, `case/arxiv-2604-01658`, `case/arxiv-2605-03042`), their case issues (#23, #24, #30), or the standing verification trackers (#21, #31); do not include them in routine cleanup or deletion reports.
- Protected branch and issue lists are repository-local; downstream papers must maintain their own lists instead of inheriting this template's IDs.
- Keep generated artifacts under ignored `dist/`; never recreate a committed generated `release/` tree.
- Keep negative or inconclusive evidence visible when it constrains a central claim.
- Do not make `paper/` depend on `.agents/`, `dist/`, or `releases/`.
- Do not merge unrelated upstream-template history into a downstream paper repository.
- Do not mechanically move or overwrite scientific content, build/CI logic, publication configuration, Human contracts, or project-specific Agent knowledge during initial adoption.
- Do not apply template adoption or updates on the default branch, or record an adoption/sync baseline before manual review and validation.

## Handoff

Report changed files, scientific or narrative meaning affected, decisions made or unresolved, impacted interfaces, variants or experiment contracts, generated release ID and manifest when relevant, adoption mappings and first baseline when adapting, template baseline/target and conflict set when syncing, and validation performed.
