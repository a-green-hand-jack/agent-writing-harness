# Agent Sidecar Anatomy

`.agents/` contains optional Agent-facing knowledge, focused skills, tools,
tests, synchronization metadata, and short-lived coordination. It supports the
ARIS paper without becoming a Human work surface or paper dependency.

## Structure

- `knowledge/`: conditional reference material; current Human contracts take priority.
- `knowledge/venues/`: active venue facts and the generic venue schema.
- `knowledge/writing/`: optional downstream Writing DNA workflow.
- `skills/`: focused procedures and thin bundled-skill wrappers.
- `vendor/`: immutable CCFA-Skills and writing-dna-skill snapshots.
- `dependencies/`: exact tool locks and vendor provenance.
- `tools/`: paper-first checks, release tooling, Overleaf, adoption, and template synchronization.
- `tests/`: standard-library positive and negative regressions.
- `runtime/`: ignored short-lived coordination and verification evidence.
- `template-sync.json`: downstream-local reviewed upstream baseline.
- `overleaf-sync.json`: project-specific paper-only Overleaf mapping.
- `documentation-consistency.json`: downstream documentation facts.
- `init-state.json`: downstream initialization marker.

## Boundary

- Human intent lives in root contracts; scientific content lives in `paper/`.
- Publication variants contain only approved presentation switches.
- Generated instances live in ignored `dist/`; durable records are Markdown.
- Agents load one relevant skill and minimum context.
- `paper/` compiles without `.agents/`.
- Generic sidecar guidance never overrides ARIS contracts or Human decisions.
