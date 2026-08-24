# Contributing

## Template development workflow

The template is developed on `template-dev` and released to `main`. This is a binding workflow principle, not a suggestion:

1. **Develop on `template-dev`.** This branch contains the complete development surface: paper-facing infrastructure plus template-development-only machinery (`.agents/evals/`, `check-vendored-skills.py`, `check-vendored-skill-evals.py`, `check-skills.py`, `check-actions.py`, `.agents/dependencies/vendored-skills/`, and development-only tests). Run `bash .agents/tools/verify.sh` there, including the vendored-skill and evaluation checks, before releasing anything.
2. **`main` is the release surface only.** It contains only paper-facing infrastructure and is the GitHub default branch, so GitHub Template creation copies exactly what a writing repo needs. Never commit template-development-only machinery to `main`.
3. **Release paper-facing changes to `main`.** After development-surface validation on `template-dev`, move only the paper-facing changes to `main` (merge or cherry-pick the paper-facing commits), through the PR merge contract below. A writing repo must never receive the development surface.
4. **Keep the surface split documented.** When the split changes, update `AGENT_GUIDE.md`, `.agents/ANATOMY.md`, `.agents/template-inheritance.json`, `README.md`, and this file together.

## Pull request merge contract

A pull request is not ready merely because GitHub reports it as mergeable.

Before merge:

1. wait for both the `PR validation` and `Reference validation` workflows to finish;
2. require every applicable job to succeed:
   - `harness` — paper-first checks and Agent regressions;
   - `references` (in `Reference validation`) — offline ledger enforcement plus locked correction-candidate and non-generative metadata audits when the protected policy enables them;
   - `latex (<variant>)` — real TeX builds and variant-surface checks;
   - `paper-only` — all variants compile with only `paper/` present;
   - `release-package` — immutable instance build, checksum validation, isolated source/flat compilation, and artifact upload;
3. inspect job logs and fix the root cause of any failure;
4. rerun the complete workflow after each fix;
5. record the successful Actions run ID and conclusions;
6. merge only the validated head SHA.

Do not remove a check to obtain a green result. External platforms or official kits that were not actually exercised remain `UNVERIFIED`.

The online reference audit may fail because of a positive metadata mismatch or
because scholarly infrastructure is unavailable. Inspect the generated
`reference-integrity-*` artifact before classifying the failure. A database miss,
timeout, or rate limit is not evidence that a citation was fabricated, and a
successful metadata match does not approve manuscript claim support.
Rate-limited or temporarily unavailable provider runs are advisory and do not
block CI; rerun them with the cache after provider cooldown. Positive
mismatches remain blocking even when another provider is throttled.
Correction candidates are retrieval artifacts, not approved edits. The Agent
reviews `corrections/candidate.bib`, `corrections/report.jsonl`, and
`corrections/run.json`, retrieves authoritative evidence, and updates
`paper/refs.bib` and the durable ledger together for unambiguous same-object
repairs. Ask the Human only when an identity/version choice can change meaning,
claim support, or source locators.

## Citation support workflow

Every substantive citation occurrence goes through the three-question
claim-to-citation review: what the manuscript claims, what the cited work says
with a verbatim passage and locator, and whether the evidence supports the
claim. The Agent runs `reference-evidence.py` (`inventory`, `resolve`, `search`,
`passages`, `packet`, `record`, `status`, `migrate`) and follows
`.agents/skills/citation-support-review/SKILL.md`.

Draft records provisional results only and never upgrades to
`human-confirmed`. Review performs independent supportive and adversarial
passes and produces a Human decision packet on disagreement. Release reuses
unchanged Human-confirmed evidence, rechecks stale, provisional, disagreement,
unavailable, and unresolved records, and fails closed on any substantive claim
without Human-confirmed support. Provider failures are classified outcomes
(`rate-limited`, `provider-unavailable`, `paper-not-indexed`, ...), never
scientific verdicts. A real DOI or metadata match never proves claim support.

`references/ledger.json` uses `paper-reference-ledger-v2`. Legacy v1 ledgers
are migrated explicitly with `reference-evidence.py migrate`; never copy a
template ledger over a populated downstream ledger.

## Scope and evidence

Keep each PR focused on one issue or tightly related design change. The PR body should state:

- the failure mode or goal;
- what changed and why;
- Human and Agent impact;
- positive and negative regression coverage, including adoption/synchronization safety when relevant;
- release-instance or artifact impact;
- external validation that remains out of scope.

## Generated outputs

Do not commit `dist/` or recreate a generated `release/` tree. Tracked release information belongs in Human-reviewed Markdown records under `releases/records/`. Published artifact changes use a new release ID rather than editing an old record.

## Protected evidence surface

The repository protects its current and future real-paper case branches and the corresponding case and standing verification issues. Do not propose or perform their deletion, and do not include them in cleanup PRs or branch/worktree/PR deletion discussions. Record the exact list in that repository's own `DECISIONS.md`; do not copy another repository's IDs.

## Documentation consistency

Treat documentation changes as part of venue, variant, synchronization, and tooling changes. Update the relevant README and Human-facing contract in the same change, then run `bash .agents/tools/verify.sh`. The documentation check rejects known retired paths, obsolete venue references, and missing Agent tool or skill paths. Current repository facts are configured in `.agents/documentation-consistency.json`; semantic review is still required for claims that cannot be proved mechanically.
