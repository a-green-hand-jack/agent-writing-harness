# Publication Variants

This directory contains small overlays on the canonical `paper/` source. A variant may control author visibility, acknowledgements, appendix inclusion, and publication-facing presentation hooks. It must not copy sections or redefine scientific claims, result meaning, or experiment interpretation.

## Layout

- `common.tex`: declares shared switches and safe defaults.
- `config/*.tex`: one small configuration per variant.
- `draft.tex`, `anonymous.tex`, `camera_ready.tex`, `arxiv.tex`: tiny build drivers that select a config and input `main.tex`.

## Build

From the repository root:

```bash
make pdf
make pdf VARIANT=anonymous
make pdf VARIANT=camera-ready
make pdf VARIANT=arxiv
```

The root `paper/main.tex` defaults to `anonymous` for direct Overleaf or source imports.
The Makefile keeps `draft` as its daily-writing default and selects other variants
explicitly.

Add a variant only after updating `PUBLICATION.md`, the checker, tests, and CI matrix. Do not maintain publication variants as long-lived branches or copied paper trees.
