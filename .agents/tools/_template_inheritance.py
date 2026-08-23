#!/usr/bin/env python3
"""Load and validate the shared template inheritance policy."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

POLICY_RELATIVE = Path(".agents/template-inheritance.json")
SCHEMA_VERSION = "paper-template-inheritance-v1"


def _relative_path(value: Any, label: str, *, prefix: bool | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if prefix is not None and prefix != value.endswith("/"):
        expectation = "end with /" if prefix else "not end with /"
        raise ValueError(f"{label} must {expectation}: {value}")
    candidate = PurePosixPath(value.rstrip("/"))
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise ValueError(f"unsafe path in {label}: {value}")
    return candidate.as_posix() + ("/" if value.endswith("/") else "")


def _path_list(
    section: dict[str, Any], key: str, *, prefix: bool | None = None
) -> tuple[str, ...]:
    values = section.get(key)
    if not isinstance(values, list):
        raise ValueError(f"template inheritance {key} must be a list")
    normalized = tuple(
        _relative_path(value, f"{key}[{index}]", prefix=prefix)
        for index, value in enumerate(values)
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"template inheritance {key} contains duplicates")
    return normalized


def parse_inheritance_policy(payload: bytes | str) -> dict[str, Any]:
    try:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid template inheritance policy: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported template inheritance policy schema")

    creation = data.get("template_creation")
    if not isinstance(creation, dict) or creation.get("inheritance") != "all-tracked-files":
        raise ValueError("template_creation.inheritance must be all-tracked-files")
    command = creation.get("post_creation_command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("template_creation.post_creation_command must be non-empty")

    adoption = data.get("adoption")
    sync = data.get("sync")
    if not isinstance(adoption, dict) or not isinstance(sync, dict):
        raise ValueError("template inheritance policy requires adoption and sync objects")
    if adoption.get("fallback") != "manual":
        raise ValueError("adoption.fallback must be manual")
    if sync.get("fallback") != "three-way":
        raise ValueError("sync.fallback must be three-way")

    adoption["required_paths"] = _path_list(adoption, "required_paths")
    adoption["safe_paths"] = _path_list(adoption, "safe_paths")
    adoption["safe_prefixes"] = _path_list(adoption, "safe_prefixes", prefix=True)
    adoption["ignored_paths"] = _path_list(adoption, "ignored_paths")
    adoption["manual_paths"] = _path_list(adoption, "manual_paths")
    sync["manual_paths"] = _path_list(sync, "manual_paths")
    sync["ignored_paths"] = _path_list(sync, "ignored_paths")

    manifest = data.get("vendored_skills_manifest")
    data["vendored_skills_manifest"] = _relative_path(
        manifest, "vendored_skills_manifest"
    )
    return data


def load_inheritance_policy(root: Path) -> dict[str, Any]:
    path = root / POLICY_RELATIVE
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular template inheritance policy: {POLICY_RELATIVE}")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read template inheritance policy: {exc}") from exc
    return parse_inheritance_policy(payload)


def combine_inheritance_policies(
    current: dict[str, Any], target: dict[str, Any]
) -> dict[str, Any]:
    """Combine policies conservatively so either revision can protect a path."""

    def union(section: str, key: str) -> tuple[str, ...]:
        return tuple(sorted(set(current[section][key]) | set(target[section][key])))

    def intersection(section: str, key: str) -> tuple[str, ...]:
        return tuple(sorted(set(current[section][key]) & set(target[section][key])))

    return {
        "schema_version": SCHEMA_VERSION,
        "template_creation": current["template_creation"],
        "adoption": {
            "required_paths": union("adoption", "required_paths"),
            "safe_paths": intersection("adoption", "safe_paths"),
            "safe_prefixes": intersection("adoption", "safe_prefixes"),
            "ignored_paths": intersection("adoption", "ignored_paths"),
            "manual_paths": union("adoption", "manual_paths"),
            "fallback": "manual",
        },
        "sync": {
            "manual_paths": union("sync", "manual_paths"),
            "ignored_paths": intersection("sync", "ignored_paths"),
            "fallback": "three-way",
        },
        "vendored_skills_manifest": current["vendored_skills_manifest"],
    }
