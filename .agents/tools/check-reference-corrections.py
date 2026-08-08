#!/usr/bin/env python3
"""Generate locked bibliography correction candidates without changing canonical sources."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SUMMARY_SCHEMA = "paper-reference-correction-run-v1"
REPORT_FIELDS = {
    "file", "key_old", "key_new", "doi_old", "doi_new", "action",
    "method", "confidence", "title_old", "title_new",
}


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_summary(path: Path, **values: Any) -> None:
    payload = {
        "schema_version": SUMMARY_SCHEMA,
        "rewrites_bibliography": False,
        "approves_bibliography_changes": False,
        "approves_claim_support": False,
        **values,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_report(path: Path, expected_keys: set[str]) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not path.is_file():
        return None, "missing correction JSONL report"
    records: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or not REPORT_FIELDS.issubset(record):
                return None, "correction report has an invalid record"
            records.append(record)
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid correction JSONL report: {exc}"
    old_keys = [record["key_old"] for record in records]
    if not all(isinstance(key, str) and key for key in old_keys):
        return None, "correction report has an invalid original key"
    if len(old_keys) != len(set(old_keys)) or set(old_keys) != expected_keys:
        return None, "correction report does not cover each bibliography key exactly once"
    for record in records:
        if record["action"] == "dropped":
            return None, f"updater dropped an entry: {record['key_old']}"
        if record["key_new"] != record["key_old"]:
            return None, f"updater changed a citation key: {record['key_old']}"
        if not isinstance(record["action"], str) or not record["action"]:
            return None, f"correction report has an invalid action: {record['key_old']}"
    return records, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--uv", default="uv")
    parser.add_argument("--timeout", type=int, default=720)
    parser.add_argument("--request-timeout", type=int, default=20)
    parser.add_argument("--rate-limit", type=int, default=30)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    output = root / "dist/reference-integrity/corrections"
    summary = output / "run.json"

    try:
        integrity = load_module(root / ".agents/tools/check-reference-integrity.py", "paper_reference_integrity")
        policy = integrity.enforcement_policy(root)
    except Exception as exc:
        write_summary(summary, outcome="infrastructure_error", detail=str(exc))
        print(f"ERROR reference correction audit could not load policy: {exc}")
        return 2
    if policy is None or policy["enforcement"] != "enforced":
        write_summary(summary, outcome="skipped", detail="protected publication policy not enabled")
        print("SKIP reference_corrections policy not enabled")
        return 0
    if integrity.check(root, "draft") != 0:
        write_summary(summary, outcome="local_validation_failed", detail="offline ledger gate failed")
        print("ERROR reference correction audit blocked by offline ledger validation")
        return 1

    bibliography = integrity.project_path(root, policy["bibliography"], "bibliography")
    original = bibliography.read_bytes()
    original_hash = hashlib.sha256(original).hexdigest()

    def canonical_matches() -> bool:
        try:
            return bibliography.read_bytes() == original
        except OSError:
            return False

    keys = set(integrity.bibtex_keys(original.decode("utf-8")))
    if not keys:
        write_summary(summary, outcome="skipped", detail="bibliography has no entries", canonical_sha256=original_hash)
        print("SKIP reference_corrections bibliography has no entries")
        return 0

    try:
        env_helper = load_module(root / ".agents/tools/_reference_env.py", "paper_reference_env")
        env_helper.load_reference_env(root)
    except Exception as exc:
        write_summary(summary, outcome="infrastructure_error", detail=str(exc), canonical_sha256=original_hash)
        print(f"ERROR reference correction audit could not load .env: {exc}")
        return 2

    uv = shutil.which(args.uv)
    dependency_root = root / ".agents/dependencies/reference-integrity"
    lock = dependency_root / "uv.lock"
    format_helper = root / ".agents/tools/_validate-bibtex-with-pybtex.py"
    correction_helper = root / ".agents/tools/_validate-bibtex-correction.py"
    if uv is None or not lock.is_file() or not format_helper.is_file() or not correction_helper.is_file():
        detail = "missing uv, committed dependency lock, or correction validation helper"
        write_summary(summary, outcome="infrastructure_error", detail=detail, canonical_sha256=original_hash)
        print(f"ERROR reference correction audit infrastructure incomplete: {detail}")
        return 2

    output.mkdir(parents=True, exist_ok=True)
    source = output / "source.bib"
    candidate = output / "candidate.bib"
    report = output / "report.jsonl"
    format_report = output / "format.json"
    validation_report = output / "validation.json"
    for stale in (candidate, report, format_report, validation_report):
        if stale.exists():
            stale.unlink()
    source.write_bytes(original)
    environment = os.environ.copy()
    environment["UV_PROJECT_ENVIRONMENT"] = str(root / "dist/reference-integrity/venv")
    environment["UV_CACHE_DIR"] = str(root / "dist/reference-integrity/uv-cache")
    mailto = environment.get("BIBTEX_CHECK_MAILTO", "").strip()
    if mailto:
        environment["BIBTEX_UPDATER_USER_AGENT"] = f"paper-reference-correction-audit/1 (mailto:{mailto})"
    command = [
        uv, "run", "--project", str(dependency_root), "--frozen", "--no-dev",
        "bibtex-update", str(source), "--output", str(candidate), "--report", str(report),
        "--cache", str(output / "http-cache.db"),
        "--resolution-cache", str(output / "resolution-cache.json"),
        "--rate-limit", str(max(1, args.rate_limit)),
        "--max-workers", str(max(1, args.workers)),
        "--timeout", str(max(1, args.request_timeout)),
        "--check-fields", "--fill-fields", "--field-fill-mode", "required",
    ]
    run_error: str | None = None
    try:
        result = subprocess.run(
            command, cwd=root, env=environment, text=True, capture_output=True,
            timeout=max(1, args.timeout), check=False,
        )
    except subprocess.TimeoutExpired:
        result = None
        run_error = "correction audit timed out"
    except OSError as exc:
        result = None
        run_error = f"could not start correction audit: {exc}"
    if not canonical_matches():
        write_summary(summary, outcome="unsafe_output", detail="canonical bibliography changed during candidate generation")
        print("ERROR reference correction audit detected canonical bibliography mutation")
        return 2
    if result is None:
        outcome = "provider_unavailable" if run_error == "correction audit timed out" else "infrastructure_error"
        write_summary(summary, outcome=outcome, detail=run_error, canonical_sha256=original_hash)
        print(f"{'WARN' if outcome == 'provider_unavailable' else 'ERROR'} reference_corrections {run_error}")
        return 0 if outcome == "provider_unavailable" else 2
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    records, report_error = read_report(report, keys)
    if report_error or not candidate.is_file():
        detail = report_error or "missing correction candidate"
        write_summary(summary, outcome="infrastructure_error", detail=detail, updater_returncode=result.returncode)
        print(f"ERROR reference correction audit produced unusable evidence: {detail}")
        return 2
    try:
        candidate_keys = set(integrity.bibtex_keys(candidate.read_text(encoding="utf-8")))
    except Exception as exc:
        detail = f"correction candidate could not be parsed: {exc}"
        write_summary(summary, outcome="unsafe_output", detail=detail, updater_returncode=result.returncode)
        print(f"ERROR reference correction audit: {detail}")
        return 2
    if candidate_keys != keys:
        detail = "correction candidate changed bibliography key coverage"
        write_summary(summary, outcome="unsafe_output", detail=detail, updater_returncode=result.returncode)
        print(f"ERROR reference correction audit: {detail}")
        return 2

    validation_command = [
        uv, "run", "--project", str(dependency_root), "--frozen", "--no-dev",
        "python", str(correction_helper), str(source), str(candidate), str(report), str(validation_report),
    ]
    try:
        validation_result = subprocess.run(
            validation_command, cwd=root, env=environment, text=True, capture_output=True,
            timeout=120, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        validation_result = None
    try:
        validation = json.loads(validation_report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        validation = None
    if not canonical_matches():
        write_summary(summary, outcome="unsafe_output", detail="canonical bibliography changed during report validation")
        print("ERROR reference correction audit detected canonical bibliography mutation")
        return 2
    if validation_result is None or validation_result.returncode != 0 or not isinstance(validation, dict) or not validation.get("passed"):
        detail = "correction report does not match candidate content"
        write_summary(summary, outcome="unsafe_output", detail=detail, updater_returncode=result.returncode)
        print(f"ERROR reference correction audit: {detail}")
        return 2

    format_command = [
        uv, "run", "--project", str(dependency_root), "--frozen", "--no-dev",
        "python", str(format_helper), str(candidate), str(format_report),
    ]
    try:
        format_result = subprocess.run(
            format_command, cwd=root, env=environment, text=True, capture_output=True,
            timeout=120, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        format_result = None
    if not canonical_matches():
        write_summary(summary, outcome="unsafe_output", detail="canonical bibliography changed during format validation")
        print("ERROR reference correction audit detected canonical bibliography mutation")
        return 2
    if format_result is None or format_result.returncode != 0:
        detail = "correction candidate failed locked Pybtex validation"
        write_summary(summary, outcome="unsafe_output", detail=detail, updater_returncode=result.returncode)
        print(f"ERROR reference correction audit: {detail}")
        return 2

    if not canonical_matches():
        write_summary(summary, outcome="unsafe_output", detail="canonical bibliography changed during validation")
        print("ERROR reference correction audit detected canonical bibliography mutation")
        return 2

    assert records is not None
    changed = validation["changed_keys"]
    incomplete = validation["incomplete_keys"]
    if result.returncode not in (0, 2):
        outcome = "infrastructure_error"
        exit_code = 2
    elif changed:
        outcome = "candidates_found"
        exit_code = 0
    elif incomplete or result.returncode == 2:
        outcome = "incomplete"
        exit_code = 0
    else:
        outcome = "no_corrections"
        exit_code = 0
    write_summary(
        summary, outcome=outcome,
        detail="candidate only; every bibliography change requires Human review",
        canonical_sha256=original_hash, updater_returncode=result.returncode,
        candidate="dist/reference-integrity/corrections/candidate.bib",
        report="dist/reference-integrity/corrections/report.jsonl",
        changed_keys=changed, incomplete_keys=incomplete,
    )
    print(f"{'WARN' if outcome != 'no_corrections' else 'OK'} reference_corrections outcome={outcome} candidates={len(changed)}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
