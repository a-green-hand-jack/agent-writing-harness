# Decisions

## DEC-0001: Evidence-first writing control plane

Decision: register contribution, claims, evidence, numbers, references, floats, notation, and release policy before treating prose as paper-facing.

Rationale: paper errors usually come from untracked factual promotion, stale numbers, citation drift, and release leakage.

## DEC-0002: Separate harness and release surfaces

Decision: `paper/` is the editing surface, `release/` is a generated tex-only surface, and harness state remains private by default.

## DEC-0003: Writing-side Bridge chassis adoption-readiness preflight (issue #6)

Decision: declare `profile: writing` and record Writing-side adoption pins for the `research-writing-bridge` chassis/protocol contracts in `state/bridge-chassis.yaml` (with `state/ccfa.yaml` as the profile/pin pointer). This is a Writing-side adoption-readiness preflight, **not** upstream Bridge conformance: the Bridge chassis-spec, protocol schemas, and golden fixtures are not vendored or pinned here, and Bridge issues #3/#6/#7 remain open. Pins must be fully explicit semver (suffix garbage and default-latest/floating pins are rejected) and ranges must use explicit comparator grammar. The capability registry carries explicit `contract_version`/`schema_version`, stays `profile: writing` / `ownership: writing-owned`, and every registered capability is classified as profile-specific so Writing's paper capabilities are never demanded as generic Bridge chassis. The compatibility matrix is provisional and its canonical rows are cross-checked against the local pins. `scripts/check-bridge-chassis.py` enforces this local self-consistency; the chassis MAJOR gate is executable (a `spec_version` MAJOR bump fails unless `approved_major` is edited in tandem, with the decision recorded at `human/decisions/README.md`).

Rationale: Writing prepares to consume the Bridge chassis-spec without silently drifting from Research, keeps its own implementation and paper-specific capabilities, and offers only the declarative-registry+parity pattern upstream as a governance-gated candidate. Passing the preflight means the Writing-side adoption surface is internally consistent, not that Writing has been validated against a published Bridge contract.

## DEC-0004: Paper-first Human-facing contract (issues #32 and #39)

Decision: make `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and `paper/` the recommended Human orientation and writing surface. Existing evidence, state, adapter, validator, and release paths remain as compatibility infrastructure during an incremental migration.

The repository must not require a Human to understand capability registries, validator topology, experiment ledgers, or Agent runtime details before starting to write. The Human-facing contract should remain short, natural-language, and useful in discussion.

Rationale: the template exists to improve Human–Agent collaboration, not to maximize the amount of visible governance. Human memory and cross-file retrieval are limited; Agents should recover context and maintain consistency, while Humans retain final responsibility for scientific and narrative decisions.

## DEC-0005: Flexible control cues and selective Agent context

Decision: use `locked`, `bounded`, `free`, and `unresolved` as flexible collaboration cues rather than a rigid machine-enforced state model.

- `locked`: an Agent may analyze and propose but must not silently change the meaning.
- `bounded`: an Agent may adjust inside the written boundary.
- `free`: an Agent may handle implementation or wording while respecting higher-level decisions.
- `unresolved`: Human and Agent have not settled the matter; proceed flexibly, keep uncertainty visible, and request a Human decision before a high-impact or hard-to-reverse choice.

Agent knowledge and skills may be rich, but they must be loaded selectively. Current Human-facing contracts and explicit decisions outrank generic knowledge, venue conventions, old adapter instructions, and Agent preferences.

Rationale: a complex schema or permission engine would make the template rigid and increase maintenance burden. Natural-language boundaries plus Agent retrieval and reasoning preserve flexibility while still protecting high-impact decisions.

## Recording future decisions

Use this file for durable, high-impact Human decisions and their rationale. Do not record every sentence edit or temporary discussion. A useful decision states what was chosen, what alternatives were rejected, which paper objects are affected, and what future change would require review. Superseded decisions should remain readable but clearly point to the newer decision.