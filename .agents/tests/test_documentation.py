from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-documentation.py"


def fixture(root: Path) -> None:
    for source in ROOT.rglob("*.md"):
        if ".git" in source.parts or "dist" in source.parts:
            continue
        target = root / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(ROOT / ".agents/tools", root / ".agents/tools", dirs_exist_ok=True)
    shutil.copy2(ROOT / ".agents/documentation-consistency.json", root / ".agents/documentation-consistency.json")


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


class DocumentationChecks(unittest.TestCase):
    def test_repository_documentation_passes(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_removed_registry_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            readme = root / "paper/figures/README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nSee lab/artifacts/figure-index.yaml.\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("removed lab artifact registry", result.stdout)

    def test_obsolete_venue_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nTarget ICLR 2026.\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("obsolete target venue ICLR 2026", result.stdout)

    def test_removed_venue_export_comment_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            style = root / "paper/style/compat.sty"
            style.parent.mkdir(parents=True, exist_ok=True)
            style.write_text(
                "% Use scripts/export-venue-template.sh.\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("removed venue-export script", result.stdout)

    def test_missing_agent_path_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nRun `.agents/tools/removed-check.py`.\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("references missing repository path", result.stdout)

    def test_missing_configured_current_fact_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            readme = root / "paper/figures/README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "There is no separate figure registry",
                    "A separate figure registry exists",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing current fact", result.stdout)


if __name__ == "__main__":
    unittest.main()
