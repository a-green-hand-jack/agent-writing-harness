from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-paper-interfaces.py"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def fixture(root: Path) -> None:
    (root / "paper/sections").mkdir(parents=True)
    (root / "paper/generated").mkdir(parents=True)
    (root / "paper/macros.tex").write_text(
        """% Fixture interface definitions.

% Interface: PaperTODO
\\providecommand{\\PaperTODO}[1]{\\textbf{[TODO: #1]}}

% Interface: PaperTitle
\\providecommand{\\PaperTitle}{Fixture Title}

% Interface: PaperAuthors
\\providecommand{\\PaperAuthors}{Fixture Authors}

% Interface: MethodName
\\providecommand{\\MethodName}{Fixture Method}

% Interface: CoreTerm
\\providecommand{\\CoreTerm}{fixture core term}

% Interface: StateSymbol
\\providecommand{\\StateSymbol}{fixture-state}

% Interface: MainResult
\\providecommand{\\MainResult}{\\PaperTODO{main result}}

% Interface: MainResultUncertainty
\\providecommand{\\MainResultUncertainty}{\\PaperTODO{main-result uncertainty}}

\\InputIfFileExists{generated/results-macros.tex}{}{}
""",
        encoding="utf-8",
    )
    (root / "paper/sections/01_abstract.tex").write_text(
        "\\PaperTitle{} \\PaperAuthors{} \\MethodName{} \\CoreTerm{} "
        "\\StateSymbol{} \\MainResult{} \\MainResultUncertainty{}\n",
        encoding="utf-8",
    )
    (root / "PAPER_INTERFACES.md").write_text(
        """# Paper Interfaces

Fixture documentation for the paper interface checker.

- `\\PaperTODO{...}` — Draft-only placeholder.
- `\\PaperTitle{}` — canonical title.
- `\\PaperAuthors{}` — canonical visible author line.
- `\\MethodName{}` — method name.
- `\\CoreTerm{}` — central concept term.
- `\\StateSymbol{}` — state notation.
- `\\MainResult{}` — main result.
- `\\MainResultUncertainty{}` — paired uncertainty.
""",
        encoding="utf-8",
    )


class PaperInterfaceChecks(unittest.TestCase):
    def test_repository_interfaces_pass(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_longer_command_cannot_satisfy_main_result_definition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            path = root / "paper/macros.tex"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("\\providecommand{\\MainResult}{\\PaperTODO{main result}}\n", ""),
                encoding="utf-8",
            )

            result = run(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing interface definition: \\MainResult", result.stdout)

    def test_longer_marker_cannot_satisfy_main_result_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            path = root / "paper/macros.tex"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("% Interface: MainResult\n", ""), encoding="utf-8")

            result = run(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing Human-readable interface marker: MainResult", result.stdout)

    def test_longer_command_cannot_satisfy_main_result_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            path = root / "paper/sections/01_abstract.tex"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("\\MainResult{}", "\\MainResultUncertainty{}"), encoding="utf-8")

            result = run(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stable interface has no active paper consumer: \\MainResult", result.stdout)

    def test_longer_command_cannot_satisfy_main_result_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            path = root / "PAPER_INTERFACES.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("\\MainResult", "\\MainResultUncertainty"), encoding="utf-8")

            result = run(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not document \\MainResult", result.stdout)


if __name__ == "__main__":
    unittest.main()
