# Contributing

## Pull request merge contract

A pull request is not ready merely because GitHub reports it as mergeable.

Before merge:

1. wait for the `PR validation` workflow to finish;
2. require every applicable job to succeed:
   - `harness` — paper-first checks and Agent-side regressions;
   - `latex` — the Human build with a real TeX toolchain;
   - `paper-only` — real TeX compilation with only `paper/` present;
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
- positive and negative regression coverage;
- external validation that remains out of scope.
