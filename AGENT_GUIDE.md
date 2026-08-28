# Agent Guide: From Template Repo to Writing Repo

This is the product-independent entry point for an Agent that encounters this
GitHub repository and needs to use it to write a paper. It applies whether the
Agent runs through Codex, Claude, OpenCode, Copilot, another coding agent, or a
plain shell-based workflow.

`AGENTS.md` remains the binding repository router. This guide explains the
end-to-end workflow and points to the current contracts and focused procedures;
it does not replace them.

## Terminology

Use these names consistently:

| Term | Meaning |
|---|---|
| **template repo** | The upstream GitHub Template repository, `a-green-hand-jack/agent-writing-harness`. It is maintained as reusable infrastructure and is not the workspace for a particular paper. |
| **brief repo** | A Human-owned repository that holds the paper brief: a `BRIEF.md` content spec (identity, claims, evidence inventory, constraints) plus instructions for using this template. It is the input that starts a paper. |
| **writing repo** | A downstream repository for one actual paper, normally created from the template repo and filled from a brief. It has independent Git history, project-specific contracts, and canonical paper content. It is the harness instance the Agent works in. |

Existing documentation may also say "upstream template" for the template repo
and "downstream paper repository" for a writing repo.

## First Determine The Repository Role

Before changing files, inspect the repository root, current branch, worktree,
remote, and initialization state:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
python3 .agents/tools/paper-init.py status
```

Route by the observed state:

| State | What the Agent should do |
|---|---|
| The remote is `a-green-hand-jack/agent-writing-harness` and `paper-init.py status` reports `upstream_template` | This is the template repo. If the Human wants to start a paper, create a separate writing repo by following the happy path below. Do not write the paper here. |
| A valid `.agents/template-origin.json` attestation confirms a separate GitHub-Template-created writing repo, its origin is not the upstream template, and `.agents/init-state.json` is absent | This is an uninitialized writing repo. Run the downstream initialization before editing paper content. |
| `.agents/template-origin.json` and `.agents/init-state.json` are valid, and `.agents/template-sync.json` identifies the configured upstream template | This is an initialized writing repo. Follow `AGENTS.md` and the routine task workflow. |
| `.agents/template-sync.json` records `adoption.status: reviewed`, while template-origin and init-state records are absent | This is a reviewed adopted writing repo. Follow `AGENTS.md`; use template synchronization for later upstream updates. |
| An existing paper repository lacks positive template-creation evidence and has no reviewed adoption state | Use template adoption. Do not copy the template tree over the existing repository. |
| An initialized or reviewed writing repo needs newer template infrastructure | Use template synchronization. Do not merge the template repo's Git history. |

If the facts conflict, stop and report the exact conflict. Do not guess whether
a repository is the template repo or a writing repo. A non-upstream origin,
copied template files, or a generic `paper-init.py status` result is not, by
itself, evidence that the repository came from this GitHub Template.

## Happy Path: Create A Writing Repo

When the Agent starts in the template repo and the Human wants a new paper, the
Agent should create the writing repo itself when its runtime has the required
GitHub and filesystem permissions. Do not ask the Human to run routine commands
that the Agent can safely run.

### 1. Collect only required creation inputs

Determine:

- the GitHub owner or organization;
- the new writing-repo name;
- repository visibility: `--private`, `--public`, or `--internal`;
- a local destination parent directory outside the template repo.

Use explicit Human instructions or already established workspace context. Ask
one focused question only if a material input is unavailable. Repository
visibility and organization ownership must not be guessed.

### 2. Verify the source and destination

Confirm that GitHub access works, the source is still a GitHub Template, the
local parent directory is correct, and the intended destination does not
already contain another repository:

```bash
gh auth status
gh repo view a-green-hand-jack/agent-writing-harness \
  --json isTemplate,nameWithOwner,defaultBranchRef,url
```

Do not place the writing repo inside the template repo. Preserve an existing
destination or remote repository instead of overwriting it.

### 3. Create from the GitHub Template and clone separately

Run the equivalent of:

```bash
gh repo create OWNER/WRITING_REPO \
  --template a-green-hand-jack/agent-writing-harness \
  --private

gh repo clone OWNER/WRITING_REPO /absolute/path/to/WRITING_REPO
```

Replace `--private` with the Human-approved visibility. Run the clone from a
safe location or provide an explicit destination, so it cannot become a nested
directory inside the template repo.

Do not use `--include-all-branches` unless the Human explicitly requires it for
a separate, reviewed reason. A normal writing repo needs the template's default
branch, not the template repo's protected case branches. Do not substitute a
fork or ordinary clone of the template repo: a writing repo must have its own
repository identity and independent history.

If remote creation succeeds but cloning fails, retry cloning the already-created
writing repo; do not create a second remote. If GitHub access is unavailable,
report the failed command and exact blocker rather than silently changing the
creation model.

### 4. Initialize the writing repo before paper work

From the new writing-repo root, first confirm a clean worktree and usable Git
commit identity, then run:

```bash
git var GIT_AUTHOR_IDENT >/dev/null
git var GIT_COMMITTER_IDENT >/dev/null
python3 .agents/tools/paper-init.py record-template-origin --commit
python3 .agents/tools/paper-init.py clean --commit
python3 .agents/tools/paper-init.py status
git status --short --branch
```

The initialization command removes template-specific governance IDs, resets
downstream-local metadata, removes the template's Overleaf configuration,
writes `.agents/init-state.json`, and creates a dedicated initialization
commit. It intentionally requires a clean worktree when `--commit` is used.
Confirm any repository-specific commit-signing and hook requirements before
running it. If commit creation fails after files were staged, do not rerun the
initializer blindly. Inspect the staged initialization change, resolve the
identity, signing, or hook failure, and create the initialization commit with
the command's reported commit message. Stop if unrelated changes appeared.

The legacy `--downstream` flag cannot bypass the required
`.agents/template-origin.json` provenance check and is not part of the normal
GitHub Template path.

After initialization:

- `paper-init.py status` must report `initialized`;
- `origin` must identify the writing repo, not the template repo;
- the worktree should be clean;
- template-specific protected branch and issue IDs must no longer govern the
  writing repo;
- the writing repo must not contain template-development-only paths
  (`.agents/evals/`, `.agents/tools/check-vendored-skills.py`,
  `.agents/tools/check-vendored-skill-evals.py`,
  `.agents/tools/check-skills.py`, `.agents/tools/check-actions.py`,
  `.agents/dependencies/vendored-skills/`); those belong to the template's
  `template-dev` branch, not to a writing repo;
- `.agents/template-sync.json` may still have an uninitialized baseline. Leave
  it that way until the first reviewed template-sync bootstrap.

Push the initialization commit so the remote writing repo, not only the local
clone, is initialized:

```bash
git push origin HEAD
git status --short --branch
git rev-parse HEAD
git rev-parse '@{upstream}'
```

The two commit IDs must match. If branch policy rejects the push, do not force
or bypass it. Push a normal review branch and follow the writing repo's merge
process; report that remote initialization remains pending until the commit is
merged.

### 5. Replace factory placeholders with writing-repo truth

The factory template is intentionally unresolved. Before substantial drafting,
inspect its placeholder title, venue, claims, experiments, author metadata, and
publication assumptions. Replace them only with retrieved repository evidence
or explicit Human decisions; otherwise mark them `unresolved`.

Initialize the Human-facing contracts in this order:

1. `PAPER.md`: paper identity, intended readers, positioning, thesis,
   contributions, narrative, style, protected decisions, and open questions.
2. `EXPERIMENTS.md`: only real paper-facing evidence questions, approved
   conditions, and interpretation limits. It is not a run ledger.
3. `PAPER_INTERFACES.md`: recurring identity, terminology, notation, results,
   claims, figures, tables, and macros that need stable meaning.
4. `PUBLICATION.md`: active variants, target venue assumptions, delivery
   boundaries, and Human review triggers.
5. `DECISIONS.md`: durable high-impact decisions and rationale, including any
   writing-repo-specific protected evidence surfaces.

Do not preserve `TODO` text, the factory target venue, example release IDs, or
template-local governance as if it were established paper fact. It is valid to
keep genuine unknowns unresolved.

### First-session Human input

Once the writing repo exists, the Agent can inspect its repository identity,
initialization state, contracts, and build surface itself. The Human does not
need to provide routine Git commands or fill every contract before the first
writing session. Provide the smallest useful packet below:

```text
Research seed: the problem, setting, and proposed idea or insight
Evidence available: code, data, results, figures, prior draft, references, or "none yet"
Target: venue/year/track and deadline, or "unresolved"
Authors and identity: author list plus anonymity or disclosure constraints
First deliverable: e.g. idea clarification, evidence plan, outline, or a named section draft from supplied claims/evidence
Constraints: language, length, compute/data limits, style examples, and locked decisions
```

The research seed and evidence inventory are the minimum needed to begin
substantive paper writing. `Evidence available: none yet` supports repository
initialization, idea clarification, an evidence plan, or an outline. A section
draft requires supplied or Human-approved claims and evidence for that section.
If those inputs are missing, the Agent must not invent a method, result,
contribution, citation, or venue choice. Missing target, authorship, style, and
constraints remain explicitly `unresolved` until the Human decides them. The
Agent should draft the five contracts from this packet and ask only for
high-impact choices that cannot be safely left unresolved.

### 6. Establish a clean starting point

Run the repository verification after project-specific initialization:

```bash
bash .agents/tools/verify.sh
make pdf
```

`make pdf` builds the daily `draft` variant. A direct build of
`paper/main.tex`, including a default Overleaf import, selects `anonymous`
instead. Do not confuse these defaults.

Commit only when the Human requests a commit or the applicable workflow
explicitly requires one. The initialization command above is the deliberate
exception because its contract includes `--commit`.

## Brief-Driven Start (Collaborative Or Autonomous)

A paper often starts from a **brief repo**: a Human-owned repository containing
`BRIEF.md` (the content spec) plus template-usage instructions and materials.
This is the recommended entry point when the goal is **autonomous** writing —
the Human supplies the brief once, opens a coding agent (TUI or headless) in
the brief repo, and the Agent creates and runs the writing repo long-term.

The Agent flow:

1. Confirm the current repository role with the `paper-orientation` gate. The
   brief repo itself is not a writing repo and must not receive paper content.
2. Read `BRIEF.md` for paper identity, thesis, contributions, evidence
   inventory, constraints, and the declared operating mode.
3. Create and initialize the writing repo exactly as in the happy path above
   (`ccf-project-scaffolder` template-create mode), or clone the brief and run
   `paper-brief-ingest` from an initialized writing repo.
4. Validate and ingest the brief into the contracts:

   ```bash
   python3 .agents/tools/paper-brief.py validate --brief <brief-repo-or-file>
   python3 .agents/tools/paper-brief.py ingest --brief <brief-repo-or-file> [--commit]
   ```

   The tool copies the brief to the writing-repo root `BRIEF.md` and fills only
   decided `PAPER.md` fields. The brief's evidence, delivery, author,
   constraints, and first-deliverable sections stay authoritative in `BRIEF.md`
   until their owner workflows update the other contracts. Missing or empty
   brief fields stay `unresolved`; never invent a value.
5. Confirm `PAPER.md` `## Operating mode` (`collaborative` or `autonomous`) and
   the approval boundary, then run `bash .agents/tools/verify.sh` and `make pdf`.
6. In **autonomous** mode, proceed through drafting, self-review, polish, and
   variant and checkpoint builds without step-by-step confirmation. Idea
   shaping and evidence analysis may be prepared as proposals only and never
   settle a Human-owned decision. Produce checkpoints (commits, builds, review
   notes) for the Human. Stop for Human approval before changing a locked item,
   approving a release, or final submission. In **collaborative** mode, follow
   the routine task workflow and wait for Human request or approval per step.

Autonomy never relaxes the strong rules: no invented contributions, facts,
results, citations, identity, approval, or external-platform success, and no
promotion of expected or unresolved results into verified evidence.

## Sources Of Truth And Decision Authority

For ordinary work in a writing repo, use this priority when sources conflict:

1. the latest explicit Human decision;
2. current `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, and
   `PUBLICATION.md` contracts, plus `REFERENCES.md`, `paper/refs.bib`, and the
   relevant `references/ledger.json` records for reference or citation tasks;
3. applicable durable rationale in `DECISIONS.md`;
4. an activated Human-approved Writing DNA under `.agents/knowledge/writing/`;
5. current official venue knowledge for an active venue task;
6. the selected task skill;
7. general writing guidance and Agent preference.

`AGENTS.md` defines repository routing and safety boundaries. Runtime-specific
instruction files may point to it, but must not create a competing paper
contract.

The collaboration cues mean:

- **locked**: analyze or propose; do not silently change the meaning;
- **bounded**: work inside the written boundary;
- **free**: implement or revise wording while preserving higher-level meaning;
- **unresolved**: keep uncertainty visible, prefer reversible progress, and ask
  before a high-impact or hard-to-reverse choice.

These cues are collaboration language, not an automated permission system. The
Human retains decisions about central claims, claim degradation, story,
experiment fairness, important result interpretation, stable interface meaning,
active variants, release approval, and external publication.

## Routine Agent Task Workflow

For each task in an initialized writing repo:

1. Read the root `AGENTS.md` instruction chain.
2. Inspect the current branch, status, diff, and the exact authored surface
   implicated by the request.
3. Read `PAPER.md` first. Read other contracts only when the task touches them.
4. Select the one primary owner workflow from `AGENTS.md`. Load its primary
   skill when the route names one; a tool-only route does not justify loading
   an unrelated skill. If the runtime has a skill loader, use it; otherwise
   read the selected `SKILL.md` directly.
5. Load only explicitly permitted sidecar skills and the minimum local context
   named by the owner. Never preload the whole skill or knowledge family.
6. Identify whether affected meaning is locked, bounded, free, or unresolved.
7. Retrieve evidence before asking the Human to decide. Use a concise decision
   packet for a real high-impact choice.
8. Make the smallest change that fully satisfies the request. Edit canonical
   `paper/` content, not a copied publication variant.
9. Run focused validation, then the applicable repository or release check.
10. Report changed files, semantic effects, decisions, unresolved items,
    affected interfaces or variants, and validation evidence.

Do not invent contributions, facts, results, citations, identity, approval, or
external-platform success. Do not promote expected results to verified evidence
or observational relationships to causal claims.

## Task Routing Index

Use `AGENTS.md` as the current routing table. The following index explains the
common routes without replacing it:

| Task | Read in addition to `PAPER.md` | Primary owner or procedure |
|---|---|---|
| Recover context at the start of a writing session | Active section and current diff | `.agents/skills/paper-orientation/SKILL.md` |
| Create and initialize a new writing repo from this GitHub Template | Repository role, GitHub creation inputs, and first-session packet | `.agents/skills/ccf-project-scaffolder/SKILL.md` in template-create mode |
| Start a paper from a Human-provided brief repo (brief → contracts, operating mode) | `BRIEF.md`, repository role, and first-session packet | `.agents/skills/paper-brief-ingest/SKILL.md` |
| Draft or substantially revise a paper section | Active section; relevant experiment, interface, and citation records only | `.agents/skills/section-writing/SKILL.md` |
| Change positioning, story architecture, section responsibility, or writing policy | Relevant paper and decision contracts | `.agents/skills/style-alignment/SKILL.md` |
| Change a central claim, experiment condition, limitation, result interpretation, or stable interface meaning | Every directly affected contract and consumer | `.agents/skills/control-review/SKILL.md` |
| Ask the Human to choose among high-impact alternatives | Retrieved options, impacts, and evidence | `.agents/skills/decision-packet/SKILL.md` |
| Design experiments or evidence structure | `EXPERIMENTS.md` and available evidence | `EXPERIMENTS.md` owner with `.agents/skills/ccf-experiment-designer/SKILL.md` as sidecar |
| Draft approved experiment or result-interpretation prose | Active section, `EXPERIMENTS.md`, and available evidence | `.agents/skills/section-writing/SKILL.md` with the experiment designer as a permitted sidecar |
| Change experiment fairness, metrics, baselines, limitations, or interpretation meaning | `EXPERIMENTS.md`, evidence, affected claims, and consumers | `.agents/skills/control-review/SKILL.md` and a Human decision |
| Add or repair a reference identity | `REFERENCES.md`, `paper/refs.bib`, relevant ledger records | `.agents/skills/reference-repair/SKILL.md` |
| Add or assess claim-supporting citations | Exact citation occurrence and evidence passages | `.agents/skills/citation-support-review/SKILL.md` |
| Add or change recurring terminology, notation, results, claims, figures, tables, or macros | `PAPER_INTERFACES.md` and every consumer | `.agents/skills/paper-interface-maintenance/SKILL.md` |
| Plan variants, venue work, or delivery targets | `PUBLICATION.md` and current official venue facts | `.agents/skills/publication-planning/SKILL.md` |
| Review a Human-declared completed manuscript version | All manuscript surfaces required by the review | `.agents/skills/manuscript-consistency-review/SKILL.md` |
| Build a Human-approved immutable release candidate | Publication, reference, venue, and release contracts | `.agents/skills/release-review/SKILL.md` |
| Bring the template into an unrelated existing paper repository | Generated inspection and mapping evidence | `.agents/skills/template-adoption/SKILL.md` |
| Bring newer template infrastructure into a writing repo | Sync metadata and generated path plan | `.agents/skills/template-sync/SKILL.md` |

Bundled `ccf-*`, Writing DNA, and tone skills are sidecars where `AGENTS.md`
explicitly permits them. They never replace the local owner or override a Human
contract. Never edit `.agents/vendor/` directly.

## Writing And Evidence Workflows

### Section drafting

For a named section, identify its reader task and the one point readers should
retain. Read only the active section, enough neighboring text for continuity,
and the relevant contract entries. Draft from available claims, evidence,
results, interfaces, and references; keep missing material visible.

Local coherence checking is part of drafting. A manuscript-wide reviewer pass
is not. Do not launch broad review or rewrite workflows while a section-writing
task is active.

### Experiments and results

`EXPERIMENTS.md` records what evidence the paper needs and how it may be
interpreted. It does not duplicate experiment code, scheduling, raw metrics, or
the code repository's run lifecycle.

Before changing a baseline, split, primary metric, evaluation protocol,
fairness condition, statistical interpretation, limitation, or claim supported
by an experiment, retrieve the evidence and obtain the required Human decision.
Keep negative and inconclusive results visible when they constrain a central
claim.

### Citations and references

Bibliographic identity and claim support are separate obligations. For every
substantive citation occurrence:

1. identify the exact manuscript claim;
2. resolve or discover the intended work;
3. retrieve bounded, verbatim evidence passages with locators;
4. decide whether those passages support the exact claim;
5. record the Draft result as provisional in `references/ledger.json`.

A title match, DOI, metadata record, abstract similarity, or real paper identity
does not prove claim support. An Agent never upgrades evidence to
`human-confirmed`. Same-object metadata repairs update `paper/refs.bib` and the
ledger together; ambiguous identity or version choices go to the Human.

### Stable paper interfaces

Use `PAPER_INTERFACES.md` and `paper/macros.tex` for recurring semantic objects.
Before changing one, find every consumer and distinguish a presentation or
value update from a meaning change. The Agent may maintain consistency and
implement approved updates; the Human decides scientific meaning and important
result interpretation.

Interfaces are not an automatic code-to-paper import mechanism. Never copy raw
results into claims without reviewing conditions, aggregation, uncertainty, and
the interpretation ceiling.

## Publication Lifecycle

### Variants and venue planning

The writing repo has one canonical authored paper under `paper/`. The
`draft`, `anonymous`, `camera-ready`, and `arxiv` variants are small
presentation overlays. They may control author visibility, acknowledgements,
appendix inclusion, labels, and packaging hooks; they must not silently diverge
in scientific prose, claims, experiment meaning, fairness, or limitations.

Load venue knowledge only when venue planning or submission is the active task.
Verify deadlines, page limits, anonymity, and operational rules against current
official sources. Internal milestones are not official deadlines.

Build variants explicitly when required:

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

### Overleaf

Overleaf is a paper-only working copy, not a second canonical source or a
release instance. Configure a writing-repo-specific
`.agents/overleaf-sync.json`; never retain the template repo's configuration or
credentials.

Validate and fetch before use:

```bash
python3 .agents/tools/overleaf-sync.py validate
python3 .agents/tools/overleaf-sync.py fetch
```

Export only from a clean canonical branch. Import online edits through a clean
`sync/overleaf-*` review branch, rebuild, and verify before merging. The first
export uses `push --bootstrap`; this is unrelated to template-sync bootstrap.
Real Overleaf compilation remains unverified until it is actually exercised.

### Manuscript review

Run a version-level consistency review only after the Human identifies a
completed manuscript version as ready. The default review is findings-only and
does not edit. Drafting and review are separate owner workflows.

### Immutable releases

A release build packages a reviewed source state; it does not itself prove
Human approval, venue acceptance, Overleaf success, arXiv success, or
publication. Use a new release ID for every revision and never overwrite an
existing instance or record.

The release procedure is owned by `.agents/skills/release-review/SKILL.md`.
Generated artifacts live under ignored `dist/<release-id>/`; tracked provenance
lives as Markdown under `releases/records/`.

## Existing Repository Adoption

Use adoption when the target is an unrelated existing paper repository, not
when starting a new paper from the GitHub Template. Initial adoption must run
on a dedicated non-default branch and preserve the existing paper, build, CI,
references, styles, and project-specific Agent knowledge.

From a trusted template checkout, the lifecycle is:

```bash
python3 .agents/tools/template-adoption.py --root /path/to/existing-paper inspect
python3 .agents/tools/template-adoption.py --root /path/to/existing-paper plan --fetch
python3 .agents/tools/template-adoption.py --root /path/to/existing-paper apply
```

The Agent then performs the manual semantic migration, runs:

```bash
python3 .agents/tools/template-adoption.py --root /path/to/existing-paper assess
python3 .agents/tools/template-adoption.py --root /path/to/existing-paper verify --builds
python3 .agents/tools/template-adoption.py --root /path/to/existing-paper finalize --reviewed
```

`assess` is diagnostic and cannot authorize finalization. `--builds` runs every
command declared in the reviewed `.agents/paper-build.json`; the historical
`--variants` spelling is an alias. A publisher-native repository may declare a
single manuscript build instead of fabricating this template's four variants.
See `LATEX_TEMPLATES.md` for the profile contract and tested template matrix.
`apply` stages only
safe missing sidecar infrastructure. Never mechanically overwrite or move
scientific prose, results, references, figures, tables, macros, venue files,
build logic, CI, Human contracts, or downstream-only files. Follow
`.agents/skills/template-adoption/SKILL.md` for the complete review contract.
An adoption never creates GitHub Template provenance or an initialization
marker: `paper-init.py status` transitions from `adoption_in_progress` to
`adoption_reviewed` when finalization succeeds.

## Template Synchronization

A writing repo has independent history. Never merge or rebase the template
repo's branch into it. Synchronization is a reviewed path-level workflow on a
dedicated non-default branch:

```bash
python3 .agents/tools/template-sync.py validate
python3 .agents/tools/template-sync.py status
python3 .agents/tools/template-sync.py fetch
python3 .agents/tools/template-sync.py plan
```

Use `plan --bootstrap` for the first reviewed synchronization when no
trustworthy baseline exists. Read the generated plan before applying anything:

- `safe` paths may be staged mechanically;
- `already` paths already match;
- `manual` paths require semantic review;
- `conflict` paths changed on both sides or have an unsafe type;
- `ignored` paths are writing-repo-local or generated state.

Apply only the safe set:

```bash
python3 .agents/tools/template-sync.py apply
```

Next inspect the generated merge bundle and deliberately resolve every manual
and conflict path. Preserve downstream scientific and project-specific meaning;
`apply` does not complete that review. Only after those resolutions are
finished and reviewed, run:

```bash
python3 .agents/tools/template-sync.py verify --reviewed
python3 .agents/tools/template-sync.py record --reviewed
```

Do not overwrite Human contracts or paper content, remove downstream-only
files, infer scientific approval from a path classification, or record a
baseline before reviewed verification succeeds. Follow
`.agents/skills/template-sync/SKILL.md` for the complete procedure.

## Verification Guide

Choose validation that proves the requested result:

| Change | Minimum relevant validation |
|---|---|
| Local prose change | Build the affected variant and inspect warnings or the rendered output as relevant |
| Contract, interface, reference, publication, or Agent-sidecar change | `bash .agents/tools/verify.sh` plus the affected build |
| Variant-sensitive paper change | Build every affected variant explicitly |
| Adoption | `template-adoption.py assess`, then reviewed `verify --builds` before finalization |
| Template synchronization | `template-sync.py verify --reviewed` before recording |
| Release candidate | The release-review procedure, strict release checks, manifest/checksum validation, and Human approval where required |

`bash .agents/tools/verify.sh` checks repository structure and contracts but is
not a substitute for every declared build or external platform test.
Never claim an unexecuted check passed.

## Prohibited Shortcuts

- Do not write a real paper directly in the template repo.
- Do not create a writing repo by forking or ordinarily cloning the template
  when GitHub Template creation is the requested workflow.
- Do not copy all template branches into a writing repo by default.
- Do not run downstream initialization against the upstream template repo.
- Do not copy a factory contract, venue, reference ledger, protected ID, or
  approval state into a writing repo as project truth.
- Do not load all skills and knowledge for ordinary work.
- Do not copy canonical scientific content into publication variants.
- Do not merge unrelated template history into a writing repo.
- Do not overwrite an existing release instance or release record.
- Do not report external publication, venue acceptance, or platform success
  without evidence from the actual platform.

## Agent Handoff Checklist

At the end of a task, report only applicable items:

- whether work occurred in the template repo or a named writing repo;
- the writing repo URL/path, branch, and initialization state when it was
  created;
- files changed;
- scientific or narrative meaning affected or explicitly preserved;
- Human decisions made and unresolved choices;
- affected paper interfaces, experiment contracts, publication variants, or
  references;
- adoption or template-sync baseline and conflict set when relevant;
- release ID and manifest when relevant;
- exact validation commands and outcomes;
- external checks that remain unverified.
