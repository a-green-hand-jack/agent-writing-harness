# Vendored-skills third-party dependencies

This lock supports running the vendored CCFA-Skills scripts on demand
(`uv sync --project .agents/dependencies/vendored-skills`). No dependency is
required to compile `paper/`, and nothing is vendored into the repository.

Direct dependencies:

- `PyYAML==6.0.3` — MIT. Used by `ccf-common/scripts/check_sources.py` (and
  related CCFA source-registry tooling).
- `pymupdf==1.27.2` — AGPL-3.0-or-later. Used by
  `ccf-paper-to-exemplar/scripts/convert.py` (and upstream's PDF extraction
  scripts) to read user-supplied paper PDFs on demand.

The vendored skills themselves are MIT (see `.agents/vendor/ccfa-skills/LICENSE`
and `.agents/vendor/writing-dna-skill/LICENSE`).

Package versions and artifact hashes are authoritative in `uv.lock`. The lock
must be regenerated and this inventory reviewed whenever any resolved version
changes.

Note: `pymupdf` is AGPL-3.0-or-later. It runs only when a user explicitly asks
to distill a paper PDF into a writing exemplar; the template itself never
ships or runs it in its verification path. Keep that boundary visible when
changing the dependency set.
