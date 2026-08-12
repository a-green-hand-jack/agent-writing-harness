#!/usr/bin/env python3
"""Validate repo-local skill discovery and reject stale adapter references."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
STALE_REFERENCE = ".agent/capabilities/registry.yaml"


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return None, "missing YAML frontmatter"
    fields: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            return None, f"invalid YAML frontmatter line: {raw_line}"
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    return fields, None


def check(root: Path) -> int:
    skills_root = root / ".agents/skills"
    if not skills_root.is_dir():
        return error("missing .agents/skills directory")

    code = 0
    seen_names: dict[str, str] = {}
    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        relative = skill_dir.relative_to(root).as_posix()
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            code |= error(f"missing {relative}/SKILL.md")
            continue
        fields, parse_error = parse_frontmatter(skill_path.read_text(encoding="utf-8"))
        if parse_error is not None:
            code |= error(f"{relative}/SKILL.md {parse_error}")
            continue
        if fields is None:
            code |= error(f"{relative}/SKILL.md missing YAML frontmatter")
            continue
        name = fields.get("name", "")
        description = fields.get("description", "")
        if not name:
            code |= error(f"{relative}/SKILL.md frontmatter requires non-empty name")
        if not description:
            code |= error(f"{relative}/SKILL.md frontmatter requires non-empty description")
        if name != skill_dir.name:
            code |= error(
                f"{relative}/SKILL.md frontmatter name {name!r} does not match directory {skill_dir.name!r}"
            )
        if name in seen_names:
            code |= error(f"duplicate skill name {name!r}: {seen_names[name]} and {relative}")
        else:
            seen_names[name] = relative

    router = root / "AGENTS.md"
    if not router.is_file():
        code |= error("missing root AGENTS.md router")
    else:
        router_text = router.read_text(encoding="utf-8")
        for name in sorted(seen_names):
            marker = f".agents/skills/{name}/SKILL.md"
            if marker not in router_text:
                code |= error(f"root AGENTS.md does not route skill: {name}")

    markdown_paths = [root / "AGENTS.md"]
    if (root / ".agents/AGENTS.md").is_file():
        markdown_paths.append(root / ".agents/AGENTS.md")
    markdown_paths.extend(sorted((root / ".agents").rglob("*.md")))
    for path in markdown_paths:
        if path.is_file() and STALE_REFERENCE in path.read_text(encoding="utf-8"):
            code |= error(f"stale adapter reference in {path.relative_to(root)}: {STALE_REFERENCE}")

    if code == 0:
        print("OK skills")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
