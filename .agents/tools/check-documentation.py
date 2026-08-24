#!/usr/bin/env python3
"""Reject known-stale documentation and verify configurable repository facts."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

CONFIG_RELATIVE = Path(".agents/documentation-consistency.json")
DEFAULT_STALE_PATTERNS: dict[str, str] = {
    r"\bICLR[ _-]?2026\b": "obsolete target venue ICLR 2026",
    r"lab/artifacts/": "removed lab artifact registry",
    r"state/float-placement-map\.yaml": "removed float-placement map",
    r"scripts/check-figures-tables\.py": "removed figure/table checker",
    r"scripts/export-venue-template\.sh": "removed venue-export script",
    r"NOT used by paper/main\.tex": "obsolete venue-compatibility usage note",
}
LOCAL_AGENT_REFERENCE_RE = re.compile(
    r"(?P<path>\.agents/(?:tools|skills|vendor|knowledge|dependencies)/[A-Za-z0-9_.\-/]+)"
)
# On-demand artifacts: like `.agents/runtime/`, these paths are created only
# when the Human activates the corresponding workflow (for example Writing DNA)
# and may not exist in a fresh template checkout. References to them are valid
# forward-references, not stale paths, so they are not existence-checked.
ON_DEMAND_REFERENCES = frozenset(
    {
        ".agents/knowledge/writing/paper-writing-dna.md",
        # Template-development-only paths: they live on the template's
        # template-dev branch and intentionally never exist in a paper-facing
        # repo. Documentation may reference them to explain the surface split.
        ".agents/tools/check-actions.py",
        ".agents/tools/check-skills.py",
        ".agents/tools/check-vendored-skills.py",
        ".agents/tools/check-vendored-skill-evals.py",
        ".agents/dependencies/vendored-skills",
        ".agents/dependencies/vendored-skills/provenance.json",
    }
)


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def read_config(root: Path) -> dict[str, Any] | None:
    path = root / CONFIG_RELATIVE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid documentation consistency config: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "paper-documentation-consistency-v1":
        raise ValueError("unsupported documentation consistency configuration")
    required_facts = data.get("required_facts")
    if not isinstance(required_facts, dict):
        raise ValueError("documentation consistency config requires required_facts object")
    result: dict[str, list[str]] = {}
    for relative, facts in required_facts.items():
        if not isinstance(relative, str) or not relative:
            raise ValueError("required_facts keys must be non-empty relative paths")
        path_value = PurePosixPath(relative)
        if path_value.is_absolute() or ".." in path_value.parts:
            raise ValueError(f"unsafe required_facts path: {relative}")
        if not isinstance(facts, list) or not all(
            isinstance(fact, str) and fact.strip() for fact in facts
        ):
            raise ValueError(f"required_facts.{relative} must be a non-empty string list")
        result[relative] = [fact.strip() for fact in facts]

    stale_patterns = data.get("stale_patterns", {})
    if not isinstance(stale_patterns, dict) or not all(
        isinstance(pattern, str) and isinstance(description, str)
        for pattern, description in stale_patterns.items()
    ):
        raise ValueError("stale_patterns must be an object mapping patterns to descriptions")
    data["_required_facts"] = result
    return data


def documentation_files(root: Path) -> list[Path]:
    return sorted(
        path
        for suffix in ("*.md", "*.tex", "*.sty")
        for path in root.rglob(suffix)
        if ".git" not in path.parts
        and "dist" not in path.parts
        and not path.relative_to(root).as_posix().startswith(".agents/runtime/")
        and path.relative_to(root).as_posix() != ".agents/vendor"
        and not path.relative_to(root).as_posix().startswith(".agents/vendor/")
    )


def tracked_runtime_files(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", ".agents/runtime"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def check(root: Path) -> int:
    code = 0
    documents = documentation_files(root)
    for relative in tracked_runtime_files(root):
        if relative != ".agents/runtime/.gitignore":
            code |= error(f"runtime output must not be tracked: {relative}")

    try:
        config = read_config(root)
    except ValueError as exc:
        code |= error(str(exc))
        config = None

    if config is None:
        stale_patterns = DEFAULT_STALE_PATTERNS
    else:
        stale_patterns = config.get("stale_patterns", {})

    for path in documents:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        for pattern, description in stale_patterns.items():
            try:
                compiled = re.compile(pattern, flags=re.IGNORECASE)
            except re.error:
                code |= error(f"invalid stale_patterns expression: {pattern}")
                continue
            if compiled.search(text):
                code |= error(f"{relative} contains {description}")

        for match in LOCAL_AGENT_REFERENCE_RE.finditer(text):
            reference = match.group("path").rstrip("./")
            if reference in ON_DEMAND_REFERENCES:
                continue
            if not (root / reference).exists():
                code |= error(f"{relative} references missing repository path: {reference}")

    required_facts = config.get("_required_facts") if config is not None else None

    if required_facts is not None:
        for relative, facts in required_facts.items():
            path = root / relative
            if not path.is_file():
                code |= error(f"missing documentation contract: {relative}")
                continue
            normalized = " ".join(path.read_text(encoding="utf-8").split())
            for fact in facts:
                if " ".join(fact.split()) not in normalized:
                    code |= error(f"{relative} is missing current fact: {fact}")

    if code == 0:
        if required_facts is None:
            print("OK documentation_consistency unconfigured")
        else:
            print("OK documentation_consistency")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
