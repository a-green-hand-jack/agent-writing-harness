# Publication Contract

This file records publication variants, delivery targets, and release-instance responsibilities. Variants are overlays on one canonical paper; delivery packages are generated outputs; release instances are immutable reviewed builds.

## Canonical paper

`paper/` is the only authored source. Claims, experiment interpretation, interface meaning, limitations, and canonical prose must not diverge by variant unless the Human explicitly approves a scientific revision in the canonical paper.

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

- central claims and contribution identity;
- result and uncertainty meaning;
- experiment interpretation and fairness conditions;
- stable terminology and notation;
- limitations or negative evidence constraining a core claim;
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

## Reference integrity

Bibliographic identity and claim support are separate review obligations. The
ledger and open-source metadata checker are governed by `REFERENCES.md`; neither
database presence nor an automated verdict approves scientific meaning.

<!-- REFERENCE-INTEGRITY:START -->
```json
{
  "schema_version": "paper-reference-integrity-policy-v1",
  "enforcement": "enforced",
  "ledger": "references/ledger.json",
  "bibliography": "paper/refs.bib"
}
```
<!-- REFERENCE-INTEGRITY:END -->

Downstream repositories must merge this protected block and the activation
marker in `paper/refs.bib`, then set downstream-local
`.agents/template-sync.json.reference_integrity.adopted` to `true`, only after
migrating their existing bibliography and reviewing the resulting ledger.
Without all three, synchronized sidecar tools and workflows remain inert and
perform no dependency installation or network access. Once adopted, a missing
marker or missing/disabled policy is a hard failure rather than a bypass.

## Delivery targets

A release instance can generate any reviewed subset of:

- `pdf` — compiled selected variant;
- `source-zip` — modular, single-entry source package;
- `arxiv-flat` — latexpand single-entry package with required style/assets;
- `overleaf-zip` — modular source package suitable for import.

A successful local package build does not prove a real venue, Overleaf, or arXiv platform accepted it.

## Venue planning knowledge

Active venue planning facts are stored under `.agents/knowledge/venues/<venue>-<year>.md` and follow the schema in `.agents/knowledge/venues/README.md`. Official deadlines, page limits, anonymity requirements, and operational rules are current constraints only when they come from a checked official source with an explicit `last_checked` value.

Agent scheduling must use official timeline facts as hard constraints and derive internal writing, experiment, review, and approval buffers separately. Internal milestones are not official deadlines. Before deadline-sensitive planning or strict release, recheck the official venue source and run:

```bash
python3 .agents/tools/check-venue-knowledge.py --strict
```

This venue planning input is distinct from capability authenticity (#21) and real environment availability (#31), but strict venue planning depends on the same honest source and freshness rules.

## Overleaf working copy

The configured Overleaf project is a collaborative working copy of canonical `paper/`, not a second canonical source or a release instance. Its Git root contains only the tracked `paper/` tree. Repository governance, Agent tooling, CI, contracts, and release records are excluded.

Exports originate from a clean canonical `main`. Online edits return through a dedicated `sync/overleaf-*` branch and must pass the ordinary paper build and repository verification before merge. A detected online edit blocks outbound replacement until reviewed and imported.

## Release instances

A release instance such as `iclr2027-submission-r1` or `arxiv-v2` binds:

- release ID and selected variant;
- strict Release or Draft-validation profile;
- canonical source fingerprint and Git audit commit;
- interface, publication contract, and variant config hashes;
- delivery artifacts and SHA-256 checksums;
- isolated source/flat compilation results;
- separate Human approval in a durable release record.

Generated instances live under ignored `dist/<release-id>/` and refuse overwrite. Tracked `releases/records/` contains Markdown provenance and decisions only, never generated TeX trees or binaries.

Published revisions use a new ID. Do not edit an old record to represent new artifacts.
