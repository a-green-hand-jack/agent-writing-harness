---
name: template-sync
description: Use when inspecting or applying reviewed updates from the upstream ccfa-writing-paper-template repository to a downstream paper.
---

# Template Sync

## Trigger

Use when a downstream paper repository needs to inspect or adopt updates from `a-green-hand-jack/ccfa-writing-paper-template`.

Do not load this skill during ordinary writing, experiment discussion, or publication work. Template synchronization is a repository-maintenance task with a separate branch and review cycle.

This is the third lifecycle variant. Read the shared repository role and
initialization gate in `.agents/skills/paper-orientation/SKILL.md` first. A
repository newly created from the GitHub Template uses this skill in
`--bootstrap` mode after its initialization commit; an unrelated repository
without a reviewed baseline uses `template-adoption` first.

## Minimum context

- `.agents/template-sync.json`;
- the current Git branch, status, and diff;
- the upstream template target commit or branch;
- the last recorded upstream baseline, when one exists;
- only the Human contracts or paper files listed as `manual` or `conflict` in the generated plan.

Do not pre-load every paper section, writing guide, venue document, or release record. Retrieve protected content only when the plan shows that an upstream change touches it.

If adoption metadata says `adoption.status: in_progress`, finish reviewed adoption first. Template sync refuses `plan`, `apply`, `verify`, and `record` until then; `reviewed` adoption remains eligible for later baseline advancement.

## Classification

The tool classifies each upstream change as:

- **safe** — downstream still matches the recorded upstream baseline, so the upstream change can be applied mechanically;
- **already** — downstream already matches the requested upstream target;
- **manual** — a protected Human-authored or project-specific surface requires semantic review even when unchanged downstream;
- **conflict** — upstream and downstream both changed, or the downstream path is not a normal file;
- **ignored** — downstream-local metadata, runtime output, or generated output must not be synchronized from upstream.

The classification is a review aid, not permission to alter scientific meaning.

## Procedure

1. Read the shared repository role and lifecycle gate. Confirm that the
   current repository is a downstream writing repository and not the upstream
   template checkout. Stop if it is the template repository or an unrelated
   repository without a reviewed adoption state.
2. Create a checkpoint commit and a dedicated branch such as
   `chore/template-sync`. Do not work on `main`, `master`, or `trunk`.
3. Confirm one valid downstream lifecycle before synchronization. A
   template-created repository must have matching `.agents/template-origin.json`
   and `.agents/init-state.json` records. An unrelated adopted repository must
   instead have `adoption.status: reviewed`; it intentionally has neither of
   those template-creation records. If adoption is `in_progress`, resume
   `template-adoption`. Do not run `paper-init.py clean` for an adoption or use
   `--downstream` as a provenance override.
4. Run:

   ```bash
   python3 .agents/tools/template-sync.py validate
   python3 .agents/tools/template-sync.py status
   python3 .agents/tools/template-sync.py fetch
   ```

5. Generate the plan:

   ```bash
   python3 .agents/tools/template-sync.py plan
   ```

   When `last_synced_commit` is uninitialized, use a first reviewed bootstrap:

   ```bash
   python3 .agents/tools/template-sync.py plan --bootstrap
   ```

<!-- paper-skill-contract: F7-TS-001-v1 -->
6. Read `.agents/runtime/template-sync/plan.md`. Before applying any safe
   change, explain why paths were classified as safe, manual, or conflict and
   state the review boundary: only the safe set may be applied mechanically,
   while manual and conflict paths require deliberate review and no
   classification authorizes a semantic change.
7. With a clean worktree on the dedicated branch, apply only the safe set:

   ```bash
   python3 .agents/tools/template-sync.py apply
   ```

   Safe changes are staged. Manual and conflict versions are exported under `.agents/runtime/template-sync/merge-bundle/` with `baseline/` and `upstream/` copies.
8. Merge manual and conflict files deliberately. Preserve the downstream paper's scientific claims, story, experiments, interfaces, venue choices, authorship, and project-specific Agent knowledge. Do not copy the upstream skeleton over populated paper content.
9. Inspect removed or renamed upstream infrastructure and remove obsolete downstream surfaces only when the replacement is understood.
10. After reviewing all manual merges, create verification evidence bound to the current plan and repository state:

   ```bash
   python3 .agents/tools/template-sync.py verify --reviewed
   ```

   This first establishes that every safe addition, modification, and deletion exactly matches the target in both the index and worktree, then runs repository verification and every build declared in `.agents/paper-build.json`. The default template profile still declares all four publication variants; an adopted publisher-native profile may declare a different reviewed command set. Any subsequent repository change makes the report stale.

11. After manual review and successful validation, record the exact upstream target:

   ```bash
   python3 .agents/tools/template-sync.py record --reviewed
   ```

   Recording rechecks the applied safe state and reruns every mandatory verification command. Runtime receipts and reports are retained as evidence but cannot authorize recording by themselves.

12. Commit the migration, open a PR, wait for the exact-head Actions run, and merge only after every applicable job succeeds.

## First synchronization

A repository created before this skill has no trustworthy recorded baseline. Use `plan --bootstrap`. In bootstrap mode:

- upstream files absent downstream may be proposed as safe additions;
- files already matching upstream are reported as already synchronized;
- existing protected content remains manual;
- existing differing infrastructure becomes conflict rather than being overwritten;
- obsolete downstream-only directories are not deleted automatically.

Record the target only after the bootstrap migration has been reviewed and validated.

## Template-development surface

The upstream default branch contains only the paper-facing surface. Template-development-only machinery (`.agents/evals/`, `check-vendored-skills.py`, `check-vendored-skill-evals.py`, `check-skills.py`, `check-actions.py`, `.agents/dependencies/vendored-skills/`, development-only tests) lives on the upstream `template-dev` branch and never enters a writing repo through synchronization.

If a generated plan proposes any dev-only path — for example from a misconfigured upstream target or a stale pre-split baseline — classify it as manual and do not apply it. A writing repo must never keep or create template-development-only files. Report them as residue if they appear.

## Safety boundary

- Never merge the unrelated upstream and downstream repository histories merely to obtain template updates.
- Never use a target unless the configured remote URL matches `.agents/template-sync.json` and the commit is reachable from its configured upstream branch.
- Never apply on the default branch or with a dirty worktree.
- Never auto-overwrite root governance documents (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`), `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, `DECISIONS.md`, paper sections, figures, tables, references, macros, venue configuration, style, or project knowledge.
- Treat CI workflows, build logic, dependency locks, `REFERENCES.md`, and `references/` ledgers as manual review surfaces. An older downstream sync engine may classify newly added files as safe, so every synchronized workflow must remain inert until the protected Human policy, the `paper/refs.bib` activation marker, and downstream-local `.agents/template-sync.json.reference_integrity.adopted=true` explicitly enable it.
- Never delete downstream-only project files because they are absent upstream.
- Never treat an Agent conflict resolution as Human approval of changed scientific meaning.
- Never record a new baseline before `verify --reviewed` succeeds for the unchanged plan, branch, HEAD, tree, and reviewed worktree state.
- Never bypass downstream PR checks. A successful template repository run does not prove a downstream migration is correct.
- Never use symlinked or wrong-type template-sync runtime directories or files; plan, bundle, receipt, report, cleanup, and custom plan paths must remain regular repository-local paths.

## Handoff

Report:

- previous and target upstream commits;
- safe paths applied;
- manual and conflict paths reviewed;
- protected scientific or publication meaning affected or explicitly preserved;
- obsolete surfaces removed;
- validation commands and exact-head CI evidence;
- the new recorded baseline.
