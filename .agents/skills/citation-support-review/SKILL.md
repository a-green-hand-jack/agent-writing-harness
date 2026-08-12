---
name: citation-support-review
description: Use when discovering a citation, checking whether a cited work supports manuscript text, retrieving evidence passages, or reviewing citation claim-support at Draft, Review, or Release strength.
---

# Citation Support Review

## Trigger

Use when a manuscript sentence cites or should cite a work and the Agent must
answer whether the evidence supports the text. This includes: a known citation
that needs support checking, an unknown citation need where a candidate source
must be discovered, evidence-passage retrieval, stale-claim detection, and
Draft/Review/Release citation-support gates.

Do not use this skill for identity, metadata, duplicate, or version repair of a
bibliographic record; route those to `reference-repair`.

## Minimum context

- the active manuscript sentence and its citation occurrence from the TeX
  source, with file and line;
- the relevant records in `references/ledger.json`, including the occurrence
  and any existing evidence records;
- `REFERENCES.md` for the durable contract, verdict semantics, and offline gates;
- the current `EXPERIMENTS.md` or `PAPER.md` constraints only when they define
  the claim or interpretation being checked.

Do not load the complete manuscript, all references, or the full ledger for an
ordinary occurrence check. Load `REFERENCES.md` once per session; it is small.

## The three questions

For every substantive citation occurrence, answer exactly three questions and
record the answers separately:

1. **What does the manuscript sentence claim?** Decompose compound factual
   content into atomic claims and record the quantities, units, conditions,
   direction, scope, and claim strength.
2. **What does the cited work actually say?** State the source's own finding
   using verbatim passages and locators. Distinguish the source's own finding
   from its discussion of another work.
3. **Does that evidence support the manuscript claim?** Decide fully supports,
   partially supports, does not support, or contradicts, using the verdict
   definitions below.

## Verdicts

Automated and Agent judgments are provisional. Verdicts are recorded per
(occurrence, citation key) and must remain separate from provider outcomes:

- `supported` — the source passages state the claim as the manuscript makes it,
  including its quantities, conditions, direction, scope, and strength.
- `partially-supported` — some atomic parts are supported and others are
  missing, weaker, or qualified differently.
- `unsupported` — the source does not state the claimed fact, or the source
  discusses the topic without the claimed content.
- `contradicted` — the source states a finding that conflicts with the claim;
  requires verbatim evidence, not a lone model label.
- `source-unavailable` — no retrievable full text or abstract could be checked;
  this is not evidence of fabrication or contradiction.

Provider failures (`rate-limited`, `provider-unavailable`, `paper-not-indexed`,
`full-text-unavailable`, `identity-ambiguous`, `no-relevant-passage`) are
infrastructure/source-availability outcomes, never scientific verdicts.

A real DOI or correct metadata does not prove claim support. Title relevance
and metadata existence alone never justify inserting a citation.

## Profiles

### Draft

Optimize for writing speed. Process only the active claim, retrieve a bounded
passage set (at most three passages by default), perform one support comparison
in the current writing context, run deterministic checks for quantities, units,
names, direction, conditions, and obvious scope mismatch, and record a passing
result as `provisional`. Never launch a reviewer persona or a manuscript-wide
reviewer pass while drafting.

Escalate to Review or Human control when the claim is central, uses causal
wording, claims novelty/precedence or strong superlatives, states exact
numerical results, relies on abstract-only evidence, is partially supported,
contradicted, or source-ambiguous.

### Review

Optimize for confidence. Revisit new, changed, provisional, stale,
`disagreement`, and unresolved occurrences only, grouped by source with
bounded batching. For each occurrence, state the claim meaning, state the
source content from exact verbatim passages, decide the verdict, then run an
independent adversarial pass looking for omitted qualifiers, scope mismatch,
numerical/directional conflict, causal overstatement, counterevidence, an
unnecessary citation, or a better source. Check each cited work independently;
check joint support only when no individual work supports the complete claim.
Mechanically validate every exact excerpt against the retrieved passage before
recording. Produce a Human decision packet when the supportive and adversarial
readings disagree or when the result touches a controlled claim.

### Release

Inventory the complete manuscript. Reuse Human-confirmed evidence only when
the claim fingerprint, citation set, source identity/version, passage hash,
and protocol version are unchanged. Recheck new, stale, provisional,
`disagreement`, unavailable, and unresolved substantive occurrences. Fail
closed on substantive claim support that is not Human-confirmed. Keep provider
and source-availability failures visible without classifying them as
contradiction or fabrication.

## Escalation and Human boundary

The Human decides claim support confirmation, claim weakening/splitting/
replacement, and any change to a central claim, causal wording, limitation, or
contested interpretation. Automated assessment can never write
`human-confirmed`. When a Human decision is required, produce a focused
decision packet containing the claim, source identity/version, exact excerpts
and locators, the supportive result, adversarial findings, disagreement, and a
recommended action (confirm, replace, add, weaken, split, reject, or leave
unresolved).

## Procedure

<!-- paper-skill-contract: F7-CSR-001-v1 -->
1. Identify the exact citation occurrence (file, line, command, keys) and
   extract the surrounding manuscript sentence; run
   `python3 .agents/tools/reference-evidence.py inventory --location FILE:LINE`
   when the occurrence is not yet recorded.
2. Resolve the cited work or discover candidates:
   `reference-evidence.py resolve KEY|DOI|arXiv|URL` for known citations, or
   `reference-evidence.py search "CLAIM" --context ...` for unknown needs.
   Never insert a citation from title relevance or metadata existence alone.
3. Retrieve evidence passages:
   `reference-evidence.py passages KEY --section ... --limit N`.
   Prefer exact Semantic Scholar snippets restricted to the resolved paper,
   then authoritative HTML/XML/source text, then abstract-only evidence, then
   on-demand Agent PDF reading. Provider misses remain visible and are not
   negative scientific evidence.
4. Build the support packet with
   `reference-evidence.py packet OCCURRENCE_ID --key KEY`, fill the claim
   meaning from question 1, and compare the sentence against the passages once
   for Draft or supportively plus adversarially for Review.
5. Record the result with
   `reference-evidence.py record --occurrence-id ... --citation-key ... --verdict ...`
   using the exact passage text, locator, source identity/version, and review
   state. `record` rejects stale packets (claim fingerprint or citation set
   drift) so the Agent must re-inventory before recording.
6. Run the offline gates after changes:
   `python3 .agents/tools/check-reference-integrity.py --profile draft`
   and `python3 .agents/tools/check-reference-integrity.py --profile release`
   for Release. Keep generated packets and caches under ignored `dist/`.

## Adopted methods and limits

These methods inform the checks inside this workflow and are recorded here so
they are not silently re-invented. None is installed, vendored, or required at
runtime, and none replaces the three-question review:

- MiniCheck — atomic-claim decomposition and grounded support checks; limit:
  entailment-style labels need Human confirmation for scientific meaning.
- AttrScore — attributable/extrapolatory/contradictory triage; limit: labels
  are heuristic and cannot approve a central claim.
- citation-guard — verify, re-attribute, and flag citations; limit: upstream
  heuristics accept first results and need field-level identity checks.
- ALCE — citation precision/recall and multi-citation necessity; limit:
  measures coverage, not scientific truth.
- ScholarQABench — citation precision/recall evaluation; limit: benchmark
  aggregates, not per-occurrence meaning.
- Citation Check — per-occurrence inventory and unused-entry warnings; the
  implementation was rejected in `REFERENCES.md` for missing tagged releases,
  locked dependencies, non-generative fail-closed output, and field-level
  matching; only its concepts are retained.
- Ai2 Scholar QA — evidence-passage retrieval and locator discipline; limit:
  retrieval quality varies by index coverage.

## Handoff

Report the changed occurrence/evidence records, the verdicts, staleness
findings, disagreement, impacted claims and interfaces, the decision packet
when applicable, and validation performed (offline gates and focused tests).
