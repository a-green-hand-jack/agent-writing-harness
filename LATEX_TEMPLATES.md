# LaTeX Template Compatibility

The paper sidecar is not tied to a conference family or to a particular
`\documentclass`. A downstream repository declares its authored source and
native build commands in `.agents/paper-build.json`; adoption and template sync
run those commands without rewriting the publisher's class, style, or source
layout.

## Build profile

The default `canonical-variants` profile preserves this template's four builds.
An adopted journal repository can instead keep one native manuscript:

```json
{
  "schema_version": "paper-build-profile-v1",
  "layout": "external-latex",
  "source_root": ".",
  "entrypoint": "manuscript.tex",
  "bibliography": "references.bib",
  "builds": [
    {
      "name": "manuscript",
      "command": ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "manuscript.tex"],
      "output": "manuscript.pdf"
    }
  ]
}
```

Paths are repository-relative. Commands are JSON argument arrays, not shell
strings. `bibliography` and `output` may be omitted. At least one named build is
required. If `output` is declared, it must be an ignored, untracked generated
file; add it to the downstream `.gitignore`. Verification isolates any old
artifact and requires the command to create a new non-symlinked, non-empty file.
Each verification command has a 30-minute timeout. Adoption and template sync
reject a command set that changes tracked, staged, or non-runtime untracked
repository state.

Safe verification command supervision currently requires Linux. The ordinary
LaTeX build commands remain usable on other platforms, but adoption and sync
verification fail closed rather than risk restoring an output while a detached
build descendant is still running.

Use one build entry when the publisher has one manuscript form. Add separate
entries only when the repository really has distinct native commands, such as
`review` and `final`. Do not invent anonymous, camera-ready, or arXiv variants
for a publisher template that does not define them. Document every declared
entrypoint and build name in `PUBLICATION.md`.

During initial adoption, `.agents/paper-build.json` is a protected manual
surface because its commands execute downstream code. Review it together with
the existing Makefile, scripts, CI, publisher files, and `PUBLICATION.md`.
`template-adoption.py verify --builds` and `template-sync.py verify --reviewed`
then run the declared command set. The old adoption flag `--variants` remains an
alias for `--builds`.

## Verified matrix

The following minimal native entries are covered by the regression matrix. The
first four use classes from the installed TeX distribution and do not vendor
publisher packages. The five official publisher samples are downloaded into
temporary CI directories, verified by SHA-256, and compiled from the package's
own source files when the dedicated CI check is enabled. The pinned URLs and
digests live in `.agents/tools/_journal_templates.py`; the current development
checkout has also passed the complete matrix locally.

| Template family | Tested identity | Upstream authority | Status |
|---|---|---|---|
| Elsevier | `elsarticle.cls` | [Elsevier LaTeX instructions](https://www.elsevier.com/authors/policies-and-guidelines/latex-instructions) and [CTAN](https://ctan.org/pkg/elsarticle) | compiled |
| IEEE journals | `IEEEtran.cls` with `journal` | [IEEE Author Center](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/use-authoring-tools-and-ieee-article-templates/ieee-article-templates/) and [CTAN](https://ctan.org/pkg/ieeetran) | compiled |
| APS/AIP | `revtex4-2.cls` | [APS REVTeX](https://journals.aps.org/revtex/) and [CTAN](https://ctan.org/pkg/revtex) | compiled |
| ACM journals/proceedings | `acmart.cls` with `manuscript` | [ACM authoring documentation](https://authors.acm.org/proceedings/production-information/preparing-your-article-with-latex) and [CTAN](https://ctan.org/pkg/acmart) | compiled |
| Springer Nature journals | `sn-jnl.cls` from the December 2024 package | [official Springer Nature package](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/18782940/data/v12) and [author support](https://www.springernature.com/gp/authors/campaigns/latex-author-support) | compiled from official package |
| AAS journals | `aastex702.cls` | [official AASTeX 7.0.2 package](https://journals.aas.org/wp-content/uploads/2026/06/aastex702.zip) and [AAS package page](https://journals.aas.org/aastex-package-for-manuscript-preparation/) | compiled from official package |
| IOP journals | `iopjournal.cls` | [official IOP package](https://publishingsupport.iopscience.iop.org/wp-content/uploads/2025/07/ioplatextemplate.zip) and [IOP template page](https://publishingsupport.iopscience.iop.org/questions/latex-template/) | compiled from official package |
| JMLR | `article` plus `jmlr2e.sty` | [official JMLR style repository](https://github.com/JmlrOrg/jmlr-style-file/tree/f413f638b407af76074813f8f88a82a7a5a81e9d) and [formatting instructions](https://www.jmlr.org/format/format.html) | compiled from pinned official repository commit |
| PLOS ONE | publisher package with `article` and `plos2025.bst` | [official PLOS package](https://journals.plos.org/plosone/s/file?id=1457/PLOS_latex_template.zip) and [PLOS LaTeX page](https://journals.plos.org/plosone/s/latex) | compiled from official package |

The official-package SHA-256 pins used by the smoke matrix are:

| Package | SHA-256 |
|---|---|
| Springer Nature package `v12` | `812e76dcaa9c28dc1bff1fb6065d51729b67d4ea140552a05088317414a3ecae` |
| AASTeX `aastex702.zip` | `008ed27b62a3b1689a256a53893df05080cd01b754b206f4833f864cb16fc25f` |
| IOP `ioplatextemplate.zip` | `796c337cc2099a86e736bf86b5d5b17f66f1b29441bb5dfc3272ff3819ce7114` |
| JMLR `jmlr2e.sty` at commit `f413f63` | `a430a875d561235951800e4e21d2631e18ddf0b369646ec276f43ea5080f27c3` |
| JMLR `sample.tex` at commit `f413f63` | `19f563441b9b288333851cc9f63be8d9e8bd6b10bd672271a598b74f6e2903e2` |
| JMLR `sample.bib` at commit `f413f63` | `89e88007d9d80c206c103c1fe8cdaa4e3e56757b310fc28448a0763869036e1c` |
| PLOS `PLOS_latex_template.zip` | `ea3a8a0fdbac77f95de47639541b09ef1583e059ace6783367490af9fa0b9a60` |

Current journal-level instructions remain authoritative. A package digest
proves only that the smoke test used the pinned downloaded bytes; it does not
prove compatibility with a publisher's upload processor, an individual
journal's current instructions, anonymity policy, page limits, source-package
rules, or acceptance by a submission portal.

The CTAN `jmlr.cls` package is not used as evidence for JMLR's current official
author template, whose documented interface is `article` plus `jmlr2e.sty`.

## Limits

A successful local build proves only that the declared command completed in
that environment. It does not prove compatibility with a publisher's upload
processor, an individual journal's current instructions, anonymity policy,
page limits, source-package rules, or acceptance by a submission portal. Lock
the publisher package version in the paper repository when it is not provided
by the execution environment, and verify the actual submission system before
claiming submission readiness.
