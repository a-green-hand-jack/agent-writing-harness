#!/usr/bin/env python3
"""Validate task-level evaluation scenarios for every vendored skill wrapper."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCENARIOS_RELATIVE = Path(".agents/evals/vendored-skills/scenarios.json")
PROVENANCE_RELATIVE = Path(".agents/dependencies/vendored-skills/provenance.json")
SCHEMA_VERSION = "paper-vendored-skill-evals-v1"
MODES = {"positive", "boundary", "workflow"}
EXPECTED_WRAPPER_COUNT = 19
VENDOR_TARGET_RE = re.compile(r"- Skill: `\.agents/vendor/(?:ccfa-skills|writing-dna-skill)/")


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def read_json_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular file: {path}")
    try:
        content = path.read_bytes()
        data = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data, content


def check(root: Path) -> int:
    provenance_path = root / PROVENANCE_RELATIVE
    try:
        scenarios_data, _ = read_json_bytes(root / SCENARIOS_RELATIVE)
        provenance, provenance_bytes = read_json_bytes(provenance_path)
    except ValueError as exc:
        return error(str(exc))
    if scenarios_data.get("schema_version") != SCHEMA_VERSION:
        return error("unsupported vendored skill evaluation schema")
    actual_provenance_hash = hashlib.sha256(provenance_bytes).hexdigest()
    if scenarios_data.get("provenance_sha256") != actual_provenance_hash:
        return error("vendored skill provenance hash mismatch")
    fixture_bundle = scenarios_data.get("fixture_bundle")
    if not isinstance(fixture_bundle, dict):
        return error("vendored skill evaluations require fixture_bundle")
    fixture_relative = fixture_bundle.get("path")
    expected_fixture_hash = fixture_bundle.get("sha256")
    if not isinstance(fixture_relative, str) or not fixture_relative:
        return error("fixture_bundle.path must be non-empty")
    fixture_path = root / fixture_relative
    try:
        fixtures_data, fixture_bytes = read_json_bytes(fixture_path)
    except ValueError as exc:
        return error(str(exc))
    actual_fixture_hash = hashlib.sha256(fixture_bytes).hexdigest()
    if expected_fixture_hash != actual_fixture_hash:
        return error("vendored skill fixture bundle hash mismatch")
    if fixtures_data.get("schema_version") != "paper-vendored-skill-fixtures-v1":
        return error("unsupported vendored skill fixture schema")
    fixtures = fixtures_data.get("fixtures")
    if not isinstance(fixtures, dict):
        return error("vendored skill fixture bundle requires fixtures object")
    wrappers = provenance.get("wrappers")
    scenarios = scenarios_data.get("scenarios")
    if not isinstance(wrappers, list) or not all(isinstance(item, str) for item in wrappers):
        return error("vendored provenance requires a wrapper list")
    if not isinstance(scenarios, list) or not all(isinstance(item, dict) for item in scenarios):
        return error("vendored skill evaluations require a scenario list")

    actual_wrappers: set[str] = set()
    skills_root = root / ".agents/skills"
    if skills_root.is_dir():
        for skill_file in sorted(skills_root.glob("*/SKILL.md")):
            try:
                text = skill_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if VENDOR_TARGET_RE.search(text):
                actual_wrappers.add(skill_file.parent.name)
    if len(actual_wrappers) != EXPECTED_WRAPPER_COUNT:
        code = error(
            f"expected {EXPECTED_WRAPPER_COUNT} vendored wrapper directories, found {len(actual_wrappers)}"
        )
    else:
        code = 0
    provenance_wrappers = set(wrappers)
    if provenance_wrappers != actual_wrappers:
        code |= error("vendored provenance wrapper list does not match wrapper directories")

    seen_ids: set[str] = set()
    seen_skills: set[str] = set()
    exact_output_ids: set[str] = set()
    required_strings = ("id", "skill", "mode", "task")
    for index, scenario in enumerate(scenarios):
        for key in required_strings:
            value = scenario.get(key)
            if not isinstance(value, str) or not value.strip():
                code |= error(f"scenario {index} requires non-empty {key}")
        scenario_id = scenario.get("id")
        skill = scenario.get("skill")
        if isinstance(scenario_id, str):
            if scenario_id in seen_ids:
                code |= error(f"duplicate scenario id: {scenario_id}")
            seen_ids.add(scenario_id)
        if isinstance(skill, str):
            if skill in seen_skills:
                code |= error(f"multiple scenarios for wrapper: {skill}")
            seen_skills.add(skill)
        if scenario.get("mode") not in MODES:
            code |= error(f"scenario {scenario_id!r} has unsupported mode")
        requires_exact_output = scenario.get("requires_exact_output", False)
        if not isinstance(requires_exact_output, bool):
            code |= error(f"scenario {scenario_id!r} has invalid requires_exact_output")
        elif requires_exact_output and isinstance(scenario_id, str):
            exact_output_ids.add(scenario_id)
        for key in ("must", "must_not"):
            values = scenario.get(key)
            if not isinstance(values, list) or not values or not all(
                isinstance(value, str) and value.strip() for value in values
            ):
                code |= error(f"scenario {scenario_id!r} requires non-empty {key}")

    expected = set(wrappers)
    missing = sorted(expected - seen_skills)
    extra = sorted(seen_skills - expected)
    if missing:
        code |= error("missing vendored skill scenarios: " + ", ".join(missing))
    if extra:
        code |= error("unknown vendored skill scenarios: " + ", ".join(extra))
    fixture_ids = set(fixtures)
    if fixture_ids != seen_ids:
        code |= error("vendored skill fixture ids do not match scenario ids")
    for scenario_id, fixture in fixtures.items():
        if not isinstance(fixture, dict):
            code |= error(f"fixture {scenario_id!r} must be an object")
            continue
        if not isinstance(fixture.get("input"), str) or not fixture["input"].strip():
            code |= error(f"fixture {scenario_id!r} requires non-empty input")
        if scenario_id in exact_output_ids and (
            not isinstance(fixture.get("expected_output"), str)
            or not fixture["expected_output"].strip()
        ):
            code |= error(f"fixture {scenario_id!r} requires exact expected_output")
        observations = fixture.get("expected_observations")
        if not isinstance(observations, list) or not observations or not all(
            isinstance(value, str) and value.strip() for value in observations
        ):
            code |= error(f"fixture {scenario_id!r} requires expected_observations")
    if code == 0:
        print(f"OK vendored_skill_evals scenarios={len(scenarios)}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
