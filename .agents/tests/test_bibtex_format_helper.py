from __future__ import annotations

import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path

try:
    import pybtex  # noqa: F401
except ImportError:
    pybtex = None

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / ".agents/tools/_validate-bibtex-with-pybtex.py"
sys.path.insert(0, str(HELPER.parent))


@unittest.skipIf(pybtex is None, "Pybtex is installed only in the locked reference environment")
class PybtexHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("paper_pybtex_validator", HELPER)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {HELPER}")
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)

    def validate(self, text: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            bibliography = Path(directory) / "refs.bib"
            bibliography.write_text(text, encoding="utf-8")
            return self.helper.validate(bibliography)

    def test_valid_classic_article_passes(self) -> None:
        report = self.validate(
            "@article{real, author={A. Author}, title={A Paper}, "
            "journal={A Journal}, year={2026}}\n"
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["keys"], ["real"])

    def test_missing_required_fields_and_bad_year_fail(self) -> None:
        report = self.validate("@article{bad, title={A Paper}, year={26}}\n")
        self.assertFalse(report["passed"])
        messages = {record["message"] for record in report["errors"]}
        self.assertIn("missing required field: author", messages)
        self.assertIn("missing required field: journal", messages)
        self.assertIn("year must contain exactly four digits", messages)

    def test_biblatex_only_type_is_rejected(self) -> None:
        report = self.validate("@online{web, title={A Page}, year={2026}}\n")
        self.assertFalse(report["passed"])
        self.assertIn("unsupported classic BibTeX entry type: online", report["errors"][0]["message"])

    def test_crossref_inherits_proceedings_title_and_year(self) -> None:
        report = self.validate(
            "@inproceedings{child, author={A. Author}, title={A Paper}, crossref={parent}}\n"
            "@proceedings{parent, title={Proceedings Title}, year={2026}}\n"
        )
        self.assertTrue(report["passed"], report["errors"])

    def test_unknown_crossref_fails(self) -> None:
        report = self.validate(
            "@inproceedings{child, author={A. Author}, title={A Paper}, crossref={missing}}\n"
        )
        self.assertFalse(report["passed"])
        self.assertIn("crossref points to unknown entry: missing", report["errors"][0]["message"])

    def test_proceedings_title_does_not_replace_child_title(self) -> None:
        report = self.validate(
            "@inproceedings{child, author={A. Author}, crossref={parent}}\n"
            "@proceedings{parent, title={Proceedings Title}, year={2026}}\n"
        )
        self.assertFalse(report["passed"])
        child_errors = [record["message"] for record in report["errors"] if record["key"] == "child"]
        self.assertEqual(child_errors, ["missing required field: title"])

    def test_duplicate_doi_and_normalized_title_fail(self) -> None:
        report = self.validate(
            "@article{one, author={A}, title={{Same} Work}, journal={J}, year={2026}, doi={10.1/X}}\n"
            "@article{two, author={B}, title={same work}, journal={J}, year={2026}, doi={https://doi.org/10.1/x}}\n"
        )
        self.assertFalse(report["passed"])
        messages = [record["message"] for record in report["errors"]]
        self.assertTrue(any("duplicate DOI identity" in message for message in messages))
        self.assertTrue(any("duplicate normalized title identity" in message for message in messages))

    def test_doi_resolver_tracking_and_semantic_macros_normalize_safely(self) -> None:
        duplicate = self.validate(
            "@article{one, author={A}, title={One}, journal={J}, year={2026}, doi={10.1/X}}\n"
            "@article{two, author={B}, title={Two}, journal={J}, year={2026}, "
            "doi={https://www.doi.org/10.1/x?utm_source=test#fragment}}\n"
        )
        self.assertFalse(duplicate["passed"])
        self.assertTrue(any("duplicate DOI identity" in record["message"] for record in duplicate["errors"]))

        distinct = self.validate(
            "@article{one, author={A}, title={Learning \\LaTeX}, journal={J}, year={2026}}\n"
            "@article{two, author={B}, title={Learning \\BibTeX}, journal={J}, year={2026}}\n"
        )
        self.assertTrue(distinct["passed"], distinct["errors"])


if __name__ == "__main__":
    unittest.main()
