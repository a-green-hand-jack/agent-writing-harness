# TODO Paper Title

[![PR validation](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml/badge.svg?branch=main)](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml)

A paper-first repository for Human–Agent collaborative scientific writing.

## Start writing

1. If this repository was created from the template and `.agents/init-state.json` does not exist, run `python3 .agents/tools/paper-init.py clean --commit` before editing paper content. This strips upstream template governance IDs and records the initialization.
2. Record thesis, story, style, protected decisions, and open questions in `PAPER.md`.
2. Record paper-facing experiment questions and interpretation boundaries in `EXPERIMENTS.md`.
3. Maintain recurring identity, terminology, notation, and results through `PAPER_INTERFACES.md` and `paper/macros.tex`.
4. Record publication variants and allowed differences in `PUBLICATION.md`.
5. Have the Agent construct and repair BibTeX from retrieved authoritative evidence, maintain `references/ledger.json` in the same change, and follow `REFERENCES.md`; never invent free-form metadata.
6. If the target venue is active, record its official planning facts under `.agents/knowledge/venues/<venue>-<year>.md`; see the venue knowledge schema before scheduling around deadlines or page limits.
7. Edit the one canonical LaTeX source under `paper/`.
8. Build:

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

Clean generated LaTeX files with `make clean`.

## Human-facing surface

- `PAPER.md` — positioning, claims, story, style, protected decisions, and unresolved work.
- `EXPERIMENTS.md` — paper-facing experiment questions and interpretation boundaries.
- `PAPER_INTERFACES.md` — stable semantic names shared by canonical and variant surfaces.
- `PUBLICATION.md` — variants, delivery targets, release-instance boundaries, and Human review triggers.
- `REFERENCES.md` and `references/ledger.json` — bibliographic identity states and Human-reviewed claim evidence.
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

`AGENTS.md` is a thin router. Agents load current contracts and one focused skill or knowledge document.

```bash
bash .agents/tools/verify.sh
```

`verify.sh` checks structure, documentation consistency, Draft contracts, interfaces, the offline reference ledger, publication variants, release-record boundaries, template-adoption and template-sync configuration, and regressions. The separate `Reference validation` workflow installs hash-locked Pybtex format validation and the open-source metadata checker only after the protected publication policy enables them.

## Adopting the template in an existing repository

An existing paper repository may use different paths, build commands, CI, venue files, and Agent instructions. Do not copy the template tree over it. Run the adoption tool from a trusted template checkout so the target repository does not need `.agents/` in advance:

```bash
python3 /path/to/ccfa-writing-paper-template/.agents/tools/template-adoption.py \
  --root /path/to/existing-paper inspect
python3 /path/to/ccfa-writing-paper-template/.agents/tools/template-adoption.py \
  --root /path/to/existing-paper plan --fetch
python3 /path/to/ccfa-writing-paper-template/.agents/tools/template-adoption.py \
  --root /path/to/existing-paper apply
```

The inspection infers candidates for the main TeX entrypoint, bibliography, sections, figures, tables, style, experiment/evaluation surfaces, build, CI, and Agent instructions. The plan applies only missing Agent-sidecar anatomy, knowledge, skills, tests, tools, and runtime-ignore infrastructure mechanically and creates an uninitialized downstream sync configuration. Paper content, Human contracts, references, venue/style configuration, build logic, CI, and existing Agent knowledge remain manual or conflict surfaces.

After repository-specific semantic migration and validation:

```bash
python3 .agents/tools/template-adoption.py verify --variants
python3 .agents/tools/template-adoption.py finalize --reviewed
```

Finalization requires a successful full-variant verification report for the unchanged downstream state, then records the exact reviewed template commit in `.agents/template-sync.json`. Subsequent template updates use `template-sync`, not adoption. See `.agents/skills/template-adoption/SKILL.md`.

## Syncing a downstream paper repository

A paper repository created from this GitHub Template, or completed through reviewed adoption, has an independent Git history. Do not merge the upstream template branch into the paper history. Use the optional Agent skill and path-level synchronization tool instead:

```bash
python3 .agents/tools/template-sync.py validate
python3 .agents/tools/template-sync.py fetch
python3 .agents/tools/template-sync.py plan               # after adoption or a recorded baseline
python3 .agents/tools/template-sync.py plan --bootstrap   # only when no trustworthy baseline exists
python3 .agents/tools/template-sync.py apply
```

The plan separates changes into `safe`, `already`, `manual`, `conflict`, and `ignored`. Safe infrastructure updates can be staged mechanically. Human contracts, paper content, references, macros, CI, build logic, dependency locks, venue configuration, style, and project knowledge remain protected and are exported to an ignored merge bundle for Agent review. Reference-integrity tooling received by an older sync engine remains inert until the protected `PUBLICATION.md` policy and `paper/refs.bib` activation marker are merged after ledger migration and downstream-local `.agents/template-sync.json` records `reference_integrity.adopted=true`.

After manual merges and successful downstream validation:

```bash
python3 .agents/tools/template-sync.py record --reviewed
```

Adoption records the first reviewed baseline during `finalize`. A template-created or older repository without a trustworthy baseline instead uses one reviewed `--bootstrap` synchronization. Future synchronizations use the recorded upstream commit as the three-way baseline and run `plan` without `--bootstrap`. See `.agents/skills/template-sync/SKILL.md`.

## Working with Overleaf

The Overleaf Git project receives only the tracked contents of `paper/`, mapped to the Overleaf project root. It never receives repository governance, CI, Agent tooling, contracts, or release records.

Add a project-specific `.agents/overleaf-sync.json` containing the remote name, Overleaf Git URL, branch, and `source_prefix: "paper"`. Credentials are never stored in tracked configuration. Validate and fetch the configured project:

```bash
python3 .agents/tools/overleaf-sync.py validate
python3 .agents/tools/overleaf-sync.py fetch
```

Export an approved clean `main`:

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

Pull requests must pass `harness`, `references`, four real-TeX variant jobs, `paper-only`, and `release-package`. See `CONTRIBUTING.md`.
