#!/usr/bin/env python3
"""Build immutable publication release instances and durable release records."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

VARIANTS = {
    "draft": "draft",
    "anonymous": "anonymous",
    "camera-ready": "camera_ready",
    "arxiv": "arxiv",
}
TARGETS = ("pdf", "source-zip", "arxiv-flat", "overleaf-zip")
RELEASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
AUX_SUFFIXES = {
    ".aux",
    ".bbl",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".synctex.gz",
}
SOURCE_CONTRACTS = (
    "PAPER.md",
    "EXPERIMENTS.md",
    "PAPER_INTERFACES.md",
    "PUBLICATION.md",
    "DECISIONS.md",
)
REFERENCE_CONTRACTS = ("REFERENCES.md", "references/ledger.json")


class ReleaseError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path, capture: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=False,
    )
    if result.returncode != 0:
        detail = ""
        if capture:
            detail = f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        raise ReleaseError(f"command failed ({result.returncode}): {' '.join(command)}{detail}")
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_file_allowed(relative: Path) -> bool:
    name = relative.name
    if name.startswith("main") and relative.parent == Path(".") and relative.suffix == ".pdf":
        return False
    if name.endswith(".synctex.gz"):
        return False
    if relative.suffix in AUX_SUFFIXES:
        return False
    return True


def iter_source_files(root: Path) -> list[tuple[Path, str]]:
    entries: list[tuple[Path, str]] = []
    for relative_text in SOURCE_CONTRACTS:
        path = root / relative_text
        if not path.is_file():
            raise ReleaseError(f"missing release source contract: {relative_text}")
        entries.append((path, relative_text))
    if reference_integrity_adopted(root):
        for relative_text in REFERENCE_CONTRACTS:
            path = root / relative_text
            if not path.is_file():
                raise ReleaseError(f"missing activated reference source contract: {relative_text}")
            entries.append((path, relative_text))
    paper_root = root / "paper"
    if not paper_root.is_dir():
        raise ReleaseError("missing canonical paper directory: paper/")
    for path in sorted(paper_root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(paper_root)
        if source_file_allowed(relative):
            entries.append((path, f"paper/{relative.as_posix()}"))
    return entries


def source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path, relative in iter_source_files(root):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def reference_integrity_adopted(root: Path) -> bool:
    path = root / ".agents/template-sync.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"invalid downstream-local template sync metadata: {exc}") from exc
    if not isinstance(data, dict):
        raise ReleaseError("downstream-local template sync metadata must be a JSON object")
    state = data.get("reference_integrity")
    if state is None:
        return False
    if not isinstance(state, dict) or not isinstance(state.get("adopted"), bool):
        raise ReleaseError("template sync reference_integrity.adopted must be boolean")
    return state["adopted"]


def reference_provenance(root: Path, profile: str) -> dict[str, object]:
    if not reference_integrity_adopted(root):
        return {
            "enforcement": "not-adopted",
            "offline_profile": profile,
            "offline_gate_passed": None,
            "online_metadata_required": False,
            "online_metadata_outcome": "not-applicable",
        }
    return {
        "enforcement": "enforced",
        "contract_sha256": sha256_file(root / "REFERENCES.md"),
        "ledger_sha256": sha256_file(root / "references/ledger.json"),
        "bibliography_sha256": sha256_file(root / "paper/refs.bib"),
        "dependency_lock_sha256": sha256_file(root / ".agents/dependencies/reference-integrity/uv.lock"),
        "offline_profile": profile,
        "offline_gate_passed": True,
        "online_metadata_required": False,
        "online_metadata_outcome": "not-required-for-release",
    }


def git_audit(root: Path) -> tuple[str | None, bool | None]:
    try:
        commit = run(["git", "rev-parse", "HEAD"], cwd=root, capture=True).stdout.strip()
        dirty_result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        dirty = bool(dirty_result.stdout.strip()) if dirty_result.returncode == 0 else None
        return commit, dirty
    except (OSError, ReleaseError):
        return None, None


def validate_release_id(release_id: str) -> None:
    if not RELEASE_ID_RE.fullmatch(release_id):
        raise ReleaseError(
            "invalid release id; use 3-64 lowercase letters, digits, dots, underscores, or hyphens"
        )


def parse_targets(value: str) -> list[str]:
    targets = [item.strip() for item in value.split(",") if item.strip()]
    if not targets:
        raise ReleaseError("at least one delivery target is required")
    unknown = sorted(set(targets) - set(TARGETS))
    if unknown:
        raise ReleaseError(f"unknown delivery target(s): {', '.join(unknown)}")
    return list(dict.fromkeys(targets))


def run_profile_checks(root: Path, profile: str) -> None:
    commands = [
        [sys.executable, ".agents/tools/check-structure.py"],
        [sys.executable, ".agents/tools/check-paper-contracts.py", "--profile", profile],
        [sys.executable, ".agents/tools/check-paper-interfaces.py"],
        [sys.executable, ".agents/tools/check-reference-integrity.py", "--profile", profile],
        [sys.executable, ".agents/tools/check-publication.py"],
    ]
    for command in commands:
        run(command, cwd=root)


def variant_pdf(root: Path, variant: str) -> Path:
    return root / "paper" / ("main.pdf" if variant == "draft" else f"main-{variant}.pdf")


def build_pdf(root: Path, variant: str) -> Path:
    run(["make", "pdf", f"VARIANT={variant}"], cwd=root)
    pdf = variant_pdf(root, variant)
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise ReleaseError(f"variant build did not produce a non-empty PDF: {pdf.relative_to(root)}")
    return pdf


def copy_source_tree(root: Path, destination: Path, variant: str) -> None:
    paper_root = root / "paper"
    destination.mkdir(parents=True, exist_ok=False)
    for path in sorted(paper_root.rglob("*")):
        if path.is_symlink():
            raise ReleaseError(f"paper source contains a symlink: {path.relative_to(root)}")
        if not path.is_file():
            continue
        relative = path.relative_to(paper_root)
        if not source_file_allowed(relative):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    canonical = destination / "main.tex"
    if not canonical.is_file():
        raise ReleaseError("source package is missing paper/main.tex")
    canonical.rename(destination / "canonical.tex")
    internal = VARIANTS[variant]
    (destination / "main.tex").write_text(
        f"\\def\\PaperVariant{{{internal}}}\n\\input{{canonical.tex}}\n",
        encoding="utf-8",
    )

    variants_root = destination / "variants"
    for driver in VARIANTS.values():
        candidate = variants_root / f"{driver}.tex"
        if candidate.exists():
            candidate.unlink()
    readme = variants_root / "README.md"
    if readme.exists():
        readme.unlink()


def deterministic_zip(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def active_tex(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def make_flat_package(source: Path, destination: Path) -> None:
    latexpand = shutil.which("latexpand")
    if latexpand is None:
        raise ReleaseError("arxiv-flat target requires latexpand")
    destination.mkdir(parents=True, exist_ok=False)
    result = run([latexpand, "main.tex"], cwd=source, capture=True)
    flattened = result.stdout.replace("{style/", "{")
    if re.search(r"\\(?:input|include)\s*\{", active_tex(flattened)):
        raise ReleaseError("latexpand output still contains an active input/include dependency")
    (destination / "main.tex").write_text(flattened, encoding="utf-8")

    refs = source / "refs.bib"
    if refs.is_file():
        shutil.copy2(refs, destination / "refs.bib")

    style_root = source / "style"
    if style_root.is_dir():
        for path in sorted(style_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".sty", ".cls", ".bst"}:
                shutil.copy2(path, destination / path.name)

    for directory in ("figures", "tables", "generated", "supplementary"):
        source_dir = source / directory
        if not source_dir.is_dir():
            continue
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() == ".tex":
                continue
            relative = path.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def verify_tex_directory(directory: Path) -> None:
    if shutil.which("latexmk") is None:
        raise ReleaseError("--verify-tex requires latexmk")
    run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=directory)
    pdf = directory / "main.pdf"
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise ReleaseError(f"isolated package compile did not produce main.pdf: {directory}")


def artifact_entry(path: Path, instance_dir: Path, target: str) -> dict[str, object]:
    return {
        "target": target,
        "path": path.relative_to(instance_dir).as_posix(),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def build_instance(args: argparse.Namespace) -> Path:
    root = args.root.expanduser().resolve()
    validate_release_id(args.release_id)
    if args.variant not in VARIANTS:
        raise ReleaseError(f"unknown variant: {args.variant}")
    targets = parse_targets(args.targets)
    dist_root = args.dist.expanduser()
    if not dist_root.is_absolute():
        dist_root = root / dist_root
    dist_root = dist_root.resolve()
    instance_dir = dist_root / args.release_id
    if instance_dir.exists():
        raise ReleaseError(f"release instance already exists and will not be overwritten: {instance_dir}")

    run_profile_checks(root, args.profile)
    pdf = build_pdf(root, args.variant)
    dist_root.mkdir(parents=True, exist_ok=True)

    temporary = Path(tempfile.mkdtemp(prefix=f".{args.release_id}-", dir=dist_root))
    artifacts_dir = temporary / "artifacts"
    artifacts_dir.mkdir()
    checks: dict[str, object] = {
        "profile_checks": True,
        "variant_pdf_compile": True,
        "isolated_source_compile": None,
        "isolated_flat_compile": None,
    }
    artifacts: list[dict[str, object]] = []

    try:
        if "pdf" in targets:
            target = artifacts_dir / "paper.pdf"
            shutil.copy2(pdf, target)
            artifacts.append(artifact_entry(target, temporary, "pdf"))

        needs_source = any(target in targets for target in ("source-zip", "overleaf-zip", "arxiv-flat"))
        source_dir: Path | None = None
        if needs_source:
            source_dir = temporary / ".source"
            copy_source_tree(root, source_dir, args.variant)
            if args.verify_tex:
                verify_tex_directory(source_dir)
                checks["isolated_source_compile"] = True

        if "source-zip" in targets and source_dir is not None:
            target = artifacts_dir / "source.zip"
            deterministic_zip(source_dir, target)
            artifacts.append(artifact_entry(target, temporary, "source-zip"))

        if "overleaf-zip" in targets and source_dir is not None:
            target = artifacts_dir / "overleaf.zip"
            deterministic_zip(source_dir, target)
            artifacts.append(artifact_entry(target, temporary, "overleaf-zip"))

        if "arxiv-flat" in targets and source_dir is not None:
            flat_dir = temporary / ".flat"
            make_flat_package(source_dir, flat_dir)
            if args.verify_tex:
                verify_tex_directory(flat_dir)
                checks["isolated_flat_compile"] = True
            target = artifacts_dir / "arxiv-flat.zip"
            deterministic_zip(flat_dir, target)
            artifacts.append(artifact_entry(target, temporary, "arxiv-flat"))

        commit, dirty = git_audit(root)
        reference_state = reference_provenance(root, args.profile)
        manifest = {
            "schema_version": "paper-release-instance-v1",
            "release_id": args.release_id,
            "variant": args.variant,
            "profile": args.profile,
            "release_ready": args.profile == "release",
            "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "source": {
                "fingerprint_sha256": source_fingerprint(root),
                "git_audit_commit": commit,
                "git_dirty": dirty,
                "paper_interfaces_sha256": sha256_file(root / "PAPER_INTERFACES.md"),
                "publication_contract_sha256": sha256_file(root / "PUBLICATION.md"),
                "variant_config_sha256": sha256_file(
                    root / "paper/variants/config" / f"{VARIANTS[args.variant]}.tex"
                ),
            },
            "reference_integrity": reference_state,
            "targets": targets,
            "checks": checks,
            "artifacts": artifacts,
        }
        manifest_path = temporary / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        report = [
            f"# Release build: {args.release_id}",
            "",
            f"- Variant: `{args.variant}`",
            f"- Profile: `{args.profile}`",
            f"- Release ready: `{str(args.profile == 'release').lower()}`",
            f"- Source fingerprint: `{manifest['source']['fingerprint_sha256']}`",
            f"- Reference integrity: `{reference_state['enforcement']}`",
            f"- Reference ledger SHA-256: `{reference_state.get('ledger_sha256', 'not-applicable')}`",
            f"- Online metadata audit: `{reference_state['online_metadata_outcome']}`",
            f"- Git audit commit: `{commit or 'unavailable'}`",
            f"- Git dirty at build: `{dirty}`",
            f"- Targets: {', '.join(targets)}",
            "",
            "## Checks",
            "",
        ]
        report.extend(f"- {name}: `{value}`" for name, value in checks.items())
        report.extend(["", "## Artifacts", ""])
        report.extend(
            f"- `{entry['path']}` — `{entry['sha256']}` ({entry['size']} bytes)"
            for entry in artifacts
        )
        (temporary / "build-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

        for hidden in (temporary / ".source", temporary / ".flat"):
            if hidden.exists():
                shutil.rmtree(hidden)
        temporary.rename(instance_dir)
        return instance_dir
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def load_manifest(instance: Path) -> dict[str, object]:
    manifest_path = instance / "manifest.json"
    if not manifest_path.is_file():
        raise ReleaseError(f"missing release manifest: {manifest_path}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"invalid release manifest JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReleaseError("release manifest must be a JSON object")
    return data


def write_record(args: argparse.Namespace) -> Path:
    instance = args.instance.expanduser().resolve()
    manifest = load_manifest(instance)
    release_id = str(manifest.get("release_id", ""))
    validate_release_id(release_id)

    output = args.output.expanduser()
    if not output.is_absolute():
        output = Path.cwd() / output
    output = output.resolve()
    if output.exists():
        raise ReleaseError(f"release record already exists and will not be overwritten: {output}")
    if args.status in {"approved", "published"} and (
        not args.human_approval or args.human_approval.strip().lower() in {"todo", "pending"}
    ):
        raise ReleaseError(f"status {args.status} requires explicit --human-approval")

    manifest_sha = sha256_file(instance / "manifest.json")
    source = manifest.get("source", {}) if isinstance(manifest.get("source"), dict) else {}
    artifacts = manifest.get("artifacts", []) if isinstance(manifest.get("artifacts"), list) else []
    lines = [
        f"# Release {release_id}",
        "",
        f"- Status: `{args.status}`",
        f"- Variant: `{manifest.get('variant')}`",
        f"- Profile: `{manifest.get('profile')}`",
        f"- Release ready: `{str(bool(manifest.get('release_ready'))).lower()}`",
        f"- Source fingerprint: `{source.get('fingerprint_sha256', '')}`",
        f"- Git audit commit: `{source.get('git_audit_commit') or 'unavailable'}`",
        f"- Manifest SHA-256: `{manifest_sha}`",
        f"- Human approval: `{args.human_approval or 'pending'}`",
        "",
        "## Artifacts",
        "",
    ]
    for artifact in artifacts:
        if isinstance(artifact, dict):
            lines.append(
                f"- `{artifact.get('target')}`: `{artifact.get('path')}` — `{artifact.get('sha256')}`"
            )
    lines.extend(["", "## Notes", "", args.notes or "None.", ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build an immutable release instance")
    build.add_argument("--id", dest="release_id", required=True)
    build.add_argument("--variant", choices=tuple(VARIANTS), required=True)
    build.add_argument("--profile", choices=("draft", "release"), default="release")
    build.add_argument("--targets", default=",".join(TARGETS))
    build.add_argument("--verify-tex", action="store_true")
    build.add_argument("--root", type=Path, default=Path.cwd())
    build.add_argument("--dist", type=Path, default=Path("dist"))

    record = subparsers.add_parser("record", help="write a durable release record")
    record.add_argument("--instance", type=Path, required=True)
    record.add_argument("--output", type=Path, required=True)
    record.add_argument(
        "--status",
        choices=("candidate", "approved", "published", "superseded", "withdrawn"),
        default="candidate",
    )
    record.add_argument("--human-approval")
    record.add_argument("--notes")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "build":
            instance = build_instance(args)
            print(f"OK release build: {instance}")
        else:
            record = write_record(args)
            print(f"OK release record: {record}")
        return 0
    except (ReleaseError, OSError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
