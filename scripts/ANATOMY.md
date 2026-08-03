# Scripts Anatomy

Small deterministic validators, indexers, exporters, and sync helpers.

- `paper_harness_checks.py`: shared validator backend. It owns schema, cross-reference, release-surface, and lightweight semantic checks used by the `check-*.py` wrappers.
- `check-bridge-chassis.py`: Writing-side Bridge chassis adoption-readiness preflight over `state/bridge-chassis.yaml` (profile, fully explicit chassis/protocol semver pins, executable MAJOR baseline gate, provisional compatibility matrix cross-checked against the canonical pins, registry contract/schema versioning and ownership drift, Writing-owned capability classification). Local self-consistency only — it is not upstream Bridge conformance. Rejects missing profile/pins, default-latest or suffixed pins, non-comparator ranges, registry drift, matrix/pin contradiction, and silent chassis MAJOR bumps.
- `compare-original-pdf.sh`: PDF fidelity gate. Its default paper root is the caller's current working directory, not the directory containing the script copy; `--paper-root` and `--compiled` make the target explicit. Extreme page-count mismatch is treated as a likely identity/setup error rather than an ordinary content diff.
- `report-numeric-exceptions.py`: JSON visibility report for numeric exception usage. It does not mutate the repo.
- `check-citation-review-worksheets.py`: validates optional citation sentence review worksheets against active TeX and ledger state.
- `report-citation-audit.py`: JSON visibility report for citation ledger coverage, paper locators, and audit status. It does not mutate the repo.
- `test-realkit-gate-negative.sh`: regression proof that `export_venue_template.py` hard-fails (never a false pass) when compiling against a broken venue-class stand-in; restores `state/conference-template.yaml` and removes `release/venue/` afterward.
- `test-pdf-fidelity-paper-root-negative.sh`: regression for cross-worktree invocation. It proves a script copy in worktree B compares the caller's worktree A and that an extreme page-count gap produces an explicit identity/setup error.
