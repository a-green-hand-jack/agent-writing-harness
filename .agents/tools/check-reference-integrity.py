#!/usr/bin/env python3
"""Validate bibliography identity records and claim-evidence review state."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from _citation_occurrences import (
    claim_fingerprint,
    scan_occurrences,
)

POLICY_START = "<!-- REFERENCE-INTEGRITY:START -->"
POLICY_END = "<!-- REFERENCE-INTEGRITY:END -->"
POLICY_SCHEMA = "paper-reference-integrity-policy-v1"
LEDGER_SCHEMAS = {"paper-reference-ledger-v1", "paper-reference-ledger-v2"}
LEDGER_SCHEMA = "paper-reference-ledger-v2"
SUPPORT_PROTOCOL_VERSION = "citation-support-protocol-v1"
REFERENCE_STATUSES = {"verified", "problematic", "unverified"}
HUMAN_REVIEW_STATES = {"pending", "human-confirmed", "human-rejected"}
REFERENCE_REVIEW_STATES = HUMAN_REVIEW_STATES | {"agent-resolved"}
SUPPORT_REVIEW_STATES = HUMAN_REVIEW_STATES | {"provisional", "disagreement"}
SUPPORT_VERDICTS = {"supported", "partially-supported", "unsupported", "contradicted", "source-unavailable"}
VERIFICATION_SOURCES = {"crossref", "openalex", "dblp", "openreview", "semantic-scholar", "publisher", "manual"}
STABLE_IDENTIFIERS = {"doi", "arxiv", "openalex", "dblp", "openreview", "semantic_scholar", "isbn", "url"}
USAGE_CLASSES = {"claim-support", "background", "method", "dataset", "other"}
NON_REFERENCE_ENTRY_TYPES = {"comment", "preamble", "string"}
CITE_RE = re.compile(r"\\(?:cite[a-zA-Z]*|nocite)\*?(?:\s*\[[^\]]*\])*\s*\{([^}]*)\}", re.DOTALL)
ACTIVATION_MARKER = "% REFERENCE_INTEGRITY_REQUIRED: references/ledger.json"
CANONICAL_BIBLIOGRAPHY = "paper/refs.bib"
CANONICAL_LEDGER = "references/ledger.json"


class IntegrityError(RuntimeError):
    pass


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


def warning(message: str) -> None:
    print(f"WARN {message}")


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def safe_relative_path(value: Any, field: str) -> Path:
    if not nonempty(value):
        raise IntegrityError(f"policy {field} must be a non-empty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise IntegrityError(f"policy {field} is unsafe: {value}")
    return Path(path.as_posix())


def project_path(root: Path, value: Any, field: str) -> Path:
    candidate = root / safe_relative_path(value, field)
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise IntegrityError(f"policy {field} escapes the repository through a symlink") from exc
    return candidate


def load_policy(root: Path) -> dict[str, Any] | None:
    publication = root / "PUBLICATION.md"
    if not publication.is_file():
        return None
    text = publication.read_text(encoding="utf-8")
    has_start = POLICY_START in text
    has_end = POLICY_END in text
    if not has_start and not has_end:
        return None
    if not has_start or not has_end:
        raise IntegrityError("PUBLICATION.md has an incomplete reference-integrity policy block")
    if text.count(POLICY_START) != 1 or text.count(POLICY_END) != 1:
        raise IntegrityError("PUBLICATION.md must contain exactly one reference-integrity policy block")
    start = text.index(POLICY_START) + len(POLICY_START)
    end = text.index(POLICY_END, start)
    body = text[start:end].strip()
    fenced = re.fullmatch(r"```json\s*(.*?)\s*```", body, re.DOTALL)
    if not fenced:
        raise IntegrityError("reference-integrity policy must be one fenced JSON object")
    try:
        policy = json.loads(fenced.group(1))
    except json.JSONDecodeError as exc:
        raise IntegrityError(f"invalid reference-integrity policy JSON: {exc}") from exc
    if not isinstance(policy, dict):
        raise IntegrityError("reference-integrity policy must be a JSON object")
    if policy.get("schema_version") != POLICY_SCHEMA:
        raise IntegrityError("unsupported reference-integrity policy schema_version")
    if policy.get("enforcement") not in {"enforced", "disabled"}:
        raise IntegrityError("reference-integrity policy enforcement must be enforced or disabled")
    if policy.get("ledger") != CANONICAL_LEDGER:
        raise IntegrityError(f"v1 reference-integrity policy ledger must be {CANONICAL_LEDGER}")
    if policy.get("bibliography") != CANONICAL_BIBLIOGRAPHY:
        raise IntegrityError(f"v1 reference-integrity policy bibliography must be {CANONICAL_BIBLIOGRAPHY}")
    return policy


def policy_required(root: Path) -> bool:
    bibliography = root / "paper/refs.bib"
    return bibliography.is_file() and ACTIVATION_MARKER in bibliography.read_text(encoding="utf-8")


def adoption_required(root: Path) -> bool:
    path = root / ".agents/template-sync.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"invalid downstream-local template sync metadata: {exc}") from exc
    if not isinstance(data, dict):
        raise IntegrityError("downstream-local template sync metadata must be a JSON object")
    state = data.get("reference_integrity")
    if state is None:
        return False
    if not isinstance(state, dict) or not isinstance(state.get("adopted"), bool):
        raise IntegrityError("template sync reference_integrity.adopted must be boolean")
    return state["adopted"]


def enforcement_policy(root: Path) -> dict[str, Any] | None:
    policy = load_policy(root)
    marker = policy_required(root)
    adopted = adoption_required(root)
    if adopted and policy is None:
        raise IntegrityError("reference-integrity activation marker requires the protected PUBLICATION.md policy")
    if adopted and not marker:
        raise IntegrityError("adopted reference integrity requires the refs.bib activation marker")
    if adopted and policy is not None and policy["enforcement"] != "enforced":
        raise IntegrityError("reference-integrity activation marker forbids disabling enforcement")
    if not adopted and (marker or (policy is not None and policy["enforcement"] == "enforced")):
        raise IntegrityError("reference-integrity policy/marker requires downstream-local adoption state")
    return policy


def strip_tex_or_bib_comments(text: str) -> str:
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


def matching_entry_end(text: str, open_index: int, opener: str) -> int:
    closer = "}" if opener == "{" else ")"
    depth = 1
    quoted = False
    escaped = False
    brace_depth = 0
    for index in range(open_index + 1, len(text)):
        character = text[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == '"':
            quoted = not quoted
            continue
        if quoted:
            continue
        if opener == "(" and character == "{":
            brace_depth += 1
        elif opener == "(" and character == "}" and brace_depth:
            brace_depth -= 1
        elif character == opener:
            depth += 1
        elif character == closer and brace_depth == 0:
            depth -= 1
            if depth == 0:
                return index
    raise IntegrityError("unterminated BibTeX entry")


def bibtex_keys(text: str) -> list[str]:
    active = strip_tex_or_bib_comments(text)
    header = re.compile(r"@\s*([A-Za-z]+)\s*([({])")
    keys: list[str] = []
    cursor = 0
    while True:
        match = header.search(active, cursor)
        if match is None:
            break
        entry_type = match.group(1).lower()
        opener = match.group(2)
        open_index = match.end() - 1
        end = matching_entry_end(active, open_index, opener)
        if entry_type not in NON_REFERENCE_ENTRY_TYPES:
            content = active[open_index + 1 : end]
            comma = content.find(",")
            if comma < 0:
                raise IntegrityError(f"BibTeX @{entry_type} entry has no citation-key separator")
            key = content[:comma].strip()
            if not key or any(character.isspace() for character in key):
                raise IntegrityError(f"BibTeX @{entry_type} entry has an invalid citation key: {key!r}")
            keys.append(key)
        cursor = end + 1
    return keys


def cited_keys(root: Path) -> set[str]:
    result: set[str] = set()
    paper = root / "paper"
    if not paper.is_dir():
        return result
    for path in sorted(paper.rglob("*.tex")):
        active = strip_tex_or_bib_comments(path.read_text(encoding="utf-8"))
        for group in CITE_RE.findall(active):
            for key in group.split(","):
                candidate = key.strip()
                if candidate and candidate != "*":
                    result.add(candidate)
    return result


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise IntegrityError(f"missing reference ledger: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IntegrityError(f"invalid reference ledger JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise IntegrityError("reference ledger must be a JSON object")
    if data.get("schema_version") not in LEDGER_SCHEMAS:
        raise IntegrityError("unsupported reference ledger schema_version")
    if not isinstance(data.get("references"), list):
        raise IntegrityError("reference ledger references must be an array")
    if not isinstance(data.get("claim_evidence"), list):
        raise IntegrityError("reference ledger claim_evidence must be an array")
    if not isinstance(data.get("citation_usages"), list):
        raise IntegrityError("reference ledger citation_usages must be an array")
    if data.get("schema_version") == LEDGER_SCHEMA:
        if not isinstance(data.get("citation_occurrences"), list):
            raise IntegrityError("reference ledger citation_occurrences must be an array")
    return data


def validate_reference_record(record: Any, profile: str, index: int) -> tuple[int, str | None]:
    label = f"ledger references[{index}]"
    if not isinstance(record, dict):
        return error(f"{label} must be an object"), None
    code = 0
    key = record.get("citation_key")
    if not nonempty(key):
        code |= error(f"{label}.citation_key must be non-empty")
        key = None
    status = record.get("status")
    if status not in REFERENCE_STATUSES:
        code |= error(f"{label}.status must be verified, problematic, or unverified")
    if not isinstance(record.get("identifiers"), dict):
        code |= error(f"{label}.identifiers must be an object")
    verification = record.get("verification")
    if not isinstance(verification, dict):
        code |= error(f"{label}.verification must be an object")
        verification = {}
    sources = verification.get("sources")
    if not isinstance(sources, list) or not all(nonempty(source) for source in sources):
        code |= error(f"{label}.verification.sources must be an array of non-empty strings")
        sources = []
    elif any(source not in VERIFICATION_SOURCES for source in sources):
        code |= error(f"{label}.verification.sources contains an unsupported source")
    checked_at = verification.get("checked_at")
    if checked_at is not None and not nonempty(checked_at):
        code |= error(f"{label}.verification.checked_at must be null or a non-empty string")
    elif nonempty(checked_at):
        try:
            dt.date.fromisoformat(checked_at)
        except ValueError:
            code |= error(f"{label}.verification.checked_at must be an ISO date")
    review = record.get("human_review")
    if not isinstance(review, dict):
        code |= error(f"{label}.human_review must be an object")
        review = {}
    review_state = review.get("state")
    if review_state not in REFERENCE_REVIEW_STATES:
        code |= error(f"{label}.human_review.state has an unsupported value")
    rationale = review.get("rationale")
    if not isinstance(rationale, str):
        code |= error(f"{label}.human_review.rationale must be a string")

    if status == "problematic":
        code |= error(f"reference {key or index} is problematic")
    elif status == "unverified":
        if profile == "release":
            code |= error(f"reference {key or index} remains unverified for release")
        else:
            warning(f"reference {key or index} is unverified")
    elif status == "verified":
        if not sources or not nonempty(checked_at):
            code |= error(f"verified reference {key or index} lacks source records or checked_at")
        identifiers = record.get("identifiers", {})
        if not any(nonempty(identifiers.get(name)) for name in STABLE_IDENTIFIERS):
            code |= error(f"verified reference {key or index} lacks a supported stable identifier")

    if review_state == "human-rejected":
        code |= error(f"reference {key or index} was rejected by Human review")
    elif review_state == "agent-resolved" and status != "verified":
        code |= error(f"reference {key or index} cannot be agent-resolved unless verified")
    elif review_state == "agent-resolved" and not nonempty(rationale):
        code |= error(f"reference {key or index} agent resolution lacks rationale")
    elif profile == "release" and review_state not in {"human-confirmed", "agent-resolved"}:
        code |= error(f"reference {key or index} lacks resolved identity review for release")
    elif review_state == "pending":
        warning(f"reference {key or index} awaits Human review")
    return code, key


CLAIM_FIELDS = (
    "citation_key",
    "manuscript_claim",
    "manuscript_location",
    "source_locator",
    "evidence_excerpt_or_rationale",
    "human_review_state",
)


def validate_claim_record(record: Any, profile: str, index: int, reference_keys: set[str]) -> int:
    label = f"ledger claim_evidence[{index}]"
    if not isinstance(record, dict):
        return error(f"{label} must be an object")
    code = 0
    for field in CLAIM_FIELDS:
        if not nonempty(record.get(field)):
            code |= error(f"{label}.{field} must be non-empty")
    key = record.get("citation_key")
    if nonempty(key) and key not in reference_keys:
        code |= error(f"{label} points to unknown citation key: {key}")
    state = record.get("human_review_state")
    if nonempty(state) and state not in HUMAN_REVIEW_STATES:
        code |= error(f"{label}.human_review_state has an unsupported value")
    elif state == "human-rejected":
        code |= error(f"{label} was rejected by Human review")
    elif profile == "release" and state != "human-confirmed":
        code |= error(f"{label} lacks Human confirmation for release")
    elif state == "pending":
        warning(f"{label} awaits Human review")
    return code


def validate_usage_records(
    records: list[Any],
    profile: str,
    cited: set[str],
    reference_keys: set[str],
    claims: list[Any],
    check_claim_evidence_cross: bool = True,
) -> int:
    code = 0
    covered: set[str] = set()
    claim_keys = {
        record.get("citation_key")
        for record in claims
        if isinstance(record, dict) and nonempty(record.get("citation_key"))
    }
    for index, record in enumerate(records):
        label = f"ledger citation_usages[{index}]"
        if not isinstance(record, dict):
            code |= error(f"{label} must be an object")
            continue
        key = record.get("citation_key")
        location = record.get("manuscript_location")
        usage = record.get("classification")
        state = record.get("human_review_state")
        if not nonempty(key):
            code |= error(f"{label}.citation_key must be non-empty")
        elif key not in reference_keys:
            code |= error(f"{label} points to unknown citation key: {key}")
        else:
            covered.add(key)
        if not nonempty(location):
            code |= error(f"{label}.manuscript_location must be non-empty")
        if usage not in USAGE_CLASSES:
            code |= error(f"{label}.classification has an unsupported value")
        if state not in HUMAN_REVIEW_STATES:
            code |= error(f"{label}.human_review_state has an unsupported value")
        elif state == "human-rejected":
            code |= error(f"{label} was rejected by Human review")
        elif profile == "release" and state != "human-confirmed":
            code |= error(f"{label} lacks Human confirmation for release")
        elif state == "pending":
            warning(f"{label} awaits Human review")
        if usage == "claim-support" and check_claim_evidence_cross and key not in claim_keys:
            code |= error(f"{label} classifies {key} as claim-support without claim_evidence")
    for key in sorted(cited - covered):
        code |= error(f"cited reference lacks a reviewed citation_usages record: {key}")
    return code


def usage_class_by_key(records: list[Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        key = record.get("citation_key")
        usage = record.get("classification")
        if nonempty(key) and usage in USAGE_CLASSES:
            result[key] = usage
    return result


def validate_occurrence_records(
    records: list[Any], profile: str, current: list[dict[str, Any]], reference_keys: set[str]
) -> int:
    """Validate v2 citation-occurrence records and manuscript coverage."""
    code = 0
    seen: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        label = f"ledger citation_occurrences[{index}]"
        if not isinstance(record, dict):
            code |= error(f"{label} must be an object")
            continue
        occurrence_id = record.get("occurrence_id")
        if not nonempty(occurrence_id):
            code |= error(f"{label}.occurrence_id must be non-empty")
        elif occurrence_id in seen:
            code |= error(f"{label} duplicates occurrence_id: {occurrence_id}")
        else:
            seen.add(occurrence_id)
        if not nonempty(record.get("manuscript_location")):
            code |= error(f"{label}.manuscript_location must be non-empty")
        if not nonempty(record.get("command")):
            code |= error(f"{label}.command must be non-empty")
        keys = record.get("citation_keys")
        if not isinstance(keys, list) or not keys or not all(nonempty(key) for key in keys):
            code |= error(f"{label}.citation_keys must be a non-empty array of non-empty strings")
            keys = []
        for key in keys:
            if key not in reference_keys:
                code |= error(f"{label} cites unknown citation key: {key}")
        if not nonempty(record.get("claim_text")):
            code |= error(f"{label}.claim_text must be non-empty")
        fingerprint = record.get("claim_fingerprint")
        if not nonempty(fingerprint):
            code |= error(f"{label}.claim_fingerprint must be non-empty")
        state = record.get("review_state")
        if state not in SUPPORT_REVIEW_STATES:
            code |= error(f"{label}.review_state has an unsupported value")
        elif state == "human-rejected":
            code |= error(f"{label} was rejected by Human review")
        by_id[occurrence_id] = record

    current_by_id: dict[str, dict[str, Any]] = {item["occurrence_id"]: item for item in current}
    for occurrence in current:
        current_id = occurrence["occurrence_id"]
        if current_id not in by_id:
            code |= error(
                f"cited occurrence lacks a citation_occurrences record: "
                f"{occurrence['manuscript_location']} {occurrence['citation_keys']}"
            )
            continue
        record = by_id[current_id]
        if profile == "release":
            if record.get("review_state") == "pending":
                code |= error(f"occurrence {current_id} remains pending for release")
            if set(record.get("citation_keys") or []) != set(occurrence["citation_keys"]):
                code |= error(f"occurrence {current_id} citation set changed since record")
            if record.get("claim_fingerprint") != occurrence["claim_fingerprint"]:
                code |= error(f"occurrence {current_id} claim fingerprint changed since record")
        elif (
            set(record.get("citation_keys") or []) != set(occurrence["citation_keys"])
            or record.get("claim_fingerprint") != occurrence["claim_fingerprint"]
        ):
            warning(f"occurrence {current_id} drifted since record; re-inventory before review")

    for occurrence_id, record in sorted(by_id.items()):
        if occurrence_id in current_by_id:
            continue
        moved = any(
            record.get("claim_fingerprint") == item["claim_fingerprint"]
            and set(record.get("citation_keys") or []) == set(item["citation_keys"])
            for item in current
        )
        if moved:
            warning(f"occurrence {occurrence_id} moved; evidence preserved by fingerprint")
        else:
            code |= error(f"occurrence {occurrence_id} is stale or removed from the manuscript")
    return code


def validate_evidence_record(
    record: Any,
    profile: str,
    index: int,
    occurrences: list[dict[str, Any]],
    reference_keys: set[str],
    usage_by_key: dict[str, str],
) -> int:
    label = f"ledger claim_evidence[{index}]"
    if not isinstance(record, dict):
        return error(f"{label} must be an object")
    code = 0
    evidence_id = record.get("evidence_id")
    if not nonempty(evidence_id):
        code |= error(f"{label}.evidence_id must be non-empty")
    occurrence_id = record.get("occurrence_id")
    if not nonempty(occurrence_id):
        code |= error(f"{label}.occurrence_id must be non-empty")
        occurrence_id = None
    key = record.get("citation_key")
    if not nonempty(key):
        code |= error(f"{label}.citation_key must be non-empty")
        key = None
    elif key not in reference_keys:
        code |= error(f"{label} points to unknown citation key: {key}")

    matched_occurrence: dict[str, Any] | None = None
    for occurrence in occurrences:
        if occurrence.get("occurrence_id") == occurrence_id:
            matched_occurrence = occurrence
            break
    if occurrence_id is not None and matched_occurrence is None:
        code |= error(f"{label} points to unknown occurrence: {occurrence_id}")
    elif matched_occurrence is not None and key is not None:
        if key not in (matched_occurrence.get("citation_keys") or []):
            code |= error(f"{label} cites {key} outside occurrence {occurrence_id}")
        recorded_fingerprint = record.get("claim_fingerprint")
        if not nonempty(recorded_fingerprint):
            code |= error(f"{label}.claim_fingerprint must be non-empty")
        elif recorded_fingerprint != matched_occurrence.get("claim_fingerprint"):
            if profile == "release":
                code |= error(f"{label} is stale: claim fingerprint changed since evidence")
            else:
                warning(f"{label} is stale: claim fingerprint changed since evidence")

    protocol = record.get("protocol_version")
    if protocol != SUPPORT_PROTOCOL_VERSION:
        if profile == "release":
            code |= error(f"{label} is stale: unsupported protocol_version: {protocol}")
        else:
            warning(f"{label} uses unsupported protocol_version: {protocol}")

    source_identity = record.get("source_identity")
    if not isinstance(source_identity, dict):
        code |= error(f"{label}.source_identity must be an object")
        source_identity = {}
    if not any(nonempty(source_identity.get(name)) for name in STABLE_IDENTIFIERS) and not nonempty(
        source_identity.get("source_hash")
    ):
        code |= error(f"{label}.source_identity lacks a stable identifier or source_hash")

    passage = record.get("passage")
    if not isinstance(passage, dict):
        code |= error(f"{label}.passage must be an object")
        passage = {}
    if not nonempty(passage.get("text")):
        code |= error(f"{label}.passage.text must be non-empty")
    if not nonempty(passage.get("locator")):
        code |= error(f"{label}.passage.locator must be non-empty")
    if not nonempty(passage.get("hash")):
        code |= error(f"{label}.passage.hash must be non-empty")
    if not nonempty(passage.get("origin")):
        code |= error(f"{label}.passage.origin must be non-empty")

    assessment = record.get("assessment")
    if not isinstance(assessment, dict):
        code |= error(f"{label}.assessment must be an object")
        assessment = {}
    verdict = assessment.get("verdict")
    if verdict not in SUPPORT_VERDICTS:
        code |= error(f"{label}.assessment.verdict has an unsupported value")
    for field in ("supported_parts", "unsupported_parts", "contradictions", "missing_qualifiers"):
        value = assessment.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            code |= error(f"{label}.assessment.{field} must be an array of strings")
    if not nonempty(assessment.get("recommended_action")):
        code |= error(f"{label}.assessment.recommended_action must be non-empty")

    state = record.get("review_state")
    if state not in SUPPORT_REVIEW_STATES:
        code |= error(f"{label}.review_state has an unsupported value")
    elif state == "human-rejected":
        code |= error(f"{label} was rejected by Human review")
    elif state == "disagreement" and profile == "release":
        code |= error(f"{label} has unresolved disagreement for release")

    updated_at = record.get("updated_at")
    if updated_at is not None and not nonempty(updated_at):
        code |= error(f"{label}.updated_at must be null or a non-empty string")
    elif nonempty(updated_at):
        try:
            dt.date.fromisoformat(updated_at)
        except ValueError:
            code |= error(f"{label}.updated_at must be an ISO date")

    is_claim_support = key is not None and usage_by_key.get(key) == "claim-support"
    if verdict == "source-unavailable":
        if profile == "release" and is_claim_support:
            code |= error(f"{label} is unresolved: source unavailable for substantive claim")
        else:
            warning(f"{label} has no retrievable source evidence")
    if is_claim_support and profile == "release" and state != "human-confirmed":
        code |= error(f"{label} lacks Human confirmation for release")
    elif is_claim_support and state == "pending":
        warning(f"{label} awaits review")
    elif is_claim_support and state == "provisional":
        warning(f"{label} is provisional and awaits Human confirmation")
    elif state == "disagreement":
        warning(f"{label} awaits a Human decision")
    return code


def validate_v2_claim_evidence_coverage(
    occurrences: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    usage_by_key: dict[str, str],
    profile: str,
) -> int:
    """Release rejects substantive occurrences without confirmed support."""
    code = 0
    covered: set[tuple[str, str]] = set()
    for record in evidence:
        if not isinstance(record, dict):
            continue
        occurrence_id = record.get("occurrence_id")
        key = record.get("citation_key")
        if nonempty(occurrence_id) and nonempty(key):
            covered.add((occurrence_id, key))
    for occurrence in occurrences:
        claim_keys = occurrence.get("citation_keys") or []
        substantive = [key for key in claim_keys if usage_by_key.get(key) == "claim-support"]
        if not substantive:
            continue
        for key in substantive:
            if (occurrence.get("occurrence_id"), key) not in covered:
                if profile == "release":
                    code |= error(
                        f"substantive occurrence {occurrence.get('occurrence_id')} ({key}) "
                        "lacks support evidence"
                    )
                else:
                    warning(
                        f"substantive occurrence {occurrence.get('occurrence_id')} ({key}) "
                        "lacks support evidence"
                    )
    return code


def check_v2_support(
    root: Path,
    ledger: dict[str, Any],
    profile: str,
    reference_keys: set[str],
    usage_records: list[Any],
) -> int:
    code = 0
    current = scan_occurrences(root)
    occurrences = ledger.get("citation_occurrences") or []
    code |= validate_occurrence_records(occurrences, profile, current, reference_keys)
    usage_by_key = usage_class_by_key(usage_records)
    for index, record in enumerate(ledger.get("claim_evidence") or []):
        code |= validate_evidence_record(
            record, profile, index, occurrences, reference_keys, usage_by_key
        )
    code |= validate_v2_claim_evidence_coverage(occurrences, ledger.get("claim_evidence") or [], usage_by_key, profile)
    if code == 0 and profile == "release":
        print(f"OK reference_integrity support occurrences={len(current)} evidence={len(ledger.get('claim_evidence') or [])}")
    return code


def check(root: Path, profile: str) -> int:
    try:
        policy = enforcement_policy(root)
    except IntegrityError as exc:
        return error(str(exc))
    if policy is None or policy["enforcement"] != "enforced":
        print("SKIP reference_integrity policy not enabled")
        return 0

    try:
        bibliography = project_path(root, policy["bibliography"], "bibliography")
        ledger_path = project_path(root, policy["ledger"], "ledger")
        if not bibliography.is_file():
            raise IntegrityError(f"missing bibliography: {bibliography.relative_to(root)}")
        bib_keys = bibtex_keys(bibliography.read_text(encoding="utf-8"))
        ledger = load_ledger(ledger_path)
    except (IntegrityError, OSError) as exc:
        return error(str(exc))

    code = 0
    for key in duplicate_values(bib_keys):
        code |= error(f"duplicate BibTeX citation key: {key}")

    ledger_keys: list[str] = []
    for index, record in enumerate(ledger["references"]):
        record_code, key = validate_reference_record(record, profile, index)
        code |= record_code
        if key is not None:
            ledger_keys.append(key)
    for key in duplicate_values(ledger_keys):
        code |= error(f"duplicate reference ledger citation key: {key}")

    bib_set = set(bib_keys)
    ledger_set = set(ledger_keys)
    for key in sorted(bib_set - ledger_set):
        code |= error(f"BibTeX citation key missing from reference ledger: {key}")
    for key in sorted(ledger_set - bib_set):
        code |= error(f"reference ledger key missing from BibTeX: {key}")
    cited = cited_keys(root)
    for key in sorted(cited - bib_set):
        code |= error(f"paper cites a key missing from BibTeX: {key}")

    ledger_version = ledger.get("schema_version")
    if ledger_version == LEDGER_SCHEMA:
        # v2: claim_evidence records use the occurrence-aware support schema.
        code |= validate_usage_records(
            ledger["citation_usages"],
            profile,
            cited & bib_set,
            ledger_set,
            ledger["claim_evidence"],
            check_claim_evidence_cross=False,
        )
        code |= check_v2_support(root, ledger, profile, ledger_set, ledger["citation_usages"])
    else:
        for index, record in enumerate(ledger["claim_evidence"]):
            code |= validate_claim_record(record, profile, index, ledger_set)
        code |= validate_usage_records(
            ledger["citation_usages"], profile, cited & bib_set, ledger_set, ledger["claim_evidence"]
        )
        if profile == "release":
            warning(
                "ledger v1 lacks occurrence-level claim support; "
                "run reference-evidence.py migrate before releasing"
            )

    if code == 0:
        print(
            "OK reference_integrity "
            f"profile={profile} references={len(bib_keys)} usages={len(ledger['citation_usages'])} "
            f"claim_evidence={len(ledger['claim_evidence'])}"
        )
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--profile", choices=("draft", "release"), default="draft")
    parser.add_argument(
        "--policy-enabled",
        action="store_true",
        help="exit 0 only when the protected publication policy explicitly enables enforcement",
    )
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if args.policy_enabled:
        try:
            policy = enforcement_policy(root)
        except IntegrityError as exc:
            error(str(exc))
            return 2
        if policy is not None and policy["enforcement"] == "enforced":
            print("ENABLED reference_integrity")
            return 0
        print("DISABLED reference_integrity")
        return 1
    return check(root, args.profile)


if __name__ == "__main__":
    sys.exit(main())
