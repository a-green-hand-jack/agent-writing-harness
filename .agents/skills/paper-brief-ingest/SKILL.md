---
name: paper-brief-ingest
description: Own the brief-to-contracts transition that starts an autonomous or collaborative paper session from a Human-provided paper brief (BRIEF.md in a brief repo). Use when the Human supplies a brief repo with paper content and template-usage instructions and a coding agent must bootstrap an initialized writing repo from the ccfa-writing-paper-template and fill its contracts. Do not use for ordinary drafting or for writing content into the upstream template repo.
---

# Paper Brief Ingest Skill

Own the transition from a Human-provided **brief repo** to an initialized
**writing repo** whose contracts are filled. This is the entry point for both
autonomous (agent-only, long-running) and collaborative paper sessions.

The brief-driven start task has exactly one owner: this skill. Repository
creation inside that task follows the `ccf-project-scaffolder` template-create
procedure as a subordinate step; that procedure keeps its own owner authority
for the standalone "create a writing repo" task and is not a second owner of
the brief-driven task.

## Trigger

- The Human supplies a brief repo (or path) containing `BRIEF.md` with the paper
  content spec and instructions for using this template.
- A coding agent must create and initialize a writing repo from the
  `ccfa-writing-paper-template` GitHub Template and fill its Human-facing
  contracts from the brief.
- The Human asks to start an autonomous or brief-driven paper session.

## Minimum context

- `BRIEF.md` in the supplied brief repo (or path) and any linked materials.
- Repository role and lifecycle gate from `paper-orientation`.
- Current `PAPER.md` (and `EXPERIMENTS.md`, `PUBLICATION.md` when the brief
  touches experiment or delivery surfaces).

## Procedure

1. Confirm the repository role with the `paper-orientation` lifecycle gate
   (`paper-init.py status`). If the current repo is the upstream template,
   switch to the template-create mode of `ccf-project-scaffolder`; never draft a
   real paper in the template repo.
2. Locate the brief. Accept a `BRIEF.md` file, a brief-repo directory
   containing `BRIEF.md`, or `brief/BRIEF.md`. For a remote brief repo, clone it
   locally first with the normal Git workflow.
3. Validate the brief shape before writing any contract:

   ```bash
   python3 .agents/tools/paper-brief.py validate --brief <path>
   ```

4. In the initialized writing repo, ingest the brief into `PAPER.md`:

   ```bash
   python3 .agents/tools/paper-brief.py ingest --brief <path> [--commit]
   ```

   The tool copies the brief to the writing-repo root `BRIEF.md` and fills only
   decided `PAPER.md` fields (identity, thesis, contributions, operating mode,
   locked and evolving areas, unresolved queue, style). Missing or empty brief
   fields stay `unresolved`. The brief's evidence, delivery, author,
   constraints, and first-deliverable sections remain authoritative in
   `BRIEF.md` until their owner workflows update `EXPERIMENTS.md`,
   `PUBLICATION.md`, and the other contracts.
5. Confirm the declared operating mode in `PAPER.md` (`collaborative` or
   `autonomous`) and the approval boundary. Never widen the boundary silently.
6. Run the downstream verification and daily draft build:

   ```bash
   bash .agents/tools/verify.sh
   make pdf
   ```

7. Hand off:
   - collaborative mode → ordinary `section-writing` on Human request;
   - autonomous mode → proceed through drafting, self-review, polish, and
     variant and checkpoint builds on your own; prepare idea shaping and
     evidence analysis as proposals only; stop for Human approval before
     changing a locked item, approving a release, or final submission.

## Contract declaration

<!-- paper-skill-contract: F7-PBI-001-v1 -->
When the brief leaves a field empty or `TODO`, keep the corresponding contract
item `unresolved` instead of inventing a value, and report it as left open.

## Boundaries

- Never invent a title, claim, result, citation, venue, author, approval, or
  release state from a missing brief field.
- Never write a real paper into the upstream template repo.
- Do not degrade an accepted brief's decided fields to `unresolved`.
- `BRIEF.md` is Human-authored input and stays `unresolved`-honest; the Agent
  does not silently change brief meaning during ingestion.
