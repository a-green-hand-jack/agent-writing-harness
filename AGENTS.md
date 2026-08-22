# Agent Entry

The ARIS paper project is primary. Start from the current Human-facing contract
and load only the context required for the active task.

## Orientation

Read in order:

1. `PAPER.md`
2. `EXPERIMENTS.md` only for experiment, evidence, or result interpretation
3. `PAPER_INTERFACES.md` only for recurring identity, terminology, notation, or results
4. `PUBLICATION.md` only for variants, venue planning, delivery, or releases
5. the active paper section and current diff

Rules:

- Preserve the imported ARIS scientific meaning, reported values, evidence scope, author identity, and venue/style unless the Human explicitly approves a change.
- Do not promote expected results into verified evidence.
- Do not turn the overnight observational trajectory into causal or comparative evidence.
- Do not copy canonical scientific content into publication variants.
- Keep generated artifacts under ignored `dist/`; never recreate a committed generated release tree.
- Keep `paper/` independent of `.agents/`, `dist/`, and `releases/`.

## Task routing

- unclear paper context or a new session: `.agents/skills/paper-orientation/SKILL.md`
- high-impact meaning or control boundary: `.agents/skills/control-review/SKILL.md`
- focused Human choice: `.agents/skills/decision-packet/SKILL.md`
- drafting or substantial section revision: `.agents/skills/section-writing/SKILL.md`
- result semantics or experiment design: `.agents/skills/ccf-experiment-designer/SKILL.md` as a sidecar
- positioning, narrative, or writing policy: `.agents/skills/style-alignment/SKILL.md`
- Human-requested completed-version review: `.agents/skills/manuscript-consistency-review/SKILL.md`
- recurring semantic interface: `.agents/skills/paper-interface-maintenance/SKILL.md`
- bibliography identity or metadata repair: `.agents/skills/reference-repair/SKILL.md`
- citation claim-support review: `.agents/skills/citation-support-review/SKILL.md`
- publication variants or venue planning: `.agents/skills/publication-planning/SKILL.md`
- template, page-limit, or anonymity checks: `.agents/skills/ccf-submission-checker/SKILL.md` as a sidecar
- release instance review: `.agents/skills/release-review/SKILL.md`
- initial template adoption: `.agents/skills/template-adoption/SKILL.md`
- downstream template synchronization: `.agents/skills/template-sync/SKILL.md`

## Bundled sidecars

Bundled wrappers route to immutable snapshots under `.agents/vendor/`. They
never override ARIS contracts or act as the primary owner when a local owner
exists.

- shared CCFA governance: `.agents/skills/ccf-common/SKILL.md`
- experiment evidence design: `.agents/skills/ccf-experiment-designer/SKILL.md`
- manuscript humanization preflight: `.agents/skills/ccf-humanization/SKILL.md`
- idea optimization: `.agents/skills/ccf-idea-optimizer/SKILL.md`
- idea scoring and triage: `.agents/skills/ccf-idea-reviewer/SKILL.md`
- claim/evidence consistency audit: `.agents/skills/ccf-integrity-auditor/SKILL.md`
- literature monitoring: `.agents/skills/ccf-literature-monitor/SKILL.md`
- literature search: `.agents/skills/ccf-literature-searcher/SKILL.md`
- assessment-only manuscript review: `.agents/skills/ccf-paper-reviewer/SKILL.md`
- PDF-to-exemplar conversion: `.agents/skills/ccf-paper-to-exemplar/SKILL.md`
- drafting engine: `.agents/skills/ccf-paper-writer/SKILL.md`
- paper workflow planning: `.agents/skills/ccf-pipeline-orchestrator/SKILL.md`
- external project scaffolding: `.agents/skills/ccf-project-scaffolder/SKILL.md`
- rebuttal writing: `.agents/skills/ccf-rebuttal-writer/SKILL.md`
- skill maintenance: `.agents/skills/ccf-skill-forger/SKILL.md`
- submission checks: `.agents/skills/ccf-submission-checker/SKILL.md`
- visual composition: `.agents/skills/ccf-visual-composer/SKILL.md`
- Writing DNA distillation: `.agents/skills/writing-dna-skill/SKILL.md`
- whitelist AI-tone cleanup: `.agents/skills/lieflat-less-ai-tone/SKILL.md`

Use exactly one primary owner skill. Bundled skills are sidecars and do not
authorize changes to claims, experiments, references, variants, or release
approval.
