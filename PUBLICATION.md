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

The default variant is `draft`. Unknown variants fail rather than silently falling back.

## Delivery targets

A release instance can generate any reviewed subset of:

- `pdf` — compiled selected variant;
- `source-zip` — modular, single-entry source package;
- `arxiv-flat` — latexpand single-entry package with required style/assets;
- `overleaf-zip` — modular source package suitable for import.

A successful local package build does not prove a real venue, Overleaf, or arXiv platform accepted it.

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
