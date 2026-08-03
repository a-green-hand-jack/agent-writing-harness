# Paper Anatomy

`paper/` is the canonical authored LaTeX project and must compile independently of the Agent sidecar.

The current paper intent and collaboration boundaries live in root `PAPER.md` and `EXPERIMENTS.md`. Stable paper-facing names are described in `PAPER_INTERFACES.md` and implemented lightly in `paper/macros.tex`.

## Directory layout

- `main.tex`: paper entry point.
- `sections/`: authored sections.
- `figures/`: figure wrappers and `srcs/` assets.
- `tables/`: table wrappers and source material.
- `style/`: reusable, project-agnostic display helpers.
- `macros.tex`: project-specific semantic interfaces.
- `generated/`: rebuildable paper artifacts; generated files are never a second authored source.
- `venue_preamble.tex`: venue-specific preamble surface.

## Lightweight interfaces

`macros.tex` provides:

- `\PaperTODO` for explicit Draft-only placeholders;
- `\MethodName` and `\CoreTerm` for identity and terminology;
- `\StateSymbol` for notation;
- `\MainResult` and `\MainResultUncertainty` for the primary result pair;
- an optional `generated/results-macros.tex` hook after Human–Agent review.

Each interface records meaning, practical control boundary, and Human-review trigger. Do not introduce a schema or generator for one-off local values.

## File naming

Section, figure-wrapper, and table-wrapper files use `NN_name.tex`:

- first digit `0` = body, `1` = appendix;
- second digit = order within the group;
- name = lowercase snake_case.

`main.tex` inputs body sections in ascending order before `\appendix`, then appendix sections in ascending order.

Figure wrappers align basenames with a source asset under `paper/figures/srcs/`, for example `figures/00_teaser.tex` and `figures/srcs/00_teaser.pdf`.

`.agents/tools/check-structure.py` enforces section inputs, ordering, wrapper/asset alignment, and the rule that `paper/` does not depend on `.agents/`.
