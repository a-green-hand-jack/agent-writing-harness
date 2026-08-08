from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

try:
    import bibtexparser  # noqa: F401
except ImportError:
    bibtexparser = None

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / ".agents/tools/_validate-bibtex-correction.py"


@unittest.skipIf(bibtexparser is None, "bibtexparser is installed only in the locked reference environment")
class BibtexCorrectionHelperTests(unittest.TestCase):
    def load_helper(self):
        spec = importlib.util.spec_from_file_location("paper_bibtex_correction_validator", HELPER)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_report_action_must_match_candidate_content(self) -> None:
        helper = self.load_helper()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bib"
            candidate = root / "candidate.bib"
            report = root / "report.jsonl"
            source.write_text("@article{real, title={Old}}\n", encoding="utf-8")
            candidate.write_text("@article{real, title={New}}\n", encoding="utf-8")
            base = {
                "file": str(source), "key_old": "real", "key_new": "real",
                "doi_old": None, "doi_new": None, "action": "unchanged",
                "method": None, "confidence": 0.0, "title_old": "Old", "title_new": "New",
            }
            report.write_text(json.dumps(base) + "\n", encoding="utf-8")
            rejected = helper.validate(source, candidate, report)
            self.assertFalse(rejected["passed"])
            self.assertIn("action does not match candidate content", rejected["errors"][0])

            base["action"] = "upgraded"
            report.write_text(json.dumps(base) + "\n", encoding="utf-8")
            accepted = helper.validate(source, candidate, report)
            self.assertTrue(accepted["passed"], accepted["errors"])
            self.assertEqual(accepted["changed_keys"], ["real"])

            base["title_new"] = "False report title"
            report.write_text(json.dumps(base) + "\n", encoding="utf-8")
            false_metadata = helper.validate(source, candidate, report)
            self.assertFalse(false_metadata["passed"])
            self.assertTrue(any("title_new" in error for error in false_metadata["errors"]))


if __name__ == "__main__":
    unittest.main()
