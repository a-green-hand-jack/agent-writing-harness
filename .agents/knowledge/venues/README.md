# Venue Knowledge

This directory stores one Markdown file per active target venue: `<venue>-<year>.md`.

## When to load

Load venue knowledge only when the task needs venue planning:

- deadline scheduling or internal milestone planning;
- page-budget, anonymous, supplementary, or required-section decisions;
- variant planning for anonymous, rebuttal, camera-ready, or release;
- strict release review before an immutable submission.

Ordinary writing and experiment sessions must not load venue knowledge just in case.

## How to fill it

1. Copy `_template.md` to `<venue>-<year>.md` for the active target.
2. Fill every field from the current official venue source.
3. Set `last_checked` to the date of the most recent verification.
4. Leave unavailable facts as `UNKNOWN`; do not turn missing official facts into assumptions.
5. Run the checker:

```bash
python3 .agents/tools/check-venue-knowledge.py
```

Before deadline-sensitive planning or strict release, recheck the official source, update `last_checked`, and run:

```bash
python3 .agents/tools/check-venue-knowledge.py --strict
```

## Rules

- Dynamic facts must come from official sources; local compilation success does not prove venue acceptance.
- Official deadlines are hard constraints for Agent scheduling. Internal milestones are derived buffers, not official deadlines.
- If official facts conflict with a Human contract, report the conflict explicitly; do not silently override the Human contract.
- `UNKNOWN` remains visible as `UNKNOWN`; the checker reports `UNVERIFIED` rather than treating it as a pass.
- Template files are venue-agnostic. A concrete `<venue>-<year>.md` file is downstream paper fact, not template default fact.
