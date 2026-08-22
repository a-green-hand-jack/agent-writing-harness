# Decisions

## DEC-0001: Paper-first repository

Decision: Human intent lives in root contracts, canonical authored LaTeX lives
under `paper/`, and optional Agent support lives under `.agents/`. The previous
duplicate harness, state, memory, and generated-release control planes are
retired.

## DEC-0002: Preserve the imported ARIS scientific object

Decision: the paper remains the attributed arXiv 2605.03042 technical report.
The migration must not change its title, authors, reported values, scientific
claims, observational qualifications, limitations, venue/style identity, or
canonical section meaning.

## DEC-0003: One canonical paper with small variants

Decision: `paper/` is the only authored source. `draft`, `anonymous`,
`camera-ready`, and `arxiv` variants may alter approved presentation switches,
not scientific prose or interpretation.

## DEC-0004: Stable paper-facing interfaces

Decision: recurring identity, terminology, state label, and reported deployment
result use lightweight interfaces in `paper/macros.tex` and
`PAPER_INTERFACES.md`. Interface implementation may change; meaning does not
change without Human review.

## DEC-0005: Observational evidence remains non-causal

Decision: the documented overnight run is one self-reported observational
trajectory. It cannot establish cross-family superiority, optimal committee
size, general effectiveness, or causal improvement. The controlled benchmark
in the appendix remains future work.

## DEC-0006: Generated releases are externalized

Decision: release artifacts live under ignored `dist/<release-id>/` and refuse
overwrite. Tracked release information is Markdown provenance under
`releases/records/`; no generated TeX or PDF tree is committed.

## DEC-0007: Overleaf is a paper-only working copy

Decision: the configured Overleaf project maps only tracked `paper/` content.
Outbound and inbound changes use `.agents/tools/overleaf-sync.py`; Overleaf is
neither a second canonical source nor an immutable release instance.

## DEC-0008: Template updates use reviewed path-level synchronization

Decision: this downstream case records a reviewed upstream baseline and uses
`template-sync.py` rather than merging unrelated template history. Human
contracts, paper content, references, macros, CI, venue files, and project
knowledge remain semantic-review surfaces.

## DEC-0009: Bundled skills remain subordinate sidecars

Decision: adopt the template's immutable CCFA-Skills and writing-dna-skill
snapshots under `.agents/vendor/`, with thin wrappers under `.agents/skills/`.
ARIS Human contracts remain authoritative. Local owner skills and current Human
decisions take precedence; bundled skills cannot approve scientific meaning,
experiments, references, publication variants, or releases.

## DEC-0010: Local case branch is protected evidence

Decision: `case/arxiv-2605-03042` is the protected local case branch for this
paper and must not be proposed for deletion or included in routine cleanup.
No upstream template issue IDs are inherited as downstream project facts.

## DEC-0014: Downstream paper initialization

Decision: this repository is a downstream real-paper case initialized from the
template. Upstream template-specific governance IDs are not downstream facts;
the repository owns its ARIS contracts, protected branch, venue state, and
release decisions.

## Recording future decisions

Record durable high-impact choices and rationale here. Do not record every
sentence edit or temporary implementation detail.
