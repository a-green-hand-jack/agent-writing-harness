#!/usr/bin/env python3
"""Validate and ingest a Human-provided paper brief into a writing repository.

The brief is the Human-authored input contract (normally ``BRIEF.md`` in a
separate brief repo). ``validate`` checks that the brief has the required
sections; ``ingest`` copies the brief into the writing repository root as
``BRIEF.md`` and fills only the paper contracts that map to decided brief
fields. Missing or empty brief fields stay ``unresolved``; the tool never
invents a title, claim, result, citation, venue, or approval state.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

BRIEF_RELATIVE = Path("BRIEF.md")
PAPER_RELATIVE = Path("PAPER.md")
COMMIT_MESSAGE = "chore: ingest paper brief into contracts"
MODE_RE = re.compile(r"^\s*[-*]\s*Mode\s*:\s*(.+)$", re.I)
ALLOWED_MODES = ("collaborative", "autonomous", "unresolved")


def raw_mode(lines: list[str]) -> str:
    """Return the raw first token of the Mode line, or '' when absent."""
    for line in lines:
        match = MODE_RE.match(line)
        if not match:
            continue
        raw = match.group(1).strip()
        return re.split(r"\s|\(", raw, maxsplit=1)[0].strip("`()").lower()
    return ""
REQUIRED_SECTIONS = (
    "Paper identity",
    "What readers should believe",
    "Operating mode",
    "Evidence and materials",
    "What must not change silently",
    "What may evolve",
    "Target and delivery",
    "Authors and identity",
    "Constraints",
    "First deliverable",
)
KEY_VALUE_RE = re.compile(r"^\s*[-*]\s*(.+?)\s*:\s*(.*)$")


class BriefError(RuntimeError):
    pass


def run(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise BriefError(
            f"git {' '.join(args)} failed: {result.stdout.strip()} {result.stderr.strip()}"
        )
    return result


def worktree_clean(root: Path) -> bool:
    result = run(root, "status", "--porcelain=v1", "--untracked-files=all", check=False)
    return not result.stdout.strip()


def find_brief(arg: str) -> tuple[Path, str]:
    candidate = Path(arg).expanduser()
    if not candidate.exists():
        raise BriefError(f"brief path does not exist: {candidate}")
    candidate = candidate.resolve()
    if candidate.is_file():
        return candidate, str(candidate)
    if candidate.is_dir():
        for relative in (BRIEF_RELATIVE, Path("brief") / "BRIEF.md"):
            path = candidate / relative
            if path.is_file() and not path.is_symlink():
                return path.resolve(), str(path)
        raise BriefError(
            f"brief directory contains neither {BRIEF_RELATIVE} nor brief/{BRIEF_RELATIVE}: "
            f"{candidate}"
        )
    raise BriefError(f"brief path is not a regular file or directory: {candidate}")


def parse_brief(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        sections[current].append(line)
    return sections


def section_values(sections: dict[str, list[str]], name: str) -> list[str]:
    return sections.get(name, [])


def key_value_pairs(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines:
        match = KEY_VALUE_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        result[key] = value
    return result


def non_todo_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if re.search(r"\bTODO\b", stripped, re.I):
            continue
        result.append(stripped)
    return result


def bullet(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith(("- ", "* ")):
        return stripped
    return f"- {stripped}"


def validate(root: Path, brief_arg: str) -> int:
    path, label = find_brief(brief_arg)
    sections = parse_brief(path.read_text(encoding="utf-8"))
    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    if missing:
        print(
            f"ERROR brief {label} missing required sections: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1
    mode = raw_mode(section_values(sections, "Operating mode"))
    if not mode:
        print(f"ERROR brief {label} Operating mode does not declare a Mode", file=sys.stderr)
        return 1
    if mode not in ALLOWED_MODES:
        print(
            f"ERROR brief {label} Mode must be collaborative, autonomous, or unresolved",
            file=sys.stderr,
        )
        return 1
    print(f"OK paper_brief validated {label} ({mode})")
    return 0


def replace_block(text: str, anchor: str, replacement: str) -> tuple[str, bool]:
    if anchor not in text:
        return text, False
    return text.replace(anchor, replacement, 1), True


def fill_identity(paper: str, pairs: dict[str, str]) -> tuple[str, list[str]]:
    changes: list[str] = []
    mappings = (
        ("working title", "- Working title: TODO Paper Title", "- Working title: {value}"),
        ("target venue", "- Target venue: unresolved (verify current official rules before submission work)", "- Target venue: {value}"),
        ("paper type", "- Paper type: unresolved", "- Paper type: {value}"),
        ("intended readers", "- Intended readers: TODO", "- Intended readers: {value}"),
        ("one-sentence positioning", "- One-sentence positioning: TODO", "- One-sentence positioning: {value}"),
    )
    for key, anchor, template in mappings:
        value = pairs.get(key, "").strip()
        if not value or re.search(r"\bTODO\b", value, re.I):
            continue
        if anchor in paper:
            paper = paper.replace(anchor, template.format(value=value), 1)
            changes.append(key)
    return paper, changes


def fill_thesis(paper: str, thesis_lines: list[str]) -> tuple[str, list[str]]:
    values = non_todo_lines(thesis_lines)
    if not values:
        return paper, []
    anchor = (
        "### Central thesis — unresolved\n\n"
        "TODO: state the single most important conclusion the paper wants readers to accept."
    )
    replacement = "### Central thesis\n\n" + "\n".join(values)
    updated, applied = replace_block(paper, anchor, replacement)
    return updated, ["central thesis"] if applied else []


def fill_contributions(paper: str, contribution_lines: list[str]) -> tuple[str, list[str]]:
    values = non_todo_lines(contribution_lines)
    if not values:
        return paper, []
    anchor = (
        "No contributions have been approved yet. Add one entry per contribution that\n"
        "the current paper can defend; there is no required number of contributions.\n\n"
        "For each contribution, record whether it is central, supporting, or optional "
        "and whether it may be weakened or removed if the evidence changes."
    )
    if anchor not in paper:
        return paper, []
    replacement = "\n".join(values)
    updated = paper.replace(anchor, replacement, 1)
    return updated, ["contributions"]


def fill_mode(paper: str, sections: dict[str, list[str]]) -> tuple[str, list[str]]:
    mode = raw_mode(section_values(sections, "Operating mode"))
    if mode not in ALLOWED_MODES:
        mode = "unresolved"
    anchor = "- Mode: unresolved (`collaborative` or `autonomous`)"
    if anchor not in paper:
        return paper, []
    paper = paper.replace(anchor, f"- Mode: {mode}", 1)
    return paper, ["operating mode"]


def fill_locked(paper: str, lines: list[str]) -> tuple[str, list[str]]:
    values = non_todo_lines(lines)
    if not values:
        return paper, []
    anchor = "Current locked items:\n\n- TODO"
    if anchor not in paper:
        return paper, []
    replacement = "Current locked items:\n\n" + "\n".join(bullet(value) for value in values)
    return paper.replace(anchor, replacement, 1), ["locked items"]


def fill_evolve(paper: str, lines: list[str]) -> tuple[str, list[str]]:
    values = non_todo_lines(lines)
    if not values:
        return paper, []
    anchor = "free unless it changes claim strength or scientific meaning.\n- TODO"
    if anchor not in paper:
        return paper, []
    extra = "\n".join(bullet(value) for value in values)
    replacement = "free unless it changes claim strength or scientific meaning.\n" + extra
    return paper.replace(anchor, replacement, 1), ["evolving areas"]


def fill_unresolved(paper: str, lines: list[str]) -> tuple[str, list[str]]:
    values = non_todo_lines(lines)
    if not values:
        return paper, []
    anchor = (
        "- TODO: title candidates\n"
        "- TODO: central thesis\n"
        "- TODO: target audience and venue fit"
    )
    if anchor not in paper:
        return paper, []
    extra = "\n".join(bullet(value) for value in values)
    replacement = anchor + "\n" + extra
    return paper.replace(anchor, replacement, 1), ["unresolved queue"]


def fill_style(paper: str, lines: list[str]) -> tuple[str, list[str]]:
    values = non_todo_lines(lines)
    if not values:
        return paper, []
    anchor = (
        "### Current style — unresolved\n\n"
        "- Positioning and voice: TODO\n"
        "- Explanation density: TODO\n"
        "- Claim-strength discipline: TODO\n"
        "- Preferred paragraph moves: TODO\n"
        "- Terms or expressions to avoid: TODO\n"
        "- Venue-specific overlay: TODO; load only when the target venue is active "
        "and current rules have been verified."
    )
    if anchor not in paper:
        return paper, []
    replacement = "### Current style\n\n" + "\n".join(bullet(value) for value in values)
    return paper.replace(anchor, replacement, 1), ["writing style"]


def ingest(root: Path, brief_arg: str, commit: bool) -> int:
    path, label = find_brief(brief_arg)
    if not (root / PAPER_RELATIVE).is_file():
        raise BriefError(f"writing repository has no {PAPER_RELATIVE}: {root}")
    brief_text = path.read_text(encoding="utf-8")
    sections = parse_brief(brief_text)
    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    if missing:
        raise BriefError(
            f"brief {label} missing required sections: {', '.join(missing)}"
        )
    if commit and not worktree_clean(root):
        raise BriefError("ingest --commit requires a clean worktree")

    paper_path = root / PAPER_RELATIVE
    paper = paper_path.read_text(encoding="utf-8")
    changes: list[str] = []

    identity = key_value_pairs(section_values(sections, "Paper identity"))
    paper, applied = fill_identity(paper, identity)
    changes.extend(applied)

    believed = sections.get("What readers should believe", [])
    thesis_lines: list[str] = []
    contribution_lines: list[str] = []
    subsection: str | None = None
    for line in believed:
        stripped = line.strip()
        if stripped.startswith("### Central thesis"):
            subsection = "thesis"
            continue
        if stripped.startswith("### Contributions"):
            subsection = "contributions"
            continue
        if subsection == "thesis":
            thesis_lines.append(line)
        elif subsection == "contributions":
            contribution_lines.append(line)

    paper, applied = fill_thesis(paper, thesis_lines)
    changes.extend(applied)
    paper, applied = fill_contributions(paper, contribution_lines)
    changes.extend(applied)
    paper, applied = fill_mode(paper, sections)
    changes.extend(applied)
    paper, applied = fill_locked(paper, section_values(sections, "What must not change silently"))
    changes.extend(applied)
    paper, applied = fill_evolve(paper, section_values(sections, "What may evolve"))
    changes.extend(applied)
    paper, applied = fill_unresolved(paper, section_values(sections, "Unresolved"))
    changes.extend(applied)
    paper, applied = fill_style(paper, section_values(sections, "Writing style"))
    changes.extend(applied)

    paper_path.write_text(paper, encoding="utf-8")
    brief_path = root / BRIEF_RELATIVE
    brief_path.write_text(brief_text, encoding="utf-8")

    filled = sorted(set(changes))
    print(f"OK paper_brief ingested {label} into " + (", ".join(filled) if filled else "contracts (no decided fields)"))
    if commit:
        run(root, "add", "--", BRIEF_RELATIVE.as_posix(), PAPER_RELATIVE.as_posix())
        run(root, "commit", "-m", COMMIT_MESSAGE)
        print("OK paper_brief committed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--brief", required=True, help="brief file, brief repo directory, or path to BRIEF.md")
    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--brief", required=True, help="brief file, brief repo directory, or path to BRIEF.md")
    ingest_parser.add_argument("--commit", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.expanduser().resolve()
    try:
        if args.command == "validate":
            return validate(root, args.brief)
        if args.command == "ingest":
            return ingest(root, args.brief, args.commit)
        raise BriefError(f"unknown command: {args.command}")
    except BriefError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
