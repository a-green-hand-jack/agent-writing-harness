#!/usr/bin/env python3
"""Verify that an updater JSONL report exactly describes its BibTeX candidate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtex_updater.utils import doi_normalize, latex_to_plain

SCHEMA = "paper-reference-correction-validation-v1"
REPORT_FIELDS = {
    "file", "key_old", "key_new", "doi_old", "doi_new", "action",
    "method", "confidence", "title_old", "title_new",
}
CHANGED_ACTIONS = {"upgraded", "field_filled"}
UNCHANGED_ACTIONS = {"unchanged", "failed", "skipped", "skipped_resolved"}


def entries(path: Path) -> dict[str, dict[str, Any]]:
    parser = BibTexParser(common_strings=True, ignore_nonstandard_types=False)
    with path.open(encoding="utf-8") as handle:
        database = bibtexparser.load(handle, parser=parser)
    return {entry["ID"]: entry for entry in database.entries}


def validate(source: Path, candidate: Path, report: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        old = entries(source)
        new = entries(candidate)
    except Exception as exc:
        return {"schema_version": SCHEMA, "passed": False, "changed_keys": [], "incomplete_keys": [],
                "errors": [f"BibTeX parse failed: {exc}"]}
    if set(old) != set(new):
        errors.append("candidate changed bibliography key coverage")

    records: list[dict[str, Any]] = []
    try:
        for line in report.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("record is not an object")
                records.append(value)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid correction JSONL report: {exc}")

    seen: set[str] = set()
    changed_keys: list[str] = []
    incomplete_keys: list[str] = []
    for record in records:
        if not REPORT_FIELDS.issubset(record):
            errors.append("correction report has an invalid record")
            continue
        key = record["key_old"]
        action = record["action"]
        if not isinstance(key, str) or not key or key in seen:
            errors.append(f"correction report has an invalid or duplicate key: {key!r}")
            continue
        seen.add(key)
        if record["key_new"] != key:
            errors.append(f"updater changed a citation key: {key}")
        if action not in CHANGED_ACTIONS | UNCHANGED_ACTIONS:
            errors.append(f"correction report has an unsupported action for {key}: {action!r}")
            continue
        actual_change = key in old and key in new and old[key] != new[key]
        if actual_change != (action in CHANGED_ACTIONS):
            errors.append(f"correction report action does not match candidate content: {key}")
        if key in old and key in new:
            expected = {
                "doi_old": doi_normalize(old[key].get("doi")),
                "doi_new": doi_normalize(new[key].get("doi")),
                "title_old": latex_to_plain(old[key].get("title") or ""),
                "title_new": new[key].get("title"),
            }
            for field, value in expected.items():
                if record[field] != value:
                    errors.append(f"correction report {field} does not match bibliography content: {key}")
        if record["file"] != str(source):
            errors.append(f"correction report source file does not match audit snapshot: {key}")
        if record["method"] is not None and not isinstance(record["method"], str):
            errors.append(f"correction report has an invalid method: {key}")
        if record["confidence"] is not None and (
            not isinstance(record["confidence"], (int, float)) or isinstance(record["confidence"], bool)
        ):
            errors.append(f"correction report has an invalid confidence: {key}")
        if actual_change:
            changed_keys.append(key)
        if action == "failed":
            incomplete_keys.append(key)
    if seen != set(old):
        errors.append("correction report does not cover each bibliography key exactly once")
    return {
        "schema_version": SCHEMA,
        "passed": not errors,
        "changed_keys": sorted(changed_keys),
        "incomplete_keys": sorted(incomplete_keys),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = validate(args.source, args.candidate, args.report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for error in result["errors"]:
        print(f"ERROR reference_correction_validation: {error}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
