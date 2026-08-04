# Decisions

## DEC-0001: Paper-first two-layer repository

Decision: the repository consists of a canonical authored paper workspace and an optional Agent sidecar. Human intent lives in root contracts; authored LaTeX lives in `paper/`; Agent support lives in `.agents/`.

## DEC-0002: Remove the old harness and duplicate control planes

Decision: the template contains no capability registry, Bridge preflight, product-specific adapter mirror, experiment/evidence ledger, worktree governance, or duplicate Human/memory store.

## DEC-0003: Flexible control cues

Decision: use `locked`, `bounded`, `free`, and `unresolved` as natural-language collaboration cues, not a rigid permission engine.

## DEC-0004: Selective Agent context

Decision: a task loads current contracts and one relevant focused skill or knowledge document. Generic knowledge never overrides an explicit current Human decision.

## DEC-0005: Stable paper-facing interfaces

Decision: recurring identity, terminology, notation, results, claims, and artifacts use lightweight Human-readable interfaces in `paper/macros.tex` and `PAPER_INTERFACES.md`.

## DEC-0006: One canonical paper with small publication overlays

Decision: `paper/` is the only canonical authored source. `paper/variants/` contains small overlays for `draft`, `anonymous`, `camera-ready`, and `arxiv`.

Variants may control author visibility, acknowledgements, appendix inclusion, and publication-facing presentation hooks. They must not copy canonical sections or silently change claims, experiment interpretation, limitations, or interface meaning.

## DEC-0007: Variant, target, and release instance are separate

Decision:

- a **variant** describes approved presentation differences;
- a **delivery target** describes PDF/source/arXiv-flat/Overleaf packaging;
- a **release instance** identifies one immutable artifact set such as `submission-r1` or `arxiv-v2`.

Rationale: these concepts have different lifecycles and must not be encoded as copied directories or long-lived branches.

## DEC-0008: Generated releases are not committed paper copies

Decision: generated instances live under ignored `dist/<release-id>/` and are delivered through CI artifacts or external systems. The repository tracks only Markdown provenance under `releases/records/`.

The obsolete committed `release/` tree is forbidden. An instance and a record refuse overwrite; new artifacts require a new release ID.

Rationale: generated copies create mechanical diff, stale mirrors, and ambiguity about authored source. Immutable instances preserve provenance without introducing another editable paper tree.

## DEC-0009: Release readiness and packaging validation are distinct

Decision: strict Release builds require all Release contracts to pass and record `release_ready: true`. CI may use an explicit Draft-validation profile to exercise packaging, but its manifest records `release_ready: false`.

Rationale: testing a toolchain must not be misrepresented as Human approval or submission readiness.

## DEC-0010: Downstream template updates use reviewed path-level synchronization

Decision: a paper repository created from this GitHub Template does not merge the upstream template history. It records the last reviewed upstream commit and uses an Agent-assisted three-way plan across that baseline, the requested upstream target, and current downstream files.

Unmodified downstream infrastructure may be applied mechanically. Human contracts, paper content, references, macros, venue configuration, style, and project-specific knowledge are protected and require semantic review. Files changed both upstream and downstream are conflicts. Downstream-only files are preserved unless explicitly removed during review.

The first synchronization of a repository already derived from this template but lacking a trustworthy recorded baseline uses bootstrap mode, followed by downstream validation and explicit baseline recording. An arbitrary existing repository with materially different structure uses the separate adoption workflow in DEC-0011. Template synchronization runs on a dedicated branch and reaches the paper repository through its normal PR and exact-head CI process.

Rationale: repositories created from GitHub templates have independent histories. Whole-tree replacement or unrelated-history merge can silently overwrite scientific meaning and project-specific work. A selective Agent workflow uses fast retrieval and comparison without transferring Human responsibility to automation.

## DEC-0011: Initial adoption is a separate evidence-backed migration

Decision: adapting an existing paper repository that was not created from the template is a distinct workflow from ongoing template synchronization. Adoption first inspects the downstream TeX graph, bibliography, assets, styles, experiment/evaluation surfaces, build commands, CI, and Agent instructions; then pins an exact template commit and produces repository-specific mappings plus a conservative path plan.

Only missing Agent-sidecar infrastructure may be staged mechanically. Human contracts, authored paper content, references, macros, venue/style files, build logic, CI, process documents, and project-specific Agent knowledge require semantic review. Adoption prefers reversible wrappers and compatibility layers over immediate moves, preserves downstream-only files by default, and records the selected template commit as the first synchronization baseline only after full-variant validation of the unchanged reviewed state.

Rationale: an arbitrary existing repository has neither a trustworthy template baseline nor guaranteed path equivalence. Treating filename similarity as semantic identity or copying a factory paper tree can destroy working build behavior and silently alter scientific meaning. A separate adoption workflow makes uncertainty, mappings, and Human responsibility explicit before normal three-way synchronization begins.

## DEC-0012: Overleaf is a paper-only two-way working copy

Decision: the configured Overleaf project is a collaborative working copy of canonical `paper/`, not a second canonical source or an immutable release surface. Overleaf receives only the tracked `paper/` tree. Outbound export runs from a clean canonical default branch; inbound online edits are imported only on a clean `sync/overleaf-*` review branch. Existing Overleaf Git history is preserved during one-time bootstrap, and remote edits block outbound replacement until reviewed and imported.

Rationale: this gives active Overleaf collaboration without exposing governance/CI/Agent surfaces or treating the Overleaf tree as a second source of truth. It is complementary to immutable release delivery and still requires real Overleaf web compilation evidence before claiming platform success.

## DEC-0013: Documentation consistency is a maintained contract

Decision: documentation and relevant LaTeX comments must reflect the current directory structure, tools, publication variants, venue facts, and synchronization workflow. A documentation consistency checker runs in the standard verification path and reads expected current facts from `.agents/documentation-consistency.json`; downstream papers update that configuration rather than editing checker source code.

Rationale: stale documentation is operationally misleading for both human and agent contributors, and a once-only cleanup would let the same class of drift return during normal template evolution.

## Recording future decisions

Record durable, high-impact Human decisions and rationale here. Do not record every sentence edit or temporary discussion. A useful decision states what was chosen, affected paper objects, rejected alternatives when relevant, and what future change requires review.
