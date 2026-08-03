# State Anatomy

`state/` is the legacy writing control plane retained for existing capabilities, validators, and real-paper case branches.

New Human-facing paper intent belongs in `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and `DECISIONS.md`. New Agent workflows enter through `.agents/tools/` or a focused skill. Do not grow `state/` merely to mirror those natural-language contracts.

- `ccfa.yaml`: existing project/profile configuration surface.
- claim, numeric, result, notation, venue, and float maps: current compatibility data consumed by deterministic checks and real cases.
- `bridge-chassis.yaml`: existing Writing-side Bridge adoption-readiness preflight; not upstream Bridge conformance and not part of the current paper-first roadmap.

This directory can be simplified only after current capabilities and real-paper cases migrate with equivalent executable evidence.
