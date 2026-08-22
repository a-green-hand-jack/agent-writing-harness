---
name: style-alignment
description: Use when setting or changing paper positioning, narrative architecture, section responsibility, writing policy, or a venue presentation overlay.
---

# Style Alignment

## Trigger

Use when setting or changing paper positioning, narrative architecture, section responsibility, writing policy, or a venue presentation overlay.

Use `section-writing` instead when drafting or revising prose within the current choices.

## Minimum context

- `PAPER.md` writing-style and story sections;
- the active section being revised;
- `.agents/knowledge/writing-style.md`;
- venue knowledge only when venue adaptation is the active task.

Do not load release tooling, all experiment state, or every exemplar by default.

## Procedure

1. Identify the style layer being changed: positioning, narrative, section, paragraph, sentence, or micro-surface.
2. Preserve higher-level Human decisions during lower-level edits.
3. Translate vague adjectives into concrete positive and negative patterns.
4. For an unresolved high-level style choice, offer a small number of meaningfully different candidates and explain effects on claims, evidence, page budget, and readers.
5. Apply the chosen style consistently across the affected surfaces.
6. Report any change that also alters claim strength or scientific interpretation.

## Human decision

The Human chooses paper positioning, central narrative, major venue tradeoffs, and any style change that strengthens, weakens, hides, or reframes a scientific commitment.

## Writing DNA adoption

The bundled `writing-dna-skill` (`.agents/skills/writing-dna-skill/SKILL.md`,
`.agents/vendor/writing-dna-skill/`) distills reusable style from a corpus.
Inside this template it is an academic-writing adapter, governed by
`.agents/knowledge/writing/README.md`:

- the corpus is built by the Human from reference papers, kept outside Git or
  under ignored `.agents/runtime/writing-dna/`;
- distilled candidate rules are reviewed by the Human before any adoption;
- only a Human-approved result may be promoted to
  `.agents/knowledge/writing/paper-writing-dna.md` and activated from
  `PAPER.md`;
- a promoted Writing DNA must not override the current paper contracts, claim
  strength, terminology, or scientific meaning.
