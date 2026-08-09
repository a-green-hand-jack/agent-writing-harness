#!/usr/bin/env python3
"""Initialize a downstream paper repository by removing template governance residue."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

INIT_STATE_RELATIVE = Path(".agents/init-state.json")
DOCUMENTATION_CONFIG_RELATIVE = Path(".agents/documentation-consistency.json")
OVERLEAF_CONFIG_RELATIVE = Path(".agents/overleaf-sync.json")
COMMIT_MESSAGE = "chore: initialize paper repository and remove template governance residue"
UPSTREAM_ORIGIN_MARKERS = (
    "a-green-hand-jack/ccfa-writing-paper-template",
)
TEMPLATE_OVERLEAF_PROJECT = "6a71e37eeb498fef8922f370"
AGENTS_PROTECTED_BRANCHES_LINE = (
    "- Never propose or perform deletion of the protected case branches "
    "(`case/arxiv-2505-22954`, `case/arxiv-2604-01658`, `case/arxiv-2605-03042`), "
    "their case issues (#23, #24, #30), or the standing verification trackers "
    "(#21, #31); do not include them in routine cleanup or deletion reports.\n"
)
DECISION_UPSTREAM_HEADING = "## DEC-0014: Case branches and verification trackers are protected evidence"
DECISION_DOWNSTREAM_HEADING = "## DEC-0014: Downstream paper initialization"
DECISION_RECORDING_HEADING = "## Recording future decisions"
DOWNSTREAM_DECISION = (
    "## DEC-0014: Downstream paper initialization\n"
    "\n"
    "Decision: this repository is a downstream paper initialized from the template. "
    "Upstream template-specific governance IDs were removed during initialization. "
    "This repository owns its own protected case branches and verification issues.\n"
    "\n"
)


class InitError(RuntimeError):
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
        raise InitError(
            f"git {' '.join(args)} failed: {result.stdout.strip()} {result.stderr.strip()}"
        )
    return result


def origin_url(root: Path) -> str:
    result = run(root, "remote", "get-url", "origin", check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def is_upstream_template(root: Path) -> bool:
    url = origin_url(root)
    return any(marker in url for marker in UPSTREAM_ORIGIN_MARKERS)


def init_state(root: Path) -> Path:
    return root / INIT_STATE_RELATIVE


def valid_init_state(root: Path) -> bool:
    path = init_state(root)
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    if (
        data.get("schema_version") != "paper-init-v1"
        or data.get("mode") != "downstream"
        or data.get("template_cleanup") is not True
    ):
        return False
    initialized_at = data.get("initialized_at")
    if not isinstance(initialized_at, str):
        return False
    try:
        timestamp = dt.datetime.fromisoformat(initialized_at)
    except ValueError:
        return False
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return False
    git_head = data.get("git_head")
    if not isinstance(git_head, str) or not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", git_head):
        return False
    return run(root, "merge-base", "--is-ancestor", git_head, "HEAD", check=False).returncode == 0


def worktree_clean(root: Path) -> bool:
    result = run(root, "status", "--porcelain=v1", "--untracked-files=all", check=False)
    return not result.stdout.strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def status(root: Path) -> int:
    marker_exists = init_state(root).is_file()
    if valid_init_state(root):
        print("OK paper_init initialized")
        return 0
    if not marker_exists and is_upstream_template(root):
        print("OK paper_init upstream_template")
        return 0
    if marker_exists:
        print(
            "UNINITIALIZED paper_init invalid marker; run "
            "`python3 .agents/tools/paper-init.py clean --commit`"
        )
        return 1
    print(
        "UNINITIALIZED paper_init downstream; run "
        "`python3 .agents/tools/paper-init.py clean --commit`"
    )
    return 1


def clean_agents(root: Path, changes: list[str]) -> None:
    path = root / "AGENTS.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if AGENTS_PROTECTED_BRANCHES_LINE in text:
        text = text.replace(AGENTS_PROTECTED_BRANCHES_LINE, "")
        write_text(path, text)
        changes.append("AGENTS.md")


def clean_decisions(root: Path, changes: list[str]) -> None:
    path = root / "DECISIONS.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if DECISION_DOWNSTREAM_HEADING in text:
        return
    start = text.find(DECISION_UPSTREAM_HEADING)
    end = text.find(DECISION_RECORDING_HEADING, start)
    if start != -1 and end != -1:
        text = text[:start] + DOWNSTREAM_DECISION + text[end:]
        write_text(path, text)
        changes.append("DECISIONS.md")


def reset_documentation_config(root: Path, changes: list[str]) -> None:
    path = root / DOCUMENTATION_CONFIG_RELATIVE
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(data, dict) or data.get("schema_version") != "paper-documentation-consistency-v1":
        return
    if data.get("required_facts") == {}:
        return
    data["required_facts"] = {}
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    changes.append(DOCUMENTATION_CONFIG_RELATIVE.as_posix())


def delete_template_overleaf_config(root: Path, changes: list[str]) -> None:
    path = root / OVERLEAF_CONFIG_RELATIVE
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if TEMPLATE_OVERLEAF_PROJECT not in text:
        return
    path.unlink()
    changes.append(OVERLEAF_CONFIG_RELATIVE.as_posix())


def write_init_state(root: Path, changes: list[str]) -> None:
    data: dict[str, Any] = {
        "schema_version": "paper-init-v1",
        "initialized_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "downstream",
        "template_cleanup": True,
        "git_head": run(root, "rev-parse", "HEAD").stdout.strip(),
    }
    path = init_state(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    changes.append(INIT_STATE_RELATIVE.as_posix())


def clean(root: Path, commit: bool, downstream: bool) -> int:
    marker_exists = init_state(root).is_file()
    if valid_init_state(root):
        print("OK paper_init already_initialized")
        return 0
    if not downstream and is_upstream_template(root):
        if marker_exists:
            raise InitError(
                "refusing to clean upstream template with an invalid initialization marker; "
                "use --downstream only after confirming this repository is a downstream paper"
            )
        print("OK paper_init upstream_template")
        return 0
    if commit and not worktree_clean(root):
        raise InitError("clean --commit requires a clean worktree")

    changes: list[str] = []
    clean_agents(root, changes)
    clean_decisions(root, changes)
    reset_documentation_config(root, changes)
    delete_template_overleaf_config(root, changes)
    write_init_state(root, changes)

    if not changes:
        print("OK paper_init clean_no_changes")
        return 0

    print("OK paper_init cleaned " + ", ".join(changes))
    if commit:
        run(root, "add", "-A")
        run(root, "commit", "-m", COMMIT_MESSAGE)
        print("OK paper_init committed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    clean_parser = subparsers.add_parser("clean")
    clean_parser.add_argument("--commit", action="store_true")
    clean_parser.add_argument(
        "--downstream",
        action="store_true",
        help="initialize as a downstream paper even when origin matches the upstream template",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.expanduser().resolve()
    try:
        if args.command == "status":
            return status(root)
        if args.command == "clean":
            return clean(root, args.commit, args.downstream)
        raise InitError(f"unknown command: {args.command}")
    except InitError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
