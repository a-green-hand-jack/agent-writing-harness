# Paper Anatomy

LaTeX source lives here. It is the primary authored paper surface.

The current paper intent and collaboration boundaries are described in root `PAPER.md` and `EXPERIMENTS.md`. Stable paper-facing names are described in root `PAPER_INTERFACES.md` and implemented lightly in `paper/macros.tex`.

## Directory layout

- `main.tex`: paper entry point.
- `sections/`: authored paper sections.
- `figures/`: figure wrappers and source assets.
- `tables/`: table wrappers and source assets.
- `style/`: reusable, project-agnostic display macros (Class API). See `style/README.md`.
- `macros.tex`: project-specific macros and stable paper-facing semantic interfaces.
- `generated/`: generated paper artifacts maintained by existing harness tools.
- `venue_preamble.tex`: venue-specific preamble surface.

## Lightweight paper interfaces

`macros.tex` ships a minimal compilable interface surface:

- `\PaperTODO` for explicit Draft-only placeholders;
- `\MethodName` and `\CoreTerm` for identity and terminology;
- `\StateSymbol` for notation;
- `\MainResult` and `\MainResultUncertainty` for the primary result pair;
- an optional `generated/results-macros.tex` override hook after Human and Agent review.

Each interface has a short comment describing its meaning, practical control boundary, and Human-review trigger. The abstract, Introduction, and Method scaffolds consume these interfaces so they are not dead definitions.

Do not build a schema or generator for one-off local values. The interface model remains Human-readable and flexible. Dedicated code-repository imports and interface version tooling are future work.

## File naming convention

`paper/sections/`, `paper/figures/`, and `paper/tables/` wrapper files use a two-digit numeric prefix: `NN_name.tex`.

- First digit: `0` = body content, `1` = appendix content.
- Second digit: order within that group, starting at `0` (e.g. `00`, `01`, `02`, ...).
- `name` is a short lowercase snake_case slug.

`paper/main.tex` inputs body sections in ascending `0`-prefixed order before `\appendix`, then appendix sections in ascending `1`-prefixed order after it.

Figure wrappers additionally align basenames with a raw asset in `paper/figures/srcs/`: `figures/00_teaser.tex` wraps `figures/srcs/00_teaser.pdf` (or `.png`/`.jpg`/`.jpeg`). `paper/figures/srcs/` holds only raw figure assets, never generated wrapper `.tex` files.

`scripts/check-anatomy-drift.py` and `scripts/check-figures-tables.py` enforce this naming and the wrapper-to-asset alignment; see `.agent/anatomy-policy.md` for the existing doctrine-level record.
