#!/usr/bin/env python3
"""Lightweight checks for the Human–Agent paper contracts."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = {
    "PAPER.md": [
        "# Paper Contract",
        "## Paper identity",
        "## What readers should believe",
        "## What must not change silently",
        "## What may evolve",
        "## Unresolved",
        "## Story and structure",
        "## Writing style",
        "## Human decisions required",
    ],
    "EXPERIMENTS.md": [
        "# Experiment Contract",
        "## Experiment overview",
        "## Result interpretation",
        "## Relationship to the code repository",
    ],
    "PAPER_INTERFACES.md": [
        "# Paper Interfaces",
        "## Keep the implementation light",
        "## Interface categories",
        "## Flexible control",
        "## Change workflow",
        "## Draft and release",
    ],
    "PUBLICATION.md": [
        "# Publication Contract",
        "## Canonical paper",
        "## Active variants",
        "## Allowed differences",
        "## Must not diverge silently",
        "## Human review triggers",
        "## Build interface",
        "## Release instances",
    ],
}
CONTROL_WORDS = ("locked", "bounded", "free", "unresolved")
FOCUSED_SKILLS = (
    "control-review",
    "decision-packet",
    "section-writing",
    "style-alignment",
    "manuscript-consistency-review",
    "paper-interface-maintenance",
    "publication-planning",
    "release-review",
)
SKILL_CONTRACT_REQUIREMENTS = {
    "F7-CR-001-v1": "control-review",
    "F7-DP-001-v1": "decision-packet",
    "F7-SW-001-v1": "section-writing",
    "F7-MCR-001-v1": "manuscript-consistency-review",
    "F7-RR-001-v1": "reference-repair",
    "F7-TS-001-v1": "template-sync",
}
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|PLACEHOLDER)\b|\\PaperTODO\b", re.I)
UNRESOLVED_CURRENT_RE = re.compile(
    r"(?:^#{2,6} .*\bunresolved\b|^\s*[-*]\s+.*\bunresolved\b|^\s*\|.*\bunresolved\b.*\|)",
    re.I,
)


def fail(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def read_text(root: Path, relative: str) -> str | None:
    path = root / relative
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def strip_fenced_code(text: str) -> str:
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def check_draft(root: Path) -> int:
    code = 0
    for relative, headings in REQUIRED_HEADINGS.items():
        text = read_text(root, relative)
        if text is None:
            code |= fail(f"missing Human-facing contract: {relative}")
            continue
        for heading in headings:
            if heading not in text:
                code |= fail(f"{relative} missing required heading: {heading}")

    paper_text = read_text(root, "PAPER.md") or ""
    lowered = paper_text.lower()
    for word in CONTROL_WORDS:
        if word not in lowered:
            code |= fail(f"PAPER.md does not explain collaboration cue: {word}")

    agents_text = read_text(root, "AGENTS.md")
    if agents_text is None:
        code |= fail("missing thin Agent router: AGENTS.md")
    else:
        line_count = len(agents_text.splitlines())
        if line_count > 120:
            code |= fail(f"AGENTS.md is no longer a thin router ({line_count} lines > 120)")
        for pattern in (
            r"read (?:the )?entire repository",
            r"read all (?:files|policies|knowledge)",
            r"load all (?:files|policies|knowledge)",
        ):
            if re.search(pattern, agents_text, re.I):
                code |= fail(f"AGENTS.md contains broad context-loading instruction: {pattern}")

    orientation = read_text(root, ".agents/skills/paper-orientation/SKILL.md")
    if orientation is None:
        code |= fail("missing orientation skill: .agents/skills/paper-orientation/SKILL.md")
    elif "## Reading order" not in orientation or "## Context hygiene" not in orientation:
        code |= fail("paper-orientation skill must define reading order and context hygiene")

    for skill in FOCUSED_SKILLS:
        relative = f".agents/skills/{skill}/SKILL.md"
        text = read_text(root, relative)
        if text is None:
            code |= fail(f"missing focused Agent skill: {relative}")
            continue
        for heading in ("## Trigger", "## Minimum context", "## Procedure"):
            if heading not in text:
                code |= fail(f"{relative} missing heading: {heading}")

    # These declarations detect contract removal or drift. They do not prove that
    # an Agent or tool follows the adjacent imperative guidance at runtime.
    for requirement_id, skill in SKILL_CONTRACT_REQUIREMENTS.items():
        relative = f".agents/skills/{skill}/SKILL.md"
        text = read_text(root, relative) or ""
        declaration = f"<!-- paper-skill-contract: {requirement_id} -->"
        if declaration not in strip_fenced_code(text).splitlines():
            code |= fail(
                f"{relative} missing exact contract declaration: {declaration} "
                "(contract presence/drift check only)"
            )

    section_writing = read_text(root, ".agents/skills/section-writing/SKILL.md") or ""
    if "Do not invoke a reviewer persona" not in section_writing:
        code |= fail("section-writing must prohibit reviewer passes during drafting")

    consistency_review = read_text(
        root, ".agents/skills/manuscript-consistency-review/SKILL.md"
    ) or ""
    for marker in (
        "Human identifies a manuscript version as ready",
        "Report findings only",
        "Do not edit",
    ):
        if marker.lower() not in consistency_review.lower():
            code |= fail(
                "manuscript-consistency-review is missing required boundary: "
                f"{marker}"
            )

    runtime_ignore = read_text(root, ".agents/runtime/.gitignore")
    if runtime_ignore is None:
        code |= fail("missing .agents/runtime/.gitignore")
    elif "*" not in runtime_ignore or "!.gitignore" not in runtime_ignore:
        code |= fail(".agents/runtime/.gitignore must ignore runtime contents and retain itself")

    if code == 0:
        print("OK paper_contracts draft")
    return code


def current_contract_lines(text: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for number, line in enumerate(strip_fenced_code(text).splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "|", "### ", "#### ")):
            result.append((number, line))
    return result


def check_release(root: Path) -> int:
    code = check_draft(root)

    for relative in ("PAPER.md", "EXPERIMENTS.md", "PUBLICATION.md"):
        text = read_text(root, relative)
        if text is None:
            continue
        for number, line in current_contract_lines(text):
            if PLACEHOLDER_RE.search(line):
                code |= fail(f"{relative}:{number} contains a release placeholder: {line.strip()}")
            if UNRESOLVED_CURRENT_RE.search(line):
                code |= fail(f"{relative}:{number} remains unresolved for release: {line.strip()}")

    paper_root = root / "paper"
    if not paper_root.is_dir():
        code |= fail("missing paper/ source directory")
    else:
        for path in sorted(paper_root.rglob("*.tex")):
            text = path.read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), start=1):
                active = line.split("%", 1)[0]
                if PLACEHOLDER_RE.search(active):
                    code |= fail(
                        f"{path.relative_to(root)}:{number} contains an active release placeholder: {active.strip()}"
                    )

    if code == 0:
        print("OK paper_contracts release")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("draft", "release"), default="draft")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    return check_release(root) if args.profile == "release" else check_draft(root)


if __name__ == "__main__":
    sys.exit(main())
