# Reference Integrity Contract

This repository separates bibliographic identity from claim support. A paper can
exist with correct metadata and still fail to support the sentence that cites
it. Neither DOI resolution nor an automated model verdict approves scientific
meaning.

## Durable records

- `paper/refs.bib` is the canonical bibliography used by LaTeX.
- `references/ledger.json` is the Human-reviewable integrity ledger.
- `dist/reference-integrity/` contains ignored online-check reports and caches.

The ledger uses `paper-reference-ledger-v1` and stores `references` as an array
so duplicate citation keys cannot be hidden by JSON object semantics.

Each bibliography record has one of three states:

- `verified` — external metadata positively matches the cited record;
- `problematic` — positive evidence shows a mismatch or defect;
- `unverified` — available sources could not establish identity.

`unverified` never means fabricated. Network failures and rate limits are
infrastructure outcomes recorded in generated reports, not scientific states in
the ledger.

## Claim evidence

Every cited key must have a `citation_usages` record classifying its use as
`claim-support`, `background`, `method`, `dataset`, or `other`, with a manuscript
location and Human review state. When a citation supports a substantive
manuscript claim, add a
`claim_evidence` record containing:

- the citation key;
- the manuscript claim and location;
- the source locator, such as page, section, figure, or theorem;
- a short evidence excerpt or rationale; and
- the Human review state.

Automated entailment or similarity checks may prioritize review, but only a
Human can mark claim evidence `human-confirmed`. Central claims, causal wording,
limitations, and contested interpretations remain subject to the paper control
contracts.

## Offline gate

The standard-library checker adds no project dependency:

```bash
python3 .agents/tools/check-reference-integrity.py --profile draft
python3 .agents/tools/check-reference-integrity.py --profile release
```

Draft blocks malformed ledgers, duplicate or uncovered keys, and
`problematic` references. It keeps `unverified` and pending Human review visible
as warnings. Release fails closed on every unresolved reference or claim-evidence
review.

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

`candidates_found` and incomplete provider lookups are advisory because an
upgrade from a preprint or a metadata replacement can change the scientific
object cited by the manuscript. A Human must inspect the artifact diff and
approve each change before editing `paper/refs.bib` or the durable ledger. The
candidate does not approve bibliographic changes or claim support.

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

`color4-alt/CiteCheck` is not included. It is MIT-licensed, but as reviewed on
2026-08-08 it has no Git tag or GitHub release, publishes an Alpha `0.1.0`
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
