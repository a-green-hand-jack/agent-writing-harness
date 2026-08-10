# Publication Contract

This file records publication variants, delivery targets, and release-instance
responsibilities. Variants are overlays on one canonical paper; delivery
packages are generated outputs rather than independent authored sources.

## Canonical paper

`paper/` is the canonical authored source. The tracked `release/` surfaces are
case-specific exports of that source and must not become independent editing
surfaces.

## Active variants

| Variant | Purpose | Authors | Acknowledgements | Full appendix | Current status |
|---|---|---:|---:|---:|---|
| `draft` | Daily writing and review | visible | hidden | included | active |
| `anonymous` | Anonymous venue submission | hidden | hidden | included | active |
| `camera-ready` | Accepted venue version | visible | enabled but empty | included | active |
| `arxiv` | Public archival version | visible | enabled but empty | included | active |

## Allowed differences

Variants may change only author and identity-bearing project-link visibility,
acknowledgements, appendix inclusion, variant labels, and publication-facing
presentation hooks.

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

## Release instances

Release instances bind a selected variant and source revision to reviewed
artifacts and checksums. Existing tracked `release/` directories are legacy
case exports; new generated artifacts belong under ignored `dist/` and must not
overwrite a previous release instance. External publication remains a separate
Human-approved action.
