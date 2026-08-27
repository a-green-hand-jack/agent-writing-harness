# LaTeX Template Compatibility

The paper sidecar is not tied to a conference family or to a particular
`\documentclass`. A downstream repository declares its authored source and
native build commands in `.agents/paper-build.json`; adoption and template sync
run those commands without rewriting the publisher's class, style, or source
layout.

## Build profile

The default `canonical-variants` profile preserves this template's four builds.
An adopted publisher-template repository can instead keep one native manuscript:

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

The following native entries are covered by the regression matrix. Installed
class fixtures exercise common journal classes plus KDD's exact ACM review
options. Ten additional samples are downloaded from official publisher or
conference sources into temporary CI directories and compiled from the
package's own source files. No third-party template package is committed to
this repository.

| Template family | Tested identity | Upstream authority | Status |
|---|---|---|---|
| Elsevier | `elsarticle.cls` | [Elsevier LaTeX instructions](https://www.elsevier.com/authors/policies-and-guidelines/latex-instructions) and [CTAN](https://ctan.org/pkg/elsarticle) | compiled |
| IEEE journals | `IEEEtran.cls` with `journal` | [IEEE Author Center](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/use-authoring-tools-and-ieee-article-templates/ieee-article-templates/) and [CTAN](https://ctan.org/pkg/ieeetran) | compiled |
| APS/AIP | `revtex4-2.cls` | [APS REVTeX](https://journals.aps.org/revtex/) and [CTAN](https://ctan.org/pkg/revtex) | compiled |
| ACM journals/proceedings | `acmart.cls` with `manuscript` | [ACM authoring documentation](https://authors.acm.org/proceedings/production-information/preparing-your-article-with-latex) and [CTAN](https://ctan.org/pkg/acmart) | compiled |
| KDD | `acmart.cls` with `sigconf,anonymous,review` | [KDD 2026 Research Track instructions](https://kdd2026.kdd.org/research-track-call-for-papers/) and [ACM proceedings template](https://www.acm.org/publications/proceedings-template) | compiled against the installed class; official ACM package download not exercised |
| Springer Nature journals | `sn-jnl.cls` from the December 2024 package | [official Springer Nature package](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/18782940/data/v12) and [author support](https://www.springernature.com/gp/authors/campaigns/latex-author-support) | compiled from official package |
| AAS journals | `aastex702.cls` | [official AASTeX 7.0.2 package](https://journals.aas.org/wp-content/uploads/2026/06/aastex702.zip) and [AAS package page](https://journals.aas.org/aastex-package-for-manuscript-preparation/) | compiled from official package |
| IOP journals | `iopjournal.cls` | [official IOP package](https://publishingsupport.iopscience.iop.org/wp-content/uploads/2025/07/ioplatextemplate.zip) and [IOP template page](https://publishingsupport.iopscience.iop.org/questions/latex-template/) | compiled from official package |
| JMLR | `article` plus `jmlr2e.sty` | [official JMLR style repository](https://github.com/JmlrOrg/jmlr-style-file) and [formatting instructions](https://www.jmlr.org/format/format.html) | compiled from the current official branch |
| PLOS ONE | publisher package with `article` and `plos2025.bst` | [official PLOS package](https://journals.plos.org/plosone/s/file?id=1457/PLOS_latex_template.zip) and [PLOS LaTeX page](https://journals.plos.org/plosone/s/latex) | compiled from official package |
| ICML | `icml2026.sty` and `example_paper.tex` | [ICML author instructions](https://icml.cc/Conferences/2026/AuthorInstructions) and [official `icml2026.zip`](https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip) | compiled from official package |
| ICLR | `iclr2026_conference.sty` and its sample | [ICLR author guide](https://iclr.cc/Conferences/2026/AuthorGuide), [official archive](https://github.com/ICLR/Master-Template/raw/master/iclr2026.zip), and [official repository](https://github.com/ICLR/Master-Template) | compiled from official package |
| NeurIPS | `neurips_2026.sty` and its sample | [NeurIPS call for papers](https://neurips.cc/Conferences/2026/CallForPapers) and [official formatting package](https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip) | compiled from official package |
| ACL | `acl.sty` and `acl_latex.tex` from the rolling repository | [ACL main-conference instructions](https://2026.aclweb.org/calls/main_conference_papers/), [ARR template requirements](https://aclrollingreview.org/cfp#paper-submission-and-templates), and [official style repository](https://github.com/acl-org/acl-style-files) | compiled from current official repository archive |
| AAAI | Author Kit `2026.1` anonymous LaTeX sample | [AAAI submission instructions](https://aaai.org/conference/aaai/aaai-26/submission-instructions/) and [official Author Kit](https://aaai.org/authorkit26-1/) | compiled from official package |

The online catalog lives in `.agents/tools/_official_templates.py`. Enable it
with `REQUIRE_OFFICIAL_LATEX_TEMPLATES=1`; `OFFICIAL_TEMPLATE_CACHE` selects the
temporary download directory. Every run fetches the current bytes at each
catalog URL, even when the cache already contains an older package. It accepts
an official update rather than comparing it with a repository-pinned digest,
then prints the actual SHA-256 and writes a neighboring
`<download>.sha256.json` audit record. Versioned URLs still require a catalog
update when an authority publishes a new path. Mutable official repositories,
including the JMLR, ICLR, and ACL sources, follow their current branches.
Smoke builds disable latexmk rc files and TeX shell escape. The Springer sample
uses latexmk's fixed DVI-to-PostScript-to-PDF route for its supplied EPS figure.

The actual digest proves only which downloaded bytes were compiled. It does not
establish that mutable upstream content is trustworthy or that a package is
accepted by a publisher's upload processor. A downstream paper repository
should retain and review the exact template version it uses; ordinary paper
builds and adoption or sync verification never download a template.

The CTAN `jmlr.cls` package is not used as evidence for JMLR's current official
author template, whose documented interface is `article` plus `jmlr2e.sty`.

## Limits

A successful local build proves only that the declared command completed in
that environment. It does not prove compatibility with a publisher's upload
processor, current venue instructions, anonymity policy, page limits,
source-package rules, or acceptance by a submission portal. Lock the publisher
package version in the paper repository when it is not provided by the
execution environment, and verify the actual submission system before claiming
submission readiness.
