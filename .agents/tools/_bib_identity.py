#!/usr/bin/env python3
"""Deterministic normalization for duplicate bibliography identity checks."""
from __future__ import annotations

import re
import unicodedata
from typing import Any
from urllib.parse import urlsplit

LATEX_COMMAND_RE = re.compile(r"\\[a-zA-Z]+\*?")
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
FORMATTING_COMMANDS = {
    "emph", "textit", "textbf", "textrm", "textsf", "texttt", "textnormal",
    "mathrm", "mathbf", "mathit", "mathsf", "mathtt", "mathcal", "operatorname",
}


def normalize_doi(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if text.lower().startswith("doi:"):
        text = text[4:].strip()
    elif re.match(r"^https?://", text, re.IGNORECASE):
        parsed = urlsplit(text)
        if parsed.hostname and parsed.hostname.lower() in {"doi.org", "dx.doi.org", "www.doi.org"}:
            text = parsed.path.lstrip("/")
    return text.lower().rstrip(". ,")


def normalize_title(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKC", value).replace("~", " ")
    text = LATEX_COMMAND_RE.sub(
        lambda match: "" if match.group()[1:].rstrip("*").casefold() in FORMATTING_COMMANDS
        else f" {match.group()[1:].rstrip('*')} ",
        text,
    ).replace("{", "").replace("}", "")
    return " ".join(TOKEN_RE.findall(text.casefold()))


def duplicate_groups(values: dict[str, str]) -> list[dict[str, object]]:
    grouped: dict[str, list[str]] = {}
    for key, value in values.items():
        if value:
            grouped.setdefault(value, []).append(key)
    return [
        {"value": value, "keys": sorted(keys)}
        for value, keys in sorted(grouped.items())
        if len(keys) > 1
    ]
