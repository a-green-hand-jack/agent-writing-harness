# Paper Anatomy

`paper/` is the one canonical authored LaTeX project and must compile independently of the Agent sidecar.

Current intent lives in `PAPER.md` and `EXPERIMENTS.md`. Stable semantic names live in `PAPER_INTERFACES.md` and `paper/macros.tex`. Publication differences live in `PUBLICATION.md` and small overlays under `paper/variants/`.

## Directory layout

- `main.tex`: canonical paper entry point with variant hooks.
- `sections/`: authored canonical sections.
- `figures/`: figure wrappers and `srcs/` assets.
- `tables/`: table wrappers and source material.
- `style/`: reusable project-agnostic display helpers.
- `macros.tex`: project-specific semantic interfaces, including canonical title and visible author identity.
- `variants/`: small publication overlays and build drivers.
- `generated/`: rebuildable paper artifacts; never a second authored source.
- `venue_preamble.tex`: venue-specific preamble surface.

## Publication variants

Supported variants are `draft`, `anonymous`, `camera-ready`, and `arxiv`.

`variants/common.tex` declares switches. `variants/config/*.tex` sets author visibility, acknowledgements, and appendix inclusion. Tiny drivers select a config and input `main.tex`.

Variants must not copy sections, redefine scientific claims, or maintain separate result meanings. Add an allowed difference only through `PUBLICATION.md`, checker/tests, and Human review.

## Lightweight interfaces

`macros.tex` provides:

- `\PaperTODO` for explicit Draft-only placeholders;
- `\PaperTitle` and `\PaperAuthors` for canonical identity;
- `\MethodName` and `\CoreTerm` for method identity and terminology;
- `\StateSymbol` for notation;
- `\MainResult` and `\MainResultUncertainty` for the primary result pair;
- an optional `generated/results-macros.tex` hook after Human–Agent review.

Anonymous variants hide `\PaperAuthors`; they do not replace the canonical identity with a second source.

## File naming

Section, figure-wrapper, and table-wrapper files use `NN_name.tex`:

- first digit `0` = body, `1` = appendix;
- second digit = order within the group;
- name = lowercase snake_case.

`main.tex` inputs body sections in ascending order before `\appendix`, then appendix sections in ascending order. Figure wrappers align basenames with source assets under `paper/figures/srcs/`.

`.agents/tools/check-structure.py` enforces section structure and paper independence. `.agents/tools/check-publication.py` enforces the small-overlay variant boundary.
