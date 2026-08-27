# Agent Sidecar Anatomy

`.agents/` contains optional Agent-facing knowledge, focused skills, tools, tests, synchronization metadata, and short-lived coordination. It supports the paper without becoming the Human's primary work surface.

## Structure

- `knowledge/`: conditional reference material. Current project contracts always take priority.
- `knowledge/venues/`: generic per-venue planning schema plus active `<venue>-<year>.md` files; template files stay venue-agnostic.
- `knowledge/writing/`: downstream-local Writing DNA workflow and the Human-approved `paper-writing-dna.md` after activation; protected from template-sync overwrite.
- `skills/`: focused procedures for orientation, the shared repository-role and initialization gate, template creation through the `ccf-project-scaffolder` wrapper, control review, decision packets, section writing, style alignment, post-version manuscript consistency review, interface maintenance, publication planning, release review, initial template adoption, downstream template synchronization, and wrappers for the bundled third-party suites.
- `vendor/`: immutable snapshots of CCFA-Skills (`v0.9.0`) and writing-dna-skill with MIT licenses; verified by `check-vendored-skills.py` against `dependencies/vendored-skills/provenance.json`; never edited locally.
- `template-inheritance.json`: machine-readable inheritance policy shared by template creation, initial adoption, and later template synchronization. It records required, safe, manual, and ignored path surfaces; downstream-local extensions remain in `template-sync.json`.
- `evals/vendored-skills/`: one task-level worker/reviewer scenario for every bundled wrapper. Deterministic CI validates scenario coverage; live sub-agent runs are explicit, non-blocking evidence stored under ignored runtime.
- `template-origin.json`: repository-bound GitHub Template provenance attestation written by template-create and required by `paper-init.py` initialization; unrelated adoptions do not create it.
- `template-sync.json`: downstream-local upstream URL, remote/branch, reviewed baseline, and optional path-policy extensions; adoption first writes an uninitialized downstream-specific configuration and pins the commit only after review.
- `overleaf-sync.json`: project-specific Overleaf Git remote/branch and the canonical `paper/` source prefix; never contains credentials.
- `documentation-consistency.json`: expected current facts for README and Human-facing contracts plus repository-local `stale_patterns` overrides; downstream papers update these facts instead of editing checker source.
- `dependencies/reference-integrity/`: exact, hash-bearing lock for the non-mutating Pybtex format gate and optional non-generative bibliography metadata checker; no package is vendored.
- `dependencies/vendored-skills/`: exact, hash-bearing lock (`PyYAML`, `pymupdf`) for running the bundled CCFA scripts on demand; `provenance.json` records vendor source commits and file hashes; no package is vendored.
- `init-state.json`: downstream initialization marker written after template-specific governance residue is removed; valid only with template-origin provenance.
- `tools/`:
  - `verify.sh` runs structure, documentation consistency, Draft contract, interface, publication, release-record, template-adoption, template-sync, and regression checks.
  - `paper-init.py` verifies GitHub Template provenance, removes template-specific governance IDs, resets downstream-local metadata, and records the initialization.
  - `paper-brief.py` validates a Human-provided paper brief and ingests it into the writing-repo contracts (copying `BRIEF.md`, filling only decided `PAPER.md` fields, leaving the rest `unresolved`).
  - `check-actions.py` rejects first-party GitHub Actions majors that are no longer Node.js 24 compatible.
  - `check-skills.py` validates repo-local skill frontmatter, router coverage, and stale adapter references.
  - `check-vendored-skills.py` validates the immutable vendor snapshots against the provenance manifest (file hashes, licenses, symlink rejection, exclusion boundary, wrapper targets, and router coverage).
  - `check-vendored-skill-evals.py` validates that every bundled wrapper has a task scenario with required and forbidden behavior; it does not invoke a model or claim output quality.
  - `check-documentation.py` rejects known retired paths, scripts, venue references, and missing Agent-sidecar references; the immutable vendor tree is exempt from first-party documentation scanning.
  - `check-venue-knowledge.py` validates active venue planning files and reports `UNVERIFIED` freshness/page-budget states.
  - `check-reference-integrity.py` performs the offline, standard-library bibliography/ledger/claim-evidence gate; `check-bibtex-format.py` runs locked classic-BibTeX syntax and field validation; `check-reference-metadata.py` runs the locked online identity audit and never approves claim support.
  - `release.sh` builds one strict immutable release instance.
  - `release.py` builds instances and writes non-overwriting release records.
  - `check-release.py` verifies manifest/artifact checksums and package boundaries.
  - `check-release-records.py` keeps tracked records Markdown-only and Human-approved where required.
  - `template-adoption.py` inspects an unrelated existing repository, proposes evidence-backed mappings, installs only missing Agent-sidecar infrastructure, verifies the result, and records the first reviewed baseline.
  - `template-sync.py` performs reviewed path-level three-way synchronization after a baseline exists.
  - `overleaf-sync.py` exports only `paper/` to Overleaf and imports online edits only through a dedicated review branch.
  - `paper-fidelity.py` produces repeatable original-vs-rebuilt PDF comparison evidence (page counts, per-page ordered-text digests, first mismatch page) and verifies file SHA-256 digests; it reports evidence and never approves a release.
  - `check-structure.py`, `check-documentation.py`, `check-paper-contracts.py`, `check-paper-interfaces.py`, and `check-publication.py` enforce the paper-first collaboration model.
- `tests/`: standard-library positive and negative regressions, including release immutability, checksum drift, adoption safety, and template-sync safety.
- `runtime/`: ignored session, worktree, release, adoption, or template-sync coordination state; never durable project truth.

## Boundary

- Human-facing intent lives in root contracts.
- The Human-authored paper brief lives in root `BRIEF.md`; it is ingested at
  bootstrap, kept as provenance and material inventory, and protected from
  template adoption/synchronization overwrite.
- Authored scientific content lives in canonical `paper/` surfaces.
- Publication variants contain only presentation switches.
- Generated release instances live in ignored `dist/` and never become authored source.
- Durable tracked release information is Markdown provenance under `releases/records/`.
- Adoption inspections, plans, verification reports, and merge bundles live in ignored `.agents/runtime/template-adoption/`.
- Template-sync plans and merge bundles live in ignored `.agents/runtime/template-sync/`.
- Agents load one relevant skill and minimum context rather than recursively reading the sidecar.
- The downstream lifecycle has one shared `paper-orientation` gate and four variants: `ccf-project-scaffolder` template-create, `paper-brief-ingest` brief-driven bootstrap, `template-adoption` unrelated-repository adoption, and `template-sync` reviewed infrastructure synchronization.
- Section writing does not automatically invoke reviewer passes. Manuscript consistency review runs only after the Human identifies a manuscript version as ready and reports findings without editing by default.
- `make pdf VARIANT=<name>` and a paper-only checkout do not require `.agents/`.
- A downstream repository initialized from the template must not keep upstream template branch/issue IDs in its governance documents.

## Template adoption

`template-adoption.py` can run from a trusted template checkout against an existing unrelated repository. It discovers the actual TeX graph, bibliography, asset/style, experiment/evaluation, build, CI, and Agent-instruction surfaces; proposes mappings; applies the adoption rules in `.agents/template-inheritance.json`; stages only missing sidecar knowledge, skills, tests, tools, and runtime-ignore infrastructure; and exports manual/conflict review copies. Scientific content and repository-specific behavior remain downstream-owned.

After semantic migration and validation, adoption writes the exact reviewed template target as the first `.agents/template-sync.json` baseline. Later changes use `template-sync.py` rather than repeating adoption.

Adoption does not run `paper-init.py`: unrelated repositories have no
template-create provenance attestation and must not be relabeled as
template-created. The adoption tool writes `adoption.status: in_progress` in
`.agents/template-sync.json`, which is the resumable state until
`finalize --reviewed` records the first reviewed baseline. A reviewed adoption
is reported as `adoption_reviewed`; it intentionally has no template-origin or
init-state record.

## Template synchronization

A downstream repository does not merge the upstream template history. `template-sync.py` compares the last recorded upstream baseline, the requested upstream target, and current downstream files. It applies the synchronization rules in `.agents/template-inheritance.json` plus downstream-local extensions in `.agents/template-sync.json`, updates only eligible files unchanged downstream, protects paper/Human surfaces, exports manual/conflict versions for Agent review, and records a new baseline only after explicit review and validation.

The initial sync of an older downstream repository uses bootstrap mode. Bootstrap does not silently delete downstream-only project files.

If `.agents/init-state.json` is missing, do not initialize automatically. A
template-created repository must first have valid `.agents/template-origin.json`
provenance; an adoption repository must finish `adoption.status: in_progress`
before planning synchronization.

## Overleaf synchronization

`overleaf-sync.py` maps canonical `paper/` to the root of the Overleaf project. Governance, CI, Agent tooling, release records, and other repository files never enter the exported tree. Export runs only from a clean canonical branch (`main`, `master`, `trunk`, or a protected `case/<name>` branch); import runs only from a clean `sync/overleaf-*` branch. An online edit blocks the next export until it has been pulled back for review.

## Release honesty

A Draft-validation package proves the packaging mechanism, not submission readiness. Strict Release requires the Release contract to pass. Real Overleaf import, official venue upload, and arXiv platform compilation remain unverified until actually exercised.

## Context hygiene

Rich knowledge is useful only when relevant. Venue guidance, publication practices, experiment advice, historical rationale, template adoption, and template synchronization are loaded on demand. Generic knowledge and upstream defaults never override a current explicit Human decision.
