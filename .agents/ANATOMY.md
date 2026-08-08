# Agent Sidecar Anatomy

`.agents/` contains optional Agent-facing knowledge, focused skills, tools, tests, synchronization metadata, and short-lived coordination. It supports the paper without becoming the Human's primary work surface.

## Structure

- `knowledge/`: conditional reference material. Current project contracts always take priority.
- `knowledge/venues/`: generic per-venue planning schema plus active `<venue>-<year>.md` files; template files stay venue-agnostic.
- `skills/`: focused procedures for orientation, control review, decision packets, style alignment, interface maintenance, publication planning, release review, initial template adoption, and downstream template synchronization.
- `template-sync.json`: downstream-local upstream URL, remote/branch, reviewed baseline, and optional path-policy extensions; adoption first writes an uninitialized downstream-specific configuration and pins the commit only after review.
- `overleaf-sync.json`: project-specific Overleaf Git remote/branch and the canonical `paper/` source prefix; never contains credentials.
- `documentation-consistency.json`: expected current facts for README and Human-facing contracts; downstream papers update these facts instead of editing checker source.
- `dependencies/reference-integrity/`: exact, hash-bearing lock for the non-mutating Pybtex format gate and optional non-generative bibliography metadata checker; no package is vendored.
- `init-state.json`: downstream initialization marker written after template-specific governance residue is removed; absent in the upstream template.
- `tools/`:
  - `verify.sh` runs structure, documentation consistency, Draft contract, interface, publication, release-record, template-adoption, template-sync, and regression checks.
  - `paper-init.py` detects downstream repositories, removes template-specific governance IDs, resets downstream-local metadata, and records the initialization.
  - `check-actions.py` rejects first-party GitHub Actions majors that are no longer Node.js 24 compatible.
  - `check-skills.py` validates repo-local skill frontmatter, router coverage, and stale adapter references.
  - `check-documentation.py` rejects known retired paths, scripts, venue references, and missing Agent-sidecar references.
  - `check-venue-knowledge.py` validates active venue planning files and reports `UNVERIFIED` freshness/page-budget states.
  - `check-reference-integrity.py` performs the offline, standard-library bibliography/ledger/claim-evidence gate; `check-bibtex-format.py` runs locked classic-BibTeX syntax and field validation; `check-reference-metadata.py` runs the locked online identity audit and never approves claim support.
  - `release.sh` builds one strict immutable release instance.
  - `release.py` builds instances and writes non-overwriting release records.
  - `check-release.py` verifies manifest/artifact checksums and package boundaries.
  - `check-release-records.py` keeps tracked records Markdown-only and Human-approved where required.
  - `template-adoption.py` inspects an unrelated existing repository, proposes evidence-backed mappings, installs only missing Agent-sidecar infrastructure, verifies the result, and records the first reviewed baseline.
  - `template-sync.py` performs reviewed path-level three-way synchronization after a baseline exists.
  - `overleaf-sync.py` exports only `paper/` to Overleaf and imports online edits only through a dedicated review branch.
  - `check-structure.py`, `check-documentation.py`, `check-paper-contracts.py`, `check-paper-interfaces.py`, and `check-publication.py` enforce the paper-first collaboration model.
- `tests/`: standard-library positive and negative regressions, including release immutability, checksum drift, adoption safety, and template-sync safety.
- `runtime/`: ignored session, worktree, release, adoption, or template-sync coordination state; never durable project truth.

## Boundary

- Human-facing intent lives in root contracts.
- Authored scientific content lives in canonical `paper/` surfaces.
- Publication variants contain only presentation switches.
- Generated release instances live in ignored `dist/` and never become authored source.
- Durable tracked release information is Markdown provenance under `releases/records/`.
- Adoption inspections, plans, verification reports, and merge bundles live in ignored `.agents/runtime/template-adoption/`.
- Template-sync plans and merge bundles live in ignored `.agents/runtime/template-sync/`.
- Agents load one relevant skill and minimum context rather than recursively reading the sidecar.
- `make pdf VARIANT=<name>` and a paper-only checkout do not require `.agents/`.
- A downstream repository initialized from the template must not keep upstream template branch/issue IDs in its governance documents.

## Template adoption

`template-adoption.py` can run from a trusted template checkout against an existing unrelated repository. It discovers the actual TeX graph, bibliography, asset/style, experiment/evaluation, build, CI, and Agent-instruction surfaces; proposes mappings; stages only missing sidecar knowledge, skills, tests, tools, and runtime-ignore infrastructure; and exports manual/conflict review copies. Scientific content and repository-specific behavior remain downstream-owned.

After semantic migration and validation, adoption writes the exact reviewed template target as the first `.agents/template-sync.json` baseline. Later changes use `template-sync.py` rather than repeating adoption.

If the adopted repository has no `.agents/init-state.json`, run `paper-init.py clean --commit` before finalization so upstream template-specific governance residue is removed.

## Template synchronization

A downstream repository does not merge the upstream template history. `template-sync.py` compares the last recorded upstream baseline, the requested upstream target, and current downstream files. It applies only files unchanged downstream, protects paper/Human surfaces, exports manual/conflict versions for Agent review, and records a new baseline only after explicit review and validation.

The initial sync of an older downstream repository uses bootstrap mode. Bootstrap does not silently delete downstream-only project files.

If `.agents/init-state.json` is missing, run `paper-init.py clean --commit` before planning synchronization.

## Overleaf synchronization

`overleaf-sync.py` maps canonical `paper/` to the root of the Overleaf project. Governance, CI, Agent tooling, release records, and other repository files never enter the exported tree. Export runs only from a clean `main`; import runs only from a clean `sync/overleaf-*` branch. An online edit blocks the next export until it has been pulled back for review.

## Release honesty

A Draft-validation package proves the packaging mechanism, not submission readiness. Strict Release requires the Release contract to pass. Real Overleaf import, official venue upload, and arXiv platform compilation remain unverified until actually exercised.

## Context hygiene

Rich knowledge is useful only when relevant. Venue guidance, publication practices, experiment advice, historical rationale, template adoption, and template synchronization are loaded on demand. Generic knowledge and upstream defaults never override a current explicit Human decision.
