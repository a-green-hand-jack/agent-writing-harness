# Contributing

## Pull request merge contract

A pull request is not ready merely because GitHub reports it as mergeable.
Before merge, wait for `PR validation` and `Reference validation`, require every
applicable job to pass, inspect failures, rerun the complete workflow after a
fix, and merge only the validated head SHA.

Required coverage includes:

- `harness`: paper-first checks, Agent regressions, and vendored-skill integrity;
- `references`: offline ledger enforcement and enabled metadata gates;
- `latex (<variant>)`: real TeX builds and identity-surface checks;
- `paper-only`: all variants compile with only `paper/` present;
- `vendored-skills`: locked runtime and applicable upstream checks;
- `release-package`: immutable Draft-validation packaging and checksum checks.

Do not remove a check to obtain a green result. External platforms or official
kits that were not exercised remain `UNVERIFIED`.

## Citation support workflow

For each substantive citation occurrence, record what the manuscript claims,
what the cited source says with an exact passage and locator, and whether the
evidence supports the claim. Follow
`.agents/skills/citation-support-review/SKILL.md` and use
`.agents/tools/reference-evidence.py`. Provider failures are infrastructure
outcomes, never scientific verdicts; metadata identity does not prove support.

## Scope and evidence

Keep each change focused. State the goal, what changed and why, Human and Agent
impact, regression coverage, release impact, and external validation that
remains out of scope.

## Generated outputs

Do not commit `dist/` or recreate a generated release tree. Tracked release
information belongs in Human-reviewed Markdown records under
`releases/records/`. New published artifacts require a new release ID.

## Protected evidence surface

`case/arxiv-2605-03042` is protected evidence for this repository. Do not
propose or perform its deletion or include it in routine cleanup.

## Documentation consistency

Update the relevant Human contract and documentation in the same change, then
run `bash .agents/tools/verify.sh`. Automated checks do not replace semantic
review of scientific claims.
