# Paper Interface Maintenance

## Trigger

Use when adding or changing a recurring paper-facing name, term, symbol, result, claim form, figure, table, or LaTeX macro.

## Minimum context

- the relevant entry in `PAPER_INTERFACES.md`;
- `paper/macros.tex` and active consumers;
- the related claim or experiment contract only when meaning or result interpretation is involved.

Do not load code-repository import assumptions; that interface is out of scope.

## Procedure

1. State the current interface meaning and control boundary.
2. Search active paper surfaces for every consumer.
3. Distinguish a presentation/value update from a semantic change.
4. Keep low-risk implementation changes local and consistent.
5. For a semantic change, show the Human the old meaning, proposed meaning, affected claims/experiments, and migration impact.
6. Update the interface and all active consumers together.
7. Report stale aliases, literal duplicates, placeholders, and unresolved uses.

## Human decision

Request Human review before changing metric, split, aggregation, uncertainty meaning, claim strength, stable terminology meaning, or an artifact's narrative responsibility.
