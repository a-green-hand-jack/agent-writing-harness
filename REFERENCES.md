# Reference Integrity Contract

This repository separates bibliographic identity from claim support. A paper can
exist with correct metadata and still fail to support the sentence that cites
it. Neither DOI resolution nor an automated model verdict approves scientific
meaning.

## Durable records

## Bibliography origin

- bibliography_origin: agent-curated

`agent-curated` means the Agent discovers and maintains entries, and the ledger
is the authority for what a citation is supported by.

`supplied-fixed` means the bibliography arrived with the task or from the Human,
is read-only, and may not gain, lose, or alter entries. The set of works is then
a Human decision that is already made, so `citation-support-review`'s
supplied-fixed-bibliography profile applies: a key's presence in the file is
sufficient to cite it at Draft strength, recorded `provisional`, without passage
retrieval. Release strength is unchanged and still requires Human-confirmed
support.


- `paper/refs.bib` is the canonical bibliography used by LaTeX.
- `references/ledger.json` is the Human-reviewable integrity ledger.
- `dist/reference-integrity/` contains ignored online-check reports and caches.
- `dist/reference-support/` contains ignored evidence-retrieval runs, support
  packets, provider outcomes, and caches.

The ledger uses `paper-reference-ledger-v2` and stores `references`,
`citation_usages`, `citation_occurrences`, and `claim_evidence` as arrays so
duplicate keys, duplicate occurrences, and multiple claims per key cannot be
hidden by JSON object semantics.

## Migration from v1

`paper-reference-ledger-v1` was key-level only. Upgrade explicitly with:

```bash
python3 .agents/tools/reference-evidence.py migrate
```

The migration scans every TeX citation occurrence, records the occurrence with
its claim text and fingerprint, and carries existing claim-evidence excerpts
over as `source-unavailable` evidence that still requires re-review. It never
silently rewrites a populated downstream ledger; run it deliberately and
review the result before Release. The offline checker keeps accepting v1 for
Draft but warns at Release until the migration runs.

## Reference identity

Each bibliography record has one of three states:

- `verified` — external metadata positively matches the cited record;
- `problematic` — positive evidence shows a mismatch or defect;
- `unverified` — available sources could not establish identity.

`unverified` never means fabricated. Network failures and rate limits are
infrastructure outcomes recorded in generated reports, not scientific states in
the ledger.

Reference identity review may be `agent-resolved` when the Agent has matched an
authoritative record with a stable identifier, recorded sources and date, and a
non-empty rationale. The legacy ledger field remains named `human_review` for
schema compatibility. `human-confirmed` is reserved for an identity/version
choice the Human actually decided. This distinction does not apply to
`citation_usages` or `claim_evidence`, which still require Human confirmation at
release.

## Claim evidence

Every cited key must have a `citation_usages` record classifying its use as
`claim-support`, `background`, `method`, `dataset`, or `other`, with a manuscript
location and Human review state.

For `paper-reference-ledger-v2`, claim evidence is bound to exact citation
occurrences. The CLI inventories every TeX occurrence with file, line, command,
citation keys, surrounding claim text, and a stable claim fingerprint:

```bash
python3 .agents/tools/reference-evidence.py inventory
```

Two different claims citing the same key require independently linked support
records. A multi-citation claim records per-key evidence and joint support only
when no individual work supports the complete claim. Each `claim_evidence`
record contains the occurrence id, citation key, claim fingerprint, protocol
version, source identity and version, verbatim passage text with locator and
hash, the support assessment (verdict, supported/unsupported parts,
contradictions, missing qualifiers, recommended action), and the review state.

Automated entailment or similarity checks may prioritize review, but only a
Human can mark claim evidence `human-confirmed`. Central claims, causal wording,
limitations, and contested interpretations remain subject to the paper control
contracts.

## Citation support

For every substantive citation occurrence the Agent answers three questions:

1. What does the manuscript sentence claim?
2. What does the cited work actually say (verbatim passage and locator)?
3. Does that evidence support the manuscript claim?

Verdicts are `supported`, `partially-supported`, `unsupported`,
`contradicted`, or `source-unavailable`. Provider failures (`rate-limited`,
`provider-unavailable`, `paper-not-indexed`, `identity-ambiguous`,
`no-relevant-passage`, `full-text-unavailable`) are infrastructure or
source-availability outcomes, never scientific verdicts; a real DOI or correct
metadata does not prove claim support.

### Staleness

Evidence is stale when the claim text fingerprint, the citation set, the source
identity or version, the passage hash, or the support protocol version changes.
`record` rejects stale packets (claim fingerprint or citation set drift) and
`check-reference-integrity.py` warns at Draft and fails at Release. Formatting-
only movement preserves evidence when the claim fingerprint and cited source
set remain unchanged.

### Profiles

- **Draft** — active claim only, bounded passages, one comparison, provisional
  result. Never a manuscript reviewer pass.
- **Review** — new, changed, provisional, stale, disagreement, and unresolved
  occurrences; independent supportive and adversarial passes; exact excerpts
  mechanically validated; Human decision packet on disagreement.
- **Release** — complete inventory; reuse Human-confirmed evidence only when
  fingerprint, citation set, source version, passage hash, and protocol version
  are unchanged; recheck stale or unresolved records; fail closed on
  substantive claim support that is not Human-confirmed.

## Offline gate

The standard-library checker adds no project dependency:

```bash
python3 .agents/tools/check-reference-integrity.py --profile draft
python3 .agents/tools/check-reference-integrity.py --profile release
```

Draft blocks malformed ledgers, duplicate or uncovered keys, and
`problematic` references. It keeps `unverified`, pending Human review, stale
occurrence drift, and missing occurrence coverage visible as warnings. Release
fails closed on every unresolved reference or claim-evidence review, every
missing or stale occurrence, and every substantive claim without
Human-confirmed support.

## BibTeX format gate

The locked MIT-licensed Pybtex parser independently checks classic BibTeX
syntax, supported entry types, standard required fields, and four-digit years.
It never rewrites the bibliography:

```bash
python3 .agents/tools/check-bibtex-format.py
```

Its report is written to `dist/reference-integrity/format.json`. The template
uses classic BibTeX with `plain.bst`, so BibLaTeX-only entry types are rejected
rather than silently accepted by a different data model. Actual LaTeX/BibTeX
compilation remains a separate integration check.

## Online metadata audit

The optional online audit uses the MIT-licensed `bibtex-updater` project's
`bibtex-check` command in non-generative mode. Its complete dependency graph is
locked under `.agents/dependencies/reference-integrity/`; nothing is vendored or
imported by `paper/`.

```bash
python3 .agents/tools/check-reference-metadata.py
```

The command requires Python 3.10+ and `uv`, installs only the locked core
dependency set in an isolated environment under `dist/reference-integrity/`,
and writes all reports and caches there. The wrapper overrides inherited uv
environment/cache paths so it cannot reuse an unrelated project environment.
Crossref, OpenAlex, DBLP, OpenReview, and Semantic Scholar availability can
change, so online output must be reviewed before updating the durable ledger.
`S2_API_KEY` is optional for a trusted local or protected-branch run. Pull-request
jobs run keylessly because they execute contributor-controlled code.

Upgrade the checker deliberately: change the exact version in the dependency
project, regenerate `uv.lock`, inspect the diff and third-party licenses, run the
fixture tests, then exercise a small known-good/known-bad bibliography before
merging. Do not install optional Scholar, Zotero, organizer, embedding, or LLM
extras.

The wrapper uses one worker and a conservative per-service request rate by
default, runs at most once for 12 minutes so CI retains time to upload evidence,
reuses its SQLite cache, and honors `BIBTEX_CHECK_MAILTO` for
Crossref/OpenAlex polite-pool identification. Configure that variable to a
monitored project contact address in trusted local or repository-variable
environments; it is not a secret. If a provider still returns 429 or activates
the checker's rate-limit circuit breaker, the run is recorded as
`rate_limited` and its evidence is uploaded. Provider network failures and
timeouts for which the upstream checker no longer exposes the original HTTP
status are recorded separately as `provider_unavailable`. Neither transient
outcome blocks CI or classifies a reference as false. Parser/runtime/report
failures and positive metadata mismatches found by available sources still
fail the audit.

`bibtex-check` and Pybtex are separate tools, but only `bibtex-check` performs
online publication-identity checks. Adding another wrapper around the same
Crossref/OpenAlex records would not create independent evidence. A second
identity checker should be required only when it has a usable open-source
license, pinned releases, safe behavior on untrusted pull requests, stable
machine output, and materially independent primary or proceedings sources.
Paper-BibChecker is not a required gate yet because its current repository has
no declared software license or tagged release and follows arbitrary URLs from
contributor-controlled BibTeX.

## Correction candidate audit

The formal online workflow also runs the locked `bibtex-update` command before
the identity audit:

```bash
python3 .agents/tools/check-reference-corrections.py
```

This stage checks required fields, attempts to fill missing required metadata,
and looks for reliable published versions of preprints. It never invokes the
updater on `paper/refs.bib`: the wrapper copies the canonical bibliography to
`dist/reference-integrity/corrections/source.bib`, writes the proposed result to
`candidate.bib`, validates exact citation-key coverage and classic BibTeX
format, and records every proposal in `report.jsonl` and `run.json`. It does not
enable in-place edits, rekeying, deduplication, Google Scholar, Google Books,
Zotero, or any optional dependency extra.

`candidates_found` and incomplete provider lookups are retrieval leads because
an upgrade from a preprint or a metadata replacement can change the scientific
object cited by the manuscript. Updater confidence never approves identity.
The candidate fails closed if it introduces a duplicate DOI/title identity or
changes normalized title wording; those findings remain available under
`dist/` for investigation.

The Agent inspects the evidence, retrieves authoritative records, and edits
`paper/refs.bib` plus the durable ledger. The Human is not expected to edit
BibTeX or approve routine same-object repairs. A Human decision is required only
when multiple plausible identities or versions remain and choosing among them
can affect claim support, source locators, or scientific meaning. The Agent may
record an unambiguous verified identity as `agent-resolved`; claim evidence and
citation-use classifications still require Human confirmation for release.

The canonical format gate independently rejects every unresolved duplicate DOI
or normalized title identity. An intentional preprint/published pair must be
resolved to the version actually cited rather than retained as indistinguishable
records.

## Service configuration

Trusted local runs automatically read the ignored root `.env` using a strict
non-shell parser. Only these names are accepted, and already-exported process
environment values take precedence:

```dotenv
BIBTEX_CHECK_MAILTO=jieke.wu@kaust.edu.sa
OPENALEX_API_KEY=
S2_API_KEY=
```

`.env.example` is the tracked template; `.env` is ignored and must never be
committed. The contact address is not secret. OpenAlex and Semantic Scholar API
keys are secrets. The correction wrapper translates the contact address into a
controlled updater User-Agent and both online wrappers inherit the API keys.

For GitHub Actions, create the contact as a repository variable and each key as
a repository secret:

```bash
gh variable set BIBTEX_CHECK_MAILTO --body "jieke.wu@kaust.edu.sa"
gh secret set OPENALEX_API_KEY
gh secret set S2_API_KEY
```

The workflow is intentionally split. Pull requests run the same online audits
without API secrets. Pushes to protected `main` and manual dispatches use the
repository secrets; manual dispatch checks out canonical `main`, not a
caller-selected feature branch. Secrets are never placed at workflow or shared
job scope. Missing optional secrets degrade to keyless provider access.
Uploaded Actions artifacts use an explicit report whitelist: dependency
environments and HTTP/SQLite caches are excluded because authenticated request
URLs or parameters can contain API keys.

Google Books and Zotero are not used by the formal workflow. The metadata audit
passes `--no-google-books`, and the locked core dependency set excludes Zotero
support.

## CiteCheck assessment

`color4-alt/CiteCheck` is not included. Its default branch was reviewed at
commit `fae7888bf7c1ce92bbafad15faf61cf55b7e2bd7` on 2026-08-08. It is
MIT-licensed, but has no Git tag or GitHub release, publishes an Alpha `0.1.0`
package without a dependency lock, emits only Markdown, and does not return a
failing status for citation findings. Most provider checks accept the first
title-search result without the field-level identity matching required here,
and provider failures are not separated from negative evidence.

CiteCheck also reads an inherited `OPENAI_API_KEY` automatically and may send
manuscript citation context to `gpt-4o-mini`; its heuristic fallback does not
provide source locators or evidence excerpts sufficient for claim-support
review. Crossref, OpenAlex, DBLP, and Semantic Scholar duplicate the existing
cascade, while its additional arXiv and PubMed paths do not validate first
results rigorously enough to provide independent positive evidence. These
properties make it unsuitable even as an advisory CI stage today. Reconsider
only after tagged releases, locked dependencies, non-generative fail-closed
operation, stable JSON output and exit codes, provider-failure classification,
repository-contained input handling, and field-level matching are available.
Useful concepts, not its implementation, are retained here: per-occurrence
citation inventory, unused-entry warnings, domain-primary retrieval leads, and
claim-support triage that produces source-locator review work rather than a
numeric approval score.

## Downstream activation

Reference-integrity enforcement is activated by the durable marker in the
already-protected `paper/refs.bib` together with the protected policy block in
`PUBLICATION.md` and downstream-local
`.agents/template-sync.json.reference_integrity.adopted=true`. The sync metadata
is never copied or overwritten by template-sync. Once adopted, deleting either
the marker or policy, or disabling the policy, is an error. A downstream
repository using an older template-sync engine
may mechanically receive new sidecar tools or CI workflow files, but those files
must skip dependency installation and network access while that policy block is
absent.

Adopt the feature on a dedicated template-sync branch:

1. sync the inert Agent-sidecar tooling;
2. inventory the downstream `refs.bib` into a reviewed ledger;
3. run the online audit in advisory mode and resolve mismatches;
4. merge the protected `PUBLICATION.md` policy block, `paper/refs.bib` marker,
   dependency lock, and CI workflow deliberately;
5. set downstream-local `reference_integrity.adopted` to `true` only after the
   ledger migration is complete;
6. run Draft and Release checks plus every publication variant;
7. record the new template baseline only after Human review.

Never copy the empty template ledger over a populated downstream ledger, and
never rewrite bibliography entries or scientific prose mechanically.
