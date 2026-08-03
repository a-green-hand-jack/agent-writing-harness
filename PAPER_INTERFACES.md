# Paper Interfaces

Paper interfaces are stable paper-facing names whose meaning must not drift silently. The interface is the shared meaning, not merely the LaTeX macro.

## Why interfaces exist

A stable interface helps Human and Agent coordinate when:

- the same title, author identity, result, term, or symbol appears in several surfaces;
- a value changes while its scientific meaning is intended to remain stable;
- a term is renamed and every old consumer must be found;
- presentation differs by publication variant without changing canonical meaning;
- metric, split, aggregation, uncertainty, or artifact responsibility might be confused.

Interfaces are not an automatic data-import system. Human and Agent may need to inspect results, discuss meaning, choose a representation, and update every consumer.

## Keep the implementation light

The default implementation is `paper/macros.tex` plus clear comments. Do not add a schema, generator, or versioning framework until a repeated real cost justifies it.

## Current minimal interface catalogue

- `\PaperTODO{...}` — explicit Draft-only placeholder; Release rejects active uses.
- `\PaperTitle{}` — canonical title shared by all variants.
- `\PaperAuthors{}` — canonical visible author line; anonymous variants hide it rather than redefine it.
- `\MethodName{}` — approved method or system name.
- `\CoreTerm{}` — preferred recurring term for the central concept.
- `\StateSymbol{}` — stable notation used by the method explanation.
- `\MainResult{}` — main result under the approved primary protocol.
- `\MainResultUncertainty{}` — uncertainty paired with `\MainResult` under the same protocol.

Each definition records meaning, practical control boundary, and Human-review trigger. Active paper and variant surfaces consume these names so they cannot silently become dead definitions.

An unresolved value is expressed with `\PaperTODO`; do not replace it with a plausible-looking invented value. Reviewed generated numeric macros may extend or override the result surface through `paper/generated/results-macros.tex`.

## What deserves an interface

Create one when:

- several paper or publication surfaces consume the same concept;
- a change could create cross-section or cross-variant drift;
- the meaning needs explicit Human awareness;
- the item should remain stable through revision or venue adaptation;
- a future change should trigger impact review.

Do not interface every local sentence, number, or formatting choice.

## Interface categories

### Identity and terminology

The initial surface uses `\PaperTitle`, `\PaperAuthors`, `\MethodName`, and `\CoreTerm`. Publication variants may hide identity but must not silently redefine it.

### Notation

The initial surface uses `\StateSymbol`.

### Results

The initial surface uses `\MainResult` and `\MainResultUncertainty`, together with their metric, conditions, aggregation, uncertainty type, unit, and display meaning.

### Claims and wording

Stable names for central claims or approved short/long forms when several surfaces depend on them.

### Artifacts

Figures, tables, or algorithms with a stable responsibility in the story, beyond a file path.

## Flexible control

Use the collaboration cues from `PAPER.md`:

- **locked** — do not change meaning silently;
- **bounded** — maintain inside the written boundary;
- **free** — implementation details may be handled autonomously;
- **unresolved** — keep uncertainty visible and choose the next step based on risk and reversibility.

Different parts of one interface may have different freedom. Meaning may be locked, value bounded, and LaTeX implementation free. A concise comment is usually enough.

## Change workflow

When an interface changes, the Agent should:

1. distinguish presentation changes from meaning changes;
2. retrieve every consumer across canonical and variant surfaces;
3. explain effects on claims, experiments, tables, captions, conclusions, and publication versions;
4. request Human review for high-impact meaning changes;
5. update the interface and all consumers consistently;
6. report unresolved or stale uses.

The Human decides scientific meaning, important result interpretation, identity, and whether a claim may strengthen, weaken, or disappear. The Agent handles retrieval, impact analysis, consistency, and low-risk implementation.

## Draft and release

Drafts may contain explicit `\PaperTODO` interfaces. Before release, required interfaces must have Human-understood meaning, no active placeholder, consistent consumers, and no silent semantic or cross-variant drift.

```bash
python3 .agents/tools/check-paper-interfaces.py
python3 .agents/tools/check-paper-contracts.py --profile release
```

## Future work

Dedicated code-repository imports and structured interface revision tooling remain deferred. Add them only after the lightweight interface reveals a concrete recurring problem.
