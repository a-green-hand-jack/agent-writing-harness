# Publication Contract

This file records publication variants, delivery targets, and release-instance responsibilities. Variants are overlays on one canonical paper; delivery packages are generated outputs; release instances are immutable reviewed builds.

## Canonical paper

`paper/` is the only authored source. Its scientific content is a verbatim migration of arXiv `2604.01658v2`. Claims, experiment interpretation, interface meaning, limitations, and canonical prose must not diverge by variant unless the Human explicitly approves a scientific revision in the canonical paper.

## Active variants

| Variant | Purpose | Authors | Acknowledgements | Full appendix | Current status |
|---|---|---:|---:|---:|---|
| `draft` | Daily writing and review | visible | hidden | included | current |
| `anonymous` | Anonymous venue submission | hidden | hidden | included | planned |
| `camera-ready` | Accepted venue version | visible | included | included | planned |
| `arxiv` | Public archival version | visible | included | included | planned |

## Allowed differences

Variants may change only publication-facing presentation:

- author visibility;
- acknowledgements;
- appendix inclusion;
- variant label and venue-specific presentation hooks;
- package and delivery target, handled by release instances rather than variant source.

## Must not diverge silently

- verbatim scientific content of the migrated source (including the commented-out `07_limitations.tex` slot);
- headline numbers and benchmark attribution;
- author identity and title;
- limitation statements in the source appendix;
- stable terminology and notation;
- canonical section content.

A required scientific difference must first be discussed and applied to the canonical paper or recorded as an explicit Human-approved exception.

## Human review triggers

Human review is required before:

- adding or removing an active variant;
- changing whether identities, acknowledgements, or appendix material appear;
- introducing variant-specific scientific prose;
- accepting a difference between two published versions;
- approving or publishing an immutable release instance.

## Build interface

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

`make pdf` defaults to `draft` for daily writing. The root `paper/main.tex` defaults to `anonymous`, so a direct Overleaf or source import compiles the anonymous submission layout. Draft, camera-ready, and arXiv must be selected explicitly. Unknown variants fail rather than silently falling back.

`.agents/paper-build.json` declares this repository's source entrypoint and the
four commands that adoption and template sync must verify. An adopted external
publisher template may instead use an `external-latex` profile with its native
entrypoint and one or more real build commands; see `LATEX_TEMPLATES.md`. The
profile changes build orchestration only and does not authorize publication
variant differences.

## Reference integrity

Bibliographic identity and claim support are separate review obligations documented in `REFERENCES.md`. This case has not adopted reference-integrity enforcement yet: the migration carried the verbatim 50-entry `paper/refs.bib`. The protected policy block, the `paper/refs.bib` activation marker, and `.agents/template-sync.json.reference_integrity.adopted=true` are deliberately absent; the offline gate therefore reports the policy as not enabled. Adoption of reference integrity is a separate reviewed step and is **unresolved**.

## Delivery targets

A release instance can generate any reviewed subset of:

- `pdf` — compiled selected variant;
- `source-zip` — modular, single-entry source package;
- `arxiv-flat` — latexpand single-entry package with required style/assets;
- `overleaf-zip` — modular source package suitable for import.

A successful local package build does not prove a real venue, Overleaf, or arXiv platform accepted it.

## Venue planning knowledge

No active venue planning file exists under `.agents/knowledge/venues/`; the migrated source uses COLM 2026 style files (`[preprint]` option), and official current-year venue rules are **unresolved** and out of scope for this round.

## Overleaf working copy

The configured Overleaf project (`overleaf-coral`, project `6a7cbcd4e3f0643e25365911`) is a collaborative working copy of canonical `paper/`, not a second canonical source or a release instance. Its Git root contains only the tracked `paper/` tree. Repository governance, Agent tooling, CI, contracts, and release records are excluded.

Exports originate from a clean canonical branch (`main` or the protected `case/arxiv-2604-01658` branch). Online edits return through a dedicated `sync/overleaf-*` branch and must pass the ordinary paper build and repository verification before merge. A detected online edit blocks outbound replacement until reviewed and imported.

## Release instances

A release instance binds:

- release ID and selected variant;
- strict Release or Draft-validation profile;
- canonical source fingerprint and Git audit commit;
- interface, publication contract, and variant config hashes;
- delivery artifacts and SHA-256 checksums;
- isolated source/flat compilation results;
- separate Human approval in a durable release record.

Generated instances live under ignored `dist/<release-id>/` and refuse overwrite. Tracked `releases/records/` contains Markdown provenance and decisions only, never generated TeX trees or binaries.

No Human-approved release instance exists for this case. The Round-1 legacy committed `release/` tree was retired into `releases/records/arxiv-2604-01658-legacy-round1.md` during template adoption. Published revisions use a new ID; do not edit an old record to represent new artifacts.
