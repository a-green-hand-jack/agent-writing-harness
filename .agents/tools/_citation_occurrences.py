#!/usr/bin/env python3
"""Shared TeX citation-occurrence scanner for claim-to-citation support."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Any

CITE_RE = re.compile(r"\\(?:cite[a-zA-Z]*|nocite)\*?(?:\s*\[[^\]]*\])*\s*\{([^}]*)\}", re.DOTALL)
PLACEHOLDER_RE = re.compile(r"\\(?:cite[a-zA-Z]*|nocite)\*?(?:\s*\[[^\]]*\])*\s*\{[^}]*\}")
SENTENCE_HARD_END_RE = re.compile(r"[.!?]\s+|\n\s*\n")
MAX_SENTENCE_WINDOW = 600


def strip_tex_or_bib_comments(text: str) -> str:
    """Remove TeX comments ('%' to end of line) while honoring escapes."""
    lines: list[str] = []
    for line in text.splitlines():
        cut = len(line)
        for index, character in enumerate(line):
            if character != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cut = index
                break
        lines.append(line[:cut])
    return "\n".join(lines)


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sentence_window(active: str, start: int, end: int) -> tuple[str, bool]:
    """Return the enclosing sentence around [start, end) in the active text.

    Expands to the previous and next sentence boundary, capping each side at
    MAX_SENTENCE_WINDOW characters and trimming at whitespace. Returns
    (window_text, truncated).
    """
    before = active[:start]
    after = active[end:]
    hard_before = [match.start() for match in SENTENCE_HARD_END_RE.finditer(before)]
    left = (hard_before[-1] + 1) if hard_before else 0
    soft_before = before.rfind(" ", max(left, start - MAX_SENTENCE_WINDOW))
    if soft_before > left:
        left = soft_before + 1
    if start - left > MAX_SENTENCE_WINDOW:
        left = before.rfind(" ", start - MAX_SENTENCE_WINDOW)
        if left < 0:
            left = start - MAX_SENTENCE_WINDOW

    hard_after = [match.end() for match in SENTENCE_HARD_END_RE.finditer(after)]
    right = end
    if hard_after:
        right = end + hard_after[0]
    if right - end > MAX_SENTENCE_WINDOW:
        right = end + MAX_SENTENCE_WINDOW
        right = max(end, after.rfind(" ", 0, right))
        if right <= end:
            right = end + MAX_SENTENCE_WINDOW

    window = active[left:right]
    truncated = start - left >= MAX_SENTENCE_WINDOW or right - end >= MAX_SENTENCE_WINDOW
    return _collapse_whitespace(window), truncated


def claim_fingerprint(claim_text: str) -> str:
    """Stable fingerprint over claim prose with citation commands neutralized.

    Citation keys are tracked separately, so changing or reordering the cited
    keys does not change the prose fingerprint; editing the prose does.
    """
    normalized = _collapse_whitespace(PLACEHOLDER_RE.sub("CITE", claim_text))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def occurrence_id(fingerprint: str, keys: list[str]) -> str:
    """Deterministic occurrence identity from prose fingerprint and key set.

    Location is intentionally excluded so formatting-only movement preserves
    the occurrence identity and its evidence, per the ledger contract.
    """
    material = fingerprint + "|" + ",".join(sorted(keys))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"occ_{digest[:16]}"


def scan_occurrences(root: Path) -> list[dict[str, Any]]:
    """Inventory every citation occurrence in paper/**/*.tex.

    Returns one record per occurrence with manuscript_location (relative
    path and line), command, citation_keys, claim_text, claim_text_truncated,
    claim_fingerprint, and occurrence_id.
    """
    occurrences: list[dict[str, Any]] = []
    paper = root / "paper"
    if not paper.is_dir():
        return occurrences
    for path in sorted(paper.rglob("*.tex")):
        text = path.read_text(encoding="utf-8")
        active = strip_tex_or_bib_comments(text)
        for match in CITE_RE.finditer(active):
            keys = [key.strip() for key in match.group(1).split(",") if key.strip() and key.strip() != "*"]
            if not keys:
                continue
            line = active.count("\n", 0, match.start()) + 1
            command_match = re.match(r"\\([A-Za-z]+)", active[match.start() :])
            command = command_match.group(1) if command_match else "cite"
            claim_text, truncated = _sentence_window(active, match.start(), match.end())
            fingerprint = claim_fingerprint(claim_text)
            relative = path.relative_to(root).as_posix()
            occurrences.append(
                {
                    "occurrence_id": occurrence_id(fingerprint, keys),
                    "manuscript_location": f"{relative}:{line}",
                    "command": command,
                    "citation_keys": keys,
                    "claim_text": claim_text,
                    "claim_text_truncated": truncated,
                    "claim_fingerprint": fingerprint,
                }
            )
    return occurrences


def location_without_line(location: str) -> str:
    """Strip the trailing ':line' from a manuscript_location."""
    return location.rsplit(":", 1)[0] if ":" in location else location


def evidence_id(occurrence_id: str, citation_key: str) -> str:
    material = occurrence_id + "|" + citation_key
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"ev_{digest[:16]}"


def normalize_posix_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = PurePosixPath(value.strip())
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    return candidate.as_posix()
