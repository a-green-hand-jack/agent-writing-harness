# Agent Sidecar Anatomy

`.agents/` contains optional Agent-facing knowledge, focused skills, tools, tests, synchronization metadata, and short-lived coordination. It supports the paper without becoming the Human's primary work surface.

## Structure

- `knowledge/`: conditional reference material. Current project contracts always take priority.
- `skills/`: focused procedures for orientation, control review, decision packets, style alignment, interface maintenance, publication planning, release review, and downstream template synchronization.
- `template-sync.json`: downstream-local upstream URL, remote/branch, last reviewed baseline, and optional path-policy extensions.
- `tools/`:
  - `verify.sh` runs structure, Draft contract, interface, publication, release-record, template-sync configuration, and regression checks.
  - `release.sh` builds one strict immutable release instance.
  - `release.py` builds instances and writes non-overwriting release records.
  - `check-release.py` verifies manifest/artifact checksums and package boundaries.
  - `check-release-records.py` keeps tracked records Markdown-only and Human-approved where required.
  - `template-sync.py` performs reviewed path-level three-way synchronization for downstream paper repositories with unrelated Git history.
  - `check-structure.py`, `check-paper-contracts.py`, `check-paper-interfaces.py`, and `check-publication.py` enforce the paper-first collaboration model.
- `tests/`: standard-library positive and negative regressions, including release immutability, checksum drift, and template-sync safety.
- `runtime/`: ignored session, worktree, release, or template-sync coordination state; never durable project truth.

## Boundary

- Human-facing intent lives in root contracts.
- Authored scientific content lives in canonical `paper/` surfaces.
- Publication variants contain only presentation switches.
- Generated release instances live in ignored `dist/` and never become authored source.
- Durable tracked release information is Markdown provenance under `releases/records/`.
- Template-sync plans and merge bundles live in ignored `.agents/runtime/template-sync/`.
- Agents load one relevant skill and minimum context rather than recursively reading the sidecar.
- `make pdf VARIANT=<name>` and a paper-only checkout do not require `.agents/`.

## Template synchronization

A downstream repository does not merge the upstream template history. `template-sync.py` compares the last recorded upstream baseline, the requested upstream target, and current downstream files. It applies only files unchanged downstream, protects paper/Human surfaces, exports manual/conflict versions for Agent review, and records a new baseline only after explicit review and validation.

The initial sync of an older downstream repository uses bootstrap mode. Bootstrap does not silently delete downstream-only project files.

## Release honesty

A Draft-validation package proves the packaging mechanism, not submission readiness. Strict Release requires the Release contract to pass. Real Overleaf import, official venue upload, and arXiv platform compilation remain unverified until actually exercised.

## Context hygiene

Rich knowledge is useful only when relevant. Venue guidance, publication practices, experiment advice, historical rationale, and template synchronization are loaded on demand. Generic knowledge and upstream defaults never override a current explicit Human decision.
