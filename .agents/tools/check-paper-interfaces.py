#!/usr/bin/env python3
"""Validate the lightweight LaTeX paper-interface surface."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED = (
    "PaperTODO",
    "PaperTitle",
    "PaperAuthors",
    "MethodName",
    "CoreTerm",
    "StateSymbol",
    "MainResult",
    "MainResultUncertainty",
)
REQUIRED_CONSUMERS = tuple(name for name in REQUIRED if name != "PaperTODO")


def command_pattern(name: str) -> str:
    return rf"\\{re.escape(name)}(?![A-Za-z@])"


def definition_pattern(name: str) -> str:
    command = command_pattern(name)
    return rf"\\(?:newcommand|renewcommand|providecommand)\s*(?:\{{\s*{command}\s*\}}|{command})"


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def active_tex(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def check(root: Path) -> int:
    macros_path = root / "paper/macros.tex"
    if not macros_path.is_file():
        return error("missing paper/macros.tex")

    raw_macros = macros_path.read_text(encoding="utf-8")
    active_macros = active_tex(raw_macros)
    code = 0

    for name in REQUIRED:
        marker = rf"^\s*%\s*Interface:\s*{re.escape(name)}\s*$"
        if not re.search(marker, raw_macros, re.M):
            code |= error(f"paper/macros.tex missing Human-readable interface marker: {name}")
        if not re.search(definition_pattern(name), active_macros):
            code |= error(f"paper/macros.tex missing interface definition: \\{name}")

    if "generated/results-macros.tex" not in active_macros:
        code |= error("paper/macros.tex must expose the generated results-macros override hook")

    consumers: dict[str, list[str]] = {name: [] for name in REQUIRED_CONSUMERS}
    paper_root = root / "paper"
    for path in sorted(paper_root.rglob("*.tex")):
        relative = path.relative_to(root).as_posix()
        if relative in {"paper/macros.tex", "paper/generated/results-macros.tex"}:
            continue
        text = active_tex(path.read_text(encoding="utf-8"))
        for name in REQUIRED_CONSUMERS:
            if re.search(command_pattern(name), text):
                consumers[name].append(relative)

    for name, paths in consumers.items():
        if not paths:
            code |= error(f"stable interface has no active paper consumer: \\{name}")

    interface_doc = root / "PAPER_INTERFACES.md"
    if not interface_doc.is_file():
        code |= error("missing PAPER_INTERFACES.md")
    else:
        interface_text = interface_doc.read_text(encoding="utf-8")
        for name in REQUIRED:
            if not re.search(command_pattern(name), interface_text):
                code |= error(f"PAPER_INTERFACES.md does not document \\{name}")

    if code == 0:
        print("OK paper_interfaces")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
