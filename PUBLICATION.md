# Publication Contract

This file records which publication variants exist, what each variant is for, and which differences are allowed. Variants are overlays on one canonical paper; they are not independent copies.

## Canonical paper

`paper/` is the only authored source. Claims, experiment interpretation, interface meaning, and canonical section prose must not diverge by variant unless the Human explicitly approves a scientific revision in the canonical paper.

## Active variants

| Variant | Purpose | Authors | Acknowledgements | Full appendix | Current status |
|---|---|---:|---:|---:|---|
| `draft` | Daily writing and review | visible | hidden | included | current |
| `anonymous` | Anonymous venue submission | hidden | hidden | included | planned |
| `camera-ready` | Accepted venue version | visible | included | included | planned |
| `arxiv` | Public archival version | visible | included | included | planned |

## Allowed differences

Variants may change only publication-facing presentation:

- author visibility;
- acknowledgements;
- appendix inclusion;
- variant label and later venue-specific presentation hooks;
- package and delivery target, which is handled by release instances rather than the variant source.

## Must not diverge silently

- central claims and contribution identity;
- result and uncertainty meaning;
- experiment interpretation and fairness conditions;
- stable terminology and notation;
- limitations or negative evidence that constrain a core claim;
- canonical section content.

A required scientific difference must first be discussed and applied to the canonical paper or recorded as an explicit Human-approved exception.

## Human review triggers

Human review is required before:

- adding or removing an active variant;
- changing whether identities, acknowledgements, or appendix material appear;
- introducing variant-specific scientific prose;
- publishing a variant as an immutable release instance;
- accepting a difference between two published versions.

## Build interface

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

The default variant is `draft`. Unknown variants must fail rather than silently fall back.

## Release instances

A variant describes how the canonical paper is presented. A release instance records a specific immutable publication such as `iclr2027-submission-r1` or `arxiv-v2`, together with its source revision, artifacts, checks, and Human approval. Release-instance storage is handled by the dedicated release workflow.
