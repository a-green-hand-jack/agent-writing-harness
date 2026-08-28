# Paper Brief

This file is the Human-authored input contract that starts a paper with this
harness. It normally lives in a separate **brief repo** that the Human owns:
that repo holds this `BRIEF.md` (the content specification) plus any supplied
materials and the instructions for using the writing template.

The Agent reads `BRIEF.md`, creates an initialized **writing repo** from the
`a-green-hand-jack/agent-writing-harness` GitHub Template, and ingests the
content here into `PAPER.md` with `paper-brief-ingest`. The brief is then kept
in the writing repo root as provenance and as the material inventory; the
evidence, delivery, author, constraints, and first-deliverable sections remain
authoritative here until their owner workflows update `EXPERIMENTS.md`,
`PUBLICATION.md`, and the other contracts.

Fill only what is actually decided. Anything left empty stays `unresolved` in
the contracts; the Agent must never invent a field. Mark **locked** only the
high-impact commitments that must not change silently.

## Paper identity

- Working title: TODO
- Target venue: unresolved (verify current official rules before submission work)
- Paper type: unresolved
- Intended readers: TODO
- One-sentence positioning: TODO

## What readers should believe

### Central thesis

TODO: the single most important conclusion the paper wants readers to accept.

### Contributions

- TODO: one entry per defensible contribution (central / supporting / optional)

## Operating mode

- Mode: unresolved (`collaborative` or `autonomous`)
- Approval boundary: in autonomous mode the Agent drafts, self-reviews,
  polishes, and builds checkpoints without step-by-step confirmation; it stops
  for Human review before changing a locked item, approving a release, or final
  submission. In collaborative mode the Human stays in the loop for each
  substantive step.

## Evidence and materials

Inventory what the Human supplies; keep it concrete (paths, repositories, URLs,
or `none yet`):

- Code / data / results: TODO
- Figures / tables: TODO
- Prior draft or notes: TODO
- References or bibliography: TODO
- Experiment questions the paper must answer: TODO

## What must not change silently

- TODO: locked claims, comparisons, limitations, or interface meaning

## What may evolve

- TODO: bounded areas where the Agent may work without re-asking

## Target and delivery

- Venue / year / track and deadline: unresolved
- Publication variants needed: unresolved (default: draft, anonymous, camera-ready, arxiv)
- Release authority: Human (approves each release instance and final submission)

## Authors and identity

- Author list: unresolved
- Anonymity / disclosure constraints: unresolved

## Constraints

- Language and length limits: TODO
- Compute / data limits: TODO
- Style examples or Writing DNA corpus: TODO

## First deliverable

- TODO: idea clarification, evidence plan, outline, or a named section draft

## Template usage note

Use the `agent-writing-harness` harness to write this paper. The Agent
creates an initialized writing repo from that GitHub Template, ingests this
brief with `paper-brief-ingest` (or `python3 .agents/tools/paper-brief.py ingest
--brief <path>`), then drafts under the declared operating mode. See
`AGENT_GUIDE.md` in the writing repo for the full workflow.
