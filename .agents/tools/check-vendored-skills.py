#!/usr/bin/env python3
"""Validate the immutable vendored third-party skill snapshots.

Checks the vendor tree against `.agents/dependencies/vendored-skills/provenance.json`:

- every manifest file exists with the exact recorded SHA-256;
- no unrecorded files, symlinks, nested Git metadata, or bytecode caches;
- every wrapper skill under `.agents/skills/` points at an existing vendor file
  under `.agents/vendor/` whose path matches the wrapper name;
- the wrapper expectation list is taken from the manifest's `"wrappers"` key
  (falling back to the built-in list when the key is missing);
- the vendor tree never ships full-text paper reproductions under
  `paper_ref/` or `references/exemplars/papers/`;
- the excluded-content boundary holds (no paper PDFs or demo images shipped);
- each source has its license file present;
- the vendored scripts verify.sh depends on are present and recorded.
Bytecode caches (`.pyc`/`__pycache__`) are tolerated and skipped entirely.

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
ALLOWED_VENDOR_PREFIXES = {"ccfa-skills", "writing-dna-skill"}
FORBIDDEN_FULLTEXT_PARTS = {"paper_ref"}
FORBIDDEN_FULLTEXT_SUBPATH = ("references", "exemplars", "papers")

# Vendored scripts that verify.sh invokes directly; a missing or unrecorded
# script means the upstream snapshot changed without a reviewed re-sync.
REQUIRED_VENDOR_SCRIPTS = (
    ".agents/vendor/ccfa-skills/ccf-common/scripts/check_markdown_links.py",
    ".agents/vendor/ccfa-skills/ccf-common/scripts/check_path_privacy.py",
)

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


def wrappers_from_manifest(manifest: dict) -> tuple[str, ...]:
    """Wrapper expectation list, preferring the manifest's `wrappers` key."""
    wrappers = manifest.get("wrappers")
    if isinstance(wrappers, list) and wrappers and all(
        isinstance(item, str) for item in wrappers
    ):
        return tuple(wrappers)
    return EXPECTED_WRAPPERS


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
            if "__pycache__" in path.parts or path.name.endswith(FORBIDDEN_SUFFIX_PYC):
                continue
            if path.is_symlink():
                code |= error(f"vendor symlink is forbidden: {path.relative_to(root)}")
                continue
            if not path.is_file():
                continue
            rel = path.relative_to(base).as_posix()
            actual[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
            if path.name in FORBIDDEN_NAMES:
                code |= error(f"forbidden vendor entry: {path.relative_to(root)}")
            if path.suffix.lower() in FORBIDDEN_SUFFIXES:
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

    code |= check_no_fulltext_dirs(root, vendor_root)
    return code


def check_no_fulltext_dirs(root: Path, vendor_root: Path) -> int:
    """Reject vendor directories that would host full-text paper reproductions."""
    code = 0
    for path in sorted(vendor_root.rglob("*")):
        if not path.is_dir():
            continue
        rel_parts = path.relative_to(vendor_root).as_posix().split("/")
        if any(part in FORBIDDEN_FULLTEXT_PARTS for part in rel_parts):
            code |= error(
                f"vendored full-text paper dir is forbidden: {path.relative_to(root)}"
            )
        for index in range(len(rel_parts) - len(FORBIDDEN_FULLTEXT_SUBPATH) + 1):
            if tuple(rel_parts[index:index + len(FORBIDDEN_FULLTEXT_SUBPATH)]) == FORBIDDEN_FULLTEXT_SUBPATH:
                code |= error(
                    f"vendored full-text paper dir is forbidden: {path.relative_to(root)}"
                )
    return code


def check_wrappers(root: Path, manifest: dict) -> int:
    code = 0
    skills_root = root / SKILLS_RELATIVE
    vendor_root = (root / VENDOR_RELATIVE).resolve()
    wrappers = wrappers_from_manifest(manifest)
    for name in wrappers:
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
                continue
            try:
                vendor_parts = target.resolve().relative_to(vendor_root).parts
            except ValueError:
                code |= error(
                    f"{wrapper.relative_to(root)} vendor target outside vendor tree: {target_rel}"
                )
                continue
            if not vendor_parts or vendor_parts[0] not in ALLOWED_VENDOR_PREFIXES:
                code |= error(
                    f"{wrapper.relative_to(root)} vendor target outside vendored skill prefixes: {target_rel}"
                )
                continue
            if name not in vendor_parts:
                code |= error(
                    f"{wrapper.relative_to(root)} vendor target does not match skill name: {target_rel}"
                )

    # Every wrapper name must be routed by the root router (mirrors check-skills).
    router = root / "AGENTS.md"
    if router.is_file():
        router_text = router.read_text(encoding="utf-8")
        for name in wrappers:
            marker = f".agents/skills/{name}/SKILL.md"
            if marker not in router_text:
                code |= error(f"root AGENTS.md does not route vendored skill: {name}")
    return code


def check_required_vendor_scripts(root: Path, manifest: dict) -> int:
    """Fail when a vendored script verify.sh depends on is missing or unrecorded."""
    code = 0
    vendor_prefix = f"{VENDOR_RELATIVE.as_posix()}/"
    recorded = {
        vendor_prefix + f"{prefix}/{inner}"
        for prefix, entries in manifest["files"].items()
        for inner in entries
    }
    for rel in REQUIRED_VENDOR_SCRIPTS:
        if not (root / rel).is_file():
            code |= error(
                f"verify.sh depends on vendored script {rel} which is missing from the vendor"
                " tree — upstream snapshot changed; review and re-sync"
            )
        elif rel not in recorded:
            code |= error(
                f"verify.sh depends on vendored script {rel} which is not recorded in the"
                " manifest — upstream snapshot changed; review and re-sync"
            )
    return code


def check(root: Path) -> int:
    manifest = load_manifest(root)
    code = check_manifest(root, manifest) | check_wrappers(root, manifest)
    code |= check_required_vendor_scripts(root, manifest)
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
