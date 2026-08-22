# Paper Anatomy

`paper/` is the one canonical authored LaTeX project and compiles independently
of the Agent sidecar. Current intent lives in `PAPER.md` and `EXPERIMENTS.md`;
stable names live in `PAPER_INTERFACES.md` and `paper/macros.tex`.

## Directory layout

- `main.tex`: canonical entry point with publication-variant hooks.
- `sections/`: authored canonical sections.
- `figures/`: figure wrappers and `srcs/` assets.
- `tables/`: table wrappers and source material.
- `style/`: reusable display helpers and the imported ICLR 2026 files.
- `macros.tex`: project-specific semantic interfaces and source-compatible shortcuts.
- `variants/`: small publication overlays and build drivers.
- `generated/`: rebuildable paper artifacts, never a second authored source.
- `supplementary/`: original source attribution and canonical original PDF.
- `venue_preamble.tex`: imported venue-specific preamble.

## Publication variants

Supported variants are `draft`, `anonymous`, `camera-ready`, and `arxiv`.
Variants may hide identity or acknowledgements and select appendix presentation;
they do not copy sections or redefine scientific meaning.

## Release boundary

Release packaging reads `paper/` and writes an ignored immutable instance under
`dist/`. It does not edit canonical files or create a tracked sibling paper.

## Lightweight interfaces

`macros.tex` provides `\PaperTODO`, `\PaperTitle`, `\PaperAuthors`,
`\MethodName`, `\CoreTerm`, `\StateSymbol`, `\MainResult`, and
`\MainResultUncertainty`, plus the reviewed
`generated/results-macros.tex` hook. Anonymous variants hide
`\PaperAuthors`; they do not redefine identity.

## File naming

Section, figure-wrapper, and table-wrapper files use `NN_name.tex`: first digit
`0` for body or `1` for appendix, second digit for order, then lowercase
snake_case. Figure wrappers align basenames with source assets under
`paper/figures/srcs/`.

`.agents/tools/check-structure.py` enforces structure and independence;
`.agents/tools/check-publication.py` enforces the small-overlay boundary.
