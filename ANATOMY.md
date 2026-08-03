# Repository Anatomy

This repository has two primary layers: one canonical authored paper and an optional Agent sidecar. Generated releases are externalized as immutable instances rather than committed copies.

## Human and authored surface

- `README.md`: direct starting point.
- `Makefile`: Human build commands with `VARIANT=...`.
- `PAPER.md`: positioning, thesis, claims, story, style, protected decisions, and unresolved work.
- `EXPERIMENTS.md`: paper-facing experiment questions and interpretation boundaries.
- `PAPER_INTERFACES.md`: stable identity, terminology, notation, result, claim, and artifact interfaces.
- `PUBLICATION.md`: variants, delivery targets, release-instance contract, and Human review boundaries.
- `DECISIONS.md`: durable rationale for important Human decisions.
- `paper/`: canonical LaTeX source and small publication overlays.
- `releases/records/`: durable Markdown provenance for reviewed release instances.

A clean copy of `paper/` must compile every supported variant independently.

## Canonical paper and variants

`paper/main.tex`, sections, figures, tables, style, references, and semantic interfaces form the canonical paper. `paper/variants/` contains only small configurations and build drivers.

Variants may control publication-facing presentation. They do not own copied sections or separate scientific content.

## Agent sidecar

- `AGENTS.md`: thin routing entrypoint.
- `.agents/knowledge/`: optional reference knowledge loaded only when relevant.
- `.agents/skills/`: focused procedures for writing, publication planning, release review, and downstream template synchronization.
- `.agents/template-sync.json`: downstream-local upstream location and last reviewed template baseline.
- `.agents/tools/`: structure, contract, interface, publication, release-build, manifest, record, and template-sync tools.
- `.agents/tests/`: positive and negative regressions.
- `.agents/runtime/`: ignored short-lived coordination, release, and template-sync state.

## Downstream template synchronization

A repository created from the GitHub Template has an independent history. Template updates are adopted through a path-level three-way plan, not by merging unrelated histories.

```text
last reviewed upstream baseline
        +
requested upstream target
        +
current downstream files
        ↓
safe / already / manual / conflict / ignored plan
        ↓
safe staged updates + ignored merge bundle
        ↓
downstream validation and PR CI
        ↓
new recorded upstream baseline
```

Human contracts and authored paper content are protected by default. Downstream-only files are not deleted merely because they are absent upstream.

## Generated release instances

- `dist/<release-id>/`: ignored immutable candidate containing manifest, report, and selected artifacts.
- GitHub Actions artifacts, GitHub Releases, Overleaf, venue portals, and arXiv: delivery systems, not authored sources.
- `releases/records/<release-id>.md`: optional tracked Human-reviewed provenance; no binaries or generated TeX trees.

The obsolete committed `release/` directory is forbidden.

## Dependency direction

```text
Human intent and decisions
        ↓
PAPER / EXPERIMENTS / INTERFACES / PUBLICATION / DECISIONS
        ↓
paper/ canonical source + small variant overlay
        ↓
make pdf VARIANT=<name>
        ↓
release.py build → ignored dist/<release-id>/ → delivery system
        ↓
optional immutable Markdown record in releases/records/

Agent task
        ↓
AGENTS.md → one focused skill / knowledge document
        ↓
.agents/tools/verify.sh, template sync, or release workflow
```

The paper must not import `.agents/`, `dist/`, or `releases/`. Generic Agent knowledge and upstream template defaults must not override a current explicit Human decision.
