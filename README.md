# TODO Paper Title

[![PR validation](https://github.com/a-green-hand-jack/agent-writing-harness/actions/workflows/pr-validation.yml/badge.svg?branch=main)](https://github.com/a-green-hand-jack/agent-writing-harness/actions/workflows/pr-validation.yml)

A paper-first repository that works as an **agent-writing harness**: from this
GitHub Template you get a **writing repo** that a coding agent (Codex, OpenCode,
Claude, Copilot, or a plain shell workflow) uses to draft, revise, evidence,
and release a paper. The harness supports both **collaborative** writing, where
the Human stays in the loop for each substantive step, and **autonomous**
writing, where the Human supplies a brief and materials and the Agent runs the
paper long-term on its own with periodic checkpoints.

Agents starting from this GitHub Template should read `AGENT_GUIDE.md` first.
It defines the product-independent path from this **template repo** to a
separate downstream **writing repo**, then indexes the writing, evidence,
publication, adoption, synchronization, and release workflows.

For the rationale behind those contracts and tools, see
`WHY_THIS_TEMPLATE.md`: it explains the writing risks the template is designed
to reduce, the complete built-in paper skill stack, its practical gains, and its
limits.

## Start writing

1. If an Agent is currently in this template repo, load `ccf-project-scaffolder` in template-create mode. It follows `AGENT_GUIDE.md` to create and initialize a separate writing repo from the GitHub Template. Do not draft a real paper in the template repo.
2. To start a paper from a **brief repo** (a Human-owned repository with a `BRIEF.md` content spec plus template-usage instructions), have the Agent load `paper-brief-ingest`: it creates the initialized writing repo, ingests the brief into the paper contracts with `python3 .agents/tools/paper-brief.py ingest --brief <path>`, and records the declared operating mode. This is the recommended entry point for autonomous agent writing.
3. If independent repository-creation evidence confirms that this repository was created from the template, its origin is not the upstream template, and `.agents/init-state.json` does not exist, run `python3 .agents/tools/paper-init.py record-template-origin --commit` followed by `python3 .agents/tools/paper-init.py clean --commit` before editing paper content. The first command records GitHub's template provenance; the second strips upstream template governance IDs and records initialization. A non-upstream origin, copied template files, or the generic `paper-init.py status` label is not enough; use template adoption for an unrelated or ambiguous existing paper repository.
4. Give the Agent the first-session packet in `AGENT_GUIDE.md`: research seed, evidence inventory, target or `unresolved`, authorship constraints, first deliverable, and hard constraints. This packet is enough to begin onboarding and contract setup; section drafting requires supplied or Human-approved claims and evidence for that section.
5. Record thesis, story, style, protected decisions, and open questions in `PAPER.md`.
6. Record only real paper-facing experiment questions and interpretation boundaries in `EXPERIMENTS.md`.
7. Maintain recurring identity, terminology, notation, and results through `PAPER_INTERFACES.md` and `paper/macros.tex`.
8. Record publication variants and allowed differences in `PUBLICATION.md`.
9. Have the Agent construct and repair BibTeX from retrieved authoritative evidence, maintain `references/ledger.json` in the same change, and follow `REFERENCES.md`; never invent free-form metadata.
10. For every substantive citation, have the Agent run the Draft citation-support check (`citation-support-review`): inventory the active occurrence, resolve or discover the source, retrieve exact passages, and record a passing result as provisional. Never insert a citation from title relevance or metadata existence alone.
11. If the target venue is active, record its official planning facts under `.agents/knowledge/venues/<venue>-<year>.md`; see the venue knowledge schema before scheduling around deadlines or page limits.
12. Edit the one canonical LaTeX source under `paper/`.
13. Build:

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

Clean generated LaTeX files with `make clean`.

## Operating modes

A writing repo declares its operating mode in `PAPER.md` (`## Operating mode`).
The mode changes how much confirmation the Agent needs, never what the Agent may
silently alter.

- **Collaborative** (`Mode: collaborative`): the Human stays in the loop for each substantive step. The Agent drafts and revises on request and brings high-impact choices to a decision packet.
- **Autonomous** (`Mode: autonomous`): the Human provides the brief and materials, then the Agent proceeds through drafting, self-review, polish, and variant and checkpoint builds on its own, and may prepare idea shaping and evidence analysis as proposals only. The Agent stops for Human approval before changing a locked item, approving a release, or final submission.

Autonomy is not a license to fabricate: even in autonomous mode the strong rules
in `AGENTS.md` apply — no invented contributions, facts, results, citations,
identity, approval, or external-platform success, and no promotion of expected
or unresolved results into verified evidence.

The commands above are this repository's default `canonical-variants` build
profile. An adopted publisher template may retain a single native entrypoint or
declare its own named builds in `.agents/paper-build.json`; see
`LATEX_TEMPLATES.md` for the schema, verified template matrix, official sources,
and validation limits.

## Human-facing surface

- `BRIEF.md` — the Human-authored paper brief (content spec plus template-usage instructions) ingested at bootstrap and kept as provenance and material inventory.
- `PAPER.md` — positioning, claims, story, style, protected decisions, operating mode, and unresolved work.
- `EXPERIMENTS.md` — paper-facing experiment questions and interpretation boundaries.
- `PAPER_INTERFACES.md` — stable semantic names shared by canonical and variant surfaces.
- `PUBLICATION.md` — variants, delivery targets, release-instance boundaries, and Human review triggers.
- `REFERENCES.md` and `references/ledger.json` — bibliographic identity states and Human-reviewed claim evidence, bound to exact citation occurrences with claim fingerprints.
- `DECISIONS.md` — durable rationale for important Human decisions.
- `paper/` — the canonical authored project and small publication overlays.

The cues **locked**, **bounded**, **free**, and **unresolved** remain flexible collaboration language, not a rigid state machine.

## Publication variants

`paper/variants/` contains small overlays for `draft`, `anonymous`, `camera-ready`, and `arxiv`. They may change author visibility, acknowledgements, appendix inclusion, and publication-facing presentation hooks. They must not copy or silently diverge scientific prose, claims, result meaning, limitations, or experiment interpretation.

The root `paper/main.tex` defaults to `anonymous` for direct Overleaf or source imports. The Makefile keeps `draft` as the daily-writing default, so local `make pdf` and Overleaf do not require the same variant selection.

## Release instances

Generated delivery artifacts are not committed as another paper tree. Build a strict immutable instance with:

```bash
RELEASE_ID=iclr2027-submission-r1 VARIANT=anonymous \
  bash .agents/tools/release.sh
```

The instance appears under ignored `dist/<release-id>/` with `manifest.json`, `build-report.md`, PDF/source artifacts, source fingerprints, checksums, and isolated-compilation receipts. `releases/records/` stores reviewed Markdown provenance only.

The factory template is intentionally unresolved, so strict release builds fail until a real paper has cleared the Release contract. CI uses an explicit Draft-validation profile to verify packaging without claiming submission readiness.

## Agent sidecar

`AGENT_GUIDE.md` is the product-independent onboarding and lifecycle index.
`AGENTS.md` remains the thin binding router: Agents load current contracts and
one focused skill or knowledge document.

```bash
bash .agents/tools/verify.sh
```

`verify.sh` checks structure, documentation consistency, Draft contracts, interfaces, the offline reference ledger (including occurrence coverage and claim-support state), publication variants, release-record boundaries, template-adoption and template-sync configuration, regressions, vendored-skill integrity, and one registered task-level evaluation scenario per bundled wrapper. The deterministic scenario check does not invoke a model; live worker/reviewer sub-agent runs are explicit non-blocking evaluations. The separate `Reference validation` workflow installs hash-locked Pybtex format validation and the open-source metadata checker only after the protected publication policy enables them.

## Bundled Agent skills

The template ships the CCFA-Skills suite and writing-dna-skill as immutable
snapshots under `.agents/vendor/` so downstream paper repositories work out of
the box without any global skill installation. All 17 `ccf-*` skills plus
`writing-dna-skill` and `lieflat-less-ai-tone` are available as wrappers under
`.agents/skills/`; each wrapper routes to the vendor snapshot and enforces the
paper-contract boundaries. Bundled skills are never loaded standalone as
owners: each task loads exactly one primary owner, and the bundled wrappers
act as sidecars (marked `sidecar` in `AGENTS.md`) that never override a local
owner skill or a Human contract.

- Writing engine: `ccf-paper-writer` runs inside the `section-writing` contract.
- Review: `ccf-paper-reviewer` and `ccf-integrity-auditor` run inside the
  Human-triggered, findings-only `manuscript-consistency-review` boundary.
- Style: `writing-dna-skill` distills a Human-approved Writing DNA under
  `.agents/knowledge/writing/` (see `.agents/knowledge/writing/README.md`) that
  never overrides the paper contracts.
- Everything else: experiment design, idea triage, literature search/monitor,
  visual composition, submission checks, rebuttals, and pipeline planning.

Vendor provenance, hashes, and excluded upstream resources (third-party paper
PDFs, the venue LaTeX corpus, demo assets) are recorded in
`.agents/dependencies/vendored-skills/provenance.json` and verified by
`.agents/tools/check-vendored-skills.py`. Never edit the vendor tree; updates
arrive through template-sync after review. See `.agents/vendor/README.md`.

The task probes under `.agents/evals/vendored-skills/` distinguish installation
evidence from live behavior. Every wrapper has one synthetic scenario with
required and forbidden behavior; model-backed runs use separate worker and
reviewer sub-agents and remain narrower than a general quality benchmark.

## Adopting the template in an existing repository

An existing paper repository may use different paths, build commands, CI, venue files, and Agent instructions. Do not copy the template tree over it. Run the adoption tool from a trusted template checkout so the target repository does not need `.agents/` in advance:

```bash
python3 /path/to/agent-writing-harness/.agents/tools/template-adoption.py \
  --root /path/to/existing-paper inspect
python3 /path/to/agent-writing-harness/.agents/tools/template-adoption.py \
  --root /path/to/existing-paper plan --fetch
python3 /path/to/agent-writing-harness/.agents/tools/template-adoption.py \
  --root /path/to/existing-paper apply
```

The inspection infers candidates for the main TeX entrypoint, bibliography, sections, figures, tables, style, experiment/evaluation surfaces, build, CI, and Agent instructions. The plan applies only missing Agent-sidecar anatomy, knowledge, skills, tests, tools, and runtime-ignore infrastructure mechanically and creates an uninitialized downstream sync configuration. Paper content, Human contracts, references, venue/style configuration, build logic, CI, and existing Agent knowledge remain manual or conflict surfaces.

After repository-specific semantic migration and validation:

```bash
python3 .agents/tools/template-adoption.py assess
python3 .agents/tools/template-adoption.py verify --builds
python3 .agents/tools/template-adoption.py finalize --reviewed
```

`assess` is a non-authorizing collect-all diagnostic: it runs every standard leaf check and every build declared in `.agents/paper-build.json`, records every outcome in `assessment.json`/`assessment.md`, and continues after failures. It is intentionally distinct from reviewed verification and can never authorize finalization. Finalization requires a successful all-build `verify` report for the unchanged downstream state, then records the exact reviewed template commit in `.agents/template-sync.json`. The legacy `--variants` flag remains an alias for `--builds`. Subsequent template updates use `template-sync`, not adoption. See `.agents/skills/template-adoption/SKILL.md`.

## Syncing a downstream paper repository

A paper repository created from this GitHub Template, or completed through reviewed adoption, has an independent Git history. Do not merge the upstream template branch into the paper history. Use the optional Agent skill and path-level synchronization tool instead:

```bash
python3 .agents/tools/template-sync.py validate
python3 .agents/tools/template-sync.py fetch
python3 .agents/tools/template-sync.py plan               # after adoption or a recorded baseline
python3 .agents/tools/template-sync.py plan --bootstrap   # only when no trustworthy baseline exists
python3 .agents/tools/template-sync.py apply
```

The shared path policy is registered in `.agents/template-inheritance.json`; downstream-local additions remain in `.agents/template-sync.json`. The plan separates changes into `safe`, `already`, `manual`, `conflict`, and `ignored`. Safe infrastructure updates can be staged mechanically. Human contracts, paper content, publication variants, references, macros, CI, build logic, dependency locks, venue configuration, style, and project knowledge remain protected and are exported to an ignored merge bundle for Agent review. Reference-integrity tooling received by an older sync engine remains inert until the protected `PUBLICATION.md` policy and `paper/refs.bib` activation marker are merged after ledger migration and downstream-local `.agents/template-sync.json` records `reference_integrity.adopted=true`.

After manual merges and successful downstream validation:

```bash
python3 .agents/tools/template-sync.py verify --reviewed
python3 .agents/tools/template-sync.py record --reviewed
```

Planning accepts only commits reachable from the configured branch of the configured upstream URL, and synchronization is blocked while adoption is `in_progress`. Template-sync runtime directories and files fail closed on symlinks and wrong filesystem types; plan, merge-bundle, application, verification, cleanup, and custom repository-local plan paths are never followed through a symlink outside the repository. Verification directly checks that every safe addition, modification, and deletion matches the target in both the index and worktree before running the repository checks and every build declared in `.agents/paper-build.json`. Recording repeats those direct state checks and reruns all mandatory commands; receipts and reports remain evidence, not authority. Reviewed adoption metadata remains compatible with later baseline advancement.

Adoption records the first reviewed baseline during `finalize`. A template-created or older repository without a trustworthy baseline instead uses one reviewed `--bootstrap` synchronization. Future synchronizations use the recorded upstream commit as the three-way baseline and run `plan` without `--bootstrap`. See `.agents/skills/template-sync/SKILL.md`.

## Working with Overleaf

The Overleaf Git project receives only the tracked contents of `paper/`, mapped to the Overleaf project root. It never receives repository governance, CI, Agent tooling, contracts, or release records.

Add a project-specific `.agents/overleaf-sync.json` containing the remote name, Overleaf Git URL, branch, and `source_prefix: "paper"`. Credentials are never stored in tracked configuration. Validate and fetch the configured project:

```bash
python3 .agents/tools/overleaf-sync.py validate
python3 .agents/tools/overleaf-sync.py fetch
```

Export an approved clean canonical branch (`main`, `master`, `trunk`, or a protected `case/<name>` branch):

```bash
python3 .agents/tools/overleaf-sync.py push
```

When Overleaf contains online edits, import them on a review branch before exporting again:

```bash
git switch -c sync/overleaf-YYYYMMDD
python3 .agents/tools/overleaf-sync.py pull
make pdf
bash .agents/tools/verify.sh
```

The one-time initial publication uses `push --bootstrap`; it preserves the pre-existing Overleaf commit in Git history while replacing the visible working tree with canonical `paper/`.

## Protected evidence surface

The repository protects its current and future real-paper case branches and the corresponding case and standing verification issues. Do not propose or perform their deletion, and do not include them in routine cleanup or branch/worktree/PR deletion discussions. Record the exact list in that repository's own `DECISIONS.md`; do not copy another repository's IDs.

## Project boundary and CI

The repository has no legacy harness, capability registry, Bridge layer, experiment ledger, product adapter mirror, or committed generated release tree. A clean copy of `paper/` compiles all variants without `.agents/`.

Pull requests must pass `harness`, `references`, four real-TeX variant jobs,
`paper-only`, and `release-package`. Template-repository development also runs
`vendored-skills` and `official-templates`; the latter never runs in a
downstream writing repository. See `CONTRIBUTING.md`.

## Development surface (template-dev branch only)

This branch (`template-dev`) is the template's development surface. It contains
template-development-only machinery that must never appear in a writing repo:
`.agents/evals/`, the vendor and skill validation checkers
(`check-vendored-skills.py`, `check-vendored-skill-evals.py`, `check-skills.py`,
`check-actions.py`), the vendored-skills dependency lock
(`.agents/dependencies/vendored-skills/`), and development-only tests.

The GitHub default branch is `main`, which contains only the paper-facing
surface and is what GitHub Template creation copies. Template development
happens on this branch; paper-facing changes are released to `main` after the
development-surface validation passes here. A writing repo must never contain
the paths listed above.
