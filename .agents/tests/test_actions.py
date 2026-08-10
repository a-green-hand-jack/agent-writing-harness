from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-actions.py"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def write_workflow(root: Path, body: str) -> None:
    path = root / ".github/workflows/test.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class ActionsChecks(unittest.TestCase):
    def test_repository_workflows_pass(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_retired_checkout_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_workflow(root, "uses: actions/checkout@v4\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("actions/checkout@v4 is below required", result.stdout)

    def test_retired_setup_python_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_workflow(root, "uses: actions/setup-python@v5\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("actions/setup-python@v5 is below required", result.stdout)

    def test_retired_upload_artifact_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_workflow(root, "uses: actions/upload-artifact@v4\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("actions/upload-artifact@v4 is below required", result.stdout)

    def test_missing_versioned_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_workflow(root, "uses: actions/checkout@main\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must use a major ref", result.stdout)

    def test_reference_workflow_keeps_online_audits_manual(self) -> None:
        workflow_path = ROOT / ".github/workflows/reference-validation.yml"
        if not workflow_path.is_file():
            sync = json.loads((ROOT / ".agents/template-sync.json").read_text(encoding="utf-8"))
            self.assertFalse(sync["reference_integrity"]["adopted"])
            return
        workflow = workflow_path.read_text(encoding="utf-8")
        manual = workflow.split("- name: Run manual online correction audit", 1)[1].split(
            "- name: Upload reference audit evidence", 1
        )[0]
        self.assertIn("- name: Run manual online metadata audit", manual)
        self.assertEqual(manual.count("github.event_name == 'workflow_dispatch'"), 2)
        self.assertNotIn("github.event_name == 'pull_request'", manual)
        self.assertNotIn("github.event_name != 'pull_request'", manual)
        self.assertIn("secrets.OPENALEX_API_KEY", manual)
        self.assertIn("secrets.S2_API_KEY", manual)
        self.assertIn("'refs/heads/main'", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("path: dist/reference-integrity/\n", workflow)
        self.assertNotIn("metadata-cache.db", workflow)
        self.assertNotIn("http-cache.db", workflow)

    def test_publication_workflow_builds_every_variant(self) -> None:
        workflow = (ROOT / ".github/workflows/publication-variants.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("variant: [draft, anonymous, camera-ready, arxiv]", workflow)
        self.assertIn("cm-super", workflow)
        self.assertIn('make pdf VARIANT="${{ matrix.variant }}"', workflow)
        self.assertIn('pdftotext "$pdf"', workflow)
        self.assertIn('grep -Fq "Anonymous authors"', workflow)
        self.assertIn('grep -Fq "Paper under double-blind review"', workflow)
        self.assertIn('grep -Fq "Ruofeng Yang"', workflow)
        self.assertIn('grep -Fq "Skill Inventory"', workflow)
        self.assertIn('! grep -Fq "wanshuiyin"', workflow)


if __name__ == "__main__":
    unittest.main()
