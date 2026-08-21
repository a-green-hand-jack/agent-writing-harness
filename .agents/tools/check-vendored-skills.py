#!/usr/bin/env python3
"""Validate the immutable vendored third-party skill snapshots.

Checks the vendor tree against `.agents/dependencies/vendored-skills/provenance.json`:

- every manifest file exists with the exact recorded SHA-256;
- no unrecorded files, symlinks, nested Git metadata, or bytecode caches;
- every wrapper skill under `.agents/skills/` points at an existing vendor file;
- the excluded-content boundary holds (no paper PDFs or demo images shipped);
- each source has its license file present.

The vendor tree must never be edited locally; upstream updates flow through
template-sync after review. This tool is standard-library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

VENDOR_RELATIVE = Path(".agents/vendor")
MANIFEST_RELATIVE = Path(".agents/dependencies/vendored-skills/provenance.json")
SKILLS_RELATIVE = Path(".agents/skills")

WRAPPER_TARGET_RE = re.compile(r"- Skill: `([^`]+)`")
FORBIDDEN_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png"}
FORBIDDEN_NAMES = {".git", "__pycache__", ".venv", "dist"}
FORBIDDEN_SUFFIX_PYC = ".pyc"

EXPECTED_WRAPPERS = (
    "ccf-common",
    "ccf-experiment-designer",
    "ccf-humanization",
    "ccf-idea-optimizer",
    "ccf-idea-reviewer",
    "ccf-integrity-auditor",
    "ccf-literature-monitor",
    "ccf-literature-searcher",
    "ccf-paper-reviewer",
    "ccf-paper-to-exemplar",
    "ccf-paper-writer",
    "ccf-pipeline-orchestrator",
    "ccf-project-scaffolder",
    "ccf-rebuttal-writer",
    "ccf-skill-forger",
    "ccf-submission-checker",
    "ccf-visual-composer",
    "writing-dna-skill",
    "lieflat-less-ai-tone",
)


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def load_manifest(root: Path) -> dict:
    path = root / MANIFEST_RELATIVE
    if not path.is_file():
        raise SystemExit("ERROR missing vendored-skills manifest: " + str(path))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR invalid vendored-skills manifest: {exc}") from exc
    if data.get("schema_version") != "paper-vendored-skills-v1":
        raise SystemExit("ERROR unsupported vendored-skills manifest schema")
    if not isinstance(data.get("sources"), list) or not data["sources"]:
        raise SystemExit("ERROR vendored-skills manifest requires sources")
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        raise SystemExit("ERROR vendored-skills manifest requires files")
    return data


def check_manifest(root: Path, manifest: dict) -> int:
    code = 0
    vendor_root = root / VENDOR_RELATIVE
    if not vendor_root.is_dir():
        return error(f"missing vendor directory: {VENDOR_RELATIVE}")

    for source in manifest["sources"]:
        name = source.get("name", "")
        license_rel = source.get("license_file", "")
        if not license_rel:
            code |= error(f"source {name!r} has no license_file")
            continue
        if not (vendor_root / license_rel).is_file():
            code |= error(f"missing license file for {name}: {license_rel}")
        if source.get("license") != "MIT":
            code |= error(f"source {name!r} license is not MIT: {source.get('license')}")

    for prefix, entries in manifest["files"].items():
        base = vendor_root / prefix
        if not base.is_dir():
            code |= error(f"missing vendor tree: {VENDOR_RELATIVE / prefix}")
            continue
        actual: dict[str, str] = {}
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                code |= error(f"vendor symlink is forbidden: {path.relative_to(root)}")
                continue
            if not path.is_file():
                continue
            rel = path.relative_to(base).as_posix()
            actual[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
            if path.name in FORBIDDEN_NAMES:
                code |= error(f"forbidden vendor entry: {path.relative_to(root)}")
            if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name.endswith(FORBIDDEN_SUFFIX_PYC):
                code |= error(
                    f"vendored content violates exclusion boundary: {path.relative_to(root)}"
                )
        for rel, expected in sorted(entries.items()):
            digest = actual.get(rel)
            if digest is None:
                code |= error(f"{VENDOR_RELATIVE / prefix}/{rel} missing from vendor tree")
            elif digest != expected:
                code |= error(f"{VENDOR_RELATIVE / prefix}/{rel} hash mismatch (vendor edited)")
        for rel in sorted(set(actual) - set(entries)):
            code |= error(f"{VENDOR_RELATIVE / prefix}/{rel} is not recorded in the manifest")

    return code


def check_wrappers(root: Path, manifest: dict) -> int:
    code = 0
    skills_root = root / SKILLS_RELATIVE
    for name in EXPECTED_WRAPPERS:
        wrapper = skills_root / name / "SKILL.md"
        if not wrapper.is_file():
            code |= error(f"missing wrapper skill: {SKILLS_RELATIVE / name}/SKILL.md")
            continue
        text = wrapper.read_text(encoding="utf-8")
        targets = WRAPPER_TARGET_RE.findall(text)
        if not targets:
            code |= error(f"{wrapper.relative_to(root)} does not declare a vendor target")
            continue
        for target_rel in targets:
            target = root / target_rel
            if not target.is_file():
                code |= error(
                    f"{wrapper.relative_to(root)} vendor target missing: {target_rel}"
                )

    # Every wrapper name must be routed by the root router (mirrors check-skills).
    router = root / "AGENTS.md"
    if router.is_file():
        router_text = router.read_text(encoding="utf-8")
        for name in EXPECTED_WRAPPERS:
            marker = f".agents/skills/{name}/SKILL.md"
            if marker not in router_text:
                code |= error(f"root AGENTS.md does not route vendored skill: {name}")
    return code


def check(root: Path) -> int:
    manifest = load_manifest(root)
    code = check_manifest(root, manifest) | check_wrappers(root, manifest)
    if code == 0:
        print("OK vendored_skills")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
