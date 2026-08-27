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

Only missing Agent-sidecar infrastructure may be staged mechanically. Human contracts, authored paper content, references, macros, venue/style files, build logic, CI, process documents, and project-specific Agent knowledge require semantic review. Adoption prefers reversible wrappers and compatibility layers over immediate moves, preserves downstream-only files by default, and records the selected template commit as the first synchronization baseline only after all builds in the reviewed `.agents/paper-build.json` pass for the unchanged state. The default profile contains the four canonical publication variants; a publisher-native `external-latex` profile may retain its actual entrypoint and command set without fabricating those variants.

Rationale: an arbitrary existing repository has neither a trustworthy template baseline nor guaranteed path equivalence. Treating filename similarity as semantic identity or copying a factory paper tree can destroy working build behavior and silently alter scientific meaning. A separate adoption workflow makes uncertainty, mappings, and Human responsibility explicit before normal three-way synchronization begins.

## DEC-0012: Overleaf is a paper-only two-way working copy

Decision: the configured Overleaf project is a collaborative working copy of canonical `paper/`, not a second canonical source or an immutable release surface. Overleaf receives only the tracked `paper/` tree. Outbound export runs from a clean canonical default branch; inbound online edits are imported only on a clean `sync/overleaf-*` review branch. Existing Overleaf Git history is preserved during one-time bootstrap, and remote edits block outbound replacement until reviewed and imported.

Rationale: this gives active Overleaf collaboration without exposing governance/CI/Agent surfaces or treating the Overleaf tree as a second source of truth. It is complementary to immutable release delivery and still requires real Overleaf web compilation evidence before claiming platform success.

## DEC-0013: Documentation consistency is a maintained contract

Decision: documentation and relevant LaTeX comments must reflect the current directory structure, tools, publication variants, venue facts, and synchronization workflow. A documentation consistency checker runs in the standard verification path and reads expected current facts from `.agents/documentation-consistency.json`; downstream papers update that configuration rather than editing checker source code.

Rationale: stale documentation is operationally misleading for both human and agent contributors, and a once-only cleanup would let the same class of drift return during normal template evolution.

## DEC-0014: Case branches and verification trackers are protected evidence

Decision: the real-paper case branches `case/arxiv-2505-22954`, `case/arxiv-2604-01658`, and `case/arxiv-2605-03042`, their corresponding case issues (#23, #24, #30), and the standing verification trackers (#21, #31) are protected evidence. Do not propose, plan, or perform their deletion. Do not include them in routine cleanup reports or branch/worktree/PR deletion discussions. New `case/` branches and their case issues receive the same protection unless a Human decision records otherwise.

Rationale: these branches and issues carry real-paper verification evidence, source/PDF previews, Round 2 state, and long-running validation contracts. Treating them as ordinary stale feature branches would erase evidence and break references used by active tracker contracts.

This decision governs this upstream template repository. Downstream paper repositories must record their own protected case branches and tracker issues in their own `DECISIONS.md`; do not copy these IDs as project facts.

## DEC-0015: Bundled third-party skill suites

Decision: the template distributes the complete functional CCFA-Skills suite
(`v0.9.0`, commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`, MIT) and
writing-dna-skill (commit `d5145ef671be70d3439524b6b72f55fe06a869a9`, MIT) as
immutable snapshots under `.agents/vendor/`, so downstream paper repositories
work out of the box without any global skill installation. All 17 `ccf-*`
skills plus `writing-dna-skill` and `lieflat-less-ai-tone` are exposed as
thin wrappers under `.agents/skills/` that route to the snapshots and enforce
the paper-contract boundaries.

The "complete functional suite" boundary excludes copyright-ambiguous content
and non-functional assets: third-party paper full-text PDFs and full-text
Markdown reproductions, the 71 MB `ccf-latex-templates` venue LaTeX corpus,
upstream demo/evaluation/plugin/CI surfaces, runtime adapter configs, and the
broken duplicate script `convert_pdf_to_card.py`. Exclusions and file hashes
are recorded in `.agents/dependencies/vendored-skills/provenance.json` and
verified by `.agents/tools/check-vendored-skills.py`.

Ownership: `section-writing` remains the local text owner and runs
`ccf-paper-writer` as its writing engine; `manuscript-consistency-review`
remains Human-triggered and findings-only with `ccf-paper-reviewer` and
`ccf-integrity-auditor` as sidecars; `style-alignment` governs approval of any
Writing DNA distilled by `writing-dna-skill`. `ccf-experiment-designer` is a sidecar of `EXPERIMENTS.md`/`section-writing` (proposals only). The vendor tree is never edited
locally; upstream updates flow through template-sync after review. Human-facing
contracts always take precedence over bundled guidance and exemplar defaults.

Rationale: this makes the template's Agent capability layer self-contained and
verifiable while keeping the paper contracts as the single source of truth, and
avoids redistributing third-party paper content whose redistribution rights are
unverified.

## DEC-0016: Brief-driven paper bootstrap

Decision: a paper can start from a Human-owned **brief repo** whose `BRIEF.md`
holds the paper content spec (identity, thesis, contributions, evidence
inventory, constraints) plus template-usage instructions. The Agent reads the
brief, creates an initialized writing repo from the GitHub Template
(`ccf-project-scaffolder` template-create mode), and ingests the brief into the
Human-facing contracts with `.agents/tools/paper-brief.py ingest --brief
<path>` (`paper-brief-ingest` skill). The brief is copied to the writing-repo
root `BRIEF.md` as provenance and material inventory.

The ingest maps only decided brief fields onto `PAPER.md`; missing or empty
fields stay `unresolved` and the tool never invents a title, claim, result,
citation, venue, author, approval, or release state. `BRIEF.md` is a protected
downstream path in template adoption and synchronization.

Rationale: this makes the harness usable for agent-only, long-running paper
sessions without hand-transcribing the first-session packet, while keeping the
Human-authored brief as the single input contract and preserving the
`unresolved`-honest boundary.

## DEC-0017: Operating modes and the autonomous approval boundary

Decision: each writing repo declares an operating mode in `PAPER.md`
(`## Operating mode`): `collaborative` or `autonomous`. The mode changes how
much confirmation the Agent needs, never what it may silently alter.

- Collaborative: the Human stays in the loop for each substantive step; the
  Agent drafts and revises on request and brings high-impact choices to a
  decision packet.
- Autonomous: the Human provides the brief and materials once; the Agent
  proceeds through idea, outline, drafting, evidence, self-review, polish, and
  variant builds on its own, producing checkpoints for Human review. The Agent
  still stops for Human approval before changing a locked item, approving a
  release, or final submission.

Autonomy does not relax the strong rules: no invented contributions, facts,
results, citations, identity, approval, or external-platform success, and no
promotion of expected or unresolved results into verified evidence.

Rationale: agent-only long-running sessions need a defined boundary between what
the Agent may drive without confirmation and the hard gates that remain Human
decisions. The mode makes that boundary visible in the contract instead of
leaving it implicit.

## DEC-0018: Domain-agnostic positioning with retained repository name

Decision: the template is positioned as a general agent-writing harness for
academic paper projects, not as a CCF-specific workflow. The repository name
retains the `ccfa-` prefix (renaming would break the GitHub Template reference),
but documentation describes the bundled CCFA-Skills suite as one bundled
capability family, not the template identity. Official publisher templates
across venues (PLOS ONE, ICML, ICLR, NeurIPS, ACL, AAAI) and the
`external-latex` build profile already reflect this.

Rationale: the harness serves papers in any field; the CCF letters in the name
are historical. Keeping the name preserves template references while the
positioning and documentation reflect the broader scope.

## Recording future decisions

Record durable, high-impact Human decisions and rationale here. Do not record every sentence edit or temporary discussion. A useful decision states what was chosen, affected paper objects, rejected alternatives when relevant, and what future change requires review.
