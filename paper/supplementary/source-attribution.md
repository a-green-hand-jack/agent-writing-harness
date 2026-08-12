# Source Attribution

## arXiv Case

- arXiv id: `2604.01658v2` (latest; the earlier record said v1 but the recorded archive SHA matches v2)
- Title: CORAL: Towards Autonomous Multi-Agent Evolution for Open-Ended Discovery
- Authors: Ao Qu, Han Zheng, Zijian Zhou, Yihao Yan, Yihong Tang, Shao Yong Ong, Fenglu Hong, Kaichen Zhou, Chonghe Jiang, Minwei Kong, Jiacheng Zhu, Xuan Jiang, Sirui Li, Cathy Wu, Bryan Kian Hsiang Low, Jinhua Zhao, Paul Pu Liang
- Venue kit: COLM 2026 (`colm2026_conference`), `[preprint]` option
- Abstract URL: https://arxiv.org/abs/2604.01658v2
- Source archive URL: https://arxiv.org/e-print/2604.01658v2
- Downloaded to: `/tmp/arxiv-2604.01658.geiM2g/source` (disposable tmp dir, not committed)
- Archive sha256: `dd23352e4e550faf8fcd160312aace325d9f86674c3580657c690a250dd714ac`
- Archive format: gzip-compressed tar (per `file`), extracted at `/tmp/arxiv-2604.01658.geiM2g/unpacked`
- Toplevel driver per `00README.json`: `colm2026_conference.tex`, compiler `pdflatex`, `texlive_version: "2025"`

## Human Gate

- Gate id: `external-source-migration` (per `.agent/capabilities/arxiv-case-harness-test.yaml`)
- Recorded by: automated case-harness-test run, case branch `case/arxiv-2604-01658`
- Recorded at: 2026-07-18

## Migration Mapping (mechanical, no invented facts)

The source is a modular directory: `colm2026_conference.tex` is the sole top-level
driver, which `\input`s `preamble.tex`, `figures/figures.tex` (an all-commented
stub), section bodies from `sections/*.tex`, the venue class
`colm2026_conference.sty`/`.bst`, and the bibliography `colm2026_conference.bib`.

Section input order in the compiled PDF (preserved verbatim in `paper/main.tex`):
abstract, Introduction, Related Work, Method (`\section{Coral: A Framework ...}`),
Experiments, Limitations, Conclusion, then the (non-`\appendix`-numbered) Appendix.
Note the source's `sections/limitations.tex` is **entirely commented out** (its
`Limitations and Future Directions` section actually lives inside the appendix,
`\label{app:future_directions}`); the empty `07_limitations` slot is kept and
`\input` in the original position (between Experiments and Conclusion) purely to
preserve source ordering.

| Source | Template destination | Notes |
| --- | --- | --- |
| `colm2026_conference.tex` preamble (colm class options, colors, `\fnum@figure/table` recolor, squishlist, author-annotation macros `\paul/\kai/\zijian/\han/\hl/\hlp`, `\title`/`\author`) + `preamble.tex` packages/promptboxes/`\graphicspath` | `paper/venue_preamble.tex` | Venue/class-bound setup kept out of `paper/macros.tex` per `paper/ANATOMY.md`. `\title`/`\author` kept here so author-affiliation superscript literals are not scanned as paper numerics. The source `\usepackage[table]{xcolor}` is replaced with `\usepackage{colortbl}` to avoid an option clash with ccfa-paper's own xcolor load (same functionality). |
| `\newcommand{\method}`, `\rowstrut`, `\stage` (from `preamble.tex`) | `paper/macros.tex` | Project-specific text macros. |
| `\begin{document}` correspondence `\footnotetext` + `\ifcolmsubmission\linenumbers\fi` + `\maketitle` + teaser `\includegraphics{figures/teaser.pdf}` | `paper/sections/00_title.tex` (teaser via `\input{figures/00_teaser}`) | Verbatim. |
| `sections/abstract.tex` | `paper/sections/01_abstract.tex` | Verbatim (incl. the source's commented-out earlier abstract draft). |
| `sections/introduction.tex` | `paper/sections/02_intro.tex` | Verbatim; `fig:paradigm_comparison` `figure*` replaced by `\input{figures/01_paradigm}`. |
| `sections/related_work.tex` | `paper/sections/03_related.tex` | Verbatim. |
| `sections/method.tex` | `paper/sections/04_method.tex` | Verbatim; `fig:coral-diagram` `figure*` replaced by `\input{figures/02_overview}`. |
| `sections/experiments.tex` | `paper/sections/05_exp.tex` | Verbatim (tables `tab:main_results`, `tab:multi-agent`, `tab:ablations` inline). |
| `sections/limitations.tex` | `paper/sections/07_limitations.tex` | Verbatim (fully commented in source; renders nothing). |
| `sections/conclusion.tex` | `paper/sections/06_conclusion.tex` | Verbatim. |
| `sections/appendix.tex` | `paper/sections/10_appendix.tex` | Verbatim; `fig:polyominoes_demo` and `fig:architecture` `figure*` blocks replaced by `\input{figures/10_polyominoes}`/`\input{figures/11_architecture}`; the two `fig:coral-ui` subfigure `\includegraphics` paths repointed to `figures/srcs/12_ui1.png`/`13_ui2.png`. |
| `figures/*.pdf|*.png` | `paper/figures/srcs/NN_name.*` | Renamed to the NN_name convention (see below). |
| `colm2026_conference.bib` | `paper/refs.bib` | Renamed only; content untouched (50 entries; 43 cited). |
| `colm2026_conference.sty`, `colm2026_conference.bst` | `paper/style/` | Venue class/bib-style. `natbib`/`fancyhdr` (`\RequirePackage`d by the class) come from the local TeX Live, not shipped here. |

## Figure Numbering

| Wrapper/asset basename | Source file | Label | Group | Rendering |
| --- | --- | --- | --- | --- |
| `00_teaser` | `figures/teaser.pdf` | `fig:teaser` | body | wrapper, inline under title |
| `01_paradigm` | `figures/search_paradigm.pdf` | `fig:paradigm_comparison` | body | wrapper |
| `02_overview` | `figures/coral_overview.pdf` | `fig:coral-diagram` | body | wrapper |
| `10_polyominoes` | `figures/polyominoes_demo.pdf` | `fig:polyominoes_demo` | appendix | wrapper |
| `11_architecture` | `figures/figure_architecture.pdf` | `fig:architecture` | appendix | wrapper |
| `12_ui1` | `figures/ui_1.png` | `fig:coral-ui-overview` | appendix | inline subfigure of `fig:coral-ui`; wrapper .tex is a comment-only alignment stub |
| `13_ui2` | `figures/ui_2.png` | `fig:coral-ui-knowledge` | appendix | inline subfigure of `fig:coral-ui`; wrapper .tex is a comment-only alignment stub |

The source's `fig:coral-ui` is a single `figure` with two `subfigure`s. The
template's one-wrapper = one-asset = one-float convention cannot express subfigure
grouping, so the float stays inline in `10_appendix.tex` and the two assets get
comment-only alignment stubs (`12_ui1.tex`, `13_ui2.tex`) that satisfy the
srcs-asset <-> wrapper naming check without duplicating the `\includegraphics`.
Recorded as migration debt / template-convention gap.

## Numeric Migration Notes

CORAL is a results-heavy empirical paper. Its Experiments (`05_exp`) and Appendix
(`10_appendix`) sections report several hundred source-stated numeric literals
(per-task scores, kernel cycle counts, percentages, and cost/efficiency figures in
`tab:main_results`, `tab:multi-agent`, `tab:ablations`, and the appendix
trajectory/kernel/cost tables). During this mechanical migration those numbers are
copied verbatim from the arXiv source; their provenance is the published source
itself (`evidence-arxiv-source`), not a locally reproduced lab artifact. They are
**bulk-accepted** via a path-scoped entry in `state/numbers/exceptions.yaml` rather
than individually registered, and are flagged needs-review as case ledger debt. The
two headline kernel scores (1363 -> 1103 cycles) are additionally registered as
verified numbers in `state/numbers/groups/main-results.yaml`. `2026` (venue/report
year) and `4.6` (Claude Opus 4.6 model version) are covered by literal exceptions.

No claim, number, or citation facts were invented during this migration. All prose,
numbers, and citations in `paper/sections/*.tex`, `paper/figures/*.tex`, and
`paper/refs.bib` are copied verbatim from the arXiv source.


## Round 2 (template adoption) corrections and fidelity evidence

- **Version identity corrected**: the Round-1 record said `v1`, but the recorded
  archive SHA-256 (`dd23352e4e550faf8fcd160312aace325d9f86674c3580657c690a250dd714ac`)
  and the committed original PDF SHA-256
  (`6baf82f122d884380dea1ce2a20a92fd4e75216f430f652819d56bb2b893085c`) match the
  arXiv v2 files, not v1. The attribution above now says v2; the v1 wording is
  preserved in Git history and in DECISIONS.md.
- **Title/author moved to interfaces**: `\title`/`\author` were moved from
  `paper/venue_preamble.tex` into `\PaperTitle`/`\PaperAuthors` in
  `paper/macros.tex`; rendered output is unchanged.
- **Venue header restored**: the venue style sets `\lhead{Preprint. Under
  review.}` inside the `\maketitle` group; modern fancyhdr does not persist it.
  `paper/sections/00_title.tex` re-applies the sty's own preprint header at top
  level after `\maketitle`, so the rebuild matches the arXiv v2 page header.
- **Known un-reproducible difference**: the official arXiv PDF page 1 carries the
  platform-injected line `arXiv:2604.01658v2 [cs.AI] 17 May 2026`; arXiv injects
  this stamp at upload time and it is not reproduced locally.
- **A/B/C/D fidelity (paper-fidelity.py evidence under
  `.agents/runtime/fidelity/`, ignored)**:
  - A (official arXiv v2 PDF, 27 pages) vs B (original source rebuilt locally
    with TeX Live 2026, 27 pages): 26/27 pages match exactly; page 1 differs
    only by the arXiv platform stamp and author-block line wrapping.
  - A (official arXiv v2 PDF, 27 pages) vs D (adopted-tree `arxiv` variant,
    27 pages): 19/27 pages match exactly after the header fix. Page 1 differs by
    the arXiv stamp and author-block line wrapping (TeX Live 2025 font metrics
    vs 2026); pages 13-19 differ by figure/table float drift from the Round-1
    structural changes plus TeX-version drift. All content is present in both.
  - C (Round-1 committed `paper/main.pdf`) vs D: identical except the restored
    header on every page.

- **CI portability fix**: `\squishlisttwo[\arabic*.]` relies on newer
  enumitem behavior; the label now spells the counter explicitly as
  `\arabic{squishlisttwoitem}.`, rendering identical labels on older TeX
  Live distributions.
