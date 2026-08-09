# Codex Adapter Anatomy

`roles/`, `workflows/`, `tool-policies/`, and `handoffs/` mirror `.agent/capabilities/`.

`skills/` contains focused paper-maintenance procedures. `tools/` and `tests/` contain
the downstream template-adoption and template-sync control plane plus inert
reference-integrity helpers; protected reference enforcement remains disabled until
`.agents/template-sync.json.reference_integrity.adopted` is explicitly approved.
