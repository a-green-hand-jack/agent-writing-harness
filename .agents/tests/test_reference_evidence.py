from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / ".agents/tools/reference-evidence.py"
CHECKER = ROOT / ".agents/tools/check-reference-integrity.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(root), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def run_checker(root: Path, profile: str = "draft") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), "--profile", profile],
        text=True,
        capture_output=True,
        check=False,
    )


def ledger_v2(references: list[dict], usages: list[dict], occurrences: list[dict], evidence: list[dict]) -> str:
    return json.dumps(
        {
            "schema_version": "paper-reference-ledger-v2",
            "references": references,
            "citation_usages": usages,
            "citation_occurrences": occurrences,
            "claim_evidence": evidence,
        },
        indent=2,
    ) + "\n"


def policy() -> str:
    return """# Publication
<!-- REFERENCE-INTEGRITY:START -->
```json
{
  "schema_version": "paper-reference-integrity-policy-v1",
  "enforcement": "enforced",
  "ledger": "references/ledger.json",
  "bibliography": "paper/refs.bib"
}
```
<!-- REFERENCE-INTEGRITY:END -->
"""


def reference(key: str) -> dict:
    return {
        "citation_key": key,
        "status": "verified",
        "identifiers": {"doi": "10.1000/example"},
        "verification": {"sources": ["crossref"], "checked_at": "2026-08-05"},
        "human_review": {"state": "agent-resolved", "rationale": "verified identity"},
    }


def usage(key: str, classification: str = "claim-support") -> dict:
    return {
        "citation_key": key,
        "manuscript_location": "paper/sections/02_intro.tex:3",
        "classification": classification,
        "human_review_state": "human-confirmed",
    }


def teX_occurrence() -> str:
    return r"""\section{Intro}
A well-known observation~\citep{k1,k2} supports the claim.
"""


def fixture(
    root: Path,
    *,
    teX: str | None = None,
    occurrences: list[dict] | None = None,
    evidence: list[dict] | None = None,
    references: list[dict] | None = None,
    usages: list[dict] | None = None,
    ledger_json: str | None = None,
) -> None:
    write(root / ".agents/template-sync.json", '{"reference_integrity":{"adopted":true}}\n')
    write(root / "PUBLICATION.md", policy())
    write(root / "paper/refs.bib", "% REFERENCE_INTEGRITY_REQUIRED: references/ledger.json\n@article{k1, title={One}, author={A}, year={2024}}\n@article{k2, title={Two}, author={B}, year={2025}}\n")
    if teX is not None:
        write(root / "paper/sections/02_intro.tex", teX)
    if ledger_json is None:
        ledger_json = ledger_v2(
            references or [reference("k1"), reference("k2")],
            usages or [usage("k1"), usage("k2", "background")],
            occurrences or [],
            evidence or [],
        )
    write(root / "references/ledger.json", ledger_json)


def inventory_occurrences(root: Path) -> list[dict]:
    result = run(root, "inventory")
    return result


class CliInventoryTests(unittest.TestCase):
    def test_inventory_detects_occurrences_with_claim_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence())
            result = inventory_occurrences(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("k1", result.stdout)
            self.assertIn("k2", result.stdout)
            cache = root / "dist/reference-support" / "20260811" / "inventory.json"
            self.assertTrue(cache.is_file())
            items = json.loads(cache.read_text(encoding="utf-8"))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["citation_keys"], ["k1", "k2"])
            self.assertTrue(items[0]["claim_fingerprint"].startswith("sha256:"))

    def test_inventory_location_filter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence())
            result = run(root, "inventory", "--location", "paper/sections/03_related.tex")
            self.assertEqual(result.returncode, 0)
            self.assertIn("occurrences=0", result.stdout)


class CliResolveTests(unittest.TestCase):
    def test_resolve_unknown_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = run(root, "resolve", "--key", "nope")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown citation key", result.stdout)

    def test_resolve_offline_key_from_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = run(root, "--offline", "resolve", "--key", "k1")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("10.1000/example", result.stdout)
            self.assertIn("source_hash", result.stdout)

    def test_resolve_fixture_crossref(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as fixture_dir:
            root = Path(directory)
            fixture(root)
            write(
                Path(fixture_dir) / "resolve_crossref_10_1000_example.json",
                json.dumps({"outcome": "ok", "record": {"title": "Fixture Title", "authors": ["A"], "year": "2024", "venue": "J", "doi": "10.1000/example"}}),
            )
            result = run(root, "--fixture-dir", fixture_dir, "resolve", "--key", "k1")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Fixture Title", result.stdout)


class CliSearchTests(unittest.TestCase):
    def test_search_offline_returns_provider_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = run(root, "--offline", "search", "some claim text")
            self.assertEqual(result.returncode, 0)
            self.assertIn("failures=semantic-scholar:provider-unavailable", result.stdout)

    def test_search_fixture_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as fixture_dir:
            root = Path(directory)
            fixture(root)
            payload = {
                "outcome": "ok",
                "candidates": [
                    {"title": "Candidate", "authors": ["A"], "year": "2024", "venue": "J", "doi": "10.1000/c", "arxiv": "", "paper_id": "abc", "provider": "semantic-scholar"}
                ],
            }
            import hashlib
            key = hashlib.sha256("some claim text".encode()).hexdigest()[:16]
            write(Path(fixture_dir) / f"search_s2_{key}.json", json.dumps(payload))
            result = run(root, "--fixture-dir", fixture_dir, "search", "some claim text", "--providers", "semantic-scholar")
            self.assertEqual(result.returncode, 0)
            self.assertIn("Candidate", result.stdout)
            self.assertIn("candidates=1", result.stdout)


class CliPassagesTests(unittest.TestCase):
    def test_passages_offline_without_identity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = run(root, "--offline", "passages", "--query", "claim")
            self.assertEqual(result.returncode, 1)
            self.assertIn("passages requires", result.stdout)

    def test_passages_fixture_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as fixture_dir:
            root = Path(directory)
            fixture(root)
            identity = {"paper_id": "abc123", "doi": "10.1000/example"}
            write(
                Path(fixture_dir) / "passages_s2_abc123.json",
                json.dumps(
                    {
                        "outcome": "ok",
                        "passages": [
                            {"text": "The source reports the observation exactly.", "section": "Results", "locator": "Sec. Results", "hash": "sha256:x", "origin": "semantic-scholar-snippet", "score": 0.9, "paper_id": "abc123"}
                        ],
                    }
                ),
            )
            result = run(
                root,
                "--fixture-dir",
                fixture_dir,
                "passages",
                "--identity-json",
                str(Path(fixture_dir) / "identity.json"),
            )
            # no identity file -> requires identity-json content; fixture identity file absent
            write(Path(fixture_dir) / "identity.json", json.dumps(identity))
            result = run(
                root,
                "--fixture-dir",
                fixture_dir,
                "passages",
                "--identity-json",
                str(Path(fixture_dir) / "identity.json"),
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Sec. Results", result.stdout)


class CliPacketTests(unittest.TestCase):
    def test_packet_unknown_occurrence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence())
            result = run(root, "packet", "occ_missing", "--key", "k1")
            self.assertNotEqual(result.returncode, 0)

    def test_packet_builds_claim_and_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence())
            inv = inventory_occurrences(root)
            cache = root / "dist/reference-support" / "20260811" / "inventory.json"
            items = json.loads(cache.read_text(encoding="utf-8"))
            occ_id = items[0]["occurrence_id"]
            result = run(root, "packet", occ_id, "--key", "k1")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            json_part = result.stdout.split("\nOK ")[0]
            payload = json.loads(json_part)
            self.assertEqual(payload["occurrence_id"], occ_id)
            self.assertEqual(payload["source"]["identity"]["citation_key"], "k1")


class CliRecordTests(unittest.TestCase):
    def test_record_requires_approval_for_human_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence())
            run(root, "inventory")
            cache = root / "dist/reference-support" / "20260811" / "inventory.json"
            items = json.loads(cache.read_text(encoding="utf-8"))
            occ_id = items[0]["occurrence_id"]
            result = run(
                root,
                "record",
                "--occurrence-id",
                occ_id,
                "--key",
                "k1",
                "--verdict",
                "supported",
                "--state",
                "human-confirmed",
                "--passage-text",
                "The source reports the observation exactly.",
                "--locator",
                "Sec. 3",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires an explicit --approval", result.stdout)

    def test_record_provisional_and_staleness_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence())
            run(root, "inventory")
            cache = root / "dist/reference-support" / "20260811" / "inventory.json"
            items = json.loads(cache.read_text(encoding="utf-8"))
            occ_id = items[0]["occurrence_id"]
            result = run(
                root,
                "record",
                "--occurrence-id",
                occ_id,
                "--key",
                "k1",
                "--verdict",
                "supported",
                "--passage-text",
                "The source reports the observation exactly.",
                "--locator",
                "Sec. 3",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OK recorded", result.stdout)
            # stale packet after claim change: rewrite TeX only, keep the ledger
            write(
                root / "paper/sections/02_intro.tex",
                r"""\section{Intro}
A completely different claim~\citep{k1} is made here.
""",
            )
            result = run(
                root,
                "record",
                "--occurrence-id",
                occ_id,
                "--key",
                "k1",
                "--verdict",
                "supported",
                "--passage-text",
                "The source reports the observation exactly.",
                "--locator",
                "Sec. 3",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                "stale packet" in result.stdout or "no longer exists in the manuscript" in result.stdout,
                result.stdout,
            )

class MigrateTests(unittest.TestCase):
    def test_migrate_rejects_v2_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence())
            result = run(root, "migrate")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not v1", result.stdout)

    def test_migrate_v1_to_v2_preserves_evidence_and_occurs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            v1 = {
                "schema_version": "paper-reference-ledger-v1",
                "references": [reference("k1"), reference("k2")],
                "citation_usages": [usage("k1"), usage("k2")],
                "claim_evidence": [
                    {
                        "citation_key": "k1",
                        "manuscript_claim": "A well-known observation supports the claim.",
                        "manuscript_location": "paper/sections/02_intro.tex:3",
                        "source_locator": "p. 4",
                        "evidence_excerpt_or_rationale": "The source states the observation.",
                        "human_review_state": "human-confirmed",
                    }
                ],
            }
            fixture(root, teX=teX_occurrence(), ledger_json=json.dumps(v1, indent=2) + "\n")
            result = run(root, "migrate")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("migrated_evidence=1", result.stdout)
            migrated = json.loads((root / "references/ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(migrated["schema_version"], "paper-reference-ledger-v2")
            self.assertEqual(len(migrated["citation_occurrences"]), 1)
            self.assertEqual(len(migrated["claim_evidence"]), 1)
            self.assertEqual(migrated["claim_evidence"][0]["assessment"]["verdict"], "source-unavailable")
            self.assertEqual(migrated["claim_evidence"][0]["review_state"], "human-confirmed")


class CheckerV2Tests(unittest.TestCase):
    def test_v2_occurrence_coverage_missing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, teX=teX_occurrence(), occurrences=[])
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks a citation_occurrences record", result.stdout)

    def test_v2_multi_claim_same_key_needs_independent_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            teX = r"""\section{Intro}
First claim~\citep{k1}. Second different claim~\citep{k1}.
"""
            fixture(root, teX=teX)
            run(root, "inventory")
            cache = root / "dist/reference-support" / "20260811" / "inventory.json"
            items = json.loads(cache.read_text(encoding="utf-8"))
            self.assertEqual(len(items), 2)
            # only one occurrence recorded -> coverage check fails for the other
            occurrences = [
                {"occurrence_id": items[0]["occurrence_id"], "manuscript_location": items[0]["manuscript_location"], "command": "citep", "citation_keys": ["k1"], "claim_text": items[0]["claim_text"], "claim_fingerprint": items[0]["claim_fingerprint"], "review_state": "pending"}
            ]
            fixture(root, teX=teX, occurrences=occurrences)
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks a citation_occurrences record", result.stdout)

    def test_release_fails_unconfirmed_substantive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            teX = r"""\section{Intro}
A claim~\citep{k1} is made.
"""
            fixture(root, teX=teX)
            run(root, "inventory")
            cache = root / "dist/reference-support" / "20260811" / "inventory.json"
            items = json.loads(cache.read_text(encoding="utf-8"))
            occ = items[0]
            occurrences = [
                {"occurrence_id": occ["occurrence_id"], "manuscript_location": occ["manuscript_location"], "command": "citep", "citation_keys": ["k1"], "claim_text": occ["claim_text"], "claim_fingerprint": occ["claim_fingerprint"], "review_state": "provisional"}
            ]
            evidence = [
                {
                    "evidence_id": "ev_abc",
                    "occurrence_id": occ["occurrence_id"],
                    "citation_key": "k1",
                    "claim_fingerprint": occ["claim_fingerprint"],
                    "protocol_version": "citation-support-protocol-v1",
                    "source_identity": {"citation_key": "k1", "doi": "10.1000/example", "source_hash": "sha256:x"},
                    "passage": {"text": "The source reports the observation.", "locator": "Sec. 3", "hash": "sha256:y", "origin": "semantic-scholar-snippet"},
                    "assessment": {"verdict": "supported", "supported_parts": [], "unsupported_parts": [], "contradictions": [], "missing_qualifiers": [], "recommended_action": "confirm"},
                    "review_state": "provisional",
                    "updated_at": "2026-08-11",
                    "reviewer": "test",
                    "approval": "",
                }
            ]
            fixture(root, teX=teX, occurrences=occurrences, evidence=evidence)
            draft = run_checker(root, "draft")
            self.assertEqual(draft.returncode, 0, draft.stdout + draft.stderr)
            release = run_checker(root, "release")
            self.assertNotEqual(release.returncode, 0)
            self.assertIn("lacks Human confirmation", release.stdout)

    def test_release_passes_confirmed_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            teX = r"""\section{Intro}
A claim~\citep{k1} is made.
"""
            fixture(root, teX=teX)
            run(root, "inventory")
            cache = root / "dist/reference-support" / "20260811" / "inventory.json"
            items = json.loads(cache.read_text(encoding="utf-8"))
            occ = items[0]
            occurrences = [
                {"occurrence_id": occ["occurrence_id"], "manuscript_location": occ["manuscript_location"], "command": "citep", "citation_keys": ["k1"], "claim_text": occ["claim_text"], "claim_fingerprint": occ["claim_fingerprint"], "review_state": "human-confirmed"}
            ]
            evidence = [
                {
                    "evidence_id": "ev_abc",
                    "occurrence_id": occ["occurrence_id"],
                    "citation_key": "k1",
                    "claim_fingerprint": occ["claim_fingerprint"],
                    "protocol_version": "citation-support-protocol-v1",
                    "source_identity": {"citation_key": "k1", "doi": "10.1000/example", "source_hash": "sha256:x"},
                    "passage": {"text": "The source reports the observation.", "locator": "Sec. 3", "hash": "sha256:y", "origin": "semantic-scholar-snippet"},
                    "assessment": {"verdict": "supported", "supported_parts": [], "unsupported_parts": [], "contradictions": [], "missing_qualifiers": [], "recommended_action": "confirm"},
                    "review_state": "human-confirmed",
                    "updated_at": "2026-08-11",
                    "reviewer": "test",
                    "approval": "Human reviewed the support packet.",
                }
            ]
            fixture(root, teX=teX, occurrences=occurrences, evidence=evidence)
            draft = run_checker(root, "draft")
            self.assertEqual(draft.returncode, 0, draft.stdout + draft.stderr)
            release = run_checker(root, "release")
            self.assertEqual(release.returncode, 0, release.stdout + release.stderr)


if __name__ == "__main__":
    unittest.main()
