from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/paper-init.py"
AGENTS_PROTECTED_LINE = (
    "- Never propose or perform deletion of the protected case branches "
    "(`case/arxiv-2505-22954`, `case/arxiv-2604-01658`, `case/arxiv-2605-03042`), "
    "their case issues (#23, #24, #30), or the standing verification trackers "
    "(#21, #31); do not include them in routine cleanup or deletion reports.\n"
)
DECISION_UPSTREAM = """## DEC-0014: Case branches and verification trackers are protected evidence

Decision: upstream template-only text.

## Recording future decisions
"""
DECISION_DOWNSTREAM = "## DEC-0014: Downstream paper initialization"


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root, check=check)


def init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@example.com")


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit_all(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-m", message)


def fixture(root: Path) -> None:
    init_repo(root)
    write(root, "AGENTS.md", "# Agent Entry\n\n" + AGENTS_PROTECTED_LINE + "\n")
    write(root, "DECISIONS.md", DECISION_UPSTREAM)
    write(
        root,
        "PUBLICATION.md",
        "Venue planning.\n\n"
        "This venue planning input is distinct from capability authenticity (#21) and "
        "real environment availability (#31), but strict venue planning depends on the "
        "same honest source and freshness rules.\n",
    )
    write(
        root,
        ".agents/documentation-consistency.json",
        json.dumps(
            {
                "schema_version": "paper-documentation-consistency-v1",
                "required_facts": {"README.md": ["The factory template is intentionally unresolved"]},
            },
            indent=2,
        )
        + "\n",
    )
    write(
        root,
        ".agents/overleaf-sync.json",
        json.dumps(
            {
                "schema_version": "paper-overleaf-sync-v1",
                "source_prefix": "paper",
                "remote": {
                    "name": "overleaf",
                    "url": "https://git@git.overleaf.com/6a71e37eeb498fef8922f370",
                    "branch": "main",
                },
            }
        )
        + "\n",
    )
    commit_all(root, "template scaffold")


def set_upstream_origin(root: Path) -> None:
    git(root, "remote", "add", "origin", "git@github.com:a-green-hand-jack/ccfa-writing-paper-template.git")


def valid_marker(root: Path, **replacements: object) -> str:
    data: dict[str, object] = {
        "schema_version": "paper-init-v1",
        "initialized_at": "2026-08-09T12:00:00+00:00",
        "mode": "downstream",
        "template_cleanup": True,
        "git_head": git(root, "rev-parse", "HEAD").stdout.strip(),
    }
    data.update(replacements)
    return json.dumps(data) + "\n"


class PaperInitTests(unittest.TestCase):
    def test_upstream_template_status_passes(self) -> None:
        result = run([sys.executable, str(TOOL), "--root", str(ROOT), "status"], ROOT, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("upstream_template", result.stdout)

    def test_upstream_template_origin_variants_are_recognized(self) -> None:
        variants = (
            "git@github.com:a-green-hand-jack/ccfa-writing-paper-template.git",
            "https://github.com/A-Green-Hand-Jack/CCFA-Writing-Paper-Template.git",
            "ssh://git@github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
        )
        for origin in variants:
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                git(root, "remote", "add", "origin", origin)
                result = run(
                    [sys.executable, str(TOOL), "--root", str(root), "status"],
                    root,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("upstream_template", result.stdout)

    def test_similar_writing_repo_origins_are_not_upstream_template(self) -> None:
        variants = (
            "git@github.com:a-green-hand-jack/ccfa-writing-paper-template-my-paper.git",
            "https://github.com/a-green-hand-jack/my-ccfa-writing-paper-template.git",
            "https://github.com/another-owner/ccfa-writing-paper-template.git",
        )
        for origin in variants:
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                git(root, "remote", "add", "origin", origin)
                result = run(
                    [sys.executable, str(TOOL), "--root", str(root), "status"],
                    root,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("UNINITIALIZED", result.stdout)
                self.assertNotIn("upstream_template", result.stdout)

    def test_clean_removes_template_governance_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)

            before = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(before.returncode, 0)
            self.assertIn("UNINITIALIZED", before.stdout)

            cleaned = run([sys.executable, str(TOOL), "--root", str(root), "clean"], root, check=False)
            self.assertEqual(cleaned.returncode, 0, cleaned.stdout + cleaned.stderr)

            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn("case/arxiv-2505-22954", agents)
            decisions = (root / "DECISIONS.md").read_text(encoding="utf-8")
            self.assertIn(DECISION_DOWNSTREAM, decisions)
            self.assertNotIn("case/arxiv-2505-22954", decisions)
            publication = (root / "PUBLICATION.md").read_text(encoding="utf-8")
            self.assertNotIn("#21", publication)
            self.assertNotIn("#31", publication)
            self.assertIn("all three depend on honest source and freshness rules", publication)
            self.assertFalse((root / ".agents/overleaf-sync.json").exists())

            documentation = json.loads(
                (root / ".agents/documentation-consistency.json").read_text(encoding="utf-8")
            )
            self.assertEqual(documentation["required_facts"], {})
            self.assertTrue((root / ".agents/init-state.json").is_file())

            after = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
            self.assertIn("initialized", after.stdout)

    def test_clean_commit_creates_initialization_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                root,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            message = git(root, "log", "-1", "--format=%s").stdout.strip()
            self.assertEqual(
                message,
                "chore: initialize paper repository and remove template governance residue",
            )

    def test_same_origin_requires_explicit_downstream_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_upstream_origin(root)

            default = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean"],
                root,
                check=False,
            )
            self.assertEqual(default.returncode, 0, default.stdout + default.stderr)
            self.assertIn("upstream_template", default.stdout)
            self.assertFalse((root / ".agents/init-state.json").exists())
            self.assertIn("case/arxiv-2505-22954", (root / "AGENTS.md").read_text(encoding="utf-8"))

            overridden = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--downstream"],
                root,
                check=False,
            )
            self.assertEqual(overridden.returncode, 0, overridden.stdout + overridden.stderr)
            self.assertTrue((root / ".agents/init-state.json").is_file())
            self.assertNotIn("case/arxiv-2505-22954", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_same_origin_commit_downstream_creates_initialization_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_upstream_origin(root)

            result = run(
                [
                    sys.executable,
                    str(TOOL),
                    "--root",
                    str(root),
                    "clean",
                    "--commit",
                    "--downstream",
                ],
                root,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("committed", result.stdout)
            self.assertTrue((root / ".agents/init-state.json").is_file())
            self.assertEqual(
                git(root, "log", "-1", "--format=%s").stdout.strip(),
                "chore: initialize paper repository and remove template governance residue",
            )

    def test_initialized_marker_takes_precedence_over_same_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_upstream_origin(root)
            write(root, ".agents/init-state.json", valid_marker(root))
            marker = (root / ".agents/init-state.json").read_bytes()

            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("initialized", result.stdout)
            self.assertNotIn("upstream_template", result.stdout)

            cleaned = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean"],
                root,
                check=False,
            )
            self.assertEqual(cleaned.returncode, 0, cleaned.stdout + cleaned.stderr)
            self.assertIn("already_initialized", cleaned.stdout)
            self.assertEqual(marker, (root / ".agents/init-state.json").read_bytes())
            self.assertIn("case/arxiv-2505-22954", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_invalid_markers_fail_closed_on_same_origin(self) -> None:
        marker_cases = {
            "empty object": "{}\n",
            "truncated JSON": '{"schema_version": "paper-init-v1"',
            "wrong schema": valid_marker(root=ROOT, schema_version="paper-init-v2"),
            "wrong mode": valid_marker(root=ROOT, mode="upstream"),
            "incomplete cleanup": valid_marker(root=ROOT, template_cleanup=False),
            "invalid timestamp": valid_marker(root=ROOT, initialized_at="yesterday"),
        }
        for label, marker in marker_cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                set_upstream_origin(root)
                write(root, ".agents/init-state.json", marker)

                before = run(
                    [sys.executable, str(TOOL), "--root", str(root), "status"],
                    root,
                    check=False,
                )
                self.assertNotEqual(before.returncode, 0)
                self.assertIn("invalid marker", before.stdout)
                self.assertNotIn("upstream_template", before.stdout)

                preserved = {
                    relative: (root / relative).read_bytes()
                    for relative in (
                        "AGENTS.md",
                        "DECISIONS.md",
                        "PUBLICATION.md",
                        ".agents/documentation-consistency.json",
                        ".agents/overleaf-sync.json",
                        ".agents/init-state.json",
                    )
                }
                cleaned = run(
                    [sys.executable, str(TOOL), "--root", str(root), "clean"],
                    root,
                    check=False,
                )
                self.assertNotEqual(cleaned.returncode, 0)
                self.assertIn("invalid initialization marker", cleaned.stderr)
                self.assertIn("--downstream", cleaned.stderr)
                self.assertEqual(
                    preserved,
                    {relative: (root / relative).read_bytes() for relative in preserved},
                )

                overridden = run(
                    [
                        sys.executable,
                        str(TOOL),
                        "--root",
                        str(root),
                        "clean",
                        "--downstream",
                    ],
                    root,
                    check=False,
                )
                self.assertEqual(overridden.returncode, 0, overridden.stdout + overridden.stderr)
                self.assertNotIn("case/arxiv-2505-22954", (root / "AGENTS.md").read_text(encoding="utf-8"))
                self.assertTrue((root / ".agents/init-state.json").is_file())

    def test_marker_bound_to_another_repository_fails_closed_on_same_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other_directory:
            root = Path(directory)
            other = Path(other_directory)
            fixture(root)
            fixture(other)
            write(other, "other-repository.txt", "different history\n")
            commit_all(other, "different repository")
            set_upstream_origin(root)
            write(root, ".agents/init-state.json", valid_marker(other))

            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid marker", result.stdout)

            preserved = {
                relative: (root / relative).read_bytes()
                for relative in (
                    "AGENTS.md",
                    "DECISIONS.md",
                    "PUBLICATION.md",
                    ".agents/documentation-consistency.json",
                    ".agents/overleaf-sync.json",
                    ".agents/init-state.json",
                )
            }
            cleaned = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean"],
                root,
                check=False,
            )
            self.assertNotEqual(cleaned.returncode, 0)
            self.assertIn("--downstream", cleaned.stderr)
            self.assertEqual(
                preserved,
                {relative: (root / relative).read_bytes() for relative in preserved},
            )

            overridden = run(
                [
                    sys.executable,
                    str(TOOL),
                    "--root",
                    str(root),
                    "clean",
                    "--downstream",
                ],
                root,
                check=False,
            )
            self.assertEqual(overridden.returncode, 0, overridden.stdout + overridden.stderr)
            self.assertNotIn("case/arxiv-2505-22954", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_marker_commit_must_be_in_current_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root, ".agents/init-state.json", valid_marker(root, git_head="f" * 40))

            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid marker", result.stdout)


if __name__ == "__main__":
    unittest.main()
