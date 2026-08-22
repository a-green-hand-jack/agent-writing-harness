# Vendored third-party skills

This directory contains immutable snapshots of third-party skill suites that
the template distributes so downstream paper repositories work out of the box
without any global skill installation.

## Layout

- `ccfa-skills/` — the CCFA-Skills suite (`v0.9.0`,
  `fd5c7e3afcc097d874d296a0e1e8118ae597f847`, MIT). All 17 `ccf-*` skills with
  their `SKILL.md`, text `references/`, `scripts/`, and required resources.
- `writing-dna-skill/` — the writing-dna-skill
  (`d5145ef671be70d3439524b6b72f55fe06a869a9`, MIT), including its
  `lieflat-less-ai-tone` skill, templates, and references.

## Rules

- **Never edit files under this directory.** The vendor tree is immutable.
  Upstream updates arrive through template-sync after review, not by local
  modification.
- First-party skills under `.agents/skills/` are thin wrappers that route to
  these snapshots and enforce the paper-contract boundaries.
- Integrity is verified by `.agents/tools/check-vendored-skills.py` against the
  hash manifest in `.agents/dependencies/vendored-skills/provenance.json`.

## Excluded upstream content

The snapshots intentionally omit copyright-ambiguous or non-functional content.
The complete exclusion list with reasons is in
`.agents/dependencies/vendored-skills/provenance.json`. The main exclusions are:

- third-party paper full-text PDFs and full-text Markdown reproductions
  (fetch the PDFs you need on demand into ignored `.agents/runtime/`);
- the 71 MB `ccf-latex-templates` venue LaTeX corpus (this template provides
  its own `paper/` build, variants, and venue knowledge);
- upstream demo/evaluation/plugin/CI surfaces and runtime adapter configs;
- `ccf-paper-writer/scripts/convert_pdf_to_card.py`, a broken upstream
  duplicate (`IndentationError`); use `ccf-paper-to-exemplar/scripts/convert.py`.

## License

Each snapshot keeps its upstream `LICENSE` file. CCFA-Skills and
writing-dna-skill are both MIT. See `THIRD_PARTY.md` in
`.agents/dependencies/vendored-skills/`.
