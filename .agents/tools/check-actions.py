#!/usr/bin/env python3
"""Reject first-party GitHub Actions pinned to retired Node.js 20 majors."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MIN_MAJORS = {
    "actions/checkout": 6,
    "actions/setup-python": 6,
    "actions/upload-artifact": 7,
}
USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)(?:\s+#.*)?$")
REF_RE = re.compile(r"^v(\d+)$")


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def check(root: Path) -> int:
    workflows = root / ".github/workflows"
    if not workflows.is_dir():
        return error("missing .github/workflows directory")

    code = 0
    seen = False
    for workflow in sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml")):
        seen = True
        for number, raw in enumerate(
            workflow.read_text(encoding="utf-8").splitlines(), start=1
        ):
            match = USES_RE.match(raw)
            if not match:
                continue
            spec = match.group(1)
            if "@" not in spec:
                code |= error(f"{workflow.name}:{number} action use is missing a ref: {spec}")
                continue
            action, ref = spec.rsplit("@", 1)
            if action not in MIN_MAJORS:
                continue
            major = REF_RE.fullmatch(ref)
            if major is None:
                code |= error(
                    f"{workflow.name}:{number} {action} must use a major ref, found {ref}"
                )
                continue
            if int(major.group(1)) < MIN_MAJORS[action]:
                code |= error(
                    f"{workflow.name}:{number} {action}@{ref} is below required "
                    f"{action}@v{MIN_MAJORS[action]}"
                )

    if not seen:
        code |= error("no workflow files found")
    if code == 0:
        print("OK actions_node24")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
