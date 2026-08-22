# Figures

Figure wrappers live in this directory. Their source assets live under
`figures/srcs/`; source provenance for this imported paper is recorded in
`paper/supplementary/source-attribution.md`. There is no separate figure registry.

## Naming convention

Figure wrapper files use a two-digit numeric prefix: `NN_name.tex`.

- First digit: `0` = body figure, `1` = appendix figure.
- Second digit: order within that group, starting at `0`.
- `name` is a short lowercase snake_case slug (e.g. `teaser`, `pipeline`).

Each wrapper's basename must match a raw asset under `figures/srcs/` with the
same basename, e.g. `figures/00_teaser.tex` wraps `\includegraphics` of
`figures/srcs/00_teaser.pdf` (or `.png`/`.jpg`/`.jpeg`). From the repository
root, `.agents/tools/check-structure.py` enforces wrapper-to-asset basename
alignment.
