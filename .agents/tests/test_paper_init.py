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


class PaperInitTests(unittest.TestCase):
    def test_upstream_template_status_passes(self) -> None:
        result = run([sys.executable, str(TOOL), "--root", str(ROOT), "status"], ROOT, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("upstream_template", result.stdout)

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


if __name__ == "__main__":
    unittest.main()
