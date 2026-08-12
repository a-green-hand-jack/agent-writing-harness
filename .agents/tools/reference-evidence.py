#!/usr/bin/env python3
"""Standard-library CLI for claim-to-citation evidence support.

Commands:
  inventory  - inventory TeX citation occurrences with claim text and fingerprint
  resolve    - resolve a known citation (key, DOI, arXiv, OpenReview, title, URL)
  search     - discover candidates for an unknown citation need
  passages   - retrieve exact evidence passages for a resolved paper
  packet     - build a claim/source/assessment support packet for semantic review
  record     - atomically record support evidence into the ledger (staleness guarded)
  status     - summarize ledger support state offline
  migrate    - explicitly migrate a paper-reference-ledger-v1 ledger to v2

The CLI never performs semantic judgments, never writes BibTeX, never launches
model calls, and never writes human-confirmed review state without an explicit
approval note. Provider failures are classified and cached; they are never
negative scientific evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html as html_lib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from _citation_occurrences import (
    claim_fingerprint,
    evidence_id,
    normalize_posix_path,
    scan_occurrences,
)

TIMEOUT_SECONDS = 15
USER_AGENT = "ccfa-writing-paper-template/reference-evidence (contact via repo)"
SUPPORT_PROTOCOL_VERSION = "citation-support-protocol-v1"
SUPPORT_VERDICTS = {
    "supported",
    "partially-supported",
    "unsupported",
    "contradicted",
    "source-unavailable",
}
SUPPORT_REVIEW_STATES = {"pending", "provisional", "human-confirmed", "human-rejected", "disagreement"}
PROVIDER_OUTCOMES = {
    "ok",
    "rate-limited",
    "provider-unavailable",
    "paper-not-indexed",
    "identity-ambiguous",
    "no-relevant-passage",
    "full-text-unavailable",
}
PASSAGE_ORIGINS = {
    "semantic-scholar-snippet",
    "semantic-scholar-abstract",
    "authoritative-html",
    "openreview",
    "aclanthology",
    "pubmed-central",
    "arxiv-html",
    "migrated-v1",
    "agent-pdf",
}
CANONICAL_LEDGER = "references/ledger.json"
DEFAULT_RUN_DIR = "dist/reference-support"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_hash(identity: dict[str, Any]) -> str:
    material = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return f"sha256:{sha256_hex(material)}"


def now_iso() -> str:
    return dt.date.today().isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def fetch_url(url: str, timeout: int = TIMEOUT_SECONDS) -> tuple[str | None, str | None]:
    """Return (outcome, text). outcome is ok or a provider failure."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return "ok", response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return "rate-limited", None
        if exc.code == 404:
            return "paper-not-indexed", None
        return "provider-unavailable", None
    except (urllib.error.URLError, TimeoutError, OSError):
        return "provider-unavailable", None


def strip_html(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_keyword_passages(text: str, query: str, limit: int) -> list[dict[str, Any]]:
    """Best-effort passage extraction: sentences containing claim keywords."""
    keywords = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", query.lower()) if len(w) > 3]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    scored: list[tuple[int, str, str]] = []
    for sentence in sentences:
        lowered = sentence.lower()
        hits = sum(1 for word in keywords if word in lowered)
        if hits == 0:
            continue
        start = max(0, lowered.find(keywords[0])) if keywords else 0
        section = ""
        match = re.search(r"\b(?:Abstract|Introduction|Method|Methods|Results|Conclusion|Discussion|Section)\b", sentence)
        if match:
            section = match.group(0)
        scored.append((hits, sentence.strip(), section))
    scored.sort(key=lambda item: (-item[0], len(item[1])))
    passages: list[dict[str, Any]] = []
    for hits, sentence, section in scored[:limit]:
        passages.append(
            {
                "text": sentence,
                "section": section,
                "locator": f"full-text{' Sec. ' + section if section else ''}",
                "hash": f"sha256:{sha256_hex(sentence)}",
                "origin": "arxiv-html",
                "score": hits,
                "keyword_hits": hits,
            }
        )
    return passages


class ProviderClient:
    """Provider calls behind injectable fixtures for deterministic tests."""

    def __init__(self, *, offline: bool = False, fixture_dir: Path | None = None, timeout: int = TIMEOUT_SECONDS):
        self.offline = offline
        self.fixture_dir = fixture_dir
        self.timeout = timeout

    def _fixture(self, name: str) -> dict[str, Any] | None:
        if self.fixture_dir is None:
            return None
        path = self.fixture_dir / f"{name}.json"
        payload = load_json(path)
        return payload if isinstance(payload, dict) else None

    # -- resolve -----------------------------------------------------------
    def resolve_crossref(self, doi: str) -> tuple[str, dict[str, Any] | None]:
        fixture = self._fixture(f"resolve_crossref_{re.sub(r'[^A-Za-z0-9]', '_', doi)}")
        if fixture is not None:
            return fixture["outcome"], fixture.get("record")
        if self.offline:
            return "provider-unavailable", None
        outcome, text = fetch_url(
            f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", self.timeout
        )
        if outcome != "ok" or text is None:
            return outcome, None
        try:
            message = json.loads(text)["message"]
        except (json.JSONDecodeError, KeyError):
            return "provider-unavailable", None
        authors = [
            " ".join(part for part in (author.get("given"), author.get("family")) if part)
            for author in message.get("author", [])
        ]
        return "ok", {
            "title": (message.get("title") or [""])[0],
            "authors": authors,
            "year": str((message.get("issued", {}) or {}).get("date-parts", [[None]])[0][0] or ""),
            "venue": (message.get("container-title") or [""])[0],
            "doi": message.get("DOI") or doi,
        }

    def resolve_openalex(self, doi: str) -> tuple[str, dict[str, Any] | None]:
        fixture = self._fixture(f"resolve_openalex_{re.sub(r'[^A-Za-z0-9]', '_', doi)}")
        if fixture is not None:
            return fixture["outcome"], fixture.get("record")
        if self.offline:
            return "provider-unavailable", None
        outcome, text = fetch_url(
            f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='')}", self.timeout
        )
        if outcome != "ok" or text is None:
            return outcome, None
        try:
            record = json.loads(text)
        except json.JSONDecodeError:
            return "provider-unavailable", None
        authors = [
            author.get("author", {}).get("display_name", "")
            for author in record.get("authorships", [])
        ]
        return "ok", {
            "title": record.get("title") or "",
            "authors": [a for a in authors if a],
            "year": str(record.get("publication_year") or ""),
            "venue": (record.get("primary_location") or {}).get("source", {}).get("display_name", "")
            if record.get("primary_location")
            else "",
            "doi": record.get("doi") or doi,
        }

    def resolve_arxiv(self, arxiv_id: str) -> tuple[str, dict[str, Any] | None]:
        fixture = self._fixture(f"resolve_arxiv_{re.sub(r'[^A-Za-z0-9]', '_', arxiv_id)}")
        if fixture is not None:
            return fixture["outcome"], fixture.get("record")
        if self.offline:
            return "provider-unavailable", None
        outcome, text = fetch_url(
            f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}", self.timeout
        )
        if outcome != "ok" or text is None:
            return outcome, None
        if "<entry>" not in text:
            return "paper-not-indexed", None
        # Extract within the first <entry> so the feed-level wrapper title is
        # never mistaken for the paper title.
        entry_text = text[text.index("<entry>"):]
        if "</entry>" in entry_text:
            entry_text = entry_text[: entry_text.index("</entry>")]
        title = re.search(r"<title>(.*?)</title>", entry_text, re.DOTALL)
        authors = re.findall(r"<name>(.*?)</name>", entry_text)
        published = re.search(r"<published>(.*?)</published>", entry_text)
        return "ok", {
            "title": strip_html(title.group(1)) if title else "",
            "authors": [strip_html(a) for a in authors],
            "year": (published.group(1)[:4]) if published else "",
            "venue": "arXiv",
            "arxiv": arxiv_id,
        }

    def resolve_semantic_scholar(self, identifier: str) -> tuple[str, dict[str, Any] | None]:
        fixture = self._fixture(f"resolve_s2_{re.sub(r'[^A-Za-z0-9]', '_', identifier)}")
        if fixture is not None:
            return fixture["outcome"], fixture.get("record")
        if self.offline:
            return "provider-unavailable", None
        url = (
            "https://api.semanticscholar.org/graph/v1/paper/"
            f"{urllib.parse.quote(identifier)}?fields=title,abstract,externalIds,venue,year,authors,tldr"
        )
        outcome, text = fetch_url(url, self.timeout)
        if outcome != "ok" or text is None:
            return outcome, None
        try:
            record = json.loads(text)
        except json.JSONDecodeError:
            return "provider-unavailable", None
        return "ok", {
            "title": record.get("title") or "",
            "authors": [a.get("name", "") for a in record.get("authors", [])],
            "year": str(record.get("year") or ""),
            "venue": record.get("venue") or "",
            "doi": (record.get("externalIds") or {}).get("DOI") or "",
            "arxiv": (record.get("externalIds") or {}).get("ArXiv") or "",
            "paper_id": record.get("paperId") or "",
            "abstract": record.get("abstract") or "",
        }

    # -- search ------------------------------------------------------------
    def search_semantic_scholar(self, query: str, limit: int) -> tuple[str, list[dict[str, Any]]]:
        fixture = self._fixture(f"search_s2_{sha256_hex(query)[:16]}")
        if fixture is not None:
            return fixture.get("outcome", "ok"), fixture.get("candidates", [])
        if self.offline:
            return "provider-unavailable", []
        url = (
            "https://api.semanticscholar.org/graph/v1/paper/search?"
            + urllib.parse.urlencode(
                {"query": query, "limit": limit, "fields": "title,externalIds,venue,year,authors"}
            )
        )
        outcome, text = fetch_url(url, self.timeout)
        if outcome != "ok" or text is None:
            return outcome, []
        try:
            records = json.loads(text).get("data", [])
        except json.JSONDecodeError:
            return "provider-unavailable", []
        return "ok", [
            {
                "title": record.get("title") or "",
                "authors": [a.get("name", "") for a in record.get("authors", [])],
                "year": str(record.get("year") or ""),
                "venue": record.get("venue") or "",
                "doi": (record.get("externalIds") or {}).get("DOI") or "",
                "arxiv": (record.get("externalIds") or {}).get("ArXiv") or "",
                "paper_id": record.get("paperId") or "",
                "provider": "semantic-scholar",
            }
            for record in records
        ]

    def search_openalex(self, query: str, limit: int) -> tuple[str, list[dict[str, Any]]]:
        fixture = self._fixture(f"search_openalex_{sha256_hex(query)[:16]}")
        if fixture is not None:
            return fixture.get("outcome", "ok"), fixture.get("candidates", [])
        if self.offline:
            return "provider-unavailable", []
        url = (
            "https://api.openalex.org/works?"
            + urllib.parse.urlencode(
                {"search": query, "per-page": limit, "select": "title,doi,publication_year,primary_location,authorships"}
            )
        )
        outcome, text = fetch_url(url, self.timeout)
        if outcome != "ok" or text is None:
            return outcome, []
        try:
            records = json.loads(text).get("results", [])
        except json.JSONDecodeError:
            return "provider-unavailable", []
        return "ok", _search_openalex_results(records)


def _source_display_name(record: dict[str, Any]) -> str:
    primary = record.get("primary_location")
    if not isinstance(primary, dict):
        return ""
    source = primary.get("source")
    if not isinstance(source, dict):
        return ""
    return source.get("display_name", "") or ""


def _search_openalex_results(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": record.get("title") or "",
            "authors": [
                author.get("author", {}).get("display_name", "")
                for author in record.get("authorships", [])
            ],
            "year": str(record.get("publication_year") or ""),
            "venue": _source_display_name(record),
            "doi": record.get("doi") or "",
            "provider": "openalex",
        }
        for record in records
    ]


# -- passages --------------------------------------------------------------

def passages_semantic_scholar(
    client: ProviderClient, identity: dict[str, Any], query: str, limit: int
) -> tuple[str, list[dict[str, Any]]]:
    paper_id = identity.get("paper_id") or ""
    fixture = client._fixture(f"passages_s2_{paper_id or sha256_hex(json.dumps(identity, sort_keys=True))[:16]}")
    if fixture is not None:
        return fixture.get("outcome", "ok"), fixture.get("passages", [])
    if client.offline:
        return "provider-unavailable", []
    url = (
        "https://api.semanticscholar.org/graph/v1/snippet/search?"
        + urllib.parse.urlencode({"query": query, "limit": limit})
    )
    outcome, text = fetch_url(url, client.timeout)
    if outcome != "ok" or text is None:
        return outcome, []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return "provider-unavailable", []
    passages: list[dict[str, Any]] = []
    for snippet in payload.get("snippets", []):
        snippet_paper = snippet.get("paperId") or ""
        if paper_id and snippet_paper and snippet_paper != paper_id:
            continue
        context = snippet.get("context") or {}
        text_value = context.get("surroundingText") or context.get("snippet") or ""
        if not text_value:
            continue
        section = snippet.get("sectionName") or ""
        passages.append(
            {
                "text": text_value.strip(),
                "section": section,
                "locator": f"Sec. {section}" if section else "snippet",
                "hash": f"sha256:{sha256_hex(text_value.strip())}",
                "origin": "semantic-scholar-snippet",
                "score": snippet.get("score") or 0,
                "paper_id": snippet_paper,
            }
        )
        if len(passages) >= limit:
            break
    return "ok", passages


def passages_arxiv_html(client: ProviderClient, arxiv_id: str, query: str, limit: int) -> tuple[str, list[dict[str, Any]]]:
    fixture = client._fixture(f"passages_arxiv_{re.sub(r'[^A-Za-z0-9]', '_', arxiv_id)}")
    if fixture is not None:
        return fixture.get("outcome", "ok"), fixture.get("passages", [])
    if client.offline:
        return "provider-unavailable", []
    outcome, text = fetch_url(f"https://arxiv.org/html/{urllib.parse.quote(arxiv_id)}", client.timeout)
    if outcome != "ok" or text is None:
        return outcome, []
    plain = strip_html(text)
    if len(plain) < 200:
        return "full-text-unavailable", []
    return "ok", extract_keyword_passages(plain, query, limit)


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------

class Ledger:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / CANONICAL_LEDGER
        self.data = load_json(self.path)
        if not isinstance(self.data, dict):
            raise ValueError(f"missing or invalid ledger at {self.path}")

    def save(self) -> None:
        write_json(self.path, self.data)


def load_reference_keys(root: Path) -> set[str]:
    ledger = Ledger(root)
    keys: set[str] = set()
    for record in ledger.data.get("references", []):
        if isinstance(record, dict) and record.get("citation_key"):
            keys.add(record["citation_key"])
    return keys


def load_usage_class(root: Path) -> dict[str, str]:
    ledger = Ledger(root)
    result: dict[str, str] = {}
    for record in ledger.data.get("citation_usages", []):
        if isinstance(record, dict) and record.get("citation_key"):
            result[record["citation_key"]] = record.get("classification", "other")
    return result


def resolve_by_key(root: Path, key: str) -> dict[str, Any] | None:
    ledger = Ledger(root)
    for record in ledger.data.get("references", []):
        if isinstance(record, dict) and record.get("citation_key") == key:
            return record
    return None


def find_occurrence(root: Path, occurrence_id: str) -> dict[str, Any] | None:
    ledger = Ledger(root)
    for record in ledger.data.get("citation_occurrences", []):
        if isinstance(record, dict) and record.get("occurrence_id") == occurrence_id:
            return record
    return None


def find_evidence(root: Path, occurrence_id: str, citation_key: str) -> dict[str, Any] | None:
    ledger = Ledger(root)
    for record in ledger.data.get("claim_evidence", []):
        if (
            isinstance(record, dict)
            and record.get("occurrence_id") == occurrence_id
            and record.get("citation_key") == citation_key
        ):
            return record
    return None


def is_substantive(usage: str | None) -> bool:
    return usage == "claim-support"


def default_run_dir(root: Path) -> Path:
    return root / DEFAULT_RUN_DIR / now_iso().replace("-", "")


def run_dir_for(root: Path, args: argparse.Namespace) -> Path:
    """Run directory honoring --run-dir when supplied."""
    if getattr(args, "run_dir", None):
        return Path(args.run_dir).expanduser().resolve()
    return default_run_dir(root)


def cache_path(run_dir: Path, name: str) -> Path:
    return run_dir / "cache" / f"{name}.json"


def record_provider_outcome(
    run_dir: Path, name: str, outcome: str, payload: Any
) -> None:
    entry = {
        "name": name,
        "outcome": outcome,
        "at": now_iso(),
        "payload": payload,
    }
    report = run_dir / "provider-outcomes.jsonl"
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def load_reference_record_by_key(root: Path, key: str) -> dict[str, Any] | None:
    return resolve_by_key(root, key)


def ref_identity_from_bibtex(root: Path, key: str) -> dict[str, Any] | None:
    """Best-effort identity from the canonical bibliography when the ledger
    reference record has no identifiers yet. Never edits BibTeX."""
    bib = root / "paper/refs.bib"
    if not bib.is_file():
        return None
    text = bib.read_text(encoding="utf-8")
    entries = re.split(r"\n@", text)
    for entry in entries:
        if "{" not in entry:
            continue
        head, _, body = entry.partition("{")
        body = body.rsplit("}", 1)[0]
        entry_key = head.strip()
        if entry_key != key:
            continue
        fields: dict[str, str] = {}
        for field_match in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}", body, re.DOTALL):
            fields[field_match.group(1).lower()] = field_match.group(2).strip()
        return {
            "title": fields.get("title", ""),
            "year": fields.get("year", ""),
            "venue": fields.get("booktitle", fields.get("journal", "")),
            "doi": fields.get("doi", ""),
            "arxiv": fields.get("arxiv", fields.get("eprint", "")),
        }
    return None


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_inventory(args: argparse.Namespace) -> int:
    root = args.root
    occurrences = scan_occurrences(root)
    location_filter = args.location
    if location_filter:
        needle = location_filter
        occurrences = [
            item for item in occurrences
            if item["manuscript_location"].startswith(needle)
        ]
    # Persist occurrences into the durable ledger so packet/record can bind
    # evidence. Existing records keep their review_state; new records are
    # pending. Removed occurrences are left for the checker to flag.
    ledger = Ledger(root)
    if ledger.data.get("schema_version") != "paper-reference-ledger-v2":
        raise ValueError(
            "inventory requires a paper-reference-ledger-v2 ledger; run migrate first"
        )
    existing = {
        item["occurrence_id"]: item
        for item in ledger.data.get("citation_occurrences", [])
        if isinstance(item, dict) and item.get("occurrence_id")
    }
    for item in occurrences:
        if item["occurrence_id"] in existing:
            existing[item["occurrence_id"]]["manuscript_location"] = item["manuscript_location"]
            existing[item["occurrence_id"]]["claim_text"] = item["claim_text"]
            existing[item["occurrence_id"]]["claim_fingerprint"] = item["claim_fingerprint"]
        else:
            item["review_state"] = "pending"
            existing[item["occurrence_id"]] = item
    current_ids = {item["occurrence_id"] for item in occurrences}
    ledger.data["citation_occurrences"] = [
        item for item in existing.values() if item["occurrence_id"] in current_ids
    ]
    ledger.save()
    run_dir = run_dir_for(root, args)
    write_json(run_dir / "inventory.json", occurrences)
    for item in occurrences:
        print(
            f"{item['manuscript_location']} "
            f"{item['occurrence_id']} [{','.join(item['citation_keys'])}] "
            f"{item['claim_text'][:90]}"
        )
    print(f"OK inventory occurrences={len(occurrences)} cache={run_dir / 'inventory.json'}")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    root = args.root
    client = ProviderClient(
        offline=args.offline, fixture_dir=args.fixture_dir, timeout=args.timeout
    )
    run_dir = run_dir_for(root, args)
    run_dir.mkdir(parents=True, exist_ok=True)

    source = args.key or args.doi or args.arxiv or args.url or args.title
    identity: dict[str, Any] = {}
    sources: list[str] = []
    failures: list[str] = []

    if args.key:
        record = resolve_by_key(root, args.key)
        if record is None:
            print(f"ERROR unknown citation key: {args.key}")
            return 1
        identifiers = record.get("identifiers") or {}
        identity = {
            "citation_key": args.key,
            "title": identifiers.get("title", ""),
            "doi": identifiers.get("doi", ""),
            "arxiv": identifiers.get("arxiv", ""),
            "openreview": identifiers.get("openreview", ""),
        }
        if not identity.get("doi") and not identity.get("arxiv"):
            bib_identity = ref_identity_from_bibtex(root, args.key)
            if bib_identity:
                identity.update({k: v for k, v in bib_identity.items() if v})
        if identity.get("doi"):
            outcome, provider_record = client.resolve_crossref(identity["doi"])
            if provider_record is not None:
                identity.update(provider_record)
                sources.append("crossref")
                record_provider_outcome(run_dir, f"resolve:{args.key}", "ok", provider_record)
            else:
                failures.append(f"crossref:{outcome}")
                record_provider_outcome(run_dir, f"resolve:{args.key}", outcome, None)
            outcome, provider_record = client.resolve_semantic_scholar(identity["doi"])
            if provider_record is not None:
                identity.update(provider_record)
                sources.append("semantic-scholar")
            else:
                failures.append(f"semantic-scholar:{outcome}")
        if identity.get("arxiv"):
            outcome, provider_record = client.resolve_arxiv(identity["arxiv"])
            if provider_record is not None:
                identity.update(provider_record)
                sources.append("arxiv")
                record_provider_outcome(run_dir, f"resolve:{args.key}", "ok", provider_record)
            else:
                failures.append(f"arxiv:{outcome}")
                record_provider_outcome(run_dir, f"resolve:{args.key}", outcome, None)
    else:
        if args.doi:
            outcome, provider_record = client.resolve_crossref(args.doi)
            if provider_record is not None:
                identity.update(provider_record)
                sources.append("crossref")
            else:
                failures.append(f"crossref:{outcome}")
            outcome, provider_record = client.resolve_semantic_scholar(args.doi)
            if provider_record is not None:
                identity.update(provider_record)
                sources.append("semantic-scholar")
            else:
                failures.append(f"semantic-scholar:{outcome}")
        if args.arxiv:
            outcome, provider_record = client.resolve_arxiv(args.arxiv)
            if provider_record is not None:
                identity.update(provider_record)
                sources.append("arxiv")
            else:
                failures.append(f"arxiv:{outcome}")
            outcome, provider_record = client.resolve_semantic_scholar(args.arxiv)
            if provider_record is not None:
                identity.update(provider_record)
                sources.append("semantic-scholar")
            else:
                failures.append(f"semantic-scholar:{outcome}")
        if args.url and "openreview" in args.url:
            identity.setdefault("openreview", args.url)
            sources.append("openreview-url")

    if not identity:
        print(f"ERROR resolve failed: source={source or 'none'} failures={','.join(failures) or 'no-provider'}")
        return 1

    identity["source_hash"] = source_hash(identity)
    identity["providers"] = sources
    identity["provider_failures"] = failures
    write_json(run_dir / f"resolve-{source}.json", identity)
    print(json.dumps(identity, indent=2, sort_keys=True))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = args.root
    client = ProviderClient(
        offline=args.offline, fixture_dir=args.fixture_dir, timeout=args.timeout
    )
    run_dir = run_dir_for(root, args)
    run_dir.mkdir(parents=True, exist_ok=True)
    query = args.query
    if args.context:
        query = f"{query} {args.context}"
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    outcome, candidates = client.search_semantic_scholar(query, args.limit)
    if outcome != "ok":
        failures.append(f"semantic-scholar:{outcome}")
        record_provider_outcome(run_dir, f"search:{query[:40]}", outcome, None)
    else:
        results.extend(candidates)
        record_provider_outcome(run_dir, f"search:{query[:40]}", "ok", candidates)
    if args.providers and "openalex" in args.providers:
        outcome, candidates = client.search_openalex(query, args.limit)
        if outcome != "ok":
            failures.append(f"openalex:{outcome}")
        else:
            results.extend(candidates)
    write_json(run_dir / f"search-{sha256_hex(query)[:16]}.json", {"query": query, "candidates": results, "failures": failures})
    for index, candidate in enumerate(results):
        print(f"{index}\t{candidate.get('year', '')}\t{candidate.get('venue', '')}\t{candidate.get('doi', '') or candidate.get('arxiv', '')}\t{candidate.get('title', '')}\t{candidate.get('provider', '')}")
    print(f"OK search candidates={len(results)} failures={','.join(failures) or 'none'}")
    return 0


def cmd_passages(args: argparse.Namespace) -> int:
    root = args.root
    client = ProviderClient(
        offline=args.offline, fixture_dir=args.fixture_dir, timeout=args.timeout
    )
    run_dir = run_dir_for(root, args)
    run_dir.mkdir(parents=True, exist_ok=True)

    identity: dict[str, Any] = {}
    if args.identity_json:
        loaded = load_json(Path(args.identity_json))
        if isinstance(loaded, dict):
            identity = loaded
    elif args.paper_id:
        identity["paper_id"] = args.paper_id
    elif args.doi:
        identity["doi"] = args.doi
        outcome, provider_record = client.resolve_crossref(args.doi)
        if provider_record is not None:
            identity.update(provider_record)
    elif args.arxiv:
        identity["arxiv"] = args.arxiv
        outcome, provider_record = client.resolve_arxiv(args.arxiv)
        if provider_record is not None:
            identity.update(provider_record)

    if not identity:
        print("ERROR passages requires --identity-json, --paper-id, --doi, or --arxiv")
        return 1

    query = args.query or "claim"
    passages: list[dict[str, Any]] = []
    failures: list[str] = []
    outcome, snippet_passages = passages_semantic_scholar(client, identity, query, args.limit)
    if outcome != "ok":
        failures.append(f"semantic-scholar:{outcome}")
        record_provider_outcome(run_dir, f"passages:{identity.get('paper_id', '') or identity.get('doi', '')}", outcome, None)
    else:
        passages.extend(snippet_passages)
        record_provider_outcome(run_dir, f"passages:{identity.get('paper_id', '') or identity.get('doi', '')}", "ok", snippet_passages)

    if not passages and identity.get("arxiv"):
        outcome, arxiv_passages = passages_arxiv_html(client, identity["arxiv"], query, args.limit)
        if outcome != "ok":
            failures.append(f"arxiv-html:{outcome}")
        else:
            passages.extend(arxiv_passages)

    if not passages:
        # abstract-only evidence fallback
        if identity.get("abstract"):
            passages.append(
                {
                    "text": identity["abstract"],
                    "section": "abstract",
                    "locator": "abstract",
                    "hash": f"sha256:{sha256_hex(identity['abstract'])}",
                    "origin": "semantic-scholar-abstract",
                    "score": 0,
                }
            )
        else:
            failures.append("full-text-unavailable")

    write_json(run_dir / f"passages-{identity.get('paper_id', '') or identity.get('doi', '') or identity.get('arxiv', '')}.json", {"identity": identity, "passages": passages, "failures": failures})
    for index, passage in enumerate(passages):
        print(f"{index}\t{passage.get('origin', '')}\t{passage.get('locator', '')}\t{passage.get('hash', '')}\t{passage.get('text', '')[:120]}")
    print(f"OK passages count={len(passages)} failures={','.join(failures) or 'none'}")
    return 0


def cmd_packet(args: argparse.Namespace) -> int:
    root = args.root
    ledger = Ledger(root)
    occurrence = find_occurrence(root, args.occurrence_id)
    if occurrence is None:
        print(f"ERROR unknown occurrence_id: {args.occurrence_id}")
        return 1
    key = args.key
    if key not in occurrence.get("citation_keys", []):
        print(f"ERROR key {key} not in occurrence {args.occurrence_id}")
        return 1
    reference = resolve_by_key(root, key)
    source_identity: dict[str, Any] = {
        "citation_key": key,
    }
    if reference:
        identifiers = reference.get("identifiers") or {}
        source_identity.update(identifiers)
        if not any(source_identity.get(name) for name in ("doi", "arxiv", "openreview", "semantic_scholar", "url")):
            bib_identity = ref_identity_from_bibtex(root, key)
            if bib_identity:
                source_identity.update({k: v for k, v in bib_identity.items() if v})
    source_identity["source_hash"] = source_hash(source_identity)
    packet = {
        "schema_version": SUPPORT_PROTOCOL_VERSION,
        "occurrence_id": args.occurrence_id,
        "citation_key": key,
        "claim": {
            "text": occurrence.get("claim_text", ""),
            "location": occurrence.get("manuscript_location", ""),
            "citation_keys": occurrence.get("citation_keys", []),
            "meaning": {},
        },
        "source": {
            "identity": source_identity,
            "passages": [],
        },
        "assessment": {},
    }
    run_dir = run_dir_for(root, args)
    run_dir.mkdir(parents=True, exist_ok=True)
    packet_path = run_dir / f"packet-{args.occurrence_id}-{key}.json"
    write_json(packet_path, packet)
    print(json.dumps(packet, indent=2, sort_keys=True))
    print(f"OK packet wrote {packet_path.relative_to(root)}")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    root = args.root
    ledger = Ledger(root)
    occurrence = find_occurrence(root, args.occurrence_id)
    if occurrence is None:
        print(f"ERROR unknown occurrence_id: {args.occurrence_id}")
        return 1
    if args.key not in occurrence.get("citation_keys", []):
        print(f"ERROR key {args.key} not in occurrence {args.occurrence_id}")
        return 1
    if args.verdict not in SUPPORT_VERDICTS:
        print(f"ERROR unsupported verdict: {args.verdict}")
        return 1
    if args.state not in SUPPORT_REVIEW_STATES:
        print(f"ERROR unsupported review state: {args.state}")
        return 1
    if args.state == "human-confirmed" and not args.approval:
        print("ERROR human-confirmed requires an explicit --approval note")
        return 1
    if args.state == "human-confirmed" and args.verdict not in {"supported", "partially-supported", "unsupported", "contradicted"}:
        print("ERROR human-confirmed requires a scientific verdict, not source-unavailable")
        return 1
    if not args.passage_text:
        print("ERROR record requires --passage-text")
        return 1
    if not args.locator:
        print("ERROR record requires --locator")
        return 1

    current = scan_occurrences(root)
    current_by_id = {item["occurrence_id"]: item for item in current}
    current_item = current_by_id.get(args.occurrence_id)
    if current_item is None:
        print(f"ERROR occurrence {args.occurrence_id} no longer exists in the manuscript; re-inventory")
        return 1
    if set(current_item["citation_keys"]) != set(occurrence["citation_keys"]):
        print("ERROR stale packet: citation set changed; re-inventory before recording")
        return 1
    if current_item["claim_fingerprint"] != occurrence["claim_fingerprint"]:
        print("ERROR stale packet: claim fingerprint changed; re-inventory before recording")
        return 1

    existing = find_evidence(root, args.occurrence_id, args.key)
    source_identity: dict[str, Any] = {
        "citation_key": args.key,
    }
    reference = resolve_by_key(root, args.key)
    if reference:
        identifiers = reference.get("identifiers") or {}
        source_identity.update(identifiers)
    if args.source_version:
        source_identity["version"] = args.source_version
    if args.doi:
        source_identity["doi"] = args.doi
    if args.arxiv:
        source_identity["arxiv"] = args.arxiv
    source_identity["source_hash"] = source_hash(source_identity)

    passage_hash = f"sha256:{sha256_hex(args.passage_text)}"
    supported_parts = [part.strip() for part in args.supported_parts.split("|")] if args.supported_parts else []
    unsupported_parts = [part.strip() for part in args.unsupported_parts.split("|")] if args.unsupported_parts else []
    contradictions = [part.strip() for part in args.contradictions.split("|")] if args.contradictions else []
    missing_qualifiers = [part.strip() for part in args.missing_qualifiers.split("|")] if args.missing_qualifiers else []

    record = {
        "evidence_id": evidence_id(args.occurrence_id, args.key),
        "occurrence_id": args.occurrence_id,
        "citation_key": args.key,
        "claim_fingerprint": occurrence["claim_fingerprint"],
        "protocol_version": SUPPORT_PROTOCOL_VERSION,
        "source_identity": source_identity,
        "passage": {
            "text": args.passage_text,
            "locator": args.locator,
            "hash": passage_hash,
            "origin": args.origin if args.origin in PASSAGE_ORIGINS else "agent-pdf",
        },
        "assessment": {
            "verdict": args.verdict,
            "supported_parts": supported_parts,
            "unsupported_parts": unsupported_parts,
            "contradictions": contradictions,
            "missing_qualifiers": missing_qualifiers,
            "recommended_action": args.action or "review",
        },
        "review_state": args.state,
        "updated_at": now_iso(),
        "reviewer": args.reviewer or "",
        "approval": args.approval or "",
    }
    if existing:
        record["evidence_id"] = existing["evidence_id"]
    replace = False
    new_evidence = []
    for item in ledger.data.get("claim_evidence", []):
        if (
            isinstance(item, dict)
            and item.get("occurrence_id") == args.occurrence_id
            and item.get("citation_key") == args.key
        ):
            new_evidence.append(record)
            replace = True
        else:
            new_evidence.append(item)
    if not replace:
        new_evidence.append(record)
    ledger.data["claim_evidence"] = new_evidence
    # Promote the occurrence review state so the coarse occurrence gate tracks
    # the most advanced per-key evidence state.
    for item in ledger.data.get("citation_occurrences", []):
        if isinstance(item, dict) and item.get("occurrence_id") == args.occurrence_id:
            item["review_state"] = args.state
    ledger.save()
    print(f"OK recorded evidence {record['evidence_id']} verdict={args.verdict} state={args.state}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = args.root
    ledger = Ledger(root)
    occurrences = ledger.data.get("citation_occurrences", [])
    evidence = ledger.data.get("claim_evidence", [])
    current = scan_occurrences(root)
    current_by_id = {item["occurrence_id"]: item for item in current}
    current_ids = set(current_by_id)
    ledger_by_id = {item["occurrence_id"]: item for item in occurrences}
    stale: list[str] = []
    for occurrence_id, occ in sorted(ledger_by_id.items()):
        current_item = current_by_id.get(occurrence_id)
        if current_item is None:
            stale.append(f"{occurrence_id}:removed")
            continue
        if occ.get("claim_fingerprint") != current_item["claim_fingerprint"]:
            stale.append(f"{occurrence_id}:claim")
        if set(occ.get("citation_keys") or []) != set(current_item["citation_keys"]):
            stale.append(f"{occurrence_id}:keys")
    counts = {
        "occurrences_ledger": len(occurrences),
        "occurrences_current": len(current),
        "evidence": len(evidence),
        "stale": len(stale),
        "uncovered_current": len(current_ids - set(ledger_by_id)),
    }
    print(json.dumps({"schema_version": ledger.data.get("schema_version"), **counts, "stale_items": stale}, indent=2, sort_keys=True))
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    root = args.root
    ledger = Ledger(root)
    if ledger.data.get("schema_version") != "paper-reference-ledger-v1":
        print(f"ERROR ledger is not v1 (found {ledger.data.get('schema_version')})")
        return 1
    current = scan_occurrences(root)
    by_key_fingerprint: dict[str, dict[str, Any]] = {}
    for claim_record in ledger.data.get("claim_evidence", []):
        if not isinstance(claim_record, dict):
            continue
        key = claim_record.get("citation_key")
        if not key:
            continue
        by_key_fingerprint.setdefault(key, claim_record)

    occurrences: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    migrated = 0
    for item in current:
        occurrences.append(
            {
                "occurrence_id": item["occurrence_id"],
                "manuscript_location": item["manuscript_location"],
                "command": item["command"],
                "citation_keys": item["citation_keys"],
                "claim_text": item["claim_text"],
                "claim_fingerprint": item["claim_fingerprint"],
                "review_state": "pending",
            }
        )
        for key in item["citation_keys"]:
            legacy = by_key_fingerprint.get(key)
            if legacy is None:
                continue
            source_identity = {"citation_key": key}
            evidence.append(
                {
                    "evidence_id": evidence_id(item["occurrence_id"], key),
                    "occurrence_id": item["occurrence_id"],
                    "citation_key": key,
                    "claim_fingerprint": item["claim_fingerprint"],
                    "protocol_version": SUPPORT_PROTOCOL_VERSION,
                    "source_identity": source_identity,
                    "passage": {
                        "text": legacy.get("evidence_excerpt_or_rationale", ""),
                        "locator": legacy.get("source_locator", ""),
                        "hash": f"sha256:{sha256_hex(legacy.get('evidence_excerpt_or_rationale', ''))}",
                        "origin": "migrated-v1",
                    },
                    "assessment": {
                        "verdict": "source-unavailable",
                        "supported_parts": [],
                        "unsupported_parts": [],
                        "contradictions": [],
                        "missing_qualifiers": [],
                        "recommended_action": "review",
                    },
                    "review_state": legacy.get("human_review_state", "pending"),
                    "updated_at": now_iso(),
                    "reviewer": "migration",
                    "approval": "",
                }
            )
            migrated += 1
    ledger.data = {
        "schema_version": "paper-reference-ledger-v2",
        "references": ledger.data.get("references", []),
        "citation_usages": ledger.data.get("citation_usages", []),
        "citation_occurrences": occurrences,
        "claim_evidence": evidence,
    }
    ledger.save()
    print(f"OK migrated ledger to v2 occurrences={len(occurrences)} migrated_evidence={migrated}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--offline", action="store_true", help="do not contact providers")
    parser.add_argument("--fixture-dir", type=Path, default=None, help="fixture cache directory for deterministic tests")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--run-dir", default="", help="fixed run directory (default: dist/reference-support/<date>)")
    sub = parser.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("inventory", help="inventory TeX citation occurrences")
    inv.add_argument("--location", default="", help="filter by manuscript location prefix")
    inv.set_defaults(func=cmd_inventory)

    res = sub.add_parser("resolve", help="resolve a known citation")
    res.add_argument("--key", default="")
    res.add_argument("--doi", default="")
    res.add_argument("--arxiv", default="")
    res.add_argument("--url", default="")
    res.add_argument("--title", default="")
    res.set_defaults(func=cmd_resolve)

    search = sub.add_parser("search", help="discover candidates for an unknown citation need")
    search.add_argument("query")
    search.add_argument("--context", default="")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--providers", default="semantic-scholar,openalex")
    search.set_defaults(func=cmd_search)

    pas = sub.add_parser("passages", help="retrieve exact evidence passages")
    pas.add_argument("--identity-json", default="")
    pas.add_argument("--paper-id", default="")
    pas.add_argument("--doi", default="")
    pas.add_argument("--arxiv", default="")
    pas.add_argument("--query", default="")
    pas.add_argument("--limit", type=int, default=3)
    pas.set_defaults(func=cmd_passages)

    pkt = sub.add_parser("packet", help="build a support packet for semantic review")
    pkt.add_argument("occurrence_id")
    pkt.add_argument("--key", required=True)
    pkt.set_defaults(func=cmd_packet)

    rec = sub.add_parser("record", help="atomically record support evidence")
    rec.add_argument("--occurrence-id", required=True)
    rec.add_argument("--key", required=True)
    rec.add_argument("--verdict", required=True)
    rec.add_argument("--state", default="provisional")
    rec.add_argument("--passage-text", default="")
    rec.add_argument("--locator", default="")
    rec.add_argument("--origin", default="agent-pdf")
    rec.add_argument("--doi", default="")
    rec.add_argument("--arxiv", default="")
    rec.add_argument("--source-version", default="")
    rec.add_argument("--supported-parts", default="")
    rec.add_argument("--unsupported-parts", default="")
    rec.add_argument("--contradictions", default="")
    rec.add_argument("--missing-qualifiers", default="")
    rec.add_argument("--action", default="")
    rec.add_argument("--reviewer", default="")
    rec.add_argument("--approval", default="")
    rec.set_defaults(func=cmd_record)

    st = sub.add_parser("status", help="summarize ledger support state")
    st.set_defaults(func=cmd_status)

    mig = sub.add_parser("migrate", help="migrate a paper-reference-ledger-v1 ledger to v2")
    mig.set_defaults(func=cmd_migrate)

    args = parser.parse_args()
    try:
        args.root = args.root.expanduser().resolve()
        return args.func(args)
    except ValueError as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
