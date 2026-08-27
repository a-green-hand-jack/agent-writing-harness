from __future__ import annotations

import json
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
        "AGENT_GUIDE.md",
        "WHY_THIS_TEMPLATE.md",
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
        ".agents/knowledge/writing/README.md",
        ".agents/knowledge/venues/README.md",
        ".agents/knowledge/venues/_template.md",
        ".agents/template-sync.json",
        ".agents/template-inheritance.json",
        ".agents/overleaf-sync.json",
        ".agents/skills/paper-orientation/SKILL.md",
        ".agents/skills/template-adoption/SKILL.md",
        ".agents/skills/template-sync/SKILL.md",
        ".agents/vendor/README.md",
        ".agents/vendor/ccfa-skills/LICENSE",
        ".agents/vendor/ccfa-skills/ccf-common/SKILL.md",
        ".agents/vendor/ccfa-skills/ccf-paper-writer/SKILL.md",
        ".agents/vendor/writing-dna-skill/LICENSE",
        ".agents/vendor/writing-dna-skill/SKILL.md",
        ".agents/tools/_template_inheritance.py",
        ".agents/tools/_paper_profile.py",
        ".agents/tools/verify.sh",
        ".agents/tools/check-documentation.py",
        ".agents/tools/check-venue-knowledge.py",
        ".agents/tools/check-publication.py",
        ".agents/tools/check-paper-profile.py",
        ".agents/tools/release.py",
        ".agents/tools/check-release.py",
        ".agents/tools/check-release-records.py",
        ".agents/tools/template-adoption.py",
        ".agents/tools/template-sync.py",
        ".agents/tools/overleaf-sync.py",
        ".agents/tools/paper-init.py",
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

    def test_template_development_surface_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            evals_dir = root / ".agents/evals" / "vendored-skills"
            evals_dir.mkdir(parents=True)
            write(evals_dir / "README.md", "# dev-only\n")
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

    def test_external_layout_allows_native_scripts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / "scripts/build-paper.sh", "#!/bin/sh\nexit 0\n")
            (root / "paper/figures/srcs/native-only.png").write_bytes(b"native asset")
            write(
                root / ".agents/paper-build.json",
                json.dumps(
                    {
                        "schema_version": "paper-build-profile-v1",
                        "layout": "external-latex",
                        "source_root": "paper",
                        "entrypoint": "paper/main.tex",
                        "bibliography": "paper/refs.bib",
                        "builds": [
                            {
                                "name": "manuscript",
                                "command": ["sh", "scripts/build-paper.sh"],
                            }
                        ],
                    }
                )
                + "\n",
            )
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_external_layout_rejects_legacy_release_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / "release").mkdir()
            write(
                root / ".agents/paper-build.json",
                json.dumps(
                    {
                        "schema_version": "paper-build-profile-v1",
                        "layout": "external-latex",
                        "source_root": "paper",
                        "entrypoint": "paper/main.tex",
                        "bibliography": "paper/refs.bib",
                        "builds": [{"name": "manuscript", "command": ["true"]}],
                    }
                )
                + "\n",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be removed: release", result.stdout)

    def test_dependency_boundary_resolves_path_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(
                root / "paper/main.tex",
                """\\documentclass{article}
\\begin{document}
\\input{paper/.././.agents/secret}
\\end{document}
""",
            )
            write(root / ".agents/secret.tex", "Control content\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-paper surface", result.stdout)

    def test_dependency_boundary_resolves_symlinked_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            secret = root / ".agents/secret.tex"
            write(secret, "Secret control content\n")
            (root / "paper/linked.tex").symlink_to(secret)
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-paper surface", result.stdout)

    def test_dependency_boundary_scans_local_style_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/secret.tex", "Control content\n")
            write(root / "paper/local.sty", "\\input{../.agents/secret}\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("paper/local.sty -> .agents/secret.tex", result.stdout)

    def test_dependency_boundary_preserves_escaped_percent_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/secret.tex", "Control content\n")
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\begin{document}",
                    "\\begin{document}\n\\%\\input{../.agents/secret}",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-paper surface", result.stdout)

    def test_dependency_boundary_resolves_graphics_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / ".agents/secret.png").write_bytes(b"control asset")
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\begin{document}",
                    "\\begin{document}\n\\includegraphics{../.agents/secret}",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-paper surface", result.stdout)

    def test_dependency_boundary_resolves_whitespace_separated_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            for suffix in ("tex", "png", "bib", "bst", "sty", "cls"):
                write(root / f".agents/secret.{suffix}", "Control content\n")
            write(
                root / "paper/main.tex",
                r"""\documentclass [11pt] {../.agents/secret}
\usepackage [draft] {../.agents/secret}
\begin{document}
\input {../.agents/secret}
\includegraphics [width=1cm] {../.agents/secret}
\bibliography {../.agents/secret}
\addbibresource [ ] {../.agents/secret}
\bibliographystyle {../.agents/secret}
\end{document}
""",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-paper surface", result.stdout)

    def test_dependency_boundary_rejects_unresolved_dynamic_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(
                root / "paper/main.tex",
                """\\documentclass{article}
\\def\\sidecar{../.agents}
\\begin{document}
\\input{\\sidecar/secret}
\\end{document}
""",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unresolved dynamic input dependency", result.stdout)

    def test_dependency_boundary_checks_input_if_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/secret.tex", "Control content\n")
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\begin{document}",
                    "\\begin{document}\n\\InputIfFileExists{../.agents/secret}{}{}",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-paper surface", result.stdout)

    def test_dependency_boundary_rejects_search_path_directives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\begin{document}",
                    "\\graphicspath{{../.agents/}}\n\\begin{document}",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported TeX dependency search path directive", result.stdout)

    def test_dependency_boundary_rejects_unbraced_input_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\begin{document}",
                    "\\begin{document}\n\\input ../.agents/secret",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported unbraced TeX input syntax", result.stdout)

    def test_dependency_boundary_rejects_pipe_input_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            main = root / "paper/main.tex"
            main.write_text(
                main.read_text(encoding="utf-8").replace(
                    "\\begin{document}",
                    '\\begin{document}\n\\input|"touch escaped"',
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported unbraced TeX input syntax", result.stdout)


if __name__ == "__main__":
    unittest.main()
