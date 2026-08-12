from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-venue-knowledge.py"
TEMPLATE = ROOT / ".agents/knowledge/venues/_template.md"


def run(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), *extra],
        text=True,
        capture_output=True,
        check=False,
    )


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class VenueKnowledgeChecks(unittest.TestCase):
    def test_unconfigured_template_passes(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("unconfigured", result.stdout)

    def test_missing_required_section_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, ".agents/knowledge/venues/iclr-2027.md", "# ICLR 2027\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing heading", result.stdout)

    def test_unknown_values_are_unverified_and_strict_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(
                root,
                ".agents/knowledge/venues/iclr-2027.md",
                TEMPLATE.read_text(encoding="utf-8").replace(
                    "venue: UNKNOWN", "venue: ICLR"
                ),
            )
            normal = run(root)
            self.assertEqual(normal.returncode, 0, normal.stdout + normal.stderr)
            self.assertIn("UNVERIFIED venue_knowledge", normal.stdout)
            strict = run(root, "--strict")
            self.assertNotEqual(strict.returncode, 0)
            self.assertIn("UNVERIFIED venue_knowledge", strict.stdout)

    def test_verified_venue_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = TEMPLATE.read_text(encoding="utf-8")
            for old, new in (
                ("venue: UNKNOWN", "venue: ICLR"),
                ("year: UNKNOWN", "year: 2027"),
                ("status: UNKNOWN", "status: active"),
                ("submission_portal: UNKNOWN", "submission_portal: https://openreview.net/example"),
                ("call_for_papers: UNKNOWN", "call_for_papers: https://example.com/cfp"),
                ("author_guidelines: UNKNOWN", "author_guidelines: https://example.com/guide"),
                ("dates_page: UNKNOWN", "dates_page: https://example.com/dates"),
                ("author_kit: UNKNOWN", "author_kit: https://example.com/kit"),
                ("policy_page: UNKNOWN", "policy_page: https://example.com/policy"),
                ("last_checked: UNKNOWN", "last_checked: 2026-08-05"),
                ("abstract_deadline: UNKNOWN", "abstract_deadline: 2026-09-01"),
                ("paper_deadline: UNKNOWN", "paper_deadline: 2026-09-08"),
                ("main_text: UNKNOWN", "main_text: 10"),
                ("page_budget_status: UNKNOWN", "page_budget_status: verified"),
            ):
                text = text.replace(old, new)
            write(root, ".agents/knowledge/venues/iclr-2027.md", text)
            result = run(root, "--strict")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OK venue_knowledge", result.stdout)


if __name__ == "__main__":
    unittest.main()
