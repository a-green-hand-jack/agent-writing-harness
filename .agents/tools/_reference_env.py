#!/usr/bin/env python3
"""Load the allowlisted local reference-service configuration without shell evaluation."""
from __future__ import annotations

import os
from pathlib import Path

ALLOWED_KEYS = {"BIBTEX_CHECK_MAILTO", "OPENALEX_API_KEY", "S2_API_KEY"}


def load_reference_env(root: Path) -> list[str]:
    path = root / ".env"
    if not path.is_file():
        return []
    loaded: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f".env:{number} must be KEY=VALUE")
        key, value = (part.strip() for part in line.split("=", 1))
        if key not in ALLOWED_KEYS:
            raise ValueError(f".env:{number} unsupported key: {key}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif value.startswith(("\"", "'")) or value.endswith(("\"", "'")):
            raise ValueError(f".env:{number} has unmatched quotes")
        if value and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded
