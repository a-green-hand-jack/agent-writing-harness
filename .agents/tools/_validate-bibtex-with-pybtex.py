#!/usr/bin/env python3
"""Parse classic BibTeX with Pybtex and enforce the template's field contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from pybtex.database import parse_file
from _bib_identity import duplicate_groups, normalize_doi, normalize_title

SCHEMA = "paper-bibtex-format-report-v1"
YEAR_RE = re.compile(r"\d{4}")
REQUIRED_FIELDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "article": (("author",), ("title",), ("journal",), ("year",)),
    "book": (("author", "editor"), ("title",), ("publisher",), ("year",)),
    "booklet": (("title",),),
    "conference": (("author",), ("title",), ("booktitle",), ("year",)),
    "inbook": (("author", "editor"), ("title",), ("chapter", "pages"), ("publisher",), ("year",)),
    "incollection": (("author",), ("title",), ("booktitle",), ("publisher",), ("year",)),
    "inproceedings": (("author",), ("title",), ("booktitle",), ("year",)),
    "manual": (("title",),),
    "mastersthesis": (("author",), ("title",), ("school",), ("year",)),
    "misc": (),
    "phdthesis": (("author",), ("title",), ("school",), ("year",)),
    "proceedings": (("title",), ("year",)),
    "techreport": (("author",), ("title",), ("institution",), ("year",)),
    "unpublished": (("author",), ("title",), ("note",)),
}
CROSSREF_REQUIRED_FIELDS = {
    "conference": {"year"},
    "inbook": {"author", "editor", "title", "publisher", "year"},
    "incollection": {"publisher", "year"},
    "inproceedings": {"year"},
}


def direct_value(entry: Any, field: str) -> bool:
    if field in {"author", "editor"}:
        return bool(entry.persons.get(field))
    value = entry.fields.get(field)
    return isinstance(value, str) and bool(value.strip())


def has_value(entries: dict[str, Any], key: str, field: str, seen: set[str] | None = None) -> bool:
    entry = entries[key]
    if direct_value(entry, field):
        return True
    parent_key = entry.fields.get("crossref")
    if not isinstance(parent_key, str) or parent_key not in entries:
        return False
    visited = set() if seen is None else set(seen)
    if key in visited:
        return False
    visited.add(key)
    parent = entries[parent_key]
    if field == "booktitle" and entry.type.lower() in {"conference", "inbook", "incollection", "inproceedings"}:
        if direct_value(parent, "title"):
            return True
    if field not in CROSSREF_REQUIRED_FIELDS.get(entry.type.lower(), set()):
        return False
    return has_value(entries, parent_key, field, visited)


def validate(path: Path) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    try:
        bibliography = parse_file(str(path), bib_format="bibtex")
    except Exception as exc:
        return {
            "schema_version": SCHEMA,
            "checker": "pybtex",
            "passed": False,
            "keys": [],
            "errors": [{"key": "", "message": f"BibTeX parse failed: {exc}"}],
        }

    for key, entry in bibliography.entries.items():
        entry_type = entry.type.lower()
        parent_key = entry.fields.get("crossref")
        if isinstance(parent_key, str) and parent_key not in bibliography.entries:
            errors.append({"key": key, "message": f"crossref points to unknown entry: {parent_key}"})
        requirements = REQUIRED_FIELDS.get(entry_type)
        if requirements is None:
            errors.append({"key": key, "message": f"unsupported classic BibTeX entry type: {entry.type}"})
            continue
        for alternatives in requirements:
            if not any(has_value(bibliography.entries, key, field) for field in alternatives):
                errors.append({"key": key, "message": f"missing required field: {' or '.join(alternatives)}"})
        year = entry.fields.get("year")
        if year is None and isinstance(parent_key, str) and parent_key in bibliography.entries:
            year = bibliography.entries[parent_key].fields.get("year")
        if year is not None and not YEAR_RE.fullmatch(year.strip()):
            errors.append({"key": key, "message": "year must contain exactly four digits"})

    duplicate_dois = duplicate_groups({
        key: normalize_doi(entry.fields.get("doi")) for key, entry in bibliography.entries.items()
    })
    duplicate_titles = duplicate_groups({
        key: normalize_title(entry.fields.get("title")) for key, entry in bibliography.entries.items()
    })
    for group in duplicate_dois:
        errors.append({
            "key": ",".join(group["keys"]),
            "message": f"duplicate DOI identity: {group['value']}",
        })
    for group in duplicate_titles:
        errors.append({
            "key": ",".join(group["keys"]),
            "message": f"duplicate normalized title identity: {group['value']}",
        })

    return {
        "schema_version": SCHEMA,
        "checker": "pybtex",
        "passed": not errors,
        "keys": sorted(bibliography.entries),
        "duplicate_dois": duplicate_dois,
        "duplicate_titles": duplicate_titles,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bibliography", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = validate(args.bibliography)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for record in result["errors"]:
        label = f" {record['key']}" if record["key"] else ""
        print(f"ERROR bibtex_format{label}: {record['message']}")
    if result["passed"]:
        print(f"OK bibtex_format checker=pybtex references={len(result['keys'])}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
