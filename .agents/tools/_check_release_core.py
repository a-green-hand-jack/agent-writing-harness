#!/usr/bin/env python3
"""Validate a generated release instance, artifacts, checksums, and package boundaries."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

RELEASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
FORBIDDEN_ZIP_ROOTS = {
    ".agent",
    ".agents",
    ".claude",
    ".git",
    ".github",
    "dist",
    "release",
    "releases",
    "state",
    "lab",
    "human",
    "memory",
    "scripts",
}
REQUIRED_SOURCE_ENTRIES = {"main.tex", "canonical.tex", "macros.tex", "refs.bib"}
REQUIRED_FLAT_ENTRIES = {"main.tex", "refs.bib"}


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(instance: Path) -> dict[str, object] | None:
    path = instance / "manifest.json"
    if not path.is_file():
        error(f"missing manifest.json: {instance}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error(f"invalid manifest JSON: {exc}")
        return None
    if not isinstance(data, dict):
        error("manifest must be a JSON object")
        return None
    return data


def safe_zip_entries(path: Path, required: set[str]) -> int:
    code = 0
    try:
        with zipfile.ZipFile(path) as archive:
            names = set()
            for info in archive.infolist():
                pure = PurePosixPath(info.filename)
                if pure.is_absolute() or ".." in pure.parts:
                    code |= error(f"unsafe ZIP path in {path.name}: {info.filename}")
                    continue
                if pure.parts and pure.parts[0] in FORBIDDEN_ZIP_ROOTS:
                    code |= error(f"forbidden repository surface in {path.name}: {info.filename}")
                if info.is_dir():
                    continue
                names.add(pure.as_posix())
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    code |= error(f"ZIP contains a symlink: {path.name}:{info.filename}")
            missing = sorted(required - names)
            for name in missing:
                code |= error(f"{path.name} missing required entry: {name}")
            if path.name == "arxiv-flat.zip" and "main.tex" in names:
                text = archive.read("main.tex").decode("utf-8", errors="replace")
                active = "\n".join(line.split("%", 1)[0] for line in text.splitlines())
                if re.search(r"\\(?:input|include)\s*\{", active):
                    code |= error("arxiv-flat.zip main.tex still contains input/include dependencies")
    except (OSError, zipfile.BadZipFile) as exc:
        code |= error(f"invalid ZIP artifact {path}: {exc}")
    return code


def check(instance: Path) -> int:
    instance = instance.expanduser().resolve()
    manifest = load_manifest(instance)
    if manifest is None:
        return 1

    code = 0
    release_id = str(manifest.get("release_id", ""))
    if not RELEASE_ID_RE.fullmatch(release_id):
        code |= error(f"manifest has invalid release_id: {release_id}")
    if instance.name != release_id:
        code |= error(f"instance directory name does not match release_id: {instance.name} != {release_id}")
    if manifest.get("schema_version") != "paper-release-instance-v1":
        code |= error("unsupported or missing release manifest schema_version")

    profile = manifest.get("profile")
    ready = manifest.get("release_ready")
    if profile not in {"draft", "release"}:
        code |= error(f"invalid release profile: {profile}")
    if ready is not (profile == "release"):
        code |= error("release_ready must be true exactly for the release profile")

    source = manifest.get("source")
    if not isinstance(source, dict):
        code |= error("manifest source must be an object")
    else:
        for key in (
            "fingerprint_sha256",
            "paper_interfaces_sha256",
            "publication_contract_sha256",
            "variant_config_sha256",
        ):
            value = source.get(key)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                code |= error(f"manifest source has invalid {key}")

    if not (instance / "build-report.md").is_file():
        code |= error("release instance missing build-report.md")

    for path in instance.rglob("*"):
        if path.is_symlink():
            code |= error(f"release instance contains a symlink: {path.relative_to(instance)}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        code |= error("manifest artifacts must be a non-empty list")
        artifacts = []

    seen_targets: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            code |= error("manifest artifact entry must be an object")
            continue
        target = str(artifact.get("target", ""))
        relative = str(artifact.get("path", ""))
        expected_sha = str(artifact.get("sha256", ""))
        expected_size = artifact.get("size")
        if target in seen_targets:
            code |= error(f"duplicate artifact target in manifest: {target}")
        seen_targets.add(target)
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or not relative.startswith("artifacts/"):
            code |= error(f"unsafe artifact path in manifest: {relative}")
            continue
        path = instance / pure
        if not path.is_file():
            code |= error(f"manifest artifact is missing: {relative}")
            continue
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            code |= error(f"artifact checksum drift: {relative}")
        if path.stat().st_size != expected_size:
            code |= error(f"artifact size drift: {relative}")
        if target in {"source-zip", "overleaf-zip"}:
            code |= safe_zip_entries(path, REQUIRED_SOURCE_ENTRIES)
        elif target == "arxiv-flat":
            code |= safe_zip_entries(path, REQUIRED_FLAT_ENTRIES)
        elif target == "pdf" and path.suffix.lower() != ".pdf":
            code |= error("pdf target does not point to a PDF artifact")

    targets = manifest.get("targets")
    if not isinstance(targets, list) or set(str(item) for item in targets) != seen_targets:
        code |= error("manifest targets do not match artifact targets")

    if code == 0:
        print(f"OK release instance: {release_id}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance", type=Path)
    args = parser.parse_args()
    return check(args.instance)


if __name__ == "__main__":
    sys.exit(main())
