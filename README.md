# TODO Paper Title

[![PR validation](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml/badge.svg?branch=main)](https://github.com/a-green-hand-jack/ccfa-writing-paper-template/actions/workflows/pr-validation.yml)

A paper-first repository for Human–Agent collaborative scientific writing.

## Start writing

1. Record thesis, story, style, protected decisions, and open questions in `PAPER.md`.
2. Record paper-facing experiment questions and interpretation boundaries in `EXPERIMENTS.md`.
3. Maintain recurring identity, terminology, notation, and results through `PAPER_INTERFACES.md` and `paper/macros.tex`.
4. Record publication variants and allowed differences in `PUBLICATION.md`.
5. Edit the one canonical LaTeX source under `paper/`.
6. Build:

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
- `DECISIONS.md` — durable rationale for important Human decisions.
- `paper/` — the canonical authored project and small publication overlays.

The cues **locked**, **bounded**, **free**, and **unresolved** remain flexible collaboration language, not a rigid state machine.

## Publication variants

`paper/variants/` contains small overlays for `draft`, `anonymous`, `camera-ready`, and `arxiv`. They may change author visibility, acknowledgements, appendix inclusion, and publication-facing presentation hooks. They must not copy or silently diverge scientific prose, claims, result meaning, limitations, or experiment interpretation.

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

`verify.sh` checks structure, Draft contracts, interfaces, publication variants, release-record boundaries, template-sync configuration, and regressions.

## Syncing a downstream paper repository

A paper repository created from this GitHub Template has an independent Git history. Do not merge the upstream template branch into the paper history. Use the optional Agent skill and path-level synchronization tool instead:

```bash
python3 .agents/tools/template-sync.py validate
python3 .agents/tools/template-sync.py fetch
python3 .agents/tools/template-sync.py plan --bootstrap   # first reviewed sync only
python3 .agents/tools/template-sync.py apply
```

The plan separates changes into `safe`, `already`, `manual`, `conflict`, and `ignored`. Safe infrastructure updates can be staged mechanically. Human contracts, paper content, references, macros, venue configuration, style, and project knowledge remain protected and are exported to an ignored merge bundle for Agent review.

After manual merges and successful downstream validation:

```bash
python3 .agents/tools/template-sync.py record --reviewed
```

Future synchronizations use the recorded upstream commit as the three-way baseline and normally run `plan` without `--bootstrap`. See `.agents/skills/template-sync/SKILL.md`.

## Project boundary and CI

The repository has no legacy harness, capability registry, Bridge layer, experiment ledger, product adapter mirror, or committed generated release tree. A clean copy of `paper/` compiles all variants without `.agents/`.

Pull requests must pass `harness`, four real-TeX variant jobs, `paper-only`, and `release-package`. See `CONTRIBUTING.md`.
