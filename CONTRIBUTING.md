# Contributing

## Pull request merge contract

A pull request is not ready merely because GitHub reports it as mergeable.

Before merge:

1. wait for the `PR validation` workflow to finish;
2. require every applicable job to succeed:
   - `harness` — paper-first checks and Agent regressions;
   - `latex (<variant>)` — real TeX builds and variant-surface checks;
   - `paper-only` — all variants compile with only `paper/` present;
   - `release-package` — immutable instance build, checksum validation, isolated source/flat compilation, and artifact upload;
3. inspect job logs and fix the root cause of any failure;
4. rerun the complete workflow after each fix;
5. record the successful Actions run ID and conclusions;
6. merge only the validated head SHA.

Do not remove a check to obtain a green result. External platforms or official kits that were not actually exercised remain `UNVERIFIED`.

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
