# Reference Integrity Contract

This repository separates bibliographic identity from claim support. A paper can
have correct metadata and still fail to support the sentence that cites it.
Neither identifier resolution nor an automated verdict approves scientific
meaning.

## Durable records

- `paper/refs.bib` is the canonical bibliography used by LaTeX.
- `references/ledger.json` is the canonical integrity ledger.
- `dist/reference-integrity/` contains ignored generated reports and caches.
- `dist/reference-support/` contains ignored occurrence inventories, support
  packets, provider outcomes, and caches.

The ledger uses `paper-reference-ledger-v2`. The reviewed migration preserved
the populated ARIS records, added occurrence-level inventory with pending
review, and did not promote any claim evidence. The retired v1 control-plane
files remain recoverable from Git history but are not current sources of truth.

The integrity ledger records bibliography identity as `verified`, `problematic`,
or `unverified`. `Unverified` does not mean fabricated. It means the cited
object's identity has not been established from authoritative records.
Automated correction candidates are retrieval leads only.

Every cited key also has a `citation_usages` record. Exact TeX occurrences are
stored in `citation_occurrences` with claim fingerprints, and reviewed support
belongs in `claim_evidence`. Citation classification and claim-evidence review
remain pending until the existing evidence-first citation ledger and manuscript
context are reviewed. Draft validation keeps those states visible as warnings;
Release validation fails closed on unresolved identity, use, occurrence, or
claim-evidence review.

## Checks

```bash
python3 .agents/tools/check-reference-integrity.py --profile draft
python3 .agents/tools/check-reference-integrity.py --profile release
python3 .agents/tools/reference-evidence.py status
python3 .agents/tools/reference-evidence.py --offline inventory
python3 .agents/tools/check-bibtex-format.py
python3 .agents/tools/check-reference-corrections.py
python3 .agents/tools/check-reference-metadata.py
```

The format gate and online audits use the exact dependency lock under
`.agents/dependencies/reference-integrity/` and isolate environments, reports,
and caches under `dist/reference-integrity/`. The correction audit never edits
`paper/refs.bib`; accepted same-object repairs must update the bibliography and
integrity ledger together while preserving citation keys.

Pull requests and pushes to `main` run only the deterministic offline ledger,
format, and helper-test gates. The provider-dependent correction and metadata
audits run only through the manual `workflow_dispatch` entry point. This keeps
ordinary validation fast and reproducible while preserving an explicit deep
audit path for reference-repair work.

## Downstream Activation

The synchronized tools and workflow remain inert until all three protected
activation controls agree:

- `PUBLICATION.md` contains the enforced reference-integrity policy;
- `paper/refs.bib` contains the canonical activation marker; and
- `.agents/template-sync.json.reference_integrity.adopted` is `true` after
  coordinator review.

All three controls are active after the reviewed structural migration. The
migrated ledger keeps unverified identities and pending citation-use review
visible without promoting them to verified evidence. Adoption means the checks
are enforced; it does not mean every reference is Release-ready.
