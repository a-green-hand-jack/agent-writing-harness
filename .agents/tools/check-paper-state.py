#!/usr/bin/env python3
"""Focused semantic checks for legacy paper-facing state.

This checker closes known gaps from real-paper mutation tests without trying to
replace scientific review. It validates cross-file identity, exception scope,
and actual venue-template use.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

INACTIVE = {"removed", "dropped", "superseded", "inactive", "archived"}
PLANNED = {"planned", "todo", "draft", "placeholder"}
PLACEHOLDER = {"", "todo", "tbd", "pending", "placeholder", "none", "null"}
OVERBROAD_PATH_PATTERNS = {
    "*",
    "**",
    "**/*",
    "paper/**",
    "paper/*.tex",
    "paper/**/*.tex",
    "paper/sections/**",
    "paper/sections/*.tex",
}
VENUE_COMMAND_RE = re.compile(
    r"\\(?:documentclass|usepackage|RequirePackage|input)\s*(?:\[[^\]]*\])?\s*\{([^{}]+)\}"
)


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def load(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in PLACEHOLDER
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def active(item: dict[str, Any]) -> bool:
    status = str(item.get("status", "")).strip().lower()
    return status not in INACTIVE and status not in PLANNED


def item_id(item: dict[str, Any], *fields: str) -> str | None:
    for field in fields:
        value = item.get(field)
        if meaningful(value):
            return str(value).strip()
    return None


def load_numbers(root: Path) -> list[dict[str, Any]]:
    registry = load(root, "state/numeric-registry.yaml")
    paths: list[str] = []
    index = registry.get("index")
    if meaningful(index):
        paths.append(str(index))
    paths.extend(str(value) for value in as_list(registry.get("groups")) if meaningful(value))

    records: list[dict[str, Any]] = []
    for relative in paths:
        doc = load(root, relative)
        for record in as_list(doc.get("numbers")):
            if isinstance(record, dict):
                records.append(record)
    return records


def check_numeric_binding(root: Path) -> int:
    claims_doc = load(root, "state/claim-evidence-map.yaml")
    claims = [item for item in as_list(claims_doc.get("claims")) if isinstance(item, dict) and active(item)]
    numbers = [item for item in load_numbers(root) if active(item)]

    code = 0
    claim_by_id: dict[str, dict[str, Any]] = {}
    number_by_id: dict[str, dict[str, Any]] = {}

    for claim in claims:
        claim_id = item_id(claim, "claim_id", "id")
        if not claim_id:
            code |= error("active claim missing claim_id")
            continue
        if claim_id in claim_by_id:
            code |= error(f"duplicate active claim_id: {claim_id}")
        claim_by_id[claim_id] = claim

    for number in numbers:
        numeric_id = item_id(number, "numeric_id", "id")
        if not numeric_id:
            code |= error("active numeric record missing numeric_id")
            continue
        if numeric_id in number_by_id:
            code |= error(f"duplicate active numeric_id: {numeric_id}")
        number_by_id[numeric_id] = number

    for claim_id, claim in claim_by_id.items():
        for numeric_id in [str(value) for value in as_list(claim.get("numeric_ids")) if meaningful(value)]:
            number = number_by_id.get(numeric_id)
            if number is None:
                code |= error(f"claim {claim_id} references missing active numeric_id: {numeric_id}")
                continue
            reciprocal = {str(value) for value in as_list(number.get("claim_ids")) if meaningful(value)}
            if claim_id not in reciprocal:
                strength = str(claim.get("claim_strength", "unspecified"))
                code |= error(
                    f"claim {claim_id} ({strength}) references {numeric_id}, but the numeric record does not reciprocate claim_ids"
                )

    for numeric_id, number in number_by_id.items():
        for claim_id in [str(value) for value in as_list(number.get("claim_ids")) if meaningful(value)]:
            claim = claim_by_id.get(claim_id)
            if claim is None:
                code |= error(f"numeric record {numeric_id} references missing active claim_id: {claim_id}")
                continue
            reciprocal = {str(value) for value in as_list(claim.get("numeric_ids")) if meaningful(value)}
            if numeric_id not in reciprocal:
                code |= error(
                    f"numeric record {numeric_id} references claim {claim_id}, but the claim does not reciprocate numeric_ids"
                )
    return code


def check_numeric_exceptions(root: Path) -> int:
    doc = load(root, "state/numbers/exceptions.yaml")
    code = 0
    for index, exception in enumerate(as_list(doc.get("exceptions")), start=1):
        if not isinstance(exception, dict) or not active(exception):
            continue
        pattern = str(exception.get("pattern", "")).strip()
        if not pattern or not re.search(r"\d", pattern):
            continue
        path_pattern = exception.get("path_pattern")
        if not meaningful(path_pattern):
            code |= error(
                f"numeric exception {index} ({pattern}) has no path_pattern and can mask unrelated active prose"
            )
            continue
        normalized = str(path_pattern).strip()
        if normalized in OVERBROAD_PATH_PATTERNS:
            code |= error(
                f"numeric exception {index} ({pattern}) uses an overbroad path_pattern: {normalized}"
            )
        if not meaningful(exception.get("reason")):
            code |= error(f"numeric exception {index} ({pattern}) missing reason")
    return code


def active_tex(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def configured_venue(doc: dict[str, Any]) -> bool:
    return any(
        meaningful(doc.get(field))
        for field in ("raw_template", "human_verified_at", "migration_exemption", "realkit_receipts")
    )


def resolve_tex_reference(root: Path, reference: str) -> bool:
    candidate = root / "paper" / reference
    if candidate.is_file():
        return True
    if candidate.suffix:
        return False
    return any((candidate.with_suffix(suffix)).is_file() for suffix in (".sty", ".cls", ".tex"))


def check_venue_usage(root: Path) -> int:
    doc = load(root, "state/conference-template.yaml")
    if not configured_venue(doc):
        return 0

    code = 0
    main_path = root / "paper/main.tex"
    preamble_path = root / "paper/venue_preamble.tex"
    if not main_path.is_file():
        return error("configured venue is missing paper/main.tex")
    main_text = active_tex(main_path.read_text(encoding="utf-8"))
    if not re.search(r"\\input\s*\{venue_preamble\}", main_text):
        code |= error("configured venue is not used: paper/main.tex must input venue_preamble")

    if not preamble_path.is_file():
        code |= error("configured venue is missing paper/venue_preamble.tex")
    else:
        preamble_text = active_tex(preamble_path.read_text(encoding="utf-8"))
        references = VENUE_COMMAND_RE.findall(preamble_text)
        if not references:
            code |= error("configured venue_preamble has no active class/package/input command")
        for reference in references:
            for item in [part.strip() for part in reference.split(",") if part.strip()]:
                if item.startswith("style/") and not resolve_tex_reference(root, item):
                    code |= error(f"configured venue preamble references missing paper asset: {item}")

    shim = doc.get("compat_shim")
    if meaningful(shim) and not (root / str(shim)).is_file():
        code |= error(f"configured venue compat_shim does not exist: {shim}")
    return code


def check(root: Path) -> int:
    code = 0
    code |= check_numeric_binding(root)
    code |= check_numeric_exceptions(root)
    code |= check_venue_usage(root)
    if code == 0:
        print("OK paper_state")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
