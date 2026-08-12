#!/usr/bin/env python3
"""Validate tracked release records and keep generated artifacts out of Git."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _release_approval import valid_human_approval

RELEASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
FIELD_LABELS = (
    "Status",
    "Variant",
    "Profile",
    "Release ready",
    "Source fingerprint",
    "Manifest SHA-256",
    "Human approval",
)
REQUIRED_HEADINGS = ("## Artifacts", "## Notes")
ALLOWED_STATUSES = {"candidate", "approved", "published", "superseded", "withdrawn"}
ALLOWED_VARIANTS = {"draft", "anonymous", "camera-ready", "arxiv"}
ALLOWED_PROFILES = {"draft", "release"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def extract_fields(text: str, path: Path) -> tuple[dict[str, str], int]:
    fields: dict[str, str] = {}
    code = 0
    for label in FIELD_LABELS:
        prefix = f"- {label}:"
        lines = [line for line in text.splitlines() if line.startswith(prefix)]
        if not lines:
            code |= error(f"release record missing field {prefix} {path.name}")
            continue
        if len(lines) != 1:
            code |= error(f"release record has duplicate field {prefix} {path.name}")
            continue
        match = re.fullmatch(rf"{re.escape(prefix)}\s*`([^`]*)`\s*", lines[0])
        if not match or not match.group(1):
            code |= error(f"release record has invalid {label.lower()} value: {path.name}")
            continue
        fields[label] = match.group(1)
    return fields, code


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
        for heading in REQUIRED_HEADINGS:
            if not re.search(rf"^{re.escape(heading)}\s*$", text, re.M):
                code |= error(f"release record missing field {heading}: {path.name}")

        fields, field_code = extract_fields(text, path)
        code |= field_code
        status = fields.get("Status")
        if status is not None and status not in ALLOWED_STATUSES:
            code |= error(f"release record has invalid status: {path.name}")
        variant = fields.get("Variant")
        if variant is not None and variant not in ALLOWED_VARIANTS:
            code |= error(f"release record has invalid variant: {path.name}")
        profile = fields.get("Profile")
        if profile is not None and profile not in ALLOWED_PROFILES:
            code |= error(f"release record has invalid profile: {path.name}")
        release_ready = fields.get("Release ready")
        if release_ready is not None and release_ready not in {"true", "false"}:
            code |= error(f"release record has invalid release ready value: {path.name}")
        for label in ("Source fingerprint", "Manifest SHA-256"):
            value = fields.get(label)
            if value is not None and not SHA256_RE.fullmatch(value):
                code |= error(f"release record has invalid {label.lower()}: {path.name}")
        approval = fields.get("Human approval")
        if status in {"approved", "published"} and (
            approval is None or not valid_human_approval(approval)
        ):
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
