from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/overleaf-sync.py"


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root, check=check)


def commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-m", message)


class OverleafSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo = base / "repo"
        self.remote = base / "overleaf.git"
        self.seed = base / "seed"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "paper").mkdir()
        (self.repo / ".agents/tools").mkdir(parents=True)
        shutil.copy2(TOOL, self.repo / ".agents/tools/overleaf-sync.py")
        (self.repo / "paper/main.tex").write_text("canonical\n", encoding="utf-8")
        (self.repo / "paper/refs.bib").write_text("refs\n", encoding="utf-8")
        (self.repo / "AGENTS.md").write_text("governance\n", encoding="utf-8")
        (self.repo / ".agents/overleaf-sync.json").write_text(
            json.dumps(
                {
                    "schema_version": "paper-overleaf-sync-v1",
                    "source_prefix": "paper",
                    "remote": {"name": "overleaf", "url": str(self.remote), "branch": "main"},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        commit(self.repo, "canonical paper")

        git(base, "init", "--bare", self.remote.name)
        self.seed.mkdir()
        git(self.seed, "init", "-b", "main")
        git(self.seed, "config", "user.name", "Overleaf User")
        git(self.seed, "config", "user.email", "overleaf@example.com")
        (self.seed / "main.tex").write_text("initial overleaf\n", encoding="utf-8")
        commit(self.seed, "initial overleaf")
        git(self.seed, "remote", "add", "origin", str(self.remote))
        git(self.seed, "push", "origin", "main")
        git(self.repo, "remote", "add", "overleaf", str(self.remote))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def tool(self, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        return run(
            [sys.executable, str(TOOL), "--root", str(self.repo), *args],
            self.repo,
            check=check,
        )

    def test_configured_repository_passes_static_validation(self) -> None:
        result = run(
            [sys.executable, str(TOOL), "--root", str(ROOT), "validate"],
            ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("source=paper/", result.stdout)
        config = json.loads((ROOT / ".agents/overleaf-sync.json").read_text(encoding="utf-8"))
        self.assertEqual(config["source_prefix"], "paper")
        remote = config["remote"]
        self.assertIsInstance(remote, dict)
        url = remote["url"]
        self.assertIsInstance(url, str)
        self.assertTrue(url)
        self.assertNotIn("token=", url.lower())
        self.assertNotIn("password=", url.lower())
        self.assertNotRegex(url, r"://[^/@]+:[^/@]+@")

    def test_bootstrap_exports_only_paper_and_preserves_remote_history(self) -> None:
        result = self.tool("push", "--bootstrap")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        git(self.repo, "fetch", "overleaf", "main")
        files = git(self.repo, "ls-tree", "-r", "--name-only", "overleaf/main").stdout.splitlines()
        self.assertEqual(files, ["main.tex", "refs.bib"])
        self.assertNotIn("AGENTS.md", files)
        self.assertEqual(git(self.repo, "rev-list", "--count", "overleaf/main").stdout.strip(), "3")

    def test_validate_allows_clean_checkout_without_local_remote(self) -> None:
        git(self.repo, "remote", "remove", "overleaf")
        result = self.tool("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_remote_edit_blocks_push_and_can_be_pulled_on_sync_branch(self) -> None:
        self.tool("push", "--bootstrap", check=True)
        git(self.seed, "pull", "--ff-only", "origin", "main")
        (self.seed / "main.tex").write_text("edited on overleaf\n", encoding="utf-8")
        commit(self.seed, "edit on overleaf")
        git(self.seed, "push", "origin", "main")

        blocked = self.tool("push")
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("contains changes not acknowledged", blocked.stderr)

        git(self.repo, "switch", "-c", "sync/overleaf-test")
        pulled = self.tool("pull")
        self.assertEqual(pulled.returncode, 0, pulled.stdout + pulled.stderr)
        self.assertEqual(
            (self.repo / "paper/main.tex").read_text(encoding="utf-8"),
            "edited on overleaf\n",
        )
        self.assertEqual((self.repo / "AGENTS.md").read_text(encoding="utf-8"), "governance\n")

    def test_push_allows_canonical_case_branch(self) -> None:
        git(self.repo, "switch", "-c", "case/arxiv-test")
        result = self.tool("push", "--bootstrap")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        git(self.repo, "fetch", "overleaf", "main")
        files = git(self.repo, "ls-tree", "-r", "--name-only", "overleaf/main").stdout.splitlines()
        self.assertEqual(files, ["main.tex", "refs.bib"])

    def test_push_refuses_feature_branch(self) -> None:
        git(self.repo, "switch", "-c", "feat/test")
        refused = self.tool("push")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("canonical branch", refused.stderr)

    def test_pull_refuses_default_branch(self) -> None:
        refused = self.tool("pull")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("dedicated sync/overleaf-* branch", refused.stderr)

    def test_configuration_rejects_embedded_credentials(self) -> None:
        config_path = self.repo / ".agents/overleaf-sync.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["remote"]["url"] = "https://user:secret@example.com/repo.git"
        config_path.write_text(json.dumps(config) + "\n", encoding="utf-8")
        result = self.tool("validate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not contain embedded credentials", result.stderr)


if __name__ == "__main__":
    unittest.main()
