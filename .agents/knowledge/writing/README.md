# Project Writing DNA

This directory governs how the bundled `writing-dna-skill` may be adapted to
ARIS. It is downstream-local project knowledge protected from template-sync
overwrite.

## Workflow

1. **Corpus.** The Human selects reference papers. Source PDFs stay outside Git
   or under ignored `.agents/runtime/writing-dna/`; never commit paper full
   texts.
2. **Distill.** Load `.agents/skills/writing-dna-skill/SKILL.md`. Optionally use
   `.agents/skills/ccf-paper-to-exemplar/SKILL.md` for section-level exemplar
   cards.
3. **Candidate.** Write candidate rules under ignored
   `.agents/runtime/writing-dna/`, not into durable project truth.
4. **Human review.** The Human approves or rejects the candidate through the
   style-alignment boundary. Only an approved result may be promoted to
   `paper-writing-dna.md` here.
5. **Activation.** The Writing DNA remains inactive until the Human records its
   activation in `PAPER.md`. Until then it is reference material.

## Academic adaptation

For papers, distill only:

- rhetorical and paragraph moves;
- section-level responsibility patterns;
- sentence density, voice, hedging, and transition preferences;
- citation weaving and evidence-presentation patterns;
- caption and figure/table narrative conventions;
- anti-patterns to avoid.

Do not inherit viewpoints, claims, terminology, citation choices, technical
content, or a named author's personal identity. ARIS project contracts and
evidence ledgers always take precedence.

## Output contract

A promoted `paper-writing-dna.md` must state the corpus identity, what it may
influence, what it must never change, and its activation status. Keep it concise
and rule-shaped rather than a prose essay.
