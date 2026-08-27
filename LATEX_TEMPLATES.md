# LaTeX Template Compatibility

The paper sidecar is not tied to a conference family or to a particular
`\documentclass`. A repository declares its authored source and native build
commands in `.agents/paper-build.json`; adoption and template sync run those
commands without rewriting the publisher's class, style, or source layout.

## Build profile

This case uses the `canonical-variants` profile with `paper/main.tex`,
`paper/refs.bib`, and the four existing Makefile builds: `draft`, `anonymous`,
`camera-ready`, and `arxiv`. An adopted publisher-template repository can
instead keep one native manuscript with an `external-latex` profile.

Paths are repository-relative. Commands are JSON argument arrays, not shell
strings. `bibliography` and `output` may be omitted. At least one named build is
required. If `output` is declared, it must be an ignored, untracked generated
file. Verification isolates any old artifact and requires the command to create
a new non-symlinked, non-empty file. Each command has a 30-minute timeout, and
verification rejects command sets that change tracked, staged, or non-runtime
untracked repository state.

Safe verification command supervision currently requires Linux. Ordinary
LaTeX builds remain usable on other platforms, but adoption and sync
verification fail closed rather than risk restoring an output while a detached
build descendant is still running.

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

A successful local build proves only that the declared command completed in
that environment. It does not prove compatibility with a publisher's upload
processor, current venue instructions, anonymity policy, page limits,
source-package rules, or acceptance by a submission portal. ARIS retains its
imported ICLR 2026 source style, while current venue-kit and platform acceptance
remain unresolved as recorded in `PUBLICATION.md`.
