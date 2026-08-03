# Scripts Anatomy

`scripts/` contains deterministic compatibility implementation used by existing capabilities, real-paper cases, release workflows, and the stable Agent entrypoints in `.agents/tools/`.

It is not the Human command surface. Humans build with `make pdf`; Agents normally invoke `bash .agents/tools/verify.sh` or `bash .agents/tools/release.sh`.

- `paper_harness_checks.py`: shared validator backend. It owns schema, cross-reference, release-surface, and lightweight semantic checks used by the `check-*.py` wrappers.
- `check-bridge-chassis.py`: existing Writing-side Bridge adoption-readiness preflight. It remains compatibility implementation and is not upstream conformance.
- `compare-original-pdf.sh`: PDF fidelity gate bound to the caller or explicit paper root, with cross-worktree and identity diagnostics.
- `export-tex-release.sh`: reconstructs TeX-only release surfaces and manifest.
- `check-latex.sh`: real authored and isolated release compilation review.
- `report-numeric-exceptions.py`, `check-citation-review-worksheets.py`, and `report-citation-audit.py`: focused visibility and validation helpers.
- `test-*.sh`: negative regression probes executed by PR CI.

Do not add a new Human-facing workflow here. Add or extend a stable `.agents/tools/` entrypoint, then use scripts as the implementation layer when appropriate. Existing files can move only after capabilities, case branches, workflows, and release evidence prove the replacement is equivalent.
