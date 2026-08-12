from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/paper-fidelity.py"

POPPLER_READY = shutil.which("pdftotext") is not None and shutil.which("pdfinfo") is not None
LATEX_READY = shutil.which("latexmk") is not None or shutil.which("pdflatex") is not None


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def build_pdf(directory: Path, name: str, text: str) -> Path:
    source = directory / f"{name}.tex"
    source.write_text(
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        f"{text}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    command = "latexmk" if shutil.which("latexmk") else "pdflatex"
    result = subprocess.run(
        [command, "-pdf", "-interaction=nonstopmode", "-halt-on-error", source.name],
        cwd=directory,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise unittest.SkipTest(f"local LaTeX build failed: {result.stdout[-500:]}")
    pdf = directory / f"{name}.pdf"
    if not pdf.is_file():
        raise unittest.SkipTest(f"local LaTeX build produced no PDF: {result.stdout[-500:]}")
    return pdf


class PaperFidelityChecksumTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_checksum_matches_expected_digest(self) -> None:
        target = self.directory / "archive.zip"
        target.write_bytes(b"original arxiv source")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        result = run(["checksum", "--file", str(target), "--sha256", digest], self.directory)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK fidelity_checksum", result.stdout)

    def test_checksum_mismatch_fails(self) -> None:
        target = self.directory / "archive.zip"
        target.write_bytes(b"original arxiv source")
        result = run(
            ["checksum", "--file", str(target), "--sha256", "0" * 64], self.directory
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("mismatch", result.stderr)

    def test_checksum_rejects_invalid_digest(self) -> None:
        target = self.directory / "archive.zip"
        target.write_bytes(b"x")
        result = run(["checksum", "--file", str(target), "--sha256", "not-hex"], self.directory)
        self.assertEqual(result.returncode, 2)
        self.assertIn("hex digest", result.stderr)


@unittest.skipUnless(POPPLER_READY and LATEX_READY, "poppler or LaTeX unavailable")
class PaperFidelityEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_identical_pdf_evidence_matches(self) -> None:
        pdf = build_pdf(self.directory, "doc", "Hello fidelity world.")
        result = run(
            [
                "evidence",
                "--label",
                "identical",
                "--original",
                str(pdf),
                "--rebuilt",
                str(pdf),
                "--out",
                "identical.json",
            ],
            self.directory,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ordered_text_equality=true", result.stdout)
        report = self.directory / ".agents/runtime/fidelity/identical.json"
        self.assertTrue(report.is_file())

    def test_text_mismatch_is_reported_and_gated(self) -> None:
        original = build_pdf(self.directory, "original", "First original sentence.")
        rebuilt = build_pdf(self.directory, "rebuilt", "Second different sentence.")
        result = run(
            [
                "evidence",
                "--label",
                "mismatch",
                "--original",
                str(original),
                "--rebuilt",
                str(rebuilt),
                "--out",
                "mismatch.json",
            ],
            self.directory,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ordered_text_equality=false", result.stdout)

        gated = run(
            [
                "evidence",
                "--label",
                "mismatch-gated",
                "--original",
                str(original),
                "--rebuilt",
                str(rebuilt),
                "--require-match",
            ],
            self.directory,
        )
        self.assertEqual(gated.returncode, 2)
        self.assertIn("mismatch required failure", gated.stderr)

    def test_missing_input_fails(self) -> None:
        result = run(
            [
                "evidence",
                "--label",
                "missing",
                "--original",
                str(self.directory / "absent.pdf"),
                "--rebuilt",
                str(self.directory / "absent.pdf"),
            ],
            self.directory,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
