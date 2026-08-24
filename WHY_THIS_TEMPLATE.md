# Why Use This Template?

This template is for papers written with both Human and Agent contributors. It
does not promise better science by itself, and it does not replace the Human's
responsibility for research decisions. Its purpose is more concrete: make the
important parts of paper work explicit, keep them connected as the manuscript
changes, and leave evidence that the delivered paper is the one that was
reviewed.

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
- What exact source and checks produced a release candidate?

The gain is not more automation for its own sake. The gain is a paper workflow
where intent, evidence, authorship, variants, and delivery remain connected.

## What It Improves

### 1. Human-Agent alignment

Paper prose often mixes high-impact decisions with low-risk editing. That makes
it difficult to tell whether an Agent is improving wording or changing the
paper's meaning.

`PAPER.md`, `EXPERIMENTS.md`, and the collaboration cues `locked`, `bounded`,
`free`, and `unresolved` make that boundary visible. An Agent can revise local
wording or formatting autonomously while escalating a changed contribution,
story, fairness condition, or interpretation.

**Practical gain:** fewer silent changes to the thesis, claim strength, or
experimental meaning, and more focused Human decisions when they are actually
needed.

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
