#!/usr/bin/env python3
"""Run the locked open-source bibliography metadata audit without approving claims."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SUMMARY_SCHEMA = "paper-reference-metadata-run-v1"


def load_integrity_module(root: Path) -> ModuleType:
    path = root / ".agents/tools/check-reference-integrity.py"
    spec = importlib.util.spec_from_file_location("paper_reference_integrity", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load structural checker: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_summary(path: Path, **values: Any) -> None:
    payload = {
        "schema_version": SUMMARY_SCHEMA,
        "approves_claim_support": False,
        **values,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]] | None:
    if not path.is_file():
        return None
    records: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    return None
                records.append(value)
    except (OSError, json.JSONDecodeError):
        return None
    return records or None


def validate_records(records: list[dict[str, Any]], bibliography_keys: set[str]) -> str | None:
    keys: list[str] = []
    for record in records:
        key = record.get("key")
        status = record.get("status")
        if not isinstance(key, str) or not key.strip():
            return "metadata report record has no non-empty key"
        if not isinstance(status, str) or not status.strip():
            return f"metadata report record {key} has no non-empty status"
        if not isinstance(record.get("abstained"), bool):
            return f"metadata report record {key} has invalid abstained flag"
        if not isinstance(record.get("coverage_incomplete"), bool):
            return f"metadata report record {key} has invalid coverage_incomplete flag"
        if not isinstance(record.get("errors"), list):
            return f"metadata report record {key} has invalid errors list"
        keys.append(key)
    if len(keys) != len(set(keys)):
        return "metadata report contains duplicate citation keys"
    if set(keys) != bibliography_keys:
        missing = sorted(bibliography_keys - set(keys))
        extra = sorted(set(keys) - bibliography_keys)
        return f"metadata report key coverage mismatch; missing={missing}, extra={extra}"
    return None


def classify_records(records: list[dict[str, Any]]) -> str:
    infrastructure_error = False
    unverified = False
    problematic = False
    for record in records:
        status = str(record.get("status", "")).strip().lower()
        if record["coverage_incomplete"] is True or any(
            token in status for token in ("api_error", "timeout", "rate_limit", "infrastructure")
        ):
            infrastructure_error = True
        elif status == "verified" and record["abstained"] is False and not record["errors"]:
            continue
        elif record["abstained"] is True or any(
            token in status for token in ("not_found", "unconfirmed", "strict_warn", "could_not_verify")
        ):
            unverified = True
        else:
            problematic = True
    if infrastructure_error:
        return "infrastructure_error"
    if problematic:
        return "reference_problem"
    if unverified:
        return "unverified"
    return "passed"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--uv", default="uv", help="uv executable used with the committed lock")
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    output = root / "dist/reference-integrity"
    report = output / "metadata.jsonl"
    summary = output / "run.json"

    try:
        integrity = load_integrity_module(root)
        policy = integrity.enforcement_policy(root)
    except Exception as exc:  # the summary must survive malformed local policy
        write_summary(summary, outcome="infrastructure_error", detail=str(exc), attempts=0)
        print(f"ERROR reference metadata audit could not load policy: {exc}")
        return 2

    if policy is None or policy["enforcement"] != "enforced":
        write_summary(summary, outcome="skipped", detail="protected publication policy not enabled", attempts=0)
        print("SKIP reference_metadata policy not enabled")
        return 0

    structural = integrity.check(root, "draft")
    if structural != 0:
        write_summary(summary, outcome="local_validation_failed", detail="offline ledger gate failed", attempts=0)
        print("ERROR reference metadata audit blocked by offline ledger validation")
        return 1

    bibliography = integrity.project_path(root, policy["bibliography"], "bibliography")
    try:
        bibliography_keys = set(integrity.bibtex_keys(bibliography.read_text(encoding="utf-8")))
    except Exception as exc:
        write_summary(summary, outcome="local_validation_failed", detail=str(exc), attempts=0)
        print(f"ERROR reference metadata audit could not read bibliography: {exc}")
        return 1
    if not bibliography_keys:
        write_summary(summary, outcome="skipped", detail="bibliography has no entries", attempts=0)
        print("SKIP reference_metadata bibliography has no entries")
        return 0

    uv = shutil.which(args.uv)
    if uv is None:
        write_summary(summary, outcome="infrastructure_error", detail=f"uv executable not found: {args.uv}", attempts=0)
        print(f"ERROR reference metadata audit requires uv: {args.uv}")
        return 2

    dependency_root = root / ".agents/dependencies/reference-integrity"
    lock = dependency_root / "uv.lock"
    if not lock.is_file():
        write_summary(summary, outcome="infrastructure_error", detail="missing committed uv.lock", attempts=0)
        print("ERROR reference metadata audit missing dependency lock")
        return 2

    output.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["UV_PROJECT_ENVIRONMENT"] = str(output / "venv")
    environment["UV_CACHE_DIR"] = str(output / "uv-cache")
    command = [
        uv,
        "run",
        "--project",
        str(dependency_root),
        "--frozen",
        "--no-dev",
        "bibtex-check",
        str(bibliography),
        "--non-generative",
        "--strict",
        "--strict-warn-cnv",
        "--cache-file",
        str(output / "metadata-cache.db"),
        "--jsonl",
        str(report),
    ]

    attempts = max(1, min(args.attempts, 3))
    last_detail = "metadata checker did not run"
    for attempt in range(1, attempts + 1):
        if report.exists():
            report.unlink()
        try:
            result = subprocess.run(
                command,
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=max(1, args.timeout),
                check=False,
            )
        except subprocess.TimeoutExpired:
            last_detail = f"metadata checker timed out after {args.timeout}s"
            continue
        records = read_jsonl(report)
        if records is not None:
            validation_error = validate_records(records, bibliography_keys)
            outcome = "infrastructure_error" if validation_error else classify_records(records)
            if outcome == "passed" and result.returncode != 0:
                outcome = "infrastructure_error"
            write_summary(
                summary,
                outcome=outcome,
                detail=validation_error or "metadata identity only; claim support remains Human-reviewed",
                attempts=attempt,
                checker_returncode=result.returncode,
                report="dist/reference-integrity/metadata.jsonl",
            )
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            if outcome == "passed" and result.returncode == 0:
                print("OK reference_metadata identity audit passed; claim support not approved")
                return 0
            if outcome == "unverified":
                print("ERROR reference metadata audit is unverified; this is not evidence of fabrication")
            elif outcome == "infrastructure_error":
                print(f"ERROR reference metadata infrastructure incomplete: {validation_error or 'checker status/output mismatch'}")
                return 2
            else:
                print("ERROR reference metadata audit found a positive problem; see generated JSONL")
            return 1
        last_detail = (
            f"metadata checker returned {result.returncode} without a valid JSONL report; "
            f"stderr={result.stderr[-1000:].strip()}"
        )

    write_summary(summary, outcome="infrastructure_error", detail=last_detail, attempts=attempts)
    print(f"ERROR reference metadata infrastructure unavailable: {last_detail}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
