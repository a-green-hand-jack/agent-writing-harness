# Section-Specific Scientific Writing

Use this document while drafting or revising one paper section. Load only the
guidance for the active surface. This is not a manuscript review checklist, and
it does not replace the current decisions in `PAPER.md`, `EXPERIMENTS.md`, or
`PAPER_INTERFACES.md`.

The guidance independently paraphrases ideas from Michael J. Black, “Writing a
good scientific paper” (8 November 2024), together with general scientific
writing practice:

https://perceiving-systems.blog/post/writing-a-good-scientific-paper

The source article is copyrighted and is not reproduced here. Its suggestions
are heuristics rather than universal rules. Paper type, evidence, audience, and
current Human decisions determine which pattern is appropriate.

## Before a section

Before writing prose, identify:

- the reader task assigned to the section in `PAPER.md`;
- the one point the reader should retain from the section;
- the claims, evidence, definitions, figures, tables, and citations available;
- what the section must establish before the next section can work;
- unresolved facts or decisions that must remain explicit placeholders.

Prefer a small sequence of rhetorical moves over a sentence-by-sentence plan.
A useful default is goal or question, obstacle or gap, response, evidence, and
implication. Use only the moves the section needs; do not force every section
into the same shape.

## Title

- Name the actual topic and distinguishing insight or contribution.
- Prefer specific, searchable terms over clever but opaque phrasing.
- Keep scope and comparative language within the strongest supported claim.
- Make the title, abstract, and conclusion describe the same paper.

## Abstract

- Establish the problem and why it matters to the intended reader.
- State the concrete limitation or unresolved need addressed by the paper.
- Present the key insight before implementation detail when possible.
- Summarize the approach, strongest supported evidence, and bounded takeaway.
- Use only claims, numbers, conditions, and terminology that agree with the body.
- Omit background, procedural detail, and contribution lists that do not help a
  reader understand the central story under the abstract budget.

## Introduction

- Move from the reader's problem to the specific obstacle that remains.
- Explain why existing approaches do not resolve that obstacle without using a
  strawman or an unsupported novelty claim.
- State the paper's key insight and show how it motivates the approach.
- Preview the evidence that will test the paper's important claims.
- Present contributions as scientific advances or findings, not a table of
  contents or a list of implementation steps.
- Ensure every promise made here is fulfilled later in the paper.

## Related work

- Organize prior work by ideas, assumptions, capabilities, or limitations that
  matter to this paper, rather than by author or publication date.
- Use primary sources and distinguish what each line of work establishes from
  what remains unresolved.
- Compare against the actual scope of prior work; do not manufacture a gap from
  a missing keyword, benchmark, or citation.
- End each group with its relationship to the present paper, while reserving
  the paper's full argument for the introduction and method.
- Keep citation identity and claim-support status consistent with
  `REFERENCES.md` and `references/ledger.json`.

## Method

- State the objective and obstacle before presenting machinery.
- Introduce assumptions, objects, dimensions, and notation before use.
- Pair formal definitions with enough intuition for the intended audience.
- Use notation only when it makes the idea more precise or easier to follow.
- Keep equations, algorithm descriptions, implementation details, and figures
  aligned; state any non-obvious mapping explicitly.
- Explain how each major component addresses the stated obstacle and identify
  conditions that bound the method's claim.

## Experiments and results

- Organize each subsection around a scientific question or approved claim.
- State the protocol and fairness conditions needed to interpret the result.
- Report the observation before proposing an explanation or mechanism.
- Name the comparator, metric, split, aggregation, uncertainty, and exclusions
  when they materially affect the statement.
- Use ablations to isolate a factor where possible; do not attribute a change
  to one factor when several conditions changed together.
- Explain what the result teaches, including negative or inconclusive evidence.
- Do not exceed the maximum interpretation recorded in `EXPERIMENTS.md`.

## Equations

- Define every symbol before or at first use and give one symbol one meaning.
- Avoid introducing a dense cluster of symbols without intervening explanation.
- Explain central concepts through complementary prose, mathematics, or figures
  rather than mechanically repeating the same information.
- Keep the mathematical formulation consistent with pseudocode and the actual
  implementation behavior when that behavior is part of the paper's claim.

## Figures, tables, and captions

- Give each artifact one clear narrative job and reference it in the body.
- Tell the reader what comparison or pattern to inspect, not merely where the
  artifact appears.
- Make captions understandable with the necessary labels, units, conditions,
  abbreviations, and scoped takeaway.
- Keep values, terminology, visual positions, and interpretations consistent
  across the artifact, caption, body, and stable interfaces.
- Prefer a simpler artifact when additional panels or columns tell unrelated
  stories or obscure the main comparison.

## Limitations

- State consequential assumptions, unsupported settings, failure modes, and
  evidence boundaries plainly.
- Connect each limitation to the claim or use case it constrains.
- Distinguish an observed failure from a plausible risk and from future work.
- Do not hide or cosmetically reframe a limitation that is required for an
  honest reading of the central result.

## Conclusion

- Answer the paper's central question using only supported takeaways.
- Reconnect the key insight, approach, evidence, and scope without repeating
  the abstract sentence by sentence.
- Preserve important qualifications and limitations.
- Introduce no new claim, result, citation, experiment, or technical concept.

## Appendix and supplementary material

- Supply derivations, implementation details, secondary analyses, and examples
  that support the main paper.
- Fulfil every promise and cross-reference made by the main text.
- Keep terminology, notation, experimental conditions, and results consistent
  with the canonical sections.
- Do not use supplementary material to repair a missing premise or unsupported
  central claim in the main paper.

## Paragraphs and sentences

- Give each paragraph one main reader task; open with enough context to make
  that task visible and close once it has been completed.
- Make logical relationships explicit when they are not already clear, but do
  not add formulaic transitions merely to connect adjacent paragraphs.
- Separate observed evidence from interpretation, mechanism, and speculation.
- Use confident language for verified observations and calibrated language for
  explanations that the evidence does not establish causally.
- Prefer precise, direct wording; remove filler and repetition without deleting
  qualifications or necessary technical detail.
- Define acronyms and specialized terms for the intended audience, then use
  them consistently.
- Give every comparison an identifiable reference point.
- Do not apply mechanical bans on particular words or sentence forms. Revise a
  construction when it is unclear, repetitive, misleading, or inconsistent
  with the current paper, not merely because it matches a generic style list.

## Drafting boundary

During drafting, perform the local checks needed to make the active section
coherent with its inputs and immediate neighbors. Do not interrupt drafting
with a manuscript-wide reviewer pass or produce a reviewer report. A separate
consistency review begins only after the Human identifies a version as ready
for review.
