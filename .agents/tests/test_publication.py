from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-publication.py"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def fixture(root: Path) -> None:
    for relative in ("PUBLICATION.md", "Makefile"):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    (root / "paper").mkdir(parents=True, exist_ok=True)
    for relative in ("paper/main.tex", "paper/macros.tex"):
        shutil.copy2(ROOT / relative, root / relative)
    shutil.copytree(ROOT / "paper/variants", root / "paper/variants")


class PublicationChecks(unittest.TestCase):
    def test_repository_variants_pass(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_draft_root_default_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\providecommand{\\PaperVariant}{anonymous}",
                    "\\providecommand{\\PaperVariant}{draft}",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must default to anonymous", result.stdout)

    def test_missing_config_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / "paper/variants/config/anonymous.tex").unlink()
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing variant config", result.stdout)

    def test_copied_section_in_variant_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            extra = root / "paper/variants/anonymous_intro.tex"
            extra.write_text("\\section{Copied content}\n", encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("do not copy paper content", result.stdout)

    def test_anonymous_acknowledgements_leak_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            config = root / "paper/variants/config/anonymous.tex"
            config.write_text(
                config.read_text(encoding="utf-8").replace(
                    "\\PaperAcknowledgementsfalse", "\\PaperAcknowledgementstrue"
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PaperAcknowledgementsfalse", result.stdout)

    def test_external_entrypoint_requires_exact_code_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".agents").mkdir()
            (root / ".agents/paper-build.json").write_text(
                json.dumps(
                    {
                        "schema_version": "paper-build-profile-v1",
                        "layout": "external-latex",
                        "source_root": ".",
                        "entrypoint": "main.tex",
                        "bibliography": None,
                        "builds": [{"name": "manuscript", "command": ["make"]}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            headings = (
                "# Publication Contract\n## Canonical paper\n`not-main.tex`\n"
                "## Active variants\n`manuscript`\n## Allowed differences\n"
                "## Must not diverge silently\n## Human review triggers\n"
                "## Build interface\n## Release instances\n"
            )
            (root / "PUBLICATION.md").write_text(headings, encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("declared entrypoint", result.stdout)


if __name__ == "__main__":
    unittest.main()
