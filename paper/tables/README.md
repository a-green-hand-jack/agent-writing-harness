# Tables

Table wrappers live in this directory. Table bodies may be authored inline or loaded from `paper/generated/tables/`. Keep the metric, split, aggregation, uncertainty, and provenance visible for quantitative results; recurring result meaning belongs in `PAPER_INTERFACES.md` and `paper/macros.tex`.

## Naming convention

Table wrapper files use the same two-digit numeric prefix as figures: `NN_name.tex`.

- First digit: `0` = body table, `1` = appendix table.
- Second digit: order within that group, starting at `0`.
- `name` is a short lowercase snake_case slug (e.g. `main_results`, `ablation`).

Tables have no `srcs/` asset directory. The repository currently has no
separate table registry or table-specific checker; the full verification entry
point is `bash .agents/tools/verify.sh`.
