---
name: reference-repair
description: Use when an Agent must investigate and repair BibTeX identity, metadata, duplicates, or preprint/version records.
---

# Reference Repair

## Authority

The Agent retrieves evidence, edits canonical BibTeX and the reference ledger,
and runs the complete validation loop. The Human is not expected to edit BibTeX
or approve routine same-object metadata repairs.

Ask the Human only when multiple plausible identities or versions remain and
the choice can change the cited object, claim support, source locator, or
scientific interpretation.

## Procedure

<!-- paper-skill-contract: F7-RR-001-v1 -->
1. Before any edit, run the format, correction-candidate, metadata, and ledger
   audits; preserve their unmodified output as the initial audit baseline.
2. Treat updater candidates as retrieval leads, never as source-of-truth edits.
3. Inspect every manuscript use and existing claim-evidence locator for the key.
4. Retrieve authoritative records, preferring DOI/publisher/proceedings,
   OpenReview, exact arXiv identifiers, or domain-primary sources.
5. Compare title, complete authors, year, venue, type, identifiers, and version
   lineage. Never rely on updater confidence alone.
6. Reject candidates with substantive title changes, new duplicate DOI/title
   identities, or evidence for a different work.
7. For an unambiguous same-object repair, edit `paper/refs.bib` and
   `references/ledger.json` in the same change. Preserve the citation key unless
   rekeying is necessary; update all uses atomically if it is.
8. Record `agent-resolved` only for a verified identity with a stable identifier,
   source list, checked date, and concise rationale. Leave insufficient evidence
   as `unverified`.
9. Never carry claim-evidence locators across a version change without checking
   the actual target document.
10. Run format, correction, metadata, Draft and Release ledger checks, every
    publication build, and the repository verification entrypoint.

## Routine Repairs

The Agent may resolve without a Human decision:

- capitalization, punctuation, whitespace, and LaTeX protection;
- exact DOI or stable identifier addition for an already matched work;
- author formatting and complete author-list repair from the authoritative record;
- page, volume, issue, venue, and type corrections for the same object;
- removal of a proven duplicate after every citation use is mapped safely.

## Decision Packet

When a Human choice is required, provide the current entry and manuscript
locations, candidate identities/versions, authoritative links and identifiers,
all metadata differences, affected claims/locators, and the Agent recommendation.
Pause only the ambiguous key; continue reversible work elsewhere.
