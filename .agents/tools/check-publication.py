#!/usr/bin/env python3
"""Validate publication variants as small overlays on one canonical paper."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VARIANTS = {
    "draft": {
        "internal": "draft",
        "anonymous": "false",
        "acknowledgements": "false",
        "appendix": "true",
    },
    "anonymous": {
        "internal": "anonymous",
        "anonymous": "true",
        "acknowledgements": "false",
        "appendix": "true",
    },
    "camera-ready": {
        "internal": "camera_ready",
        "anonymous": "false",
        "acknowledgements": "true",
        "appendix": "true",
    },
    "arxiv": {
        "internal": "arxiv",
        "anonymous": "false",
        "acknowledgements": "true",
        "appendix": "true",
    },
}
PUBLICATION_HEADINGS = (
    "# Publication Contract",
    "## Canonical paper",
    "## Active variants",
    "## Allowed differences",
    "## Must not diverge silently",
    "## Human review triggers",
    "## Build interface",
    "## Release instances",
)


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def active_lines(path: Path) -> list[str]:
    return [
        line.split("%", 1)[0].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.split("%", 1)[0].strip()
    ]


def check(root: Path) -> int:
    code = 0
    publication = root / "PUBLICATION.md"
    if not publication.is_file():
        code |= error("missing PUBLICATION.md")
        publication_text = ""
    else:
        publication_text = publication.read_text(encoding="utf-8")
        for heading in PUBLICATION_HEADINGS:
            if heading not in publication_text:
                code |= error(f"PUBLICATION.md missing heading: {heading}")

    variants_root = root / "paper/variants"
    common = variants_root / "common.tex"
    if not common.is_file():
        code |= error("missing paper/variants/common.tex")
    else:
        common_text = common.read_text(encoding="utf-8")
        for switch in ("PaperAnonymous", "PaperAcknowledgements", "PaperFullAppendix"):
            if f"\\newif\\if{switch}" not in common_text:
                code |= error(f"variant common config missing switch: {switch}")

    allowed_tex = {"common.tex"}
    for public_name, spec in VARIANTS.items():
        internal = spec["internal"]
        driver = variants_root / f"{internal}.tex"
        config = variants_root / "config" / f"{internal}.tex"
        allowed_tex.add(f"{internal}.tex")
        allowed_tex.add(f"config/{internal}.tex")

        if f"`{public_name}`" not in publication_text:
            code |= error(f"PUBLICATION.md does not list variant: {public_name}")

        if not driver.is_file():
            code |= error(f"missing variant driver: {driver.relative_to(root)}")
        else:
            lines = active_lines(driver)
            expected = [f"\\def\\PaperVariant{{{internal}}}", "\\input{main.tex}"]
            if lines != expected:
                code |= error(
                    f"variant driver must only select the variant and input main.tex: {driver.relative_to(root)}"
                )

        if not config.is_file():
            code |= error(f"missing variant config: {config.relative_to(root)}")
        else:
            text = config.read_text(encoding="utf-8")
            expected_switches = {
                f"\\PaperAnonymous{spec['anonymous']}",
                f"\\PaperAcknowledgements{spec['acknowledgements']}",
                f"\\PaperFullAppendix{spec['appendix']}",
            }
            for switch in expected_switches:
                if switch not in text:
                    code |= error(f"{config.relative_to(root)} missing expected switch: {switch}")
            if "\\input{sections/" in text or "\\include{sections/" in text:
                code |= error(f"variant config must not own canonical section content: {config.relative_to(root)}")

    if variants_root.is_dir():
        for path in variants_root.rglob("*.tex"):
            relative = path.relative_to(variants_root).as_posix()
            if relative not in allowed_tex:
                code |= error(f"unexpected TeX file in variants; do not copy paper content: {relative}")

    main_path = root / "paper/main.tex"
    if not main_path.is_file():
        code |= error("missing paper/main.tex")
    else:
        main = main_path.read_text(encoding="utf-8")
        required_fragments = (
            "\\providecommand{\\PaperVariant}{draft}",
            "\\input{variants/common}",
            "\\input{variants/config/\\PaperVariant}",
            "\\ifPaperAnonymous",
            "\\ifPaperAcknowledgements",
            "\\ifPaperFullAppendix",
        )
        for fragment in required_fragments:
            if fragment not in main:
                code |= error(f"paper/main.tex missing publication variant hook: {fragment}")

    makefile = root / "Makefile"
    if not makefile.is_file():
        code |= error("missing Makefile")
    else:
        make_text = makefile.read_text(encoding="utf-8")
        for public_name in VARIANTS:
            if public_name not in make_text:
                code |= error(f"Makefile does not declare supported variant: {public_name}")
        if "VARIANT ?= draft" not in make_text:
            code |= error("Makefile must default VARIANT to draft")

    if code == 0:
        print("OK publication_variants")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
