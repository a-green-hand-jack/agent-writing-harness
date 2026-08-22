# Publication Contract

This file records publication variants, delivery targets, Overleaf boundaries,
and release-instance responsibilities. Variants are overlays on one canonical
paper; delivery packages are generated outputs rather than authored sources.

## Canonical paper

`paper/` is the only canonical authored source. Claims, evidence
interpretation, interface meaning, limitations, and prose do not diverge by
variant. A clean paper-only checkout must compile without `.agents/`.

## Active variants

| Variant | Purpose | Authors | Acknowledgements | Full appendix | Current status |
|---|---|---:|---:|---:|---|
| `draft` | Daily writing and review | visible | hidden | included | current |
| `anonymous` | Anonymous venue submission | hidden | hidden | included | active |
| `camera-ready` | Accepted venue version | visible | enabled but empty | included | active |
| `arxiv` | Public archival version | visible | enabled but empty | included | active |

## Allowed differences

Variants may change only author and identity-bearing project-link visibility,
acknowledgements, appendix inclusion, variant labels, and publication-facing
presentation hooks. Packaging format belongs to a release instance, not a
variant source tree.

## Must not diverge silently

Central claims, result meaning, experiment interpretation, terminology,
limitations, and canonical section content must remain in `paper/` and must not
diverge by variant without explicit Human approval.

## Human review triggers

Human review is required before adding or removing a variant, changing identity
or acknowledgement visibility, introducing variant-specific scientific prose,
accepting differences between published versions, or publishing an immutable
release instance.

## Build interface

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

`make pdf` defaults to `draft` for daily writing. The root `paper/main.tex` defaults to `anonymous` for direct Overleaf and source imports. The ARIS source
contains no acknowledgement text, so enabling that slot in `camera-ready` and
`arxiv` intentionally emits no additional prose.

## Reference integrity

Bibliographic identity and claim support are separate review obligations. The
ledger and metadata checks are governed by `REFERENCES.md`; automated metadata
results do not approve scientific meaning or claim support.

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

The migration records unresolved identity and citation-use review explicitly.
Draft validation permits those pending states with warnings; Release validation
fails closed until the corresponding review is completed.

## Platform evidence

The canonical arXiv paper has been compared with the source arXiv version, and
the synchronized Overleaf project has compiled successfully in the browser.
These observations do not assert acceptance by an external submission system.

## Delivery targets

A reviewed release instance may generate `pdf`, `source-zip`, `arxiv-flat`, and
`overleaf-zip` targets. Successful local packaging does not prove acceptance by
ICLR, Overleaf, or arXiv.

## Venue planning knowledge

The active style target is ICLR 2026. Current official deadlines, page limits,
anonymity rules, track, and author-kit identity remain `UNKNOWN` until checked
against official sources in `.agents/knowledge/venues/iclr-2026.md`. A local
compile is not venue acceptance evidence.

## Overleaf working copy

The configured Overleaf project is a collaborative working copy of canonical
`paper/`, not a second source or a release instance. Its Git root contains only
the tracked `paper/` tree. Export is allowed only from a clean canonical branch;
online edits return through a dedicated `sync/overleaf-*` review branch.

## Release instances

Release instances bind a selected variant and source revision to reviewed
artifacts and checksums. Generated artifacts belong under ignored
`dist/<release-id>/` and must not overwrite an existing instance. Tracked
`releases/records/` contains Markdown provenance only. External publication
remains a separate Human-approved action.
