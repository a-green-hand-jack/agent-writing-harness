# Release Review

## Trigger

Use when preparing a submission, arXiv package, camera-ready version, or other Human-approved release candidate.

## Minimum context

- `PAPER.md`, `EXPERIMENTS.md`, and `PAPER_INTERFACES.md`;
- current applicable decisions;
- active paper source and release diff;
- venue rules only from current official sources when a venue is involved.

Do not load historical alternatives unless a current conflict requires them.

## Procedure

1. Run the Draft contract check and summarize current state.
2. Run the Release contract check; do not suppress unresolved or placeholder failures.
3. List high-impact changes since the last Human review.
4. Check claim strength, experiment interpretation, stable interfaces, limitations, negative evidence, anonymity, references, figures, tables, and compilation.
5. Run the repository's deterministic and real-LaTeX checks.
6. Mark unavailable external environments as unverified, not successful.
7. Produce a short release summary with blockers, accepted exceptions, residual risks, and an Agent recommendation.

## Human decision

Only the Human approves the release candidate and accepts explicit residual risk or exceptions. Bind approval to the reviewed Git revision and release artifacts.
