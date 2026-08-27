# Why Use This Template?

This template is an **agent-writing harness**. From it you create a writing repo
that coding agents use to draft, revise, evidence, and release a paper. The
harness works in two operating modes: **collaborative** writing, where the
Human and the Agent work step by step, and **autonomous** writing, where the
Human supplies a paper brief and materials and the Agent runs the paper
long-term on its own, producing checkpoints for Human review.

It does not promise better science by itself, and it does not replace the
Human's responsibility for research decisions. Its purpose is more concrete:
make the important parts of paper work explicit, keep them connected as the
manuscript changes, and leave evidence that the delivered paper is the one that
was reviewed.

## The Short Version

An ordinary LaTeX repository mainly answers: “Where are the source files, and
how do I compile them?” This template also answers:

- What is the paper trying to make readers believe?
- Which decisions must an Agent not change silently?
- Which experiment questions and interpretation limits support each claim?
- Which terms, results, figures, and tables must stay consistent across the
  manuscript and publication variants?
- Does each substantive citation support the sentence where it appears?
- Which changes are safe to automate, which require review, and which remain
  unresolved?
- Which specialized writing, literature, experiment, review, visual, and
  submission workflow should help with the current task?
- What exact source and checks produced a release candidate?

The gain is not more automation for its own sake. The gain is a paper workflow
where intent, evidence, authorship, variants, and delivery remain connected.

## A Built-In Paper Skill Stack

The template is not only a collection of LaTeX files and checks. A writing repo
inherits a project-local skill stack that can support the paper from early idea
work through rebuttal and release. The skills are stored in the repository, so
the workflow does not depend on every Agent runtime having the same global
installation.

The stack has two layers:

- **Local owner skills** decide how work enters this paper's contracts and
  canonical source. They preserve project-specific intent and Human authority.
- **Bundled sidecar skills** contribute specialized research and writing
  methods. The template ships immutable snapshots of the CCFA-Skills suite and
  writing-dna-skill under `.agents/vendor/`, with local wrappers under
  `.agents/skills/` and verified provenance and hashes.

Each task loads one local owner and only the relevant sidecars. A sidecar may
help draft, search, analyze, review, or compose, but it cannot override the
Human request, paper contracts, approved evidence, or the local owner. This
combination matters: the writing repo gains specialist capability without
turning generic skill guidance into authority over the paper.

### Local owner skills

These skills connect Agent work to the writing repo's current state:

| Skill | How it helps the paper |
|---|---|
| `paper-orientation` | Recovers the minimum current context at the start of a session without loading the whole repository or stale history. |
| `ccf-project-scaffolder` template-create mode | Creates and initializes an independent writing repo from the GitHub Template, pushes its initialization commit, and hands off with a first-session paper packet. |
| `section-writing` | Owns drafting and substantial revision of a named section from the current claims, evidence, interfaces, references, and section responsibility. |
| `style-alignment` | Governs positioning, narrative architecture, section responsibilities, writing policy, venue overlays, and adoption of a Human-approved Writing DNA. |
| `control-review` | Retrieves impact and requires the right Human decision before a central claim, story choice, experiment condition, limitation, interpretation, or stable interface meaning changes. |
| `decision-packet` | Turns a focused high-impact choice into comparable alternatives with effects, evidence, risks, and unresolved points for the Human. |
| `paper-interface-maintenance` | Keeps recurring names, terms, symbols, results, claims, figures, tables, and macros consistent across every consumer. |
| `reference-repair` | Investigates and repairs BibTeX identity, metadata, duplicates, and preprint or publication-version records without inventing entries. |
| `citation-support-review` | Discovers sources, retrieves exact evidence passages, and checks whether a cited work supports the specific manuscript occurrence at Draft, Review, or Release strength. |
| `manuscript-consistency-review` | Runs a findings-only consistency review after the Human declares a manuscript version ready; it does not silently rewrite the paper. |
| `publication-planning` | Manages publication variants, venue planning, deadlines, official rules, and permitted differences without creating separate scientific copies. |
| `release-review` | Builds and checks a Human-approved immutable submission, arXiv, or camera-ready release instance with provenance. |
| `template-adoption` | Maps an existing paper repository into this workflow without mechanically overwriting scientific content or repository-specific behavior. |
| `template-sync` | Brings reviewed infrastructure updates into a writing repo through a path-level plan while protecting downstream paper content and decisions. |

### Bundled CCFA-Skills capabilities

The template includes all 17 `ccf-*` skills from the CCFA-Skills suite. They
cover more than prose generation:

| Skill | How it can help |
|---|---|
| `ccf-idea-optimizer` | Develops a rough research direction into concrete problem, gap, insight, method, novelty, and evidence-plan candidates. Multiple candidates remain neutral peers until the Human chooses. |
| `ccf-idea-reviewer` | Scores, ranks, compares, and triages early ideas on explicit request, including prior-art awareness and venue-fit risk as review dimensions. Scores remain diagnostic, and the Human chooses the direction. |
| `ccf-literature-searcher` | Searches and screens related work, prior art, datasets, benchmarks, citation candidates, and research opportunities as an external-retrieval task. |
| `ccf-literature-monitor` | Tracks new arXiv, OpenReview, conference, lab, and competitor work that may affect novelty, positioning, or the related-work surface. |
| `ccf-experiment-designer` | Structures datasets, baselines, metrics, ablations, robustness tests, chart evidence, and result-table semantics; it never invents results, and consequential choices remain Human decisions. |
| `ccf-paper-writer` | Supplies the drafting, revision, polishing, and compression engine used inside the local `section-writing` workflow. |
| `ccf-humanization` | Runs a narrow post-draft sidecar for prose de-defending and warning-only concerns without changing claims, evidence, structure, terminology meaning, or limitations. Experiment-facing tasks may separately use its experiment-integrity policy, not that policy as a prose pass. |
| `ccf-paper-to-exemplar` | Converts Human-provided paper PDFs into distilled section-level writing exemplar cards so rhetorical techniques can be reused without copying scientific content or wording. |
| `ccf-visual-composer` | Composes and quality-checks figures, plots, visual tables, diagrams, icons, palettes, and editable visual assets from supplied content or values. |
| `ccf-paper-reviewer` | Provides assessment-only scientific, writing, format, readiness, scoring, and cross-version review only after the Human marks a completed manuscript version ready and requests the findings-only `manuscript-consistency-review`; it does not edit the paper. |
| `ccf-integrity-auditor` | Runs findings-only numeric audit and result-to-claim numeric consistency checks. Citation support and BibTeX repair stay with `citation-support-review` and `reference-repair`. |
| `ccf-submission-checker` | Checks venue template, page limit, anonymity, camera-ready rules, LaTeX/PDF output, metadata, fonts, supplementary material, artifacts, licenses, and policy freshness. |
| `ccf-rebuttal-writer` | Organizes rebuttals, author responses, response letters, reviewer-comment ledgers, revision summaries, and conservative resubmission plans. |
| `ccf-pipeline-orchestrator` | Plans project stages, goals, constraints, gates, artifacts, and handoffs, then routes work to the responsible skill; it does not pretend to execute every specialty itself. |
| `ccf-project-scaffolder` generic scaffold mode | Prepares external CCF paper project folders, templates, configuration, and artifact directories outside the normal template-creation path. Its local template-create mode owns the GitHub Template to writing-repo transition. |
| `ccf-common` | Maintains shared CCFA routing, evidence, privacy, task-mode, handoff, and artifact contracts. It supports the capability layer but is not loaded for ordinary paper work. |
| `ccf-skill-forger` | Maintains and audits skills, triggers, resources, scripts, privacy boundaries, and family governance. It improves the tool layer, not manuscript content directly. |

### Writing DNA and final tone cleanup

The writing-dna-skill family adds two more wrappers:

| Skill | How it can help |
|---|---|
| `writing-dna-skill` | Distills a reviewed paper corpus into reusable academic writing rules: rhetorical and paragraph moves, section responsibilities, sentence density, voice, hedging, transitions, citation weaving, and caption or figure/table narration. A candidate becomes project knowledge only after Human review through `style-alignment` and explicit activation in `PAPER.md`. |
| `lieflat-less-ai-tone` | Applies a whitelist-based final cleanup of recognized AI writing tells after writing is complete, leaving unmatched text and the article framework unchanged. |

Writing DNA is not author imitation. Source papers contribute transferable
rhetorical patterns, not their claims, terminology, citations, technical
content, distinctive wording, or a named author's identity. The activated
project DNA remains below Human decisions and paper contracts in precedence.

**Practical gain:** the Agent can use task-specific research and writing
procedures, learn a Human-approved project style, and carry those capabilities
with the writing repo, while the owner/sidecar boundary keeps scientific meaning
under local control.

## What It Improves

### 1. Human-Agent alignment

Paper prose often mixes high-impact decisions with low-risk editing. That makes
it difficult to tell whether an Agent is improving wording or changing the
paper's meaning.

`PAPER.md`, `EXPERIMENTS.md`, and the collaboration cues `locked`, `bounded`,
`free`, and `unresolved` make that boundary visible. An Agent can revise local
wording or formatting autonomously while escalating a changed contribution,
story, fairness condition, or interpretation.

`PAPER.md` also declares the operating mode (`## Operating mode`). In
**collaborative** mode the Human stays in the loop for each substantive step.
In **autonomous** mode the Human provides the brief and materials once, and the
Agent proceeds through idea, outline, drafting, evidence, self-review, polish,
and variant builds without step-by-step confirmation, stopping for Human
approval before changing a locked item, approving a release, or final
submission. The mode changes how much confirmation the Agent needs, never what
it may silently alter.

**Practical gain:** fewer silent changes to the thesis, claim strength, or
experimental meaning, more focused Human decisions when they are actually
needed, and a safe way for an Agent to run a paper end to end when the Human is
not available to review every step.

### 2. A stable paper narrative

In an ad hoc repository, the central claim, terminology, story, and unresolved
questions may live only in conversations or in scattered prose. New sections
can then drift away from the intended paper.

`PAPER.md` records the paper identity, thesis, contributions, story, style, and
Human decisions in a compact contract. It is not a second manuscript or a
large project ledger; it is the place to recover the current narrative before
writing.

**Practical gain:** an Agent can retrieve the paper's current intent before
drafting, and a Human can inspect whether a revision still serves the same
paper.

### 3. Evidence-aware claims

A citation can have correct metadata and still fail to support the sentence that
uses it. Likewise, a result can be numerically correct while its interpretation
overreaches the experiment.

`EXPERIMENTS.md` records paper-facing questions and interpretation boundaries.
`REFERENCES.md` and `references/ledger.json` separate bibliographic identity
from claim support and bind evidence to exact citation occurrences. The
workflow keeps unsupported, partial, contradicted, unavailable, and unresolved
states visible instead of treating every automated check as approval.

**Practical gain:** fewer citation-by-title errors, fewer unsupported claims,
and a clearer path from an experiment or source passage to the sentence it is
allowed to support.

### 4. Consistency across the manuscript

The same method name, metric, notation, result, uncertainty value, and artifact
responsibility often appears in the abstract, method, experiments, tables,
captions, and conclusion. Manual updates leave obvious opportunities for drift.

`PAPER_INTERFACES.md` identifies recurring paper-facing meanings and the
consumers that need review when they change. Lightweight LaTeX macros provide a
shared surface without forcing the project into a heavy data pipeline. The
verification tools check structure, interfaces, contracts, and reference
coverage.

**Practical gain:** changes are easier to propagate and audit, while local
wording remains flexible instead of every sentence becoming a formal
interface.

### 5. One scientific source, controlled publication forms

Anonymous submission, camera-ready, arXiv, and daily drafts have different
presentation requirements. Maintaining separate copied paper trees turns those
requirements into a source of scientific divergence.

The template keeps `paper/` as the one canonical authored source. Variants are
small overlays that may control author visibility, acknowledgements, appendix
inclusion, and presentation hooks, but may not silently redefine claims,
results, terminology, limitations, or experiment interpretation.

Overleaf is handled separately as a paper-only collaborative working copy, not
as a publication variant, release instance, or second canonical source.

**Practical gain:** publication-specific packaging is possible without creating
multiple competing versions of the scientific content.

### 6. Reproducible delivery and review

“The PDF compiled” is weaker than knowing which source, variant, checks, and
review decisions produced it. It is also easy to overwrite a delivery artifact
or confuse a draft build with a submission-ready release.

The release workflow creates an immutable, ignored instance under `dist/` with
a manifest, source fingerprints, checksums, build receipts, and selected
artifacts. `releases/records/` can hold the Human-reviewed provenance without
committing generated paper trees. CI builds the supported variants and checks
the repository boundaries.

**Practical gain:** reviewers can compare a delivery package with its recorded
source fingerprints and build receipts, and a new submission gets a new release
identity instead of silently rewriting an old one.

### 7. Safer reuse and maintenance

Template-derived writing repos have their own paper content and Git history.
They should receive useful infrastructure updates without importing unrelated
template history or overwriting project-specific decisions.

The adoption and synchronization workflows classify changes as safe, already
present, manual, conflict, or ignored. Human contracts, paper content,
references, build logic, CI, venue configuration, and downstream knowledge are
protected by default.

**Practical gain:** the template can evolve while the writing repo keeps
ownership of its scientific work and receives updates through reviewable,
path-level changes.

## What This Does Not Do

The template is infrastructure for disciplined collaboration, not a research
quality oracle. It does not:

- invent a thesis, contribution, result, experiment, or citation;
- decide whether a claim is scientifically important or novel;
- turn expected or unresolved results into evidence;
- prove that a benchmark comparison is fair;
- replace Human review of central claims, interpretation, or release approval;
- guarantee acceptance by a venue, Overleaf, arXiv, or any other platform;
- make an under-specified paper complete merely by adding files and checks.

The factory copy is intentionally unresolved. The Human still has to supply the
paper's identity, research decisions, evidence, interpretation, and approvals.
The template makes those responsibilities visible and gives the Agent a safer
place to work inside them.

## Who Benefits Most

This template is most useful when:

- a paper is drafted or revised by a coding agent, either collaboratively or autonomously for a long-running session;
- the Human wants to supply a brief and materials once and let the Agent drive the paper forward with checkpoints;
- a paper is revised repeatedly with Agent assistance;
- several contributors need a shared record of narrative and experiment
  boundaries;
- one paper must produce anonymous, camera-ready, or arXiv forms, or maintain
  an Overleaf working copy;
- citations and result interpretations need occurrence-level review;
- the project is expected to survive venue changes, template updates, or a
  handoff to another Agent.

For a one-off document with no Agent collaboration, no publication variants,
and no need for durable evidence or release records, a smaller LaTeX setup may
be sufficient.

## How To Start

If this repository is the template repo, begin with `AGENT_GUIDE.md` and create
a separate writing repo. Do not draft a real paper in the template repo.

In the writing repo, read `AGENTS.md` first. It routes each task to the minimum
relevant context:

1. Read `PAPER.md` for current intent and claims.
2. Read `EXPERIMENTS.md` for experiment, evidence, or result work.
3. Read `PAPER_INTERFACES.md` when recurring names or results are affected.
4. Read `PUBLICATION.md` for variant or delivery work.
5. Read `REFERENCES.md` for citation identity or claim-support work.

The guide explains repository setup; this document explains why the setup is
worth keeping.
