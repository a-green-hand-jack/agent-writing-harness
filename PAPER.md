# Paper Contract

This file is the short, Human-readable source of truth for what the paper is trying to be.
Keep it useful during discussion and revision; do not turn it into a complete research ledger.

The control words below are collaboration cues, not a rigid permission system:

- **locked** — an Agent may analyze or propose a change, but must not silently change the meaning.
- **bounded** — an Agent may adjust the item inside the written boundary.
- **free** — an Agent may handle the implementation or wording while respecting higher-level decisions.
- **unresolved** — Human and Agent have not settled the matter; proceed flexibly, keep uncertainty visible, and ask before making a high-impact or hard-to-reverse choice.

## Paper identity

- Working title: TODO Paper Title
- Target venue: unresolved (verify current official rules before submission work)
- Paper type: unresolved
- Intended readers: TODO
- One-sentence positioning: TODO

## What readers should believe

### Central thesis — unresolved

TODO: state the single most important conclusion the paper wants readers to accept.

### Contributions

No contributions have been approved yet. Add one entry per contribution that
the current paper can defend; there is no required number of contributions.

For each contribution, record whether it is central, supporting, or optional and whether it may be weakened or removed if the evidence changes.

## What must not change silently

Use this section only for high-impact commitments. Examples include:

- the scientific identity of the central claim;
- the primary comparison or fairness condition;
- the main narrative arc;
- a limitation or negative result required for an honest conclusion;
- the meaning of a stable paper interface such as `\MainAccuracy`.

Current locked items:

- TODO

## What may evolve

Record bounded areas where an Agent may keep working without repeatedly asking for approval.
Write the boundary in concrete language rather than “adjust as appropriate.”

- Introduction examples and paragraph boundaries: free unless they change the main framing.
- Local sentence wording: free unless it changes claim strength or scientific meaning.
- TODO

## Unresolved

This is a working queue, not a failure list. Keep candidates and uncertainty explicit.
An Agent should prefer low-risk, reversible progress and bring high-impact choices to the Human with a concise decision packet.

- TODO: title candidates
- TODO: central thesis
- TODO: target audience and venue fit

## Story and structure

### Narrative arc — unresolved

TODO: describe the preferred progression, for example problem → gap → insight → method → evidence.

### Section responsibilities

| Section | Reader task | Must preserve | Flexible elements |
|---|---|---|---|
| Abstract | TODO | TODO | wording and compression |
| Introduction | TODO | TODO | examples and paragraph boundaries |
| Related work | TODO | TODO | grouping and ordering |
| Method | TODO | TODO | local explanation order |
| Experiments | TODO | TODO | presentation order within the approved questions |
| Conclusion | TODO | TODO | compression and emphasis within approved claims |

## Writing style

Describe concrete choices, not only adjectives such as “clear” or “professional.”
Include a few positive and negative patterns that an Agent can apply consistently.

### Current style — unresolved

- Positioning and voice: TODO
- Explanation density: TODO
- Claim-strength discipline: TODO
- Preferred paragraph moves: TODO
- Terms or expressions to avoid: TODO
- Venue-specific overlay: TODO; load only when the target venue is active and current rules have been verified.

## Human decisions required

The Human retains final responsibility for:

- central contributions and claims;
- whether a claim may degrade, be removed, or require more experiments;
- the main story and paper positioning;
- primary metrics, baselines, evaluation fairness, and result interpretation;
- changes to the meaning of stable paper interfaces;
- final release approval.

Agents should retrieve the relevant context, affected sections, alternatives, and risks before asking the Human to decide.
