# Paper Interfaces

Paper interfaces are stable, paper-facing names for concepts that appear in several places and whose meaning must not drift silently.

Examples include:

```tex
\MethodName{}
\PrimaryMetric{}
\MainAccuracy{}
\MainAccuracyStd{}
```

The interface is the shared meaning, not merely the LaTeX macro. A macro is one convenient implementation consumed by the abstract, body, tables, captions, appendix, and rebuttal.

## Why interfaces exist

A stable interface helps Human and Agent coordinate when:

- the same result or term appears in several sections;
- a value changes but its scientific meaning is intended to remain stable;
- a term is renamed and old wording must be found;
- rounding or presentation changes across a table and prose;
- a result's metric, split, aggregation, or uncertainty might be confused;
- a figure or table is replaced but must keep the same narrative responsibility.

Interfaces are not an automatic data-import system. Human and Agent may need to inspect experiments, discuss meaning, choose a result, decide display precision, and then update the interface and all of its consumers.

## Keep the implementation light

The default implementation remains `paper/macros.tex` plus clear comments. Do not add a schema, generator, or versioning framework until a repeated real cost justifies it.

A useful interface definition looks like:

```tex
% Interface: MainAccuracy
% Meaning: mean test accuracy under the primary approved protocol.
% Control: bounded — the value may change when approved runs change;
%          metric, split, aggregation, or checkpoint selection require Human review.
% Status: unresolved
\newcommand{\MainAccuracy}{\textbf{TODO}}
```

The exact comment format is intentionally informal. What matters is that a Human can understand the meaning and an Agent can retrieve the boundary.

## What deserves an interface

Create one when at least one of the following is true:

- several paper surfaces consume the same concept;
- a change could create cross-section drift;
- the meaning needs explicit Human awareness;
- the item should remain stable through revision or venue adaptation;
- a future change should trigger an impact review.

Do not interface every local sentence, number, or formatting choice.

## Interface categories

### Identity and terminology

Method names, component names, dataset abbreviations, and important recurring terms.

### Notation

Symbols whose meaning must stay consistent across sections and equations.

### Results

Paper-facing values together with their metric, conditions, aggregation, uncertainty, unit, and display meaning.

### Claims and wording

Stable names for central claims or approved short/long forms when several surfaces depend on them.

### Artifacts

Figures, tables, or algorithms that have a stable responsibility in the story, beyond a file path.

## Flexible control

Use the collaboration cues from `PAPER.md`:

- **locked** — do not change meaning silently;
- **bounded** — maintain inside the written boundary;
- **free** — implementation details may be handled autonomously;
- **unresolved** — keep uncertainty visible and choose the next step based on risk and reversibility.

Different parts of the same interface can have different practical freedom. For example, the meaning may be locked, the value bounded, and the LaTeX implementation free. This does not require a machine-readable matrix; a concise comment is usually enough.

## Change workflow

When an interface changes, the Agent should:

1. determine whether only wording/presentation changed or the meaning changed;
2. retrieve every consumer in active paper surfaces;
3. explain the effect on claims, experiments, tables, captions, and conclusions;
4. request Human review for high-impact meaning changes;
5. update the interface and all consumers consistently;
6. report unresolved or stale uses.

The Human decides scientific meaning, important result interpretation, and whether a claim may strengthen, weaken, or disappear. The Agent handles retrieval, impact analysis, consistency maintenance, and low-risk implementation work.

## Draft and release

Drafts may contain explicit TODO or unresolved interfaces. They must not look like verified final values.

Before release, required interfaces should have a Human-understood meaning, no active placeholder, consistent consumers, and no silent semantic change. Detailed release policy is tracked separately in #38.

## Future work

Dedicated code-repository imports, structured provenance, interface revisions, and compatibility tooling are intentionally deferred. Add them only after the simple Human-readable interface has been used enough to reveal a concrete recurring problem.