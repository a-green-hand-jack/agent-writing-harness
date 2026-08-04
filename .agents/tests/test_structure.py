from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-structure.py"


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fixture(root: Path) -> None:
    for relative in (
        "README.md",
        "Makefile",
        "PAPER.md",
        "EXPERIMENTS.md",
        "PAPER_INTERFACES.md",
        "PUBLICATION.md",
        "DECISIONS.md",
        "AGENTS.md",
        "releases/README.md",
        "releases/records/README.md",
        "paper/macros.tex",
        "paper/venue_preamble.tex",
        "paper/refs.bib",
        "paper/variants/README.md",
        "paper/variants/common.tex",
        "paper/variants/draft.tex",
        "paper/variants/anonymous.tex",
        "paper/variants/camera_ready.tex",
        "paper/variants/arxiv.tex",
        ".agents/knowledge/README.md",
        ".agents/template-sync.json",
        ".agents/skills/paper-orientation/SKILL.md",
        ".agents/skills/template-adoption/SKILL.md",
        ".agents/skills/template-sync/SKILL.md",
        ".agents/tools/verify.sh",
        ".agents/tools/check-actions.py",
        ".agents/tools/check-skills.py",
        ".agents/tools/check-publication.py",
        ".agents/tools/release.py",
        ".agents/tools/check-release.py",
        ".agents/tools/check-release-records.py",
        ".agents/tools/template-adoption.py",
        ".agents/tools/template-sync.py",
        ".agents/tools/overleaf-sync.py",
        ".agents/runtime/.gitignore",
    ):
        write(root / relative)
    write(root / "paper/sections/00_title.tex", "Title\n")
    write(root / "paper/sections/01_abstract.tex", "Abstract\n")
    write(root / "paper/sections/02_intro.tex", "Intro\n")
    write(root / "paper/sections/10_appendix.tex", "Appendix\n")
    write(
        root / "paper/main.tex",
        """\\documentclass{article}
\\begin{document}
\\input{sections/00_title}
\\input{sections/01_abstract}
\\input{sections/02_intro}
\\appendix
\\input{sections/10_appendix}
\\end{document}
""",
    )
    (root / "paper/figures/srcs").mkdir(parents=True)


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


class StructureChecks(unittest.TestCase):
    def test_minimal_paper_first_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_obsolete_surface_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / "release").mkdir()
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be removed", result.stdout)

    def test_dangling_section_input_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\input{sections/02_intro}", "\\input{sections/09_missing}"
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dangling section input", result.stdout)


if __name__ == "__main__":
    unittest.main()
