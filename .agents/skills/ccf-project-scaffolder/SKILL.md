---
name: ccf-project-scaffolder
description: Create and initialize a new downstream writing repository from the a-green-hand-jack/ccfa-writing-paper-template GitHub Template, or scaffold an external CCF paper project. Use for GitHub Template creation, repository setup, project scaffolding, and reproducible workspace setup. Do not use to overwrite an existing paper repository, plan workflow stages only, or generate research content.
---

# CCF Project Scaffolder (bundled)

Bundled from the CCFA-Skills suite (MIT). The canonical upstream skill lives in the immutable vendor tree; this wrapper routes to it and enforces the paper-contract boundaries. Do not edit the vendor tree.

## Canonical content

Load the full upstream skill and its resources from the vendor tree (immutable; never edit):

- Skill: `.agents/vendor/ccfa-skills/ccf-project-scaffolder/SKILL.md`
- Resources: any existing sibling `references/`, `scripts/`, `resources/`, `templates/`, or `assets/` directories under `.agents/vendor/ccfa-skills/ccf-project-scaffolder`.

## Local precedence

1. Current Human request and Human-approved decisions.
2. `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md`.
3. Local owner skill or contract boundary (see below).
4. Current official venue knowledge: `.agents/knowledge/venues/`.
5. Human-approved Writing DNA: `.agents/knowledge/writing/paper-writing-dna.md` (only when the Human has activated it).
6. Upstream CCFA guidance.
7. Upstream exemplar defaults and generic quotas.

## Owner and boundary

The vendor content describes generic external CCF scaffolding. This local
wrapper adds a template-create mode owned by this repository. Read the shared
repository role and lifecycle gate in
`.agents/skills/paper-orientation/SKILL.md` before choosing a mode.

In template-create mode, this skill owns the complete operational transition
from the upstream GitHub Template to an independently identified, initialized
writing repository. It does not write scientific content or silently decide
paper identity, claims, evidence, venue, authorship, or approval.

Never scaffold over this repository's structure; the template's own `paper/` tree is the canonical scaffold.

## Template-create mode

Use this mode only when the current repository has been observed as
`upstream_template` or when the Agent has switched to a separately validated
trusted checkout with that role. A request made from another repository must
first locate and validate the trusted template checkout; do not run this mode
against the current downstream or unrelated paper repository.

### Required operational inputs

Determine, without guessing:

- GitHub owner or organization;
- new writing-repository name;
- visibility: `--private`, `--public`, or `--internal`;
- local destination parent outside the template repository.

The Human may also provide the first-session paper packet documented by the
shared lifecycle gate. Do not require the Human to provide routine Git
commands, repository status, or template file lists.

### Procedure

1. Run the shared lifecycle gate and confirm that the current origin is exactly
   `a-green-hand-jack/ccfa-writing-paper-template` and that
   `paper-init.py status` reports `upstream_template`. Stop on any conflict.
2. Verify GitHub access and source identity without printing credentials:

   ```bash
   gh auth status
   gh repo view a-green-hand-jack/ccfa-writing-paper-template \
     --json isTemplate,nameWithOwner,defaultBranchRef,url
   ```

   Require `isTemplate: true`. Check that the destination parent exists and
   the intended local destination does not already contain a repository.
3. Create the new GitHub repository from the template and clone it separately:

   ```bash
   gh repo create OWNER/WRITING_REPO \
     --template a-green-hand-jack/ccfa-writing-paper-template \
     --private
   gh repo clone OWNER/WRITING_REPO /absolute/path/to/WRITING_REPO
   ```

   Substitute the Human-approved visibility and destination. Do not fork,
   ordinarily clone the template, request `--include-all-branches`, or place
   the writing repo inside the template repo. If creation succeeds but clone
   fails, retry the clone of the existing repository; never create a second
   remote.
4. In the new clone, confirm a clean worktree, usable Git identity, and an
   origin that identifies the new writing repository. Then run exactly:

   ```bash
    git var GIT_AUTHOR_IDENT >/dev/null
    git var GIT_COMMITTER_IDENT >/dev/null
    python3 .agents/tools/paper-init.py record-template-origin --commit
    python3 .agents/tools/paper-init.py clean --commit
   python3 .agents/tools/paper-init.py status
   git status --short --branch
   ```

    Do not use `--downstream` on the normal GitHub Template path. The provenance
    command checks the new repository through GitHub's `template_repository`
    field and records that evidence in `.agents/template-origin.json` before
    initialization. Inspect and
   resolve identity, signing, or hook failures before retrying; do not rerun
   the initializer blindly after a partial commit attempt.
5. Push the initialization commit so the remote repository is initialized too:

   ```bash
   git push origin HEAD
   git status --short --branch
   git rev-parse HEAD
   git rev-parse '@{upstream}'
   ```

   Require matching local and upstream commit IDs. If branch policy rejects the
   push, do not force or bypass it; report that remote initialization remains
   pending and follow the repository's review process.
6. Pass the first-session paper packet to the writing-repo orientation flow.
   Draft or update the five Human contracts only from that packet, repository
   evidence, and explicit Human decisions. Leave unknown title, venue, type,
   authorship, claims, results, experiments, and style as `unresolved`.
   When the Human provides a **brief repo** (a `BRIEF.md` content spec plus
   template-usage instructions), ingest it with `paper-brief-ingest` instead of
   hand-filling the contracts: validate and then run
   `python3 .agents/tools/paper-brief.py ingest --brief <path>`. Confirm the
   declared `Mode` (`collaborative` or `autonomous`) before paper work begins.
7. Run the downstream verification and daily draft build after initialization:

   ```bash
   bash .agents/tools/verify.sh
   make pdf
   ```

   A newly created repository has no reviewed template-sync baseline. Do not
   record one during creation; the first reviewed infrastructure update uses
   `template-sync.py plan --bootstrap` after the paper repository has been
   reviewed.

## Generic scaffold mode

When the target is an external or new CCF project that is not a repository
created from this GitHub Template, follow the bundled vendor workflow for
structure and metadata only. Do not use generic `ccfa.yaml` scaffolding to
replace this template's paper-first contracts.

## Provenance

Source: https://github.com/mikubaka88/CCFA-Skills (v0.9.0) at commit `fd5c7e3afcc097d874d296a0e1e8118ae597f847`. Excluded upstream resources (third-party paper PDFs, venue LaTeX template corpus, demo/evaluation assets, runtime adapter configs, broken duplicate scripts) are recorded in `.agents/dependencies/vendored-skills/provenance.json`. Fetch reference PDFs on demand into ignored `.agents/runtime/`; never write into `.agents/vendor/`.
