from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
PROFILE_TOOL = ROOT / ".agents/tools/check-paper-profile.py"
PUBLICATION_TOOL = ROOT / ".agents/tools/check-publication.py"
sys.path.insert(0, str(ROOT / ".agents/tools"))

from _official_templates import (
    OFFICIAL_TEMPLATES,
    OfficialTemplate,
    OfficialTemplateError,
    RemoteFile,
    _sha256,
    _download,
    _extract,
    run_smoke_matrix,
    smoke_test,
)
from _paper_profile import ProfileError, finish_output, run_profile_command
import _paper_profile


def run(tool: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(tool), "--root", str(root)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def write_external_profile(root: Path, *, output: str | None = None) -> None:
    build: dict[str, object] = {
        "name": "manuscript",
        "command": ["latexmk", "-pdf", "manuscript.tex"],
    }
    if output is not None:
        build["output"] = output
    data = {
        "schema_version": "paper-build-profile-v1",
        "layout": "external-latex",
        "source_root": ".",
        "entrypoint": "manuscript.tex",
        "bibliography": "references.bib",
        "builds": [build],
    }
    path = root / ".agents/paper-build.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")


class PaperProfileTests(unittest.TestCase):
    def test_repository_profile_passes(self) -> None:
        result = run(PROFILE_TOOL, ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_external_single_manuscript_profile_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            (root / "manuscript.tex").write_text(
                "\\documentclass{article}\n\\begin{document}Paper\\end{document}\n",
                encoding="utf-8",
            )
            (root / "references.bib").write_text("", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_profile_rejects_forbidden_source_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            path = root / ".agents/paper-build.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["source_root"] = "dist"
            data["entrypoint"] = "dist/manuscript.tex"
            data["bibliography"] = "dist/references.bib"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("generated or Agent-control surface", result.stdout)

    def test_profile_rejects_shell_command_string(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            path = root / ".agents/paper-build.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["builds"][0]["command"] = "latexmk -pdf manuscript.tex"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("argv list", result.stdout)

    def test_profile_rejects_nul_in_build_command_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            path = root / ".agents/paper-build.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["builds"][0]["command"] = ["true", "\u0000"]
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without NUL bytes", result.stdout)
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_profile_rejects_parent_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            path = root / ".agents/paper-build.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["entrypoint"] = "../paper.tex"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("safe repository-relative path", result.stdout)

    def test_profile_rejects_non_tex_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            path = root / ".agents/paper-build.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["entrypoint"] = "README.md"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".tex source file", result.stdout)

    def test_profile_rejects_non_bib_bibliography(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            path = root / ".agents/paper-build.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["bibliography"] = "references.txt"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".bib file", result.stdout)

    def test_profile_rejects_tex_entrypoint_without_document_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            (root / "references.bib").write_text("", encoding="utf-8")
            (root / "manuscript.tex").write_text("README text\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("document declaration", result.stdout)

    def test_profile_rejects_commented_tex_entrypoint_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            (root / "references.bib").write_text("", encoding="utf-8")
            (root / "manuscript.tex").write_text(
                "% \\documentclass{article}\n",
                encoding="utf-8",
            )
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("document declaration", result.stdout)

    def test_profile_rejects_symlinked_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory)
            outside = Path(external) / "outside.tex"
            outside.write_text("\\documentclass{article}\n", encoding="utf-8")
            write_external_profile(root)
            (root / "references.bib").write_text("", encoding="utf-8")
            (root / "manuscript.tex").symlink_to(outside)
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not traverse a symlink", result.stdout)

    def test_profile_rejects_duplicate_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root, output="manuscript.pdf")
            path = root / ".agents/paper-build.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["builds"].append(
                {
                    "name": "second",
                    "command": ["latexmk", "-pdf", "manuscript.tex"],
                    "output": "manuscript.pdf",
                }
            )
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate paper build output", result.stdout)

    def test_profile_rejects_output_collision_with_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root, output="manuscript.tex")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("protected source path", result.stdout)

    def test_profile_rejects_release_output_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root, output="release/manuscript.pdf")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("protected source path", result.stdout)

    def test_canonical_profile_rejects_reduced_build_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = json.loads((ROOT / ".agents/paper-build.json").read_text(encoding="utf-8"))
            profile["builds"] = profile["builds"][:1]
            path = root / ".agents/paper-build.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(profile) + "\n", encoding="utf-8")
            result = run(PROFILE_TOOL, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("standard builds declaration", result.stdout)

    def test_external_publication_contract_names_entry_and_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_external_profile(root)
            (root / "PUBLICATION.md").write_text(
                "\n".join(
                    (
                        "# Publication Contract",
                        "## Canonical paper",
                        "The entrypoint is `manuscript.tex`.",
                        "## Active variants",
                        "The declared build is `manuscript`.",
                        "## Allowed differences",
                        "## Must not diverge silently",
                        "## Human review triggers",
                        "## Build interface",
                        "## Release instances",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            result = run(PUBLICATION_TOOL, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_profile_refuses_non_linux_before_launch_and_restores_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            marker = root / "launched"
            with mock.patch.object(_paper_profile.sys, "platform", "darwin"):
                with self.assertRaisesRegex(ProfileError, "requires Linux"):
                    run_profile_command(
                        root,
                        ["sh", "-c", "touch launched"],
                        output="manuscript.pdf",
                    )
            self.assertFalse(marker.exists())
            self.assertEqual(output.read_bytes(), b"previous output")

    def test_profile_refuses_without_subreaper_before_launch_and_restores_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            marker = root / "launched"
            with mock.patch.object(_paper_profile, "_enable_child_subreaper", return_value=False):
                with self.assertRaisesRegex(ProfileError, "child-subreaper"):
                    run_profile_command(
                        root,
                        ["sh", "-c", "touch launched"],
                        output="manuscript.pdf",
                    )
            self.assertFalse(marker.exists())
            self.assertEqual(output.read_bytes(), b"previous output")

@unittest.skipUnless(sys.platform == "linux", "safe build supervision requires Linux")
class InstalledLatexTemplateTests(unittest.TestCase):
    CASES = {
        "elsarticle": (
            "elsarticle",
            r"""\documentclass{elsarticle}
\begin{document}\begin{frontmatter}\title{Fixture}\author{Author}
\begin{abstract}Abstract.\end{abstract}\end{frontmatter}Body.\end{document}
""",
        ),
        "IEEEtran": (
            "IEEEtran",
            r"""\documentclass[journal]{IEEEtran}
\title{Fixture}\author{Author}\begin{document}\maketitle
\begin{abstract}Abstract.\end{abstract}Body.\end{document}
""",
        ),
        "revtex4-2": (
            "revtex4-2",
            r"""\documentclass{revtex4-2}
\begin{document}\title{Fixture}\author{Author}
\begin{abstract}Abstract.\end{abstract}\maketitle Body.\end{document}
""",
        ),
        "acmart": (
            "acmart",
            r"""\documentclass[manuscript]{acmart}
\setcopyright{none}\acmConference{}{}{}\acmBooktitle{}
\title{Fixture}\author{Author}\affiliation{\institution{Institution}\country{Country}}
\begin{document}\begin{abstract}Abstract.\end{abstract}\maketitle Body.\end{document}
""",
        ),
        "kdd-2026": (
            "acmart",
            r"""\documentclass[sigconf,anonymous,review]{acmart}
\setcopyright{none}\acmConference{}{}{}\acmBooktitle{}
\title{Fixture}\author{Anonymous Author}
\begin{document}\begin{abstract}Abstract.\end{abstract}\maketitle Body.\end{document}
""",
        ),
    }

    def test_installed_latex_templates_compile(self) -> None:
        latexmk = shutil.which("latexmk")
        kpsewhich = shutil.which("kpsewhich")
        if latexmk is None or kpsewhich is None:
            self.skipTest("latexmk and kpsewhich are required")
        unavailable: list[str] = []
        compiled = 0
        for fixture, (class_name, source) in self.CASES.items():
            with self.subTest(fixture=fixture, document_class=class_name):
                available = subprocess.run(
                    [kpsewhich, f"{class_name}.cls"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if available.returncode != 0 or not available.stdout.strip():
                    unavailable.append(fixture)
                    continue
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / "manuscript.tex").write_text(source, encoding="utf-8")
                    result, _ = run_profile_command(
                        root,
                        [
                            latexmk,
                            "-pdf",
                            "-interaction=nonstopmode",
                            "-halt-on-error",
                            "manuscript.tex",
                        ],
                        timeout_seconds=180,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertGreater((root / "manuscript.pdf").stat().st_size, 0)
                    compiled += 1
        if os.environ.get("REQUIRE_INSTALLED_LATEX_TEMPLATES") == "1":
            self.assertEqual(unavailable, [], f"missing required LaTeX templates: {unavailable}")
        if compiled == 0:
            self.skipTest("none of the journal matrix classes is installed")


class OfficialLatexPackageTests(unittest.TestCase):
    PLATFORM_INDEPENDENT_TESTS = {
        "test_failed_build_refuses_cleanup_through_symlinked_output_parent",
        "test_official_archive_rejects_parent_traversal",
        "test_official_archive_rejects_symlink_member",
        "test_official_download_accepts_updates_and_records_digest",
        "test_official_download_rejects_hash_mismatch",
        "test_official_matrix_uses_current_sources",
    }

    def setUp(self) -> None:
        if (
            sys.platform != "linux"
            and self._testMethodName not in self.PLATFORM_INDEPENDENT_TESTS
        ):
            self.skipTest("safe build supervision requires Linux")

    def test_official_matrix_uses_current_sources(self) -> None:
        self.assertEqual(
            {template.name for template in OFFICIAL_TEMPLATES},
            {
                "springer-nature",
                "aas",
                "iop",
                "jmlr",
                "plos-one",
                "icml-2026",
                "iclr-2026",
                "neurips-2026",
                "acl-2026",
                "aaai-2026",
            },
        )
        for template in OFFICIAL_TEMPLATES:
            with self.subTest(template=template.name):
                self.assertTrue(template.venue)
                self.assertTrue(template.identity)
                self.assertTrue(template.authority_url.startswith("https://"))
                self.assertTrue(template.entrypoint)
                self.assertTrue(template.output)
                self.assertIn(template.latexmk_mode, {"-pdf", "-pdfps"})
                self.assertTrue(template.files)
                for remote in template.files:
                    self.assertIsNone(remote.sha256)
                    self.assertTrue(remote.url.startswith("https://"))

    def test_official_packages_compile(self) -> None:
        if os.environ.get("REQUIRE_OFFICIAL_LATEX_TEMPLATES") != "1":
            self.skipTest("official package smoke tests are enabled only in CI")
        if shutil.which("latexmk") is None:
            self.fail("REQUIRE_OFFICIAL_LATEX_TEMPLATES=1 requires latexmk")
        cache_override = os.environ.get("OFFICIAL_TEMPLATE_CACHE")
        if cache_override:
            failures = run_smoke_matrix(Path(cache_override))
        else:
            with tempfile.TemporaryDirectory(prefix="ccfa-official-template-cache-") as directory:
                failures = run_smoke_matrix(Path(directory))
        self.assertEqual(failures, {}, "official LaTeX smoke failures: " + repr(failures))

    def test_official_download_accepts_updates_and_records_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            source.write_bytes(b"first official package")
            remote = RemoteFile(name="package.bin", url=source.as_uri())
            cache = root / "cache"

            downloaded = _download(remote, cache)
            first_digest = _sha256(downloaded)
            source.write_bytes(b"updated official package")
            downloaded = _download(remote, cache)
            second_digest = _sha256(downloaded)

            self.assertNotEqual(first_digest, second_digest)
            self.assertEqual(downloaded.read_bytes(), b"updated official package")
            record = json.loads(
                (cache / "package.bin.sha256.json").read_text(encoding="utf-8")
            )
            self.assertEqual(record["schema_version"], "official-template-download-v1")
            self.assertEqual(record["url"], source.as_uri())
            self.assertEqual(record["sha256"], second_digest)

    def test_official_download_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            source.write_bytes(b"official package bytes")
            remote = RemoteFile(
                name="package.bin",
                url=source.as_uri(),
                sha256="0" * 64,
            )
            with self.assertRaises(OfficialTemplateError):
                _download(remote, root / "cache")
            self.assertFalse((root / "cache/package.bin").exists())

    def test_official_smoke_disables_latexmk_rc_and_shell_escape(self) -> None:
        if shutil.which("latexmk") is None:
            self.skipTest("latexmk is required")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "package.zip"
            rc_marker = root / "latexmkrc-ran"
            tex_marker = root / "shell-escape-ran"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr(
                    ".latexmkrc",
                    f"system('touch', '{rc_marker}');\n",
                )
                package.writestr(
                    "sample.tex",
                    (
                        "\\documentclass{article}\n"
                        f"\\immediate\\write18{{touch {tex_marker}}}\n"
                        "\\begin{document}Fixture\\end{document}\n"
                    ),
                )
            template = OfficialTemplate(
                name="security-fixture",
                venue="security fixture",
                identity="local",
                authority_url="https://example.invalid/fixture",
                files=(RemoteFile(name="package.zip", url=archive.as_uri()),),
                archive="package.zip",
                sample_root=None,
                entrypoint="sample.tex",
                output="sample.pdf",
            )

            smoke_test(template, root / "cache")

            self.assertFalse(rc_marker.exists())
            self.assertFalse(tex_marker.exists())

    def test_official_archive_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "package.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../outside.txt", "must not extract")
            with self.assertRaises(OfficialTemplateError):
                _extract(archive, root / "stage")
            self.assertFalse((root / "outside.txt").exists())

    def test_official_archive_rejects_symlink_member(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "package.zip"
            member = zipfile.ZipInfo("link.txt")
            member.create_system = 3
            member.external_attr = (0o120777 << 16) | 0o777
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr(member, "../outside.txt")
            with self.assertRaisesRegex(OfficialTemplateError, "symlink"):
                _extract(archive, root / "stage")
            self.assertFalse((root / "outside.txt").exists())

    def test_failed_build_refuses_cleanup_through_symlinked_output_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory)
            outside = Path(external) / "manuscript.pdf"
            outside.write_bytes(b"keep this file")
            (root / "build").symlink_to(Path(external), target_is_directory=True)
            with self.assertRaises(ProfileError):
                finish_output(root, "build/manuscript.pdf", None, command_succeeded=False)
            self.assertEqual(outside.read_bytes(), b"keep this file")

    def test_profile_command_rejects_dangling_output_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            outside = Path(external) / "missing.pdf"
            (root / "manuscript.pdf").symlink_to(outside)
            with self.assertRaisesRegex(ProfileError, "must not traverse a symlink"):
                run_profile_command(
                    root,
                    ["sh", "-c", "printf changed > manuscript.pdf"],
                    output="manuscript.pdf",
                )
            self.assertFalse(outside.exists())

    def test_profile_command_rejects_and_unstages_tracked_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "init"],
                cwd=root,
                check=True,
            )
            result, ready = run_profile_command(
                root,
                ["sh", "-c", "printf changed > manuscript.pdf; git add -f manuscript.pdf"],
                output="manuscript.pdf",
            )
            self.assertEqual(result.returncode, 0)
            self.assertFalse(ready)
            self.assertFalse((root / "manuscript.pdf").exists())
            self.assertEqual(
                subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout,
                "",
            )

    def test_profile_command_rejects_output_after_ignore_rule_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            result, ready = run_profile_command(
                root,
                ["sh", "-c", ": > .gitignore; printf changed > manuscript.pdf"],
                output="manuscript.pdf",
            )
            self.assertEqual(result.returncode, 0)
            self.assertFalse(ready)
            self.assertFalse((root / "manuscript.pdf").exists())

    def test_failed_output_cleanup_refuses_when_unstaging_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            output = root / "manuscript.pdf"
            output.write_bytes(b"generated output")
            subprocess.run(["git", "add", "manuscript.pdf"], cwd=root, check=True)
            real_run = subprocess.run

            def fail_unstage(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if command[:2] == ["git", "rm"]:
                    return subprocess.CompletedProcess(command, 1, "", "index is locked")
                return real_run(command, **kwargs)

            with mock.patch.object(_paper_profile.subprocess, "run", side_effect=fail_unstage):
                with self.assertRaisesRegex(ProfileError, "cannot remove failed build output"):
                    finish_output(root, "manuscript.pdf", None, command_succeeded=False)
            self.assertTrue(output.is_file())

    def test_profile_command_timeout_restores_previous_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            expired = subprocess.TimeoutExpired(["build"], 1, output="partial", stderr="")
            with mock.patch("_paper_profile._run_profile_subprocess", side_effect=expired):
                result, ready = run_profile_command(
                    root,
                    ["build"],
                    output="manuscript.pdf",
                    timeout_seconds=1,
                )
            self.assertEqual(result.returncode, 124)
            self.assertFalse(ready)
            self.assertEqual(output.read_bytes(), b"previous output")
            self.assertEqual(list(root.glob(".*.paper-build-backup-*")), [])

    def test_profile_command_decodes_invalid_output_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ready = run_profile_command(
                Path(directory),
                [
                    sys.executable,
                    "-c",
                    "import os; os.write(1, b'bad: \\xff\\n')",
                ],
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue(ready)
            self.assertEqual(result.stdout, "bad: \ufffd\n")

    def test_profile_command_refuses_unrelated_active_child(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
            try:
                with self.assertRaisesRegex(ProfileError, "unrelated child processes"):
                    run_profile_command(Path(directory), ["true"])
                self.assertIsNone(unrelated.poll())
            finally:
                unrelated.terminate()
                unrelated.wait()

    def test_profile_timeout_kills_detached_descendant_before_output_restore(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            child = (
                "import pathlib, sys, time; "
                "time.sleep(0.7); "
                "pathlib.Path(sys.argv[1]).write_bytes(b'child output')"
            )
            parent = (
                "import subprocess, sys, time; "
                "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]], "
                "start_new_session=True, stdin=subprocess.DEVNULL, "
                "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                "time.sleep(10)"
            )
            command = [sys.executable, "-c", parent, child, str(output)]
            result, ready = run_profile_command(
                root,
                command,
                output="manuscript.pdf",
                timeout_seconds=0.2,
            )
            self.assertEqual(result.returncode, 124)
            self.assertFalse(ready)
            self.assertEqual(output.read_bytes(), b"previous output")
            time.sleep(1)
            self.assertEqual(output.read_bytes(), b"previous output")

    def test_profile_timeout_does_not_wait_for_reparented_pipe_holder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            ready = root / "ready"
            grandchild = """
import os
import pathlib
import signal
import sys
import time

def fork_late_writer(signum, frame):
    if os.fork() == 0:
        os.setsid()
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        time.sleep(0.8)
        pathlib.Path(sys.argv[2]).write_bytes(b"late child output")
        os._exit(0)
    os._exit(0)

signal.signal(signal.SIGTERM, fork_late_writer)
pathlib.Path(sys.argv[1]).write_text("ready")
while True:
    time.sleep(1)
"""
            child = (
                "import os, subprocess, sys; "
                "subprocess.Popen([sys.executable, '-c', sys.argv[2], sys.argv[1], sys.argv[3]], "
                "start_new_session=True); "
                "os._exit(0)"
            )
            parent = """
import pathlib
import subprocess
import sys
import time

subprocess.Popen(
    [sys.executable, "-c", sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]],
    start_new_session=True,
)
deadline = time.time() + 2
while not pathlib.Path(sys.argv[2]).exists() and time.time() < deadline:
    time.sleep(0.01)
time.sleep(10)
"""
            command = [
                sys.executable,
                "-c",
                parent,
                child,
                str(ready),
                grandchild,
                str(output),
            ]
            started = time.monotonic()
            result, ready = run_profile_command(
                root,
                command,
                output="manuscript.pdf",
                timeout_seconds=0.2,
            )
            elapsed = time.monotonic() - started
            self.assertEqual(result.returncode, 124)
            self.assertFalse(ready)
            self.assertLess(elapsed, 2.5)
            self.assertEqual(output.read_bytes(), b"previous output")
            time.sleep(1)
            self.assertEqual(output.read_bytes(), b"previous output")

    def test_failed_build_restores_output_after_cleaning_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("build/\n", encoding="utf-8")
            output = root / "build/manuscript.pdf"
            output.parent.mkdir()
            output.write_bytes(b"previous output")
            result, ready = run_profile_command(
                root,
                ["sh", "-c", "rm -rf build; exit 1"],
                output="build/manuscript.pdf",
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(ready)
            self.assertEqual(output.read_bytes(), b"previous output")

    def test_failed_build_restores_output_replaced_by_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            victim = Path(external) / "victim.pdf"
            victim.write_bytes(b"victim")
            command = [
                sys.executable,
                "-c",
                "import pathlib, sys; pathlib.Path('manuscript.pdf').symlink_to(sys.argv[1]); raise SystemExit(1)",
                str(victim),
            ]
            result, ready = run_profile_command(
                root,
                command,
                output="manuscript.pdf",
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(ready)
            self.assertEqual(output.read_bytes(), b"previous output")
            self.assertEqual(victim.read_bytes(), b"victim")

    def test_failed_build_restores_output_after_parent_becomes_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("build/\n", encoding="utf-8")
            output = root / "build/manuscript.pdf"
            output.parent.mkdir()
            output.write_bytes(b"previous output")
            outside = Path(external)
            sentinel = outside / "sentinel"
            sentinel.write_bytes(b"outside")
            command = [
                sys.executable,
                "-c",
                (
                    "import pathlib, shutil, sys; shutil.rmtree('build'); "
                    "pathlib.Path('build').symlink_to(sys.argv[1], target_is_directory=True); "
                    "raise SystemExit(1)"
                ),
                str(outside),
            ]
            result, ready = run_profile_command(
                root,
                command,
                output="build/manuscript.pdf",
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(ready)
            self.assertEqual(output.read_bytes(), b"previous output")
            self.assertFalse(output.parent.is_symlink())
            self.assertEqual(sentinel.read_bytes(), b"outside")

    def test_failed_build_restores_output_after_parent_becomes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("build/\n", encoding="utf-8")
            output = root / "build/manuscript.pdf"
            output.parent.mkdir()
            output.write_bytes(b"previous output")
            result, ready = run_profile_command(
                root,
                ["sh", "-c", "rm -rf build; printf obstacle > build; exit 1"],
                output="build/manuscript.pdf",
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(ready)
            self.assertEqual(output.read_bytes(), b"previous output")

    def test_interrupted_profile_command_restores_previous_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            with mock.patch(
                "_paper_profile._run_profile_subprocess",
                side_effect=KeyboardInterrupt,
            ), self.assertRaises(KeyboardInterrupt):
                run_profile_command(root, ["build"], output="manuscript.pdf")
            self.assertEqual(output.read_bytes(), b"previous output")
            self.assertEqual(list(root.glob(".*.paper-build-backup-*")), [])

    def test_real_interrupt_kills_detached_descendant_before_restore(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            (root / ".gitignore").write_text("manuscript.pdf\n", encoding="utf-8")
            output = root / "manuscript.pdf"
            output.write_bytes(b"previous output")
            wrapper = r"""
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time

sys.path.insert(0, sys.argv[2])
from _paper_profile import run_profile_command

root = pathlib.Path(sys.argv[1])
output = root / "manuscript.pdf"
child = (
    "import pathlib, sys, time; "
    "time.sleep(0.8); "
    "pathlib.Path(sys.argv[1]).write_bytes(b'child output')"
)
parent = (
    "import subprocess, sys, time; "
    "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]], "
    "start_new_session=True, stdin=subprocess.DEVNULL, "
    "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
    "time.sleep(10)"
)
timer = threading.Timer(0.3, lambda: os.kill(os.getpid(), signal.SIGINT))
timer.start()
try:
    run_profile_command(
        root,
        [sys.executable, "-c", parent, child, str(output)],
        output="manuscript.pdf",
    )
except KeyboardInterrupt:
    pass
else:
    raise SystemExit("profile command was not interrupted")
timer.join()
time.sleep(1)
if output.read_bytes() != b"previous output":
    raise SystemExit("detached child changed the restored output")
"""
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    wrapper,
                    str(root),
                    str(ROOT / ".agents/tools"),
                ],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(output.read_bytes(), b"previous output")


if __name__ == "__main__":
    unittest.main()
