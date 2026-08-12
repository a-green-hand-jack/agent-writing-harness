#!/usr/bin/env python3
"""Produce repeatable arXiv fidelity evidence for paper PDF comparisons.

Two subcommands:

- `checksum`: verify a file against an expected SHA-256 hex digest. This pins
  the provenance of downloaded original arXiv archives and PDFs.
- `evidence`: compare an original PDF against a rebuilt PDF page by page using
  poppler's pdftotext/pdfinfo. The report records page counts, per-page
  ordered-text digests, and the first mismatching page. It writes JSON evidence
  under .agents/runtime/fidelity/ (ignored) and is evidence-only by default;
  pass --require-match to fail when the ordered text does not match.

This tool reports evidence; it never approves a release or a publication.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = "paper-fidelity-v1"
CHUNK = 1024 * 1024


class FidelityError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(CHUNK)
            if not block:
                return digest.hexdigest()
            digest.update(block)


def run(*command: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(command), text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise FidelityError(
            f"command failed ({result.returncode}): {' '.join(command)}"
            f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def require_poppler() -> None:
    for tool in ("pdftotext", "pdfinfo"):
        if shutil.which(tool) is None:
            raise FidelityError(f"required poppler tool is missing: {tool}")


def page_count(path: Path) -> int:
    output = run("pdfinfo", str(path)).stdout
    for line in output.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError as exc:
                raise FidelityError(f"cannot parse page count for {path}") from exc
    raise FidelityError(f"pdfinfo reported no page count for {path}")


def page_text(path: Path, page: int) -> str:
    result = run("pdftotext", "-f", str(page), "-l", str(page), str(path), "-")
    return " ".join(result.stdout.split())


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cmd_checksum(args: argparse.Namespace) -> int:
    path = Path(args.file).expanduser().resolve()
    if not path.is_file():
        raise FidelityError(f"file is missing: {path}")
    expected = args.sha256.strip().lower()
    if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        raise FidelityError("--sha256 must be a 64-character hex digest")
    actual = sha256_file(path)
    if actual != expected:
        raise FidelityError(f"SHA-256 mismatch for {path}\n  expected: {expected}\n  actual:   {actual}")
    print(f"OK fidelity_checksum file={path.name} sha256={actual}")
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    require_poppler()
    original = Path(args.original).expanduser().resolve()
    rebuilt = Path(args.rebuilt).expanduser().resolve()
    if not original.is_file():
        raise FidelityError(f"original PDF is missing: {original}")
    if not rebuilt.is_file():
        raise FidelityError(f"rebuilt PDF is missing: {rebuilt}")

    original_pages = page_count(original)
    rebuilt_pages = page_count(rebuilt)
    pages: list[dict[str, object]] = []
    first_mismatch_page: int | None = None
    for page in range(1, max(original_pages, rebuilt_pages) + 1):
        original_text = page_text(original, page) if page <= original_pages else ""
        rebuilt_text = page_text(rebuilt, page) if page <= rebuilt_pages else ""
        match = original_text == rebuilt_text
        if first_mismatch_page is None and not match:
            first_mismatch_page = page
        pages.append(
            {
                "page": page,
                "match": match,
                "original_ordered_text_sha256": digest_text(original_text),
                "rebuilt_ordered_text_sha256": digest_text(rebuilt_text),
            }
        )

    report = {
        "schema_version": SCHEMA_VERSION,
        "label": args.label,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "original": {
            "path": original.name,
            "sha256": sha256_file(original),
            "pages": original_pages,
        },
        "rebuilt": {
            "path": rebuilt.name,
            "sha256": sha256_file(rebuilt),
            "pages": rebuilt_pages,
        },
        "page_counts_match": original_pages == rebuilt_pages,
        "ordered_text_equality": first_mismatch_page is None,
        "first_mismatch_page": first_mismatch_page,
        "pages": pages,
    }

    out = Path(args.out)
    if not out.is_absolute():
        root = Path(args.root).expanduser().resolve()
        out = (root / ".agents/runtime/fidelity" / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"OK fidelity_evidence label={args.label} "
        f"pages={original_pages}/{rebuilt_pages} "
        f"ordered_text_equality={str(report['ordered_text_equality']).lower()} "
        f"first_mismatch_page={first_mismatch_page} "
        f"out={out}"
    )
    if args.require_match and not report["ordered_text_equality"]:
        raise FidelityError(
            f"ordered-text mismatch required failure; first mismatch on page {first_mismatch_page}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)

    checksum = subparsers.add_parser("checksum")
    checksum.add_argument("--file", required=True)
    checksum.add_argument("--sha256", required=True)
    checksum.set_defaults(handler=cmd_checksum)

    evidence = subparsers.add_parser("evidence")
    evidence.add_argument("--label", required=True)
    evidence.add_argument("--original", required=True)
    evidence.add_argument("--rebuilt", required=True)
    evidence.add_argument("--require-match", action="store_true")
    evidence.add_argument("--out", type=Path, default=Path(f"{dt.date.today():%Y%m%d}-compare.json"))
    evidence.set_defaults(handler=cmd_evidence)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except FidelityError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
