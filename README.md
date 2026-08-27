# ARIS: Autonomous Research via Adversarial Multi-Agent Collaboration

A paper-first repository for the ARIS technical report, using its imported ICLR
2026 style and preserving arXiv 2605.03042 source attribution.

## Human-facing surface

- `PAPER.md`: thesis, contributions, story, style, protected meaning, and unresolved work.
- `EXPERIMENTS.md`: observational evidence, future-work protocol, and interpretation boundaries.
- `PAPER_INTERFACES.md`: stable identity, terminology, notation, and reported-result meaning.
- `PUBLICATION.md`: variants, Overleaf boundary, delivery targets, and immutable release policy.
- `REFERENCES.md` and `references/ledger.json`: bibliography identity and occurrence-level claim-support states.
- `DECISIONS.md`: durable project decisions.
- `paper/`: the only canonical authored LaTeX project.

The cues **locked**, **bounded**, **free**, and **unresolved** are flexible
Human-Agent collaboration language, not a separate permission engine.

## Build

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

`make pdf` defaults to `draft`; `paper/main.tex` defaults to `anonymous` for a
direct source or Overleaf import. Clean generated LaTeX files with `make clean`.

The commands above are this repository's `canonical-variants` build profile.
`.agents/paper-build.json` records the same native entrypoint and commands for
adoption and template-sync verification; see `LATEX_TEMPLATES.md` for the
schema, verified template matrix, official sources, and validation limits.

## Validate

```bash
bash .agents/tools/verify.sh
```

The verification chain checks paper-first structure, Human contracts, stable
interfaces, references, publication variants, release boundaries, template
synchronization, regressions, and immutable vendored skills. Real TeX builds
remain separate integration evidence and must cover all four variants.

## Releases and Overleaf

Generated delivery artifacts belong under ignored `dist/<release-id>/`; never
commit another paper tree. Durable reviewed provenance belongs under
`releases/records/`.

The configured Overleaf project is a paper-only working copy. Use
`.agents/tools/overleaf-sync.py` to validate, fetch, import, or export the
tracked `paper/` tree. Overleaf never receives governance, CI, contracts, or
Agent tooling, and it is not a second canonical source.

## Agent sidecar

`AGENTS.md` is a thin router. Agents start from the current Human contracts and
load one primary owner skill plus explicitly allowed sidecars.

This repository ships the CCFA-Skills suite and writing-dna-skill as immutable
snapshots under `.agents/vendor/`. All 17 `ccf-*` skills plus
`writing-dna-skill` and `lieflat-less-ai-tone` are available as wrappers under
`.agents/skills/`; they never override ARIS contracts or approve scientific
meaning. Vendor provenance and hashes are recorded under
`.agents/dependencies/vendored-skills/`.
