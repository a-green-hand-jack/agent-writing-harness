#!/usr/bin/env python3
"""Validate and ingest a Human-provided paper brief into a writing repository.

The brief is the Human-authored input contract (normally ``BRIEF.md`` in a
separate brief repo). ``validate`` checks that the brief has the required
sections and a valid operating mode. ``ingest`` runs inside an initialized
writing repository: it copies the brief to the repository root as ``BRIEF.md``
and fills only the decided ``PAPER.md`` fields that have a recognized target.
Missing or empty brief fields stay ``unresolved``; the tool never invents a
title, claim, result, citation, venue, author, approval, or release state.

``ingest`` refuses to run outside a Git repository, on a symlinked root, or in
the upstream template repository, and it fails closed when a decided brief
field has no recognized contract target. Other contracts (``EXPERIMENTS.md``,
``PUBLICATION.md``) are updated by their owner workflows; the brief stays
authoritative in ``BRIEF.md`` until then.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

BRIEF_RELATIVE = Path("BRIEF.md")
PAPER_RELATIVE = Path("PAPER.md")
COMMIT_MESSAGE = "chore: ingest paper brief into contracts"
MODE_RE = re.compile(r"^\s*[-*]\s*Mode\s*:\s*(.+)$", re.I)
ALLOWED_MODES = ("collaborative", "autonomous", "unresolved")
UPSTREAM_REPOSITORY = "a-green-hand-jack/ccfa-writing-paper-template"
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
    "Template usage note",
)
KEY_VALUE_RE = re.compile(r"^\s*[-*]\s*(.+?)\s*:\s*(.*)$")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|unresolved)\b", re.I)


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
    if result.returncode != 0:
        return False
    return not result.stdout.strip()


def has_symlink_component(path: Path) -> bool:
    """True when any component of the absolute path is a symlink."""
    if path.is_symlink():
        return True
    parent = path.parent
    while parent != parent.parent:
        if parent.is_symlink():
            return True
        parent = parent.parent
    return False


def origin_url(root: Path) -> str:
    result = run(root, "remote", "get-url", "origin", check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def repository_identity(url: str) -> str:
    value = url.strip()
    scp_match = re.fullmatch(r"[^/@\s]+@github\.com:(?P<path>.+)", value, flags=re.IGNORECASE)
    if scp_match:
        path = scp_match.group("path")
    else:
        path = value.split("://", 1)[-1]
        path = path.split("/", 1)[-1] if "github.com/" in value else path
    path = path.rstrip("/")
    if path.lower().endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return ""
    return "/".join(parts).lower()


def require_writing_repository(root: Path) -> None:
    """Refuse to write paper content outside an initialized writing repo."""
    if root.is_symlink() or not root.is_dir():
        raise BriefError(f"root is not a regular directory: {root}")
    toplevel = run(root, "rev-parse", "--show-toplevel", check=False)
    if toplevel.returncode != 0 or not toplevel.stdout.strip():
        raise BriefError(f"ingest requires a Git repository: {root}")
    try:
        if Path(toplevel.stdout.strip()).resolve() != root.resolve():
            raise BriefError(f"ingest root must be the Git top-level: {root}")
    except OSError:
        raise BriefError(f"ingest root must be the Git top-level: {root}")
    identity = repository_identity(origin_url(root))
    if identity == UPSTREAM_REPOSITORY:
        raise BriefError("refusing to ingest paper content into the upstream template repository")
    for relative in (PAPER_RELATIVE, BRIEF_RELATIVE):
        path = root / relative
        if path.is_symlink():
            raise BriefError(f"refusing to overwrite a symlinked destination: {relative}")


def find_brief(arg: str) -> tuple[Path, str]:
    candidate = Path(arg).expanduser()
    if has_symlink_component(candidate):
        raise BriefError(f"brief path must not traverse a symlink: {candidate}")
    if not candidate.exists():
        raise BriefError(f"brief path does not exist: {candidate}")
    if candidate.is_file():
        return candidate.resolve(), str(candidate)
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


def raw_mode(lines: list[str]) -> str:
    """Return the raw first token of the Mode line, or '' when absent."""
    for line in lines:
        match = MODE_RE.match(line)
        if not match:
            continue
        raw = match.group(1).strip()
        return re.split(r"\s|\(", raw, maxsplit=1)[0].strip("`()").lower()
    return ""


def brief_errors(sections: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    if missing:
        errors.append(f"missing required sections: {', '.join(missing)}")
    mode = raw_mode(section_values(sections, "Operating mode"))
    if not mode:
        errors.append("Operating mode does not declare a Mode")
    elif mode not in ALLOWED_MODES:
        errors.append("Mode must be collaborative, autonomous, or unresolved")
    return errors


def decided_lines(lines: list[str]) -> list[str]:
    """Return non-empty lines that are not TODO/TBD/unresolved placeholders."""
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if PLACEHOLDER_RE.search(stripped):
            continue
        result.append(stripped)
    return result


def decided_value(value: str) -> bool:
    return bool(value.strip()) and not PLACEHOLDER_RE.search(value)


def bullet(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith(("- ", "* ")):
        return stripped
    return f"- {stripped}"


def apply_block(paper: str, anchor: str, replacement: str) -> tuple[str, bool]:
    if anchor not in paper:
        return paper, False
    return paper.replace(anchor, replacement, 1), True


def fill_identity(paper: str, pairs: dict[str, str]) -> tuple[str, list[str], list[str]]:
    applied: list[str] = []
    failed: list[str] = []
    mappings = (
        ("working title", "- Working title: TODO Paper Title", "- Working title: {value}"),
        ("target venue", "- Target venue: unresolved (verify current official rules before submission work)", "- Target venue: {value}"),
        ("paper type", "- Paper type: unresolved", "- Paper type: {value}"),
        ("intended readers", "- Intended readers: TODO", "- Intended readers: {value}"),
        ("one-sentence positioning", "- One-sentence positioning: TODO", "- One-sentence positioning: {value}"),
    )
    for key, anchor, template in mappings:
        value = pairs.get(key, "").strip()
        if not decided_value(value):
            continue
        updated, ok = apply_block(paper, anchor, template.format(value=value))
        if ok:
            paper = updated
            applied.append(key)
        else:
            failed.append(key)
    return paper, applied, failed


def fill_thesis(paper: str, thesis_lines: list[str]) -> tuple[str, list[str], list[str]]:
    values = decided_lines(thesis_lines)
    if not values:
        return paper, [], []
    anchor = (
        "### Central thesis — unresolved\n\n"
        "TODO: state the single most important conclusion the paper wants readers to accept."
    )
    replacement = "### Central thesis\n\n" + "\n".join(values)
    updated, ok = apply_block(paper, anchor, replacement)
    return updated, ["central thesis"] if ok else [], ["central thesis"] if not ok else []


def fill_contributions(paper: str, contribution_lines: list[str]) -> tuple[str, list[str], list[str]]:
    values = decided_lines(contribution_lines)
    if not values:
        return paper, [], []
    anchor = (
        "No contributions have been approved yet. Add one entry per contribution that\n"
        "the current paper can defend; there is no required number of contributions.\n\n"
        "For each contribution, record whether it is central, supporting, or optional "
        "and whether it may be weakened or removed if the evidence changes."
    )
    updated, ok = apply_block(paper, anchor, "\n".join(values))
    return updated, ["contributions"] if ok else [], ["contributions"] if not ok else []


def fill_mode(paper: str, sections: dict[str, list[str]]) -> tuple[str, list[str], list[str]]:
    mode = raw_mode(section_values(sections, "Operating mode"))
    if mode not in ALLOWED_MODES:
        mode = "unresolved"
    anchor = "- Mode: unresolved (`collaborative` or `autonomous`)"
    updated, ok = apply_block(paper, anchor, f"- Mode: {mode}")
    return updated, ["operating mode"] if ok else [], ["operating mode"] if not ok else []


def fill_locked(paper: str, lines: list[str]) -> tuple[str, list[str], list[str]]:
    values = decided_lines(lines)
    if not values:
        return paper, [], []
    anchor = "Current locked items:\n\n- TODO"
    replacement = "Current locked items:\n\n" + "\n".join(bullet(value) for value in values)
    updated, ok = apply_block(paper, anchor, replacement)
    return updated, ["locked items"] if ok else [], ["locked items"] if not ok else []


def fill_evolve(paper: str, lines: list[str]) -> tuple[str, list[str], list[str]]:
    values = decided_lines(lines)
    if not values:
        return paper, [], []
    anchor = "free unless it changes claim strength or scientific meaning.\n- TODO"
    extra = "\n".join(bullet(value) for value in values)
    replacement = "free unless it changes claim strength or scientific meaning.\n" + extra
    updated, ok = apply_block(paper, anchor, replacement)
    return updated, ["evolving areas"] if ok else [], ["evolving areas"] if not ok else []


def fill_unresolved(paper: str, lines: list[str]) -> tuple[str, list[str], list[str]]:
    values = decided_lines(lines)
    if not values:
        return paper, [], []
    anchor = (
        "- TODO: title candidates\n"
        "- TODO: central thesis\n"
        "- TODO: target audience and venue fit"
    )
    extra = "\n".join(bullet(value) for value in values)
    replacement = anchor + "\n" + extra
    updated, ok = apply_block(paper, anchor, replacement)
    return updated, ["unresolved queue"] if ok else [], ["unresolved queue"] if not ok else []


def fill_style(paper: str, lines: list[str]) -> tuple[str, list[str], list[str]]:
    values = decided_lines(lines)
    if not values:
        return paper, [], []
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
    replacement = "### Current style\n\n" + "\n".join(bullet(value) for value in values)
    updated, ok = apply_block(paper, anchor, replacement)
    return updated, ["writing style"] if ok else [], ["writing style"] if not ok else []


def validate(root: Path, brief_arg: str) -> int:
    path, label = find_brief(brief_arg)
    sections = parse_brief(path.read_text(encoding="utf-8"))
    errors = brief_errors(sections)
    if errors:
        print(f"ERROR brief {label}: " + "; ".join(errors), file=sys.stderr)
        return 1
    mode = raw_mode(section_values(sections, "Operating mode"))
    print(f"OK paper_brief validated {label} ({mode})")
    return 0


def ingest(root: Path, brief_arg: str, commit: bool) -> int:
    path, label = find_brief(brief_arg)
    require_writing_repository(root)
    brief_text = path.read_text(encoding="utf-8")
    sections = parse_brief(brief_text)
    errors = brief_errors(sections)
    if errors:
        raise BriefError(f"brief {label}: " + "; ".join(errors))
    if commit and not worktree_clean(root):
        raise BriefError("ingest --commit requires a clean worktree")

    paper_path = root / PAPER_RELATIVE
    paper = paper_path.read_text(encoding="utf-8")
    applied: list[str] = []
    failed: list[str] = []

    identity = key_value_pairs(section_values(sections, "Paper identity"))
    paper, applied_fields, failed_fields = fill_identity(paper, identity)
    applied.extend(applied_fields)
    failed.extend(failed_fields)

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

    for fill, args in (
        (fill_thesis, (thesis_lines,)),
        (fill_contributions, (contribution_lines,)),
        (fill_mode, (sections,)),
        (fill_locked, (section_values(sections, "What must not change silently"),)),
        (fill_evolve, (section_values(sections, "What may evolve"),)),
        (fill_unresolved, (section_values(sections, "Unresolved"),)),
        (fill_style, (section_values(sections, "Writing style"),)),
    ):
        paper, applied_fields, failed_fields = fill(paper, *args)
        applied.extend(applied_fields)
        failed.extend(failed_fields)

    if failed:
        raise BriefError(
            "decided brief fields have no recognized contract target; nothing was written: "
            + ", ".join(sorted(set(failed)))
        )

    paper_path.write_text(paper, encoding="utf-8")
    brief_path = root / BRIEF_RELATIVE
    brief_path.write_text(brief_text, encoding="utf-8")

    filled = sorted(set(applied))
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
