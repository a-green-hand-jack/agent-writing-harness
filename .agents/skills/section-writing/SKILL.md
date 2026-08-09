---
name: section-writing
description: Use when drafting or substantially revising a specific paper section from the current paper contracts and available evidence.
---

# Section Writing

## Trigger

Use when drafting or substantially revising a title, abstract, introduction,
related-work section, method, experiment section, limitation section,
conclusion, appendix, caption, or other named paper section.

Do not use this skill for a manuscript-wide review after a version is complete.

## Minimum context

- the paper identity, thesis, contributions, story, section responsibility, and
  writing choices relevant to the active section in `PAPER.md`;
- the active section and only the neighboring text needed for continuity;
- the matching surface in `.agents/knowledge/scientific-writing.md`;
- `EXPERIMENTS.md` only for experiment, result, evidence, or interpretation text;
- `PAPER_INTERFACES.md` only for recurring terminology, notation, claims,
  results, figures, tables, or macros;
- `REFERENCES.md` and relevant ledger records only when citations or external
  claim support are involved.

Do not load the complete manuscript, all references, release tooling, or venue
knowledge unless the active section actually requires them.

## Procedure

1. Identify the active section and its reader task from `PAPER.md`.
2. State the one point the reader should retain and the inputs that support it.
3. Select only the applicable section guidance and rhetorical moves from
   `.agents/knowledge/scientific-writing.md`.
4. Separate scientific content from presentation. Preserve locked and bounded
   meaning while handling free wording directly.
<!-- paper-skill-contract: F7-SW-001-v1 -->
5. If the prompt introduces, fabricates, removes, or materially changes a
   citation or claim-support request, inspect `REFERENCES.md` and the relevant
   records in `references/ledger.json` before drafting; do not invent support.
6. Draft from available claims, evidence, results, interfaces, and references.
   Keep missing material visible rather than filling it plausibly.
7. Check the active section locally for defined terms, claim strength,
   citation placement, figure/table references, and continuity with immediate
   neighbors.
8. Report any unresolved input or proposed wording that would change a claim,
   experiment interpretation, consequential limitation, or interface meaning.

## Drafting boundary

Do not invoke a reviewer persona, launch parallel reviewer passes, audit the
complete manuscript, or emit a manuscript review report while drafting. A
local coherence check is part of writing; a version-level consistency review
is a separate Human-requested task.

## Human decision

The Human decides the central story, contribution and claim identity, important
result interpretation, and any section responsibility that changes what the
paper promises. The Agent may draft and revise inside the current boundary.
