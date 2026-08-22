# Section-Specific Scientific Writing

Use this document while drafting or revising one paper section. Load only the
guidance for the active surface. This is not a manuscript review checklist, and
it does not replace the current decisions in `PAPER.md`, `EXPERIMENTS.md`, or
`PAPER_INTERFACES.md`.

This guidance incorporates and adapts Michael J. Black, “Writing a good
scientific paper” (8 November 2024), as its primary source, together with
general scientific-writing practice:

https://perceiving-systems.blog/post/writing-a-good-scientific-paper

The Human has confirmed that the project may reuse the article, including its
templates and distinctive guidance. Attribution is retained so Agents can
inspect the complete source and its examples. Its suggestions remain
heuristics rather than universal rules: paper type, evidence, audience, venue,
and current Human decisions determine which pattern is appropriate.

## Core writing model

Write one paper around one memorable scientific story. Subproblems may support
that story, but two independent headline ideas usually compete for the reader's
attention.

Use **Goal, Problem, Solution** as the default narrative rhythm:

1. Establish a goal that the audience cares about.
2. Identify the concrete obstacle that prevents existing approaches from
   reaching it.
3. Present the insight that changes what is possible.
4. Explain the resulting solution.
5. Repeat the problem-solution rhythm for the next genuine obstacle when the
   method or argument has multiple layers.

The **nugget** is the key insight that makes a previously difficult or
apparently unsolvable problem tractable. It is not the implementation or the
technical contribution list. State how the nugget changes the way the problem
is understood, then derive the technical contribution from it.

Before outlining the paper, explain the work as a talk or to a colleague. The
order needed to teach the idea with little text is a strong candidate for the
paper's order. Record what the listener needs to know and where they ask
questions. Do not preserve the chronological order in which the research was
performed when a clearer explanatory order exists.

## Before a section

Before writing prose, identify:

- the goal and why the intended audience should care;
- the audience and who might use or build on the work;
- a testable hypothesis, even if the literal sentence does not appear in the
  paper;
- the impediment that has prevented the goal from being achieved;
- the nugget or key insight that makes progress possible;
- a three-sentence elevator pitch;
- the teaser image that would explain the core idea visually;
- the strongest relevant prior work and its actual limitations;
- the quantitative evaluation, simple baseline, and qualitative demo;
- the principal risks and whether the required data are available;
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

- Treat the title as the abstract compressed into one memorable line.
- Name the actual topic and distinguishing insight or contribution.
- Prefer specific, searchable terms over clever but opaque phrasing.
- Keep scope and comparative language within the strongest supported claim.
- Make the title, abstract, and conclusion describe the same paper.
- A qualified “Towards” title can honestly signal preliminary progress; an “On”
  title can fit a paper centered on an insight, foundation, or unification.
- Do not distort the title merely to include an acronym.

## Method name or acronym

- Prefer a short, pronounceable, distinctive name that helps readers remember,
  search for, refer to, and cite the work.
- An acronym should be approximately invertible: its expansion should remind a
  reader of the name, and the name should reinforce the method's idea.
- Avoid generic names that are difficult to search or imply ownership of an
  entire problem area.
- A clear scientific title is more important than fitting the acronym into it.

## Abstract

- Establish the problem and why it matters to the intended reader.
- State the concrete limitation or unresolved need addressed by the paper.
- Present the key insight before implementation detail when possible.
- Summarize the approach, strongest supported evidence, and bounded takeaway.
- Use only claims, numbers, conditions, and terminology that agree with the body.
- Omit background, procedural detail, and contribution lists that do not help a
  reader understand the central story under the abstract budget.

When useful, adapt Black's Goal-Problem-Solution scaffold rather than treating
it as text that must be filled mechanically:

> [Topic] is widely used in [field] and matters for [applications or users].
> Recent work addresses this problem through [dominant approach].
> Unfortunately, these approaches [specific limitation].
> In contrast, we [nugget or different way of seeing the problem].
> This addresses [obstacle]; however, [remaining obstacle] is still unresolved.
> Consequently, we develop [method or component].
> While promising, [new difficulty] is non-trivial.
> Therefore, we [second response, when genuinely needed].
> We evaluate [method] on [data and conditions] and find [bounded result].
> [Artifact availability, only when approved and accurate].

Use equivalent transitions and omit unnecessary moves. The point is the
repeated goal-problem-solution logic, not the words “unfortunately,” “in
contrast,” or “therefore.”

## Teaser

- Treat the teaser as a visual abstract that can communicate the main idea with
  the title and abstract before the reader enters the paper.
- Prefer one of three jobs: summarize compelling results, expose the failure of
  existing approaches and the new response, or give a simple conceptual system
  overview.
- A detailed pipeline is usually weaker on the first page than an immediately
  understandable conceptual cartoon.
- Make the takeaway visible without requiring the body text.

## Introduction

- Move from the reader's problem to the specific obstacle that remains.
- Explain what the audience needs rather than what the authors happen to be
  interested in.
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
- Follow important lines of work far enough back to support any historical or
  first-work claim; recent search results alone do not establish precedence.

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

- Test a credible simple baseline before assuming that a complex method is
  necessary.
- Organize each subsection around a scientific question or approved claim.
- State the protocol and fairness conditions needed to interpret the result.
- Report the observation before proposing an explanation or mechanism.
- Name the comparator, metric, split, aggregation, uncertainty, and exclusions
  when they materially affect the statement.
- Use ablations to isolate a factor where possible; do not attribute a change
  to one factor when several conditions changed together.
- Change one factor at a time when the purpose is causal attribution.
- Treat comparisons as opportunities to learn and teach, not merely to defeat
  competing methods.
- Explain what the result teaches, including negative or inconclusive evidence.
- Do not exceed the maximum interpretation recorded in `EXPERIMENTS.md`.

## Equations

- Write equations early enough for discrepancies to reveal implementation bugs.
- Once results come from a concrete implementation, the paper's equations must
  describe that implementation honestly rather than a cleaner intended method.
- Define every symbol before or at first use and give one symbol one meaning.
- Avoid introducing a dense cluster of symbols without intervening explanation.
- Explain central concepts through complementary prose, mathematics, or figures
  rather than mechanically repeating the same information.
- Keep the mathematical formulation consistent with pseudocode and the actual
  implementation behavior when that behavior is part of the paper's claim.
- Maintain a notation table while writing when the method is symbol-heavy.
- Punctuate displayed equations as parts of sentences.
- Check the rendered paper for overfull equations, unintended paragraph breaks,
  and ambiguous hats, subscripts, indices, and dimensions.

## Figures, tables, and captions

- Design key figures early, using sketches or placeholders when results are not
  ready; this helps expose which experiments the story requires.
- Treat the sequence of figures and captions as a compact paper that should
  communicate the main idea and evidence on its own.
- Give each artifact one clear narrative job and reference it in the body.
- Tell the reader what comparison or pattern to inspect, not merely where the
  artifact appears.
- Make captions understandable with the necessary labels, units, conditions,
  abbreviations, and scoped takeaway.
- Keep values, terminology, visual positions, and interpretations consistent
  across the artifact, caption, body, and stable interfaces.
- Prefer a simpler artifact when additional panels or columns tell unrelated
  stories or obscure the main comparison.
- Make labels legible at normal page scale, label axes and units, and use color
  to encode information rather than decoration alone.
- Point to important visual details with annotations when they are obvious to
  the author but easy for a reader to miss.

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

- Use fewer words: remove filler, tighten the argument, and prefer the shortest
  explanation that preserves necessary meaning and qualification.
- Write an early rough draft to establish logical structure before polishing
  grammar. Good papers emerge through repeated rewriting.
- Explain a central concept through text, an equation, and a figure when those
  three views provide complementary intuition and precision.
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
- Prefer direct claims about what was done over hesitant constructions such as
  “we aim to,” “can be,” or “allows to” when the action actually occurred.
- Distinguish author actions from method behavior: the method optimizes or
  predicts; the authors design, evaluate, or observe.
- Keep tense, capitalization, citation style, and compound-adjective
  hyphenation consistent. Present tense is often effective for methods and
  enduring prior work, while historical data collection may require past tense.
- Avoid unsupported absolutes such as “unique” or “paramount” and vague verbs
  such as “provides,” “enables,” or “allows” when a mechanism can be named.
- Do not write a section roadmap unless a genuinely complicated method needs a
  brief overview to reduce reader effort.
- Do not apply mechanical bans on particular words or sentence forms. Revise a
  construction when it is unclear, repetitive, misleading, or inconsistent
  with the current paper, not merely because it matches a generic style list.
- Bundled writing-engine guardrails (for example em-dash or filler-pattern
  thresholds in `ccf-paper-writer`'s prose-quality-guardrails) are diagnostic
  signals, not automatic bans: a pattern flagged by a threshold may still be
  right when it carries evidence-bounded meaning; resolve conflicts in favor
  of clarity and scientific meaning.

## Final pass

- Start writing early enough for multiple complete proofreading passes by more
  than one person. A deadline-day draft cannot receive the same level of
  structural and technical scrutiny.
- Read every word, including the title, captions, equations, footnotes,
  appendix references, and bibliography.
- Read once as if encountering the topic for the first time: expand unknown
  acronyms, question unstated assumptions, and verify that each inference is
  available to the reader rather than only to the authors.
- Search the rendered PDF for unresolved references such as `?`, inspect margin
  overflow and tiny figure text, and confirm that each artifact is cited.
- Proofread bibliography metadata, cite the definitive version when known, and
  check for missing foundational and current work through the repository's
  reference-repair process.
- When reducing page count, first tighten paragraphs that end with one or two
  words, remove repetition, simplify artifacts, and improve equation layout.
  Do not hide overflow with indiscriminate negative spacing.

## Supplement and video

- Deliver everything promised by the main text and mention the supplement or
  video where venue rules permit.
- Keep supplemental material polished, concise, consistent with the canonical
  paper, and within the venue's rules for additional experiments.
- Include useful secondary evidence, representative examples, and failure cases
  rather than only favorable results.
- Use video as a distinct teaching medium, not a filmed copy of the paper.
  Script it, narrate it, exploit time and motion, and test playback on multiple
  systems.

## Drafting boundary

During drafting, perform the local checks needed to make the active section
coherent with its inputs and immediate neighbors. Do not interrupt drafting
with a manuscript-wide reviewer pass or produce a reviewer report. A separate
consistency review begins only after the Human identifies a version as ready
for review.
