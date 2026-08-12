from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-documentation.py"

FIXTURE_CONFIG = {
    "schema_version": "paper-documentation-consistency-v1",
    "required_facts": {
        "paper/figures/README.md": ["There is no separate figure registry"],
    },
    "stale_patterns": {
        r"\bICLR[ _-]?2026\b": "obsolete target venue ICLR 2026",
        r"lab/artifacts/": "removed lab artifact registry",
        r"state/float-placement-map\.yaml": "removed float-placement map",
        r"scripts/check-figures-tables\.py": "removed figure/table checker",
        r"scripts/export-venue-template\.sh": "removed venue-export script",
        r"NOT used by paper/main\.tex": "obsolete venue-compatibility usage note",
    },
}


def fixture(root: Path) -> None:
    for source in ROOT.rglob("*.md"):
        if ".git" in source.parts or "dist" in source.parts:
            continue
        target = root / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(ROOT / ".agents/tools", root / ".agents/tools", dirs_exist_ok=True)
    config = root / ".agents"
    config.mkdir(parents=True, exist_ok=True)
    (config / "documentation-consistency.json").write_text(
        json.dumps(FIXTURE_CONFIG) + "\n", encoding="utf-8"
    )


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

    def test_stale_patterns_override_allows_downstream_venue_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            config = root / ".agents/documentation-consistency.json"
            data = json.loads(config.read_text(encoding="utf-8"))
            data["stale_patterns"] = {}
            config.write_text(json.dumps(data) + "\n", encoding="utf-8")
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nTarget ICLR 2026.\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
