# Repository Anatomy

This repository has two primary layers: one canonical authored paper and an
optional Agent sidecar. Generated releases are immutable ignored instances,
not committed copies.

## Human and authored surface

- `PAPER.md`: positioning, thesis, claims, story, style, protected decisions, and unresolved work.
- `EXPERIMENTS.md`: observational evidence and experiment-interpretation boundaries.
- `PAPER_INTERFACES.md`: stable identity, terminology, notation, and result interfaces.
- `PUBLICATION.md`: variants, delivery targets, Overleaf, and release boundaries.
- `REFERENCES.md` and `references/ledger.json`: bibliography identity and claim-support state.
- `DECISIONS.md`: durable rationale for important decisions.
- `paper/`: the only canonical authored LaTeX project and its small variant overlays.
- `releases/records/`: Markdown provenance for reviewed immutable instances.

A clean copy of `paper/` must compile all supported variants independently.

## Agent sidecar

- `AGENTS.md`: thin routing entry point for ARIS paper work.
- `.agents/knowledge/`: optional context loaded only when relevant.
- `.agents/skills/`: focused local procedures, the shared repository-role gate, template lifecycle workflows, and bundled-skill wrappers.
- `.agents/vendor/`: immutable third-party skill snapshots.
- `.agents/tools/` and `.agents/tests/`: verification, release, adoption, synchronization, and regression tooling.
- `.agents/runtime/`: ignored short-lived coordination and verification evidence.
- `.agents/template-sync.json`: downstream-local reviewed template baseline.
- `.agents/overleaf-sync.json`: paper-only Overleaf working-copy configuration.

ARIS is a reviewed real-paper case hosted in the template repository. It uses
the reviewed-adoption lifecycle state rather than claiming GitHub Template
provenance; later infrastructure updates use path-level template synchronization.

## Generated release instances

- `dist/<release-id>/`: ignored generated candidate with manifest, report, and selected artifacts.
- `releases/records/<release-id>.md`: optional tracked Human-reviewed provenance only.
- GitHub Actions artifacts, Overleaf, venue portals, and arXiv: delivery systems, not authored sources.

## Dependency direction

Human contracts govern canonical `paper/`; builds produce ignored `dist/`
instances; optional records capture reviewed provenance. Generic Agent guidance
or template defaults never override a current Human decision or ARIS scientific
meaning.
