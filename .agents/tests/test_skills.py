from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-skills.py"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def skill(name: str, description: str = "Use for focused work.") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n"


def fixture(root: Path) -> None:
    write(root / "AGENTS.md", "# Agent Entry\n\n## Task routing\n\n- focused work -> `.agents/skills/alpha/SKILL.md`\n")
    write(root / ".agents/skills/alpha/SKILL.md", skill("alpha"))


class SkillChecks(unittest.TestCase):
    def test_repository_skills_pass(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_frontmatter_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/skills/alpha/SKILL.md", "# Alpha\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing YAML frontmatter", result.stdout)

    def test_empty_name_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/skills/alpha/SKILL.md", skill(""))
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires non-empty name", result.stdout)

    def test_empty_description_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/skills/alpha/SKILL.md", "---\nname: alpha\ndescription: \n---\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires non-empty description", result.stdout)

    def test_name_directory_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/skills/alpha/SKILL.md", skill("beta"))
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match directory", result.stdout)

    def test_duplicate_name_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/skills/beta/SKILL.md", skill("alpha"))
            write(root / "AGENTS.md", "# Agent Entry\n\nfocused -> `.agents/skills/beta/SKILL.md`\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate skill name", result.stdout)

    def test_missing_router_entry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / "AGENTS.md", "# Agent Entry\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not route skill", result.stdout)

    def test_stale_adapter_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/AGENTS.md", "Read ../.agent/capabilities/registry.yaml\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stale adapter reference", result.stdout)


if __name__ == "__main__":
    unittest.main()
