---
name: template-adoption
description: Use when adapting an existing paper repository to this template or establishing a reviewed first migration baseline.
---

# Template Adoption

## Trigger

Use when an existing paper repository was not created from `a-green-hand-jack/ccfa-writing-paper-template`, has no trustworthy template baseline, or uses materially different paths and build conventions that require a reviewed first migration.

Do not use this skill for ordinary upstream updates after adoption. Once `.agents/template-sync.json` records explicit `adoption.status: reviewed` state for the baseline, route future updates to `.agents/skills/template-sync/SKILL.md`. A non-null baseline alone is not evidence that adoption completed.

Do not use this skill for a repository newly created from the GitHub Template.
That path is owned by `ccf-project-scaffolder` in template-create mode and then
uses `template-sync --bootstrap` for its first reviewed infrastructure update.

## Minimum context

- the downstream repository root, current branch, status, and diff;
- the selected upstream template URL, branch, and exact target commit;
- the detected LaTeX entrypoint and its `\input` / `\include` graph;
- bibliography, figures, tables, style/venue files, experiment/evaluation surfaces, build commands, and CI workflows that are actually referenced;
- existing `AGENTS.md`, `CLAUDE.md`, Copilot/Cursor instructions, or project-specific Agent knowledge;
- only the Human contracts and authored files implicated by the generated mapping plan.

Do not recursively preload the whole repository. Start from the inspection report, then retrieve a candidate file only when its mapping or semantics must be reviewed.

## Adoption model

Initial adoption is not an unrelated-history merge and not a whole-tree copy. It has four distinct responsibilities:

1. **inspect** — discover concrete repository evidence without changing files;
2. **plan** — pin an exact template commit, classify template paths, and propose repository-specific mappings;
3. **apply** — stage only missing Agent-sidecar infrastructure classified as `safe`;
4. **finalize** — after semantic migration and validation, record the selected template commit as the first synchronization baseline.

The synchronization metadata carries explicit adoption state. `in_progress` identifies a resumable adoption; `reviewed` identifies completion bound to the exact target and verified repository fingerprint. Baseline equality does not substitute for this state.

The plan uses the same safety vocabulary as template synchronization:

- **safe** — a missing sidecar-anatomy file, `.agents/knowledge/`, `.agents/skills/`, `.agents/tests/`, `.agents/tools/`, or runtime-ignore file that can be added without overwriting downstream work;
- **already** — the downstream file already matches the selected template target;
- **manual** — Human contracts, paper content, references, build logic, CI, publication configuration, process documents, or any unclassified surface requiring semantic review; an exact byte match does not waive review for a protected surface;
- **conflict** — an existing downstream Agent-sidecar path differs from the template, or a path is a symlink/non-file entry;
- **ignored** — generated adoption state, synchronization metadata, or runtime output.

## Procedure

1. Read the repository role and lifecycle gate in
   `.agents/skills/paper-orientation/SKILL.md`. Confirm that this is an
   unrelated or ambiguous existing paper repository, not the upstream template
   and not a GitHub Template-created downstream repository. Create a checkpoint
   commit and a dedicated branch such as `chore/template-adoption`. Do not work
   on `main`, `master`, or `trunk`.
2. Run the adoption tool from a trusted template checkout. The target repository does not need to contain `.agents/` yet:

   ```bash
   python3 /path/to/ccfa-writing-paper-template/.agents/tools/template-adoption.py \
     --root /path/to/existing-paper inspect

   python3 /path/to/ccfa-writing-paper-template/.agents/tools/template-adoption.py \
     --root /path/to/existing-paper plan --fetch
   ```

3. Read `.agents/runtime/template-adoption/inspection.md` and `plan.md`. Explain:
   - the inferred main TeX entrypoint and alternatives;
   - bibliography, section, figure, table, style, experiment/evaluation, build, CI, and Agent-instruction mappings;
   - every `safe`, `manual`, and `conflict` path;
   - uncertain or missing evidence.
4. With a clean worktree on the dedicated branch, apply only the safe set:

   ```bash
   python3 /path/to/ccfa-writing-paper-template/.agents/tools/template-adoption.py \
     --root /path/to/existing-paper apply
   ```

   The tool stages missing Agent-sidecar anatomy, knowledge, skills, tests, tools, and runtime-ignore infrastructure, creates a downstream-specific `.agents/template-sync.json` with an uninitialized baseline, and exports upstream/downstream review copies under `.agents/runtime/template-adoption/merge-bundle/`. It does not create Human contracts, move paper content, replace build logic, rewrite CI, or record the target as reviewed.
   If stale or prematurely recorded sync/adoption metadata remains from an incomplete attempt, review its provenance and explicitly resume with `apply --recover-reviewed`. Recovery preserves prior baseline metadata in the adoption audit history; it does not treat that baseline as reviewed or silently erase it.
   Do not run `paper-init.py clean` and do not create
   `.agents/template-origin.json` or `.agents/init-state.json`. Those records
   prove the separate GitHub Template-created lifecycle. During adoption,
   `paper-init.py status` reports `adoption_in_progress`; after reviewed
   finalization it reports `adoption_reviewed`.
5. Perform the semantic migration deliberately:
    - preserve a working publisher-native entrypoint through an `external-latex` profile, or prefer a thin `paper/main.tex` compatibility wrapper before moving it;
   - preserve section identity and input order while paths are normalized;
   - map one authoritative bibliography rather than copying references into divergent files;
   - preserve figure source assets, wrappers, generated-table provenance, venue classes, styles, and bibliography styles;
    - merge Make targets and CI jobs into the existing build and protection model instead of replacing it;
    - merge the template's runtime ignore rules into the existing `.gitignore`
      without replacing downstream patterns, so verification does not leave
      bytecode or generated output untracked;
   - merge Agent routing and safety rules while retaining project-specific knowledge;
   - initialize `PAPER.md`, `EXPERIMENTS.md`, `PAPER_INTERFACES.md`, `PUBLICATION.md`, and `DECISIONS.md` only from repository evidence and Human decisions. Mark unknown claims, authorship, results, venue choices, and approval as unresolved.
6. Inspect downstream-only files and obsolete surfaces. Do not delete them merely because the template lacks them. Remove or redirect a surface only after its replacement and dependency impact are understood.
7. Run the explicit collect-all assessment after the repository has the intended template shape:

   ```bash
   python3 .agents/tools/template-adoption.py assess
   ```

   Assessment executes every standard leaf check and all builds declared in `.agents/paper-build.json` independently, records all outcomes in `.agents/runtime/template-adoption/assessment.json` and `assessment.md`, and does not stop at the first failure. It is diagnostic only: even a successful assessment cannot authorize finalization and is not a substitute for reviewed verification.
8. Run focused reviewed verification:

   ```bash
   python3 .agents/tools/template-adoption.py verify --builds
   ```

   The verification report records the exact template target, fresh inspection/mapping fingerprint, declared command set, expected output checks, and a fingerprint of the reviewed downstream state. Finalization also requires the profile entrypoint and all five Human contracts to be present. The historical `--variants` flag remains an alias for `--builds`. Also run any repository-specific experiment, artifact, or deployment checks that the generic template cannot know about. External venue portals, Overleaf import, and arXiv compilation remain unverified until actually exercised.
9. After Human review and successful declared-build validation, record the exact template target as the first sync baseline. Finalization refuses a missing, failed, agent-only, wrong-target, stale, or assessment-only report:

   ```bash
   python3 .agents/tools/template-adoption.py finalize --reviewed
   ```

10. Review the staged `.agents/template-sync.json`, commit the migration, open a PR, and merge only after the downstream repository's exact-head CI succeeds. Future template updates use `template-sync.py plan`, not adoption.

## Mapping principles

- Evidence outranks naming conventions. A file named `main.tex` is only a candidate until its document class, document body, inputs, bibliography, and build usage support the mapping.
- Prefer wrappers and compatibility layers over immediate moves. Reversible migration is safer than structural cleanup performed before the build graph is understood.
- A path mapping does not imply semantic equivalence. `README.md` is not automatically `PAPER.md`; an experiment script is not automatically evidence for a paper claim.
- Existing build and CI behavior is part of the downstream contract. Preserve successful commands, required checks, caching, artifact publication, and protected-branch semantics.
- The first baseline means “reviewed against this exact template commit,” not “all downstream files are identical to the template.”

## Template-development surface

The template's default branch is the paper-facing surface only. Template-development-only machinery — `.agents/evals/`, the vendor and skill validation checkers (`check-vendored-skills.py`, `check-vendored-skill-evals.py`, `check-skills.py`, `check-actions.py`), the vendored-skills dependency lock (`.agents/dependencies/vendored-skills/`), and development-only tests — lives on the template's `template-dev` branch and is never part of a writing repo.

Adoption must not install any of these dev-only paths. If an older template snapshot or an interrupted run stages them, treat them as template residue: do not keep them, do not treat them as required infrastructure, and remove or redirect them only after understanding their dependency impact, following the same discipline as other obsolete surfaces. If the generated plan contains a dev-only path, flag it for review instead of applying it.

The paper-facing surface a writing repo should contain is documented in `.agents/ANATOMY.md` and `.agents/template-inheritance.json`.

## Safety boundary

- Never merge unrelated template and downstream histories to perform adoption.
- Never apply on a default branch or with a dirty worktree.
- Never mechanically overwrite or move scientific prose, results, references, figures, tables, macros, venue/style files, build scripts, CI workflows, Human contracts, or project-specific Agent knowledge.
- Never infer or invent contributions, claims, evidence, authorship, venue selection, experiment interpretation, release approval, or publication success.
- Never delete downstream-only files solely because the template does not contain them.
- Never finalize a baseline before the manual mapping set has been reviewed and the downstream repository has been validated.
- Never infer completed adoption from a non-null or target-equal baseline; require explicit reviewed adoption state produced from current full verification.
- Never fabricate GitHub Template provenance or an initialization marker for an
  unrelated adopted repository.
- Never treat a successful template harness as proof that external submission systems or project-specific workflows succeeded.

## Handoff

Report:

- downstream starting head and adoption branch;
- template URL, ref, and exact target commit;
- inferred mappings with confidence and important alternatives;
- safe paths staged;
- manual and conflict paths reviewed;
- wrappers, moves, redirects, or obsolete surfaces introduced or removed;
- scientific, experimental, publication, build, CI, and Agent meaning preserved or changed;
- validation commands and exact-head CI evidence;
- the first recorded template baseline;
- unresolved Human decisions or external validation.
