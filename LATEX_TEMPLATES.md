# LaTeX Template Compatibility

The paper sidecar is not tied to a conference family or to a particular
`\documentclass`. A repository declares its authored source and native build
commands in `.agents/paper-build.json`; adoption and template sync run those
commands without rewriting the publisher's class, style, or source layout.

## Build profile

This case uses the `canonical-variants` profile with `paper/main.tex`,
`paper/refs.bib`, and the four existing Makefile builds: `draft`, `anonymous`,
`camera-ready`, and `arxiv`. An adopted publisher-template repository can
instead retain its native manuscript with an `external-latex` profile.

Paths are repository-relative. Commands are JSON argument arrays, not shell
strings. Declared outputs must be ignored and untracked. Verification isolates
old outputs, requires a new non-symlinked and non-empty artifact, limits each
command to 30 minutes, and rejects changes to tracked, staged, or non-runtime
untracked repository state. Safe command supervision currently requires Linux.

## Verified matrix

The template repository tests installed fixtures for Elsevier, IEEE, REVTeX,
ACM, and KDD. It also downloads and compiles current official packages for
Springer Nature, AAS, IOP, JMLR, PLOS ONE, ICML, ICLR, NeurIPS, ACL, and AAAI.
No third-party template package is committed to this case branch.

The online catalog lives in `.agents/tools/_official_templates.py`. It records
the actual SHA-256 of downloaded bytes and disables latexmk rc files and TeX
shell escape. Ordinary paper builds and adoption or sync verification never
download a template. The template-maintenance CI runs this online matrix on
`main`; case-branch CI validates this paper's retained source and four declared
builds instead.

## Limits

A successful local build does not prove publisher upload compatibility,
current venue rules, anonymity policy, page limits, source-package compliance,
or submission-portal acceptance. CORAL retains its existing COLM 2026 source
style; current venue-kit and platform acceptance remain unresolved as recorded
in `PUBLICATION.md`.
