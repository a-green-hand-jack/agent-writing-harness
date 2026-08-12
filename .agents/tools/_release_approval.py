"""Structured Human approval grammar shared by release record tools."""
from __future__ import annotations

import datetime as dt
import re
import unicodedata

APPROVAL_RE = re.compile(
    r"Approved by (?:(?P<display>[^\[\]]+) )?"
    r"\[id:@(?P<handle>[A-Za-z0-9](?:[A-Za-z0-9._-]{0,62}))\] "
    r"on (?P<date>\d{4}-\d{2}-\d{2})"
)


def valid_human_approval(value: str) -> bool:
    if "`" in value or any(
        unicodedata.category(character).startswith("C") for character in value
    ):
        return False
    match = APPROVAL_RE.fullmatch(value)
    if match is None:
        return False
    display = match.group("display")
    if display is not None and (display != display.strip() or not display):
        return False
    try:
        dt.date.fromisoformat(match.group("date"))
    except ValueError:
        return False
    return True
