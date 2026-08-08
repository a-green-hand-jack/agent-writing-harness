#!/usr/bin/env python3
"""Run the locked Pybtex syntax and required-field gate without rewriting BibTeX."""
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

SUMMARY_SCHEMA = "paper-bibtex-format-run-v1"
REPORT_SCHEMA = "paper-bibtex-format-report-v1"


def load_integrity_module(root: Path) -> ModuleType:
    path = root / ".agents/tools/check-reference-integrity.py"
    spec = importlib.util.spec_from_file_location("paper_reference_integrity", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load structural checker: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_summary(path: Path, **values: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": SUMMARY_SCHEMA, "rewrites_bibliography": False, **values}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_report(path: Path, expected_keys: set[str]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid or missing Pybtex report: {exc}"
    if not isinstance(report, dict) or report.get("schema_version") != REPORT_SCHEMA:
        return None, "Pybtex report has an unsupported schema"
    if report.get("checker") != "pybtex" or not isinstance(report.get("passed"), bool):
        return None, "Pybtex report has invalid checker or passed fields"
    keys = report.get("keys")
    errors = report.get("errors")
    if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
        return None, "Pybtex report has an invalid key list"
    if len(keys) != len(set(keys)):
        return None, "Pybtex report contains duplicate keys"
    if report["passed"] and set(keys) != expected_keys:
        return None, "Pybtex report does not cover every bibliography key"
    if not isinstance(errors, list) or not all(
        isinstance(item, dict) and isinstance(item.get("key"), str) and isinstance(item.get("message"), str)
        for item in errors
    ):
        return None, "Pybtex report has an invalid errors list"
    if report["passed"] == bool(errors):
        return None, "Pybtex report passed state contradicts its errors"
    return report, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--uv", default="uv", help="uv executable used with the committed lock")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    output = root / "dist/reference-integrity"
    report_path = output / "format.json"
    summary_path = output / "format-run.json"

    try:
        integrity = load_integrity_module(root)
        policy = integrity.enforcement_policy(root)
    except Exception as exc:
        write_summary(summary_path, outcome="infrastructure_error", detail=str(exc))
        print(f"ERROR BibTeX format gate could not load policy: {exc}")
        return 2
    if policy is None or policy["enforcement"] != "enforced":
        write_summary(summary_path, outcome="skipped", detail="protected publication policy not enabled")
        print("SKIP bibtex_format policy not enabled")
        return 0

    bibliography = integrity.project_path(root, policy["bibliography"], "bibliography")
    try:
        keys = set(integrity.bibtex_keys(bibliography.read_text(encoding="utf-8")))
    except Exception as exc:
        write_summary(summary_path, outcome="format_problem", detail=str(exc))
        print(f"ERROR BibTeX format gate could not parse bibliography keys: {exc}")
        return 1
    if not keys:
        write_summary(summary_path, outcome="skipped", detail="bibliography has no entries")
        print("SKIP bibtex_format bibliography has no entries")
        return 0

    uv = shutil.which(args.uv)
    dependency_root = root / ".agents/dependencies/reference-integrity"
    lock = dependency_root / "uv.lock"
    helper = root / ".agents/tools/_validate-bibtex-with-pybtex.py"
    if uv is None or not lock.is_file() or not helper.is_file():
        detail = "missing uv, committed dependency lock, or Pybtex helper"
        write_summary(summary_path, outcome="infrastructure_error", detail=detail)
        print(f"ERROR BibTeX format gate infrastructure incomplete: {detail}")
        return 2

    output.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["UV_PROJECT_ENVIRONMENT"] = str(output / "venv")
    environment["UV_CACHE_DIR"] = str(output / "uv-cache")
    command = [
        uv, "run", "--project", str(dependency_root), "--frozen", "--no-dev",
        "python", str(helper), str(bibliography), str(report_path),
    ]
    if report_path.exists():
        report_path.unlink()
    try:
        result = subprocess.run(
            command, cwd=root, env=environment, text=True, capture_output=True,
            timeout=max(1, args.timeout), check=False,
        )
    except subprocess.TimeoutExpired:
        write_summary(summary_path, outcome="infrastructure_error", detail="Pybtex format gate timed out")
        print("ERROR BibTeX format gate timed out")
        return 2
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    report, validation_error = load_report(report_path, keys)
    if validation_error:
        write_summary(summary_path, outcome="infrastructure_error", detail=validation_error)
        print(f"ERROR BibTeX format gate produced unusable evidence: {validation_error}")
        return 2
    assert report is not None
    if report["passed"] and result.returncode == 0:
        outcome = "passed"
    elif not report["passed"] and result.returncode == 1:
        outcome = "format_problem"
    else:
        outcome = "infrastructure_error"
    write_summary(
        summary_path, outcome=outcome,
        detail="classic BibTeX syntax and required fields; bibliography was not rewritten",
        checker_returncode=result.returncode, report="dist/reference-integrity/format.json",
    )
    return 0 if outcome == "passed" else (2 if outcome == "infrastructure_error" else 1)


if __name__ == "__main__":
    sys.exit(main())
