#!/usr/bin/env python3
"""Validate tracked release records and keep generated artifacts out of Git."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RELEASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
REQUIRED_FIELDS = (
    "- Status:",
    "- Variant:",
    "- Profile:",
    "- Release ready:",
    "- Source fingerprint:",
    "- Manifest SHA-256:",
    "- Human approval:",
    "## Artifacts",
    "## Notes",
)
ALLOWED_STATUSES = {"candidate", "approved", "published", "superseded", "withdrawn"}


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def extract_backtick_field(text: str, label: str) -> str | None:
    match = re.search(rf"^{re.escape(label)}\s*`([^`]*)`\s*$", text, re.M)
    return match.group(1) if match else None


def check(root: Path) -> int:
    code = 0
    releases = root / "releases"
    records = releases / "records"
    for path in (releases / "README.md", records / "README.md"):
        if not path.is_file():
            code |= error(f"missing release documentation: {path.relative_to(root)}")

    if not records.is_dir():
        return code | error("missing releases/records directory")

    for path in sorted(records.iterdir()):
        if path.name == "README.md":
            continue
        if path.is_dir() or path.suffix.lower() != ".md":
            code |= error(f"releases/records may contain Markdown records only: {path.name}")
            continue
        release_id = path.stem
        if not RELEASE_ID_RE.fullmatch(release_id):
            code |= error(f"invalid release record filename: {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith(f"# Release {release_id}\n"):
            code |= error(f"release record title does not match filename: {path.name}")
        for field in REQUIRED_FIELDS:
            if field not in text:
                code |= error(f"release record missing field {field}: {path.name}")
        status = extract_backtick_field(text, "- Status:")
        approval = extract_backtick_field(text, "- Human approval:")
        if status not in ALLOWED_STATUSES:
            code |= error(f"release record has invalid status: {path.name}")
        if status in {"approved", "published"} and (not approval or approval.lower() in {"pending", "todo"}):
            code |= error(f"approved/published release record lacks Human approval: {path.name}")

    legacy = root / "release"
    if legacy.exists():
        code |= error("legacy committed release/ tree must not exist")
    if code == 0:
        print("OK release_records")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
