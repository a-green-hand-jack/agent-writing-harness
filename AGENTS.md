# Agent Entry

The paper project is primary. Begin with the current Human-facing contract and load only the context needed for the active task.

## Orientation

1. Read `PAPER.md`.
2. Read `EXPERIMENTS.md` only when the task touches experiments, evidence, claim support, or result interpretation.
3. Read `PAPER_INTERFACES.md` only when the task changes recurring terminology, notation, results, claims, figures, tables, or macros.
4. Read the relevant current decisions in `DECISIONS.md`.
5. Read `.agents/skills/paper-orientation/SKILL.md` when starting a new session or when context is unclear.
6. Load one task-specific skill or knowledge document. Do not load every policy, venue, ledger, and historical file by default.

Legacy `state/`, `lab/`, `.agent/`, `.claude/`, adapter, and validator surfaces remain available during the migration. Consult them only when the current task or a declared check requires them.

## Task routing

Load one focused skill when its trigger applies:

- high-impact meaning or permission boundary → `.agents/skills/control-review/SKILL.md`;
- a focused Human choice is needed → `.agents/skills/decision-packet/SKILL.md`;
- paper positioning, structure, or prose style → `.agents/skills/style-alignment/SKILL.md`;
- recurring term, notation, result, artifact, or macro → `.agents/skills/paper-interface-maintenance/SKILL.md`;
- submission or release candidate → `.agents/skills/release-review/SKILL.md`.

Do not load all five for ordinary local edits.

## Collaboration boundary

The control words are flexible cues, not a rigid permission engine:

- **locked** — analyze or propose, but do not silently change the meaning;
- **bounded** — adjust inside the written boundary;
- **free** — handle the implementation or wording while respecting higher-level decisions;
- **unresolved** — keep uncertainty visible, prefer reversible progress, and ask before a high-impact or hard-to-reverse choice.

The Human decides central claims, whether a claim may degrade, the main story, experiment fairness, important result interpretation, stable interface meaning, and final release approval.

The Agent should do the retrieval work: find relevant contracts and prior decisions, identify affected sections and interfaces, compare alternatives, explain risks, and ask one focused question when a Human decision is needed.

## Strong rules

- Do not invent contributions, facts, results, citations, or Human approval.
- Do not promote expected or unresolved results into verified evidence.
- Do not turn correlation into causal language without appropriate support.
- Do not silently strengthen, weaken, replace, or remove a locked claim, story decision, experiment condition, limitation, or interface meaning.
- Keep negative or inconclusive evidence visible when it constrains a central claim.
- Report missing tools or unverified environments honestly; never false-pass.
- Do not expose `state/`, `lab/`, `memory/`, `.agent/`, `.claude/`, `.agents/`, `.git/`, `.github/`, or `human/` in release surfaces.
- Do not put symlinks in release surfaces; release exports must be reconstructible from their manifest.

## Handoff

Report the files changed, any scientific or narrative meaning affected, decisions made or still unresolved, impacted paper interfaces or experiment contracts, and the focused validation performed.
