# Contributing

## Pull request merge contract

A pull request is not ready merely because GitHub reports it as mergeable. Before merge:

1. wait for the `PR validation` workflow to finish;
2. require every applicable job to succeed:
   - `harness` — deterministic checks and all negative regressions;
   - `latex` — Human build, authored-paper review, release rebuild, and isolated arXiv compilation;
   - `paper-only` — real TeX compilation with only the `paper/` project present;
3. if a job fails, read the job log, identify whether the implementation or test fixture is wrong, fix the root cause, and rerun the complete workflow;
4. record the successful Actions run ID and job conclusions in the pull request or linked issue;
5. merge only the exact head SHA that was validated.

Do not remove a check simply to obtain a green result. Do not report an unavailable external environment as successful; use `UNVERIFIED` and keep the relevant environment tracker open.

## Scope and evidence

Keep each pull request focused on one issue or tightly related failure class. The PR body should state:

- the failure mode or design goal;
- what changed and why;
- user and Agent impact;
- negative regression coverage;
- external validation that remains out of scope.

Real Overleaf import, arXiv upload, and official venue-kit execution require their own evidence under the environment and case trackers. Local compilation does not substitute for those external runs.
