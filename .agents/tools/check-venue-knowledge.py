#!/usr/bin/env python3
"""Validate venue planning knowledge files and report UNVERIFIED states."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

VENUES_RELATIVE = Path(".agents/knowledge/venues")
IGNORED = {"README.md", "_template.md"}
REQUIRED_HEADINGS = (
    "## Identity",
    "## Official sources",
    "## Last checked",
    "## Timeline",
    "## Page limits",
    "## Submission rules",
    "## Unknowns and uncertainties",
)
REQUIRED_FIELDS = (
    "last_checked:",
    "submission_portal:",
    "author_kit:",
    "main_text:",
    "page_budget_status:",
)


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def field_value(text: str, field: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"- {field}:") or stripped.startswith(f"{field}:"):
            return stripped.split(":", 1)[1].strip()
    return ""


def check_venue(root: Path, relative: str, strict: bool) -> int:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    code = 0
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            code |= error(f"{relative} missing heading: {heading}")
    for field in REQUIRED_FIELDS:
        if field not in text:
            code |= error(f"{relative} missing field: {field}")
    if code:
        return code

    unverified: list[str] = []
    if field_value(text, "last_checked").upper() in {"", "UNKNOWN"}:
        unverified.append("freshness")
    if field_value(text, "submission_portal").upper() in {"", "UNKNOWN"}:
        unverified.append("submission_portal")
    if field_value(text, "author_kit").upper() in {"", "UNKNOWN"}:
        unverified.append("author_kit")
    if field_value(text, "main_text").upper() in {"", "UNKNOWN"}:
        unverified.append("page_budget")
    if field_value(text, "page_budget_status").upper() in {"", "UNKNOWN"}:
        unverified.append("page_budget_status")

    if unverified:
        print(f"UNVERIFIED venue_knowledge {relative}: {', '.join(sorted(set(unverified)))}")
        if strict:
            code |= 1
    else:
        print(f"OK venue_knowledge {relative}")
    return code


def check(root: Path, strict: bool) -> int:
    venues = root / VENUES_RELATIVE
    if not venues.is_dir():
        print("OK venue_knowledge unconfigured")
        return 0
    files = sorted(
        path.relative_to(root).as_posix()
        for path in venues.glob("*.md")
        if path.name not in IGNORED
    )
    if not files:
        print("OK venue_knowledge unconfigured")
        return 0
    code = 0
    for relative in files:
        code |= check_venue(root, relative, strict)
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    return check(args.root.expanduser().resolve(), args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
