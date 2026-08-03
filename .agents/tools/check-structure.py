#!/usr/bin/env python3
"""Check the paper-first repository structure without legacy harness state."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FORBIDDEN = (
    ".agent",
    ".claude",
    "state",
    "lab",
    "human",
    "memory",
    "scripts",
    "PROJECT.md",
)
REQUIRED = (
    "README.md",
    "Makefile",
    "PAPER.md",
    "EXPERIMENTS.md",
    "PAPER_INTERFACES.md",
    "PUBLICATION.md",
    "DECISIONS.md",
    "AGENTS.md",
    "paper/main.tex",
    "paper/macros.tex",
    "paper/venue_preamble.tex",
    "paper/refs.bib",
    "paper/sections/00_title.tex",
    "paper/sections/01_abstract.tex",
    "paper/sections/10_appendix.tex",
    "paper/variants/README.md",
    "paper/variants/common.tex",
    "paper/variants/draft.tex",
    "paper/variants/anonymous.tex",
    "paper/variants/camera_ready.tex",
    "paper/variants/arxiv.tex",
    ".agents/knowledge/README.md",
    ".agents/skills/paper-orientation/SKILL.md",
    ".agents/tools/verify.sh",
    ".agents/tools/check-publication.py",
    ".agents/runtime/.gitignore",
)
SECTION_RE = re.compile(r"^[01]\d_[a-z][a-z0-9_]*\.tex$")
INPUT_RE = re.compile(r"\\input\{sections/([^}]+)\}")
ASSET_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def active_tex(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def check_required(root: Path) -> int:
    code = 0
    for relative in REQUIRED:
        if not (root / relative).is_file():
            code |= error(f"missing required paper-first file: {relative}")
    for relative in FORBIDDEN:
        if (root / relative).exists():
            code |= error(f"legacy harness surface must be removed: {relative}")
    return code


def check_sections(root: Path) -> int:
    main_path = root / "paper/main.tex"
    sections_root = root / "paper/sections"
    if not main_path.is_file() or not sections_root.is_dir():
        return error("missing paper/main.tex or paper/sections/")

    code = 0
    names = sorted(path.name for path in sections_root.glob("*.tex"))
    for name in names:
        if not SECTION_RE.fullmatch(name):
            code |= error(f"section file does not follow NN_name.tex: {name}")

    main = active_tex(main_path.read_text(encoding="utf-8"))
    inputs = INPUT_RE.findall(main)
    for anchor in ("00_title", "01_abstract", "10_appendix"):
        if anchor not in inputs:
            code |= error(f"paper/main.tex does not input sections/{anchor}.tex")
    for stem in inputs:
        if not (sections_root / f"{stem}.tex").is_file():
            code |= error(f"paper/main.tex has dangling section input: {stem}")

    appendix_index = main.find("\\appendix")
    body = [stem for stem in inputs if stem.startswith("0")]
    appendix = [stem for stem in inputs if stem.startswith("1")]
    if body != sorted(body):
        code |= error("body section inputs are not in ascending NN order")
    if appendix != sorted(appendix):
        code |= error("appendix section inputs are not in ascending NN order")
    for stem in body:
        if appendix_index >= 0 and main.find(f"\\input{{sections/{stem}}}") > appendix_index:
            code |= error(f"body section appears after appendix: {stem}")
    for stem in appendix:
        if appendix_index < 0 or main.find(f"\\input{{sections/{stem}}}") < appendix_index:
            code |= error(f"appendix section appears before \\appendix: {stem}")
    return code


def check_figures(root: Path) -> int:
    wrappers = root / "paper/figures"
    assets = wrappers / "srcs"
    if not wrappers.is_dir() or not assets.is_dir():
        return 0
    code = 0
    wrapper_stems = {path.stem for path in wrappers.glob("*.tex")}
    asset_stems = {
        path.stem
        for path in assets.iterdir()
        if path.is_file() and path.suffix.lower() in ASSET_EXTENSIONS
    }
    for stem in sorted(wrapper_stems - asset_stems):
        code |= error(f"figure wrapper has no matching source asset: {stem}")
    for stem in sorted(asset_stems - wrapper_stems):
        code |= error(f"figure source asset has no matching wrapper: {stem}")
    return code


def check_dependency_boundary(root: Path) -> int:
    code = 0
    forbidden_tokens = (
        "../.agents",
        "../state",
        "../lab",
        "../scripts",
        "../../.agents",
        "../../state",
        "../../lab",
        "../../scripts",
    )
    for path in sorted((root / "paper").rglob("*.tex")):
        text = active_tex(path.read_text(encoding="utf-8"))
        for token in forbidden_tokens:
            if token in text:
                code |= error(
                    f"paper source depends on non-paper surface: {path.relative_to(root)} -> {token}"
                )
    return code


def check(root: Path) -> int:
    code = (
        check_required(root)
        | check_sections(root)
        | check_figures(root)
        | check_dependency_boundary(root)
    )
    if code == 0:
        print("OK paper_structure")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
