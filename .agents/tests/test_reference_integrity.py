from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / ".agents/tools/check-reference-integrity.py"
METADATA = ROOT / ".agents/tools/check-reference-metadata.py"
FORMAT = ROOT / ".agents/tools/check-bibtex-format.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def reference(key: str, *, status: str = "verified", review: str = "human-confirmed") -> dict[str, object]:
    return {
        "citation_key": key,
        "status": status,
        "identifiers": {"doi": "10.0000/example"} if status == "verified" else {},
        "verification": {
            "sources": ["crossref"] if status == "verified" else [],
            "checked_at": "2026-08-05" if status == "verified" else None,
        },
        "human_review": {"state": review, "rationale": "Reviewed fixture."},
    }


def claim(key: str, *, state: str = "human-confirmed") -> dict[str, str]:
    return {
        "citation_key": key,
        "manuscript_claim": "The cited work reports the stated observation.",
        "manuscript_location": "paper/sections/02_intro.tex:3",
        "source_locator": "p. 4, Sec. 2",
        "evidence_excerpt_or_rationale": "The source states the observation directly.",
        "human_review_state": state,
    }


def ledger(
    references: list[dict[str, object]],
    claims: list[dict[str, str]] | None = None,
    usages: list[dict[str, str]] | None = None,
) -> str:
    return json.dumps(
        {
            "schema_version": "paper-reference-ledger-v1",
            "references": references,
            "citation_usages": usages or [],
            "claim_evidence": claims or [],
        },
        indent=2,
    ) + "\n"


def fixture(
    root: Path,
    bib: str,
    records: list[dict[str, object]],
    claims: list[dict[str, str]] | None = None,
    usages: list[dict[str, str]] | None = None,
) -> None:
    write(root / ".agents/template-sync.json", '{"reference_integrity":{"adopted":true}}\n')
    write(root / "PUBLICATION.md", policy())
    write(root / "paper/refs.bib", "% REFERENCE_INTEGRITY_REQUIRED: references/ledger.json\n" + bib)
    write(root / "references/ledger.json", ledger(records, claims, usages))


def run_checker(root: Path, profile: str = "draft") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), "--profile", profile],
        text=True,
        capture_output=True,
        check=False,
    )


class ReferenceIntegrityTests(unittest.TestCase):
    def test_current_repository_passes_draft_and_fails_release_closed(self) -> None:
        draft = run_checker(ROOT, "draft")
        self.assertEqual(draft.returncode, 0, draft.stdout + draft.stderr)

        release = run_checker(ROOT, "release")
        self.assertNotEqual(release.returncode, 0, release.stdout + release.stderr)
        self.assertIn("lacks Human confirmation for release", release.stdout)

    def test_missing_policy_skips_for_legacy_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_checker(Path(directory))
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP reference_integrity policy not enabled", result.stdout)

    def test_activation_marker_prevents_policy_deletion_or_disable(self) -> None:
        for publication in ("", policy().replace('"enforced"', '"disabled"')):
            with self.subTest(publication=bool(publication)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write(root / ".agents/template-sync.json", '{"reference_integrity":{"adopted":true}}\n')
                write(root / "PUBLICATION.md", publication)
                write(root / "paper/refs.bib", "% REFERENCE_INTEGRITY_REQUIRED: references/ledger.json\n")
                result = run_checker(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("activation marker", result.stdout)

    def test_adopted_state_prevents_deleting_both_marker_and_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root / ".agents/template-sync.json", '{"reference_integrity":{"adopted":true}}\n')
            write(root / "paper/refs.bib", "")
            result = run_checker(root, "release")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires the protected PUBLICATION.md policy", result.stdout)

    def test_v1_policy_paths_are_canonical(self) -> None:
        for field, replacement in (("bibliography", "alternate.bib"), ("ledger", "alternate.json")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root, "", [])
                publication = (root / "PUBLICATION.md").read_text(encoding="utf-8")
                canonical = "paper/refs.bib" if field == "bibliography" else "references/ledger.json"
                write(root / "PUBLICATION.md", publication.replace(canonical, replacement))
                result = run_checker(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"policy {field} must be", result.stdout)

    def test_policy_rejects_repository_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(
                root / "PUBLICATION.md",
                policy().replace('"paper/refs.bib"', '"../outside.bib"'),
            )
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("policy bibliography must be paper/refs.bib", result.stdout)

    def test_nested_braces_and_non_reference_entries_parse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(
                root,
                """@string{venue = "Journal"}
@comment{ignored @article{fake, title={Fake}}}
@preamble{"ignored"}
@article{real,
  title = {{A {Nested} Title}},
  note = "quoted {value}",
  journal = venue
}
""",
                [reference("real")],
            )
            result = run_checker(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("references=1", result.stdout)

    def test_parenthesis_bibtex_tracks_braces_and_starred_citation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(
                root,
                "@article(real, title={A ) with @article{fake, nested}}, year={2026})\n",
                [reference("real")],
            )
            write(root / "paper/section.tex", "\\citep*{missing}\n")
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("paper cites a key missing from BibTeX: missing", result.stdout)
            self.assertNotIn("fake", result.stdout)

    def test_every_cited_key_requires_reviewed_usage_classification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, "@article{real, title={A}}\n", [reference("real")])
            write(root / "paper/section.tex", "\\cite{real}\n")
            missing = run_checker(root)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("lacks a reviewed citation_usages record", missing.stdout)

            write(
                root / "references/ledger.json",
                ledger(
                    [reference("real")],
                    usages=[{
                        "citation_key": "real",
                        "manuscript_location": "paper/section.tex:1",
                        "classification": "background",
                        "human_review_state": "human-confirmed",
                    }],
                ),
            )
            passed = run_checker(root, "release")
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

    def test_claim_support_usage_requires_claim_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(
                root,
                "@article{real, title={A}}\n",
                [reference("real")],
                usages=[{
                    "citation_key": "real",
                    "manuscript_location": "paper/section.tex:1",
                    "classification": "claim-support",
                    "human_review_state": "human-confirmed",
                }],
            )
            write(root / "paper/section.tex", "\\cite{real}\n")
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without claim_evidence", result.stdout)

    def test_duplicate_bibtex_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, "@article{dup, title={A}}\n@book{dup, title={B}}\n", [reference("dup")])
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate BibTeX citation key: dup", result.stdout)

    def test_missing_and_extra_ledger_keys_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, "@article{bib_only, title={A}}\n", [reference("ledger_only")])
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("BibTeX citation key missing from reference ledger: bib_only", result.stdout)
            self.assertIn("reference ledger key missing from BibTeX: ledger_only", result.stdout)

    def test_duplicate_ledger_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, "@article{dup, title={A}}\n", [reference("dup"), reference("dup")])
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate reference ledger citation key: dup", result.stdout)

    def test_unverified_warns_in_draft_but_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified", review="pending")])
            draft = run_checker(root, "draft")
            self.assertEqual(draft.returncode, 0, draft.stdout + draft.stderr)
            self.assertIn("WARN reference unknown is unverified", draft.stdout)
            release = run_checker(root, "release")
            self.assertNotEqual(release.returncode, 0)
            self.assertIn("remains unverified for release", release.stdout)

    def test_problematic_blocks_draft(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, "@article{bad, title={A}}\n", [reference("bad", status="problematic")])
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reference bad is problematic", result.stdout)

    def test_agent_resolved_verified_identity_passes_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = reference("real")
            record["human_review"] = {"state": "agent-resolved", "rationale": "Matched exact DOI and publisher record."}
            fixture(root, "@article{real, title={A}}\n", [record])
            result = run_checker(root, "release")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_agent_resolved_cannot_mark_unverified_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = reference("real", status="unverified")
            record["human_review"] = {"state": "agent-resolved", "rationale": "Insufficient evidence."}
            fixture(root, "@article{real, title={A}}\n", [record])
            result = run_checker(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot be agent-resolved unless verified", result.stdout)

    def test_agent_resolved_identity_does_not_bypass_pending_usage_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = reference("real")
            record["human_review"] = {"state": "agent-resolved", "rationale": "Exact DOI and publisher match."}
            fixture(
                root,
                "@article{real, title={A}}\n",
                [record],
                usages=[{
                    "citation_key": "real",
                    "manuscript_location": "paper/section.tex:1",
                    "classification": "background",
                    "human_review_state": "pending",
                }],
            )
            write(root / "paper/section.tex", "\\cite{real}\n")
            result = run_checker(root, "release")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks Human confirmation for release", result.stdout)

    def test_claim_evidence_required_fields(self) -> None:
        for field in (
            "citation_key",
            "manuscript_claim",
            "manuscript_location",
            "source_locator",
            "evidence_excerpt_or_rationale",
            "human_review_state",
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                evidence = claim("real")
                evidence[field] = ""
                fixture(root, "@article{real, title={A}}\n", [reference("real")], [evidence])
                result = run_checker(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f".{field} must be non-empty", result.stdout)

    def test_pending_claim_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, "@article{real, title={A}}\n", [reference("real")], [claim("real", state="pending")])
            draft = run_checker(root, "draft")
            self.assertEqual(draft.returncode, 0, draft.stdout + draft.stderr)
            release = run_checker(root, "release")
            self.assertNotEqual(release.returncode, 0)
            self.assertIn("lacks Human confirmation for release", release.stdout)


class ReferenceMetadataTests(unittest.TestCase):
    def run_metadata(self, root: Path, uv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(METADATA), "--root", str(root), "--uv", uv, "--attempts", "1", "--timeout", "5"],
            text=True,
            capture_output=True,
            check=False,
        )

    def add_lock(self, root: Path) -> None:
        write(root / ".agents/dependencies/reference-integrity/uv.lock", "fixture lock\n")
        write(root / ".agents/tools/check-reference-integrity.py", CHECKER.read_text(encoding="utf-8"))
        write(root / ".agents/tools/_reference_env.py", (ROOT / ".agents/tools/_reference_env.py").read_text(encoding="utf-8"))

    def test_policy_absent_skips_without_uv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            result = self.run_metadata(root, "definitely-missing-uv")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "skipped")

    def test_missing_uv_is_infrastructure_error_not_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            result = self.run_metadata(root, "definitely-missing-uv")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "infrastructure_error")
            self.assertFalse(summary["approves_claim_support"])

    def test_valid_checker_report_never_approves_claim_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{real, title={A}}\n", [reference("real")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
assert sys.argv[sys.argv.index('--rate-limit') + 1] == '30'
assert sys.argv[sys.argv.index('--workers') + 1] == '1'
assert '--no-google-books' in sys.argv
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'real', 'status': 'verified', 'abstained': False,
    'coverage_incomplete': False, 'errors': []
}) + '\\n')
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "passed")
            self.assertFalse(summary["approves_claim_support"])

    def test_not_found_report_is_unverified_not_fabricated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'unknown', 'status': 'not_found', 'abstained': True,
    'coverage_incomplete': False, 'errors': []
}) + '\\n')
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("not evidence of fabrication", result.stdout)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "unverified")

    def test_api_error_is_infrastructure_error_even_with_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{real, title={A}}\n", [reference("real")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'real', 'status': 'api_error', 'abstained': False,
    'coverage_incomplete': True, 'errors': ['API_ERROR']
}) + '\\n')
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "infrastructure_error")

    def test_rate_limit_is_advisory_not_a_reference_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'unknown', 'status': 'strict_warn_cnv', 'abstained': False,
    'coverage_incomplete': False, 'errors': []
}) + '\\n')
print("Service 'dblp' is rate-limited/unavailable", file=sys.stderr)
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("CI not blocked", result.stdout)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "rate_limited")
            self.assertTrue(summary["rate_limit_degraded"])

    def test_rate_limit_does_not_hide_positive_metadata_problem(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{bad, title={A}}\n", [reference("bad")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'bad', 'status': 'author_mismatch', 'abstained': False,
    'coverage_incomplete': False, 'errors': []
}) + '\\n')
print("Service 'semanticscholar' is rate-limited/unavailable", file=sys.stderr)
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "reference_problem")
            self.assertTrue(summary["rate_limit_degraded"])

    def test_authenticated_rate_limit_banner_is_not_throttling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'unknown', 'status': 'strict_warn_cnv', 'abstained': False,
    'coverage_incomplete': False, 'errors': []
}) + '\\n')
print('Using Semantic Scholar API key (authenticated rate limits)')
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "unverified")
            self.assertFalse(summary["rate_limit_degraded"])

    def test_cached_rate_limit_circuit_is_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'unknown', 'status': 'api_error', 'abstained': True,
    'coverage_incomplete': True,
    'errors': ['circuit open for service semanticscholar']
}) + '\\n')
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "rate_limited")
            self.assertTrue(summary["rate_limit_degraded"])

    def test_rate_limit_does_not_hide_unrelated_infrastructure_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(
                root,
                "@article{limited, title={A}}\n@article{broken, title={B}}\n",
                [reference("limited", status="unverified"), reference("broken", status="unverified")],
            )
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
records = [
    {'key': 'limited', 'status': 'api_error', 'abstained': True,
     'coverage_incomplete': True, 'errors': ['circuit open for service dblp']},
    {'key': 'broken', 'status': 'api_error', 'abstained': True,
     'coverage_incomplete': True, 'errors': ['unexpected parser failure']},
]
target.write_text(''.join(json.dumps(record) + '\\n' for record in records))
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "infrastructure_error")
            self.assertTrue(summary["rate_limit_degraded"])

    def test_active_rate_limit_circuit_with_network_retry_error_is_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'unknown', 'status': 'api_error', 'abstained': True,
    'coverage_incomplete': True,
    'errors': ['Network failure after retries for Semantic Scholar']
}) + '\\n')
print("Service 'semanticscholar' is rate-limited/unavailable", file=sys.stderr)
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "rate_limited")
            self.assertTrue(summary["rate_limit_degraded"])

    def test_rate_limit_status_does_not_hide_parser_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{broken, title={A}}\n", [reference("broken", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'broken', 'status': 'rate_limit', 'abstained': True,
    'coverage_incomplete': True, 'errors': ['unexpected parser failure']
}) + '\\n')
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "infrastructure_error")
            self.assertTrue(summary["rate_limit_degraded"])

    def test_parser_timeout_text_is_not_a_provider_outage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{broken, title={A}}\n", [reference("broken", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'broken', 'status': 'api_error', 'abstained': True,
    'coverage_incomplete': True, 'errors': ['Exception: bibliography parser timed out']
}) + '\\n')
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "infrastructure_error")

    def test_upstream_request_timeout_is_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'unknown', 'status': 'api_error', 'abstained': True,
    'coverage_incomplete': True, 'errors': ['Request timed out']
}) + '\\n')
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "provider_unavailable")

    def test_provider_network_failures_are_advisory_without_claiming_rate_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(
                root,
                "@article{dblp, title={A}}\n@article{openalex, title={B}}\n",
                [reference("dblp", status="unverified"), reference("openalex", status="unverified")],
            )
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
records = [
    {'key': 'dblp', 'status': 'api_error', 'abstained': True,
     'coverage_incomplete': True, 'errors': ['Network failure after retries for DBLP']},
    {'key': 'openalex', 'status': 'api_error', 'abstained': True,
     'coverage_incomplete': True, 'errors': ['Network failure after retries for OpenAlex']},
]
target.write_text(''.join(json.dumps(record) + '\\n' for record in records))
print("Service 'dblp' is rate-limited/unavailable", file=sys.stderr)
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "provider_unavailable")
            self.assertEqual(summary["rate_limited_services"], ["dblp"])

    def test_pre_circuit_provider_network_failure_is_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_lock(root)
            fixture(root, "@article{unknown, title={A}}\n", [reference("unknown", status="unverified")])
            runner = root / "fake-uv"
            write(
                runner,
                """#!/usr/bin/env python3
import json, pathlib, sys
target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    'key': 'unknown', 'status': 'api_error', 'abstained': True,
    'coverage_incomplete': True,
    'errors': ['Network failure after retries for https://api.semanticscholar.org']
}) + '\\n')
raise SystemExit(4)
""",
            )
            runner.chmod(0o755)
            result = self.run_metadata(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
            self.assertEqual(summary["outcome"], "provider_unavailable")
            self.assertFalse(summary["rate_limit_degraded"])

    def test_malformed_or_wrong_key_report_is_infrastructure_error(self) -> None:
        cases = (
            {"key": "real", "status": "verified"},
            {
                "key": "extra", "status": "verified", "abstained": False,
                "coverage_incomplete": False, "errors": [],
            },
        )
        for record in cases:
            with self.subTest(record=record), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.add_lock(root)
                fixture(root, "@article{real, title={A}}\n", [reference("real")])
                runner = root / "fake-uv"
                write(
                    runner,
                    "#!/usr/bin/env python3\nimport json, pathlib, sys\n"
                    "target = pathlib.Path(sys.argv[sys.argv.index('--jsonl') + 1])\n"
                    "target.parent.mkdir(parents=True, exist_ok=True)\n"
                    f"target.write_text(json.dumps({record!r}) + '\\\\n')\n",
                )
                runner.chmod(0o755)
                result = self.run_metadata(root, str(runner))
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                summary = json.loads((root / "dist/reference-integrity/run.json").read_text())
                self.assertEqual(summary["outcome"], "infrastructure_error")


class BibtexFormatTests(unittest.TestCase):
    def run_format(self, root: Path, uv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(FORMAT), "--root", str(root), "--uv", uv, "--timeout", "5"],
            text=True,
            capture_output=True,
            check=False,
        )

    def add_tools(self, root: Path) -> None:
        write(root / ".agents/dependencies/reference-integrity/uv.lock", "fixture lock\n")
        write(root / ".agents/tools/check-reference-integrity.py", CHECKER.read_text(encoding="utf-8"))
        write(root / ".agents/tools/_validate-bibtex-with-pybtex.py", "# fixture helper\n")

    def test_empty_bibliography_skips_without_uv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_tools(root)
            fixture(root, "", [])
            result = self.run_format(root, "definitely-missing-uv")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/format-run.json").read_text())
            self.assertEqual(summary["outcome"], "skipped")
            self.assertFalse(summary["rewrites_bibliography"])

    def test_valid_complete_pybtex_report_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_tools(root)
            fixture(root, "@article{real, author={A}, title={T}, journal={J}, year={2026}}\n", [reference("real")])
            runner = root / "fake-uv"
            write(
                runner,
                "#!/usr/bin/env python3\nimport json, pathlib, sys\n"
                "target = pathlib.Path(sys.argv[-1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                "target.write_text(json.dumps({'schema_version': 'paper-bibtex-format-report-v1', "
                "'checker': 'pybtex', 'passed': True, 'keys': ['real'], 'errors': []}) + '\\n')\n",
            )
            runner.chmod(0o755)
            result = self.run_format(root, str(runner))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/format-run.json").read_text())
            self.assertEqual(summary["outcome"], "passed")

    def test_pybtex_format_problem_is_not_infrastructure_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_tools(root)
            fixture(root, "@article{bad, title={T}}\n", [reference("bad")])
            runner = root / "fake-uv"
            write(
                runner,
                "#!/usr/bin/env python3\nimport json, pathlib, sys\n"
                "target = pathlib.Path(sys.argv[-1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                "target.write_text(json.dumps({'schema_version': 'paper-bibtex-format-report-v1', "
                "'checker': 'pybtex', 'passed': False, 'keys': ['bad'], "
                "'errors': [{'key': 'bad', 'message': 'missing required field: author'}]}) + '\\n')\n"
                "raise SystemExit(1)\n",
            )
            runner.chmod(0o755)
            result = self.run_format(root, str(runner))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/format-run.json").read_text())
            self.assertEqual(summary["outcome"], "format_problem")

    def test_contradictory_pybtex_report_is_infrastructure_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_tools(root)
            fixture(root, "@article{real, title={T}}\n", [reference("real")])
            runner = root / "fake-uv"
            write(
                runner,
                "#!/usr/bin/env python3\nimport json, pathlib, sys\n"
                "target = pathlib.Path(sys.argv[-1])\n"
                "target.parent.mkdir(parents=True, exist_ok=True)\n"
                "target.write_text(json.dumps({'schema_version': 'paper-bibtex-format-report-v1', "
                "'checker': 'pybtex', 'passed': True, 'keys': ['real'], "
                "'errors': [{'key': 'real', 'message': 'contradiction'}]}) + '\\n')\n",
            )
            runner.chmod(0o755)
            result = self.run_format(root, str(runner))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("contradicts", result.stdout)

    def test_stale_report_cannot_mask_helper_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.add_tools(root)
            fixture(root, "@article{real, title={T}}\n", [reference("real")])
            stale = root / "dist/reference-integrity/format.json"
            write(
                stale,
                json.dumps({
                    "schema_version": "paper-bibtex-format-report-v1",
                    "checker": "pybtex",
                    "passed": False,
                    "keys": ["real"],
                    "errors": [{"key": "real", "message": "old finding"}],
                }) + "\n",
            )
            runner = root / "fake-uv"
            write(runner, "#!/usr/bin/env python3\nraise SystemExit(2)\n")
            runner.chmod(0o755)
            result = self.run_format(root, str(runner))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("invalid or missing Pybtex report", result.stdout)


if __name__ == "__main__":
    unittest.main()
