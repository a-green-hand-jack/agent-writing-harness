from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
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

## DEC-0015: Generally applicable decision

Decision: this decision remains applicable downstream.

## Recording future decisions
"""
DECISION_DOWNSTREAM = "## DEC-0014: Downstream paper initialization"


def run(
    command: list[str],
    cwd: Path,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
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


@contextmanager
def fake_gh(template_repository: str = "a-green-hand-jack/ccfa-writing-paper-template"):
    with tempfile.TemporaryDirectory() as directory:
        executable = Path(directory) / "gh"
        executable.write_text(
            "#!/usr/bin/env sh\n"
            f"printf '%s\\n' '{template_repository}'\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = f"{directory}:{env.get('PATH', '')}"
        yield env


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
    write(
        root,
        ".agents/template-sync.json",
        json.dumps(
            {
                "always_manual": [],
                "ignored_paths": [],
                "last_synced_at": None,
                "last_synced_commit": None,
                "schema_version": "paper-template-sync-v1",
                "upstream": {
                    "branch": "main",
                    "remote": "template",
                    "url": "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
                },
            }
        )
        + "\n",
    )
    commit_all(root, "template scaffold")


def set_upstream_origin(root: Path) -> None:
    git(root, "remote", "add", "origin", "git@github.com:a-green-hand-jack/ccfa-writing-paper-template.git")


def set_template_origin(root: Path) -> None:
    repository = "a-green-hand-jack/example-paper"
    git(root, "remote", "add", "origin", f"git@github.com:{repository}.git")
    write(
        root,
        ".agents/template-origin.json",
        json.dumps(
            {
                "downstream_repository": repository,
                "git_head": git(root, "rev-parse", "HEAD").stdout.strip(),
                "schema_version": "paper-template-origin-v1",
                "template_repository": "a-green-hand-jack/ccfa-writing-paper-template",
                "verification": "github_api_template_repository",
                "verified_at": "2026-08-09T12:00:00+00:00",
            }
        )
        + "\n",
    )
    commit_all(root, "record template provenance")


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


def reviewed_sync_metadata(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "adoption": {
            "prior_sync_history": [],
            "reviewed_at": "2026-08-25T12:00:00+00:00",
            "status": "reviewed",
            "target_commit": "a" * 40,
            "verification_repository_fingerprint": "b" * 64,
        },
        "last_synced_at": "2026-08-25T12:00:00+00:00",
        "last_synced_commit": "a" * 40,
        "schema_version": "paper-template-sync-v1",
        "upstream": {
            "branch": "main",
            "remote": "template",
            "url": "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
        },
    }
    data.update(overrides)
    return data


class PaperInitTests(unittest.TestCase):
    def test_upstream_template_status_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_upstream_origin(root)
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
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
            set_template_origin(root)

            before = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(before.returncode, 0)
            self.assertIn("UNINITIALIZED", before.stdout)

            with fake_gh() as env:
                cleaned = run(
                    [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                    root,
                    check=False,
                    env=env,
                )
            self.assertEqual(cleaned.returncode, 0, cleaned.stdout + cleaned.stderr)

            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn("case/arxiv-2505-22954", agents)
            decisions = (root / "DECISIONS.md").read_text(encoding="utf-8")
            self.assertIn(DECISION_DOWNSTREAM, decisions)
            self.assertNotIn("case/arxiv-2505-22954", decisions)
            # Later generally-applicable decisions must survive downstream clean.
            self.assertIn("## DEC-0015: Generally applicable decision", decisions)
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
            set_template_origin(root)
            with fake_gh() as env:
                result = run(
                    [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                    root,
                    check=False,
                    env=env,
                )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            message = git(root, "log", "-1", "--format=%s").stdout.strip()
            self.assertEqual(
                message,
                "chore: initialize paper repository and remove template governance residue",
            )

    def test_clean_refuses_missing_sync_metadata_before_first_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as directory, fake_gh() as env:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            (root / ".agents/template-sync.json").unlink()
            commit_all(root, "remove sync metadata")

            refused = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                root,
                check=False,
                env=env,
            )

            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("template-sync.json", refused.stderr)
            self.assertFalse((root / ".agents/init-state.json").exists())

    def test_repeated_clean_refuses_missing_sync_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory, fake_gh() as env:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            first = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                root,
                check=False,
                env=env,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            (root / ".agents/template-sync.json").unlink()
            commit_all(root, "remove sync metadata after initialization")

            refused = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                root,
                check=False,
                env=env,
            )

            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("template-sync.json", refused.stderr)

    def test_status_recognizes_in_progress_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(
                root,
                ".agents/template-sync.json",
                json.dumps(
                    {
                        "adoption": {
                            "prior_sync_history": [],
                            "status": "in_progress",
                            "target_commit": "a" * 40,
                        },
                        "last_synced_at": None,
                        "last_synced_commit": None,
                        "schema_version": "paper-template-sync-v1",
                        "upstream": {
                            "branch": "main",
                            "remote": "template",
                            "url": "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
                        },
                    }
                )
                + "\n",
            )
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("adoption_in_progress", result.stdout)

    def test_status_recognizes_reviewed_adoption_without_template_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root, ".agents/template-sync.json", json.dumps(reviewed_sync_metadata()) + "\n")
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("adoption_reviewed", result.stdout)

    def test_status_rejects_reviewed_adoption_with_template_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            write(root, ".agents/init-state.json", valid_marker(root))
            write(root, ".agents/template-sync.json", json.dumps(reviewed_sync_metadata()) + "\n")
            commit_all(root, "record conflicting reviewed adoption")
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("adoption must not carry", result.stdout)

    def test_status_rejects_in_progress_adoption_with_template_origin_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            write(
                root,
                ".agents/template-sync.json",
                json.dumps(
                    {
                        "adoption": {
                            "prior_sync_history": [],
                            "status": "in_progress",
                            "target_commit": "a" * 40,
                        },
                        "last_synced_at": None,
                        "last_synced_commit": None,
                        "schema_version": "paper-template-sync-v1",
                        "upstream": {
                            "branch": "main",
                            "remote": "template",
                            "url": "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
                        },
                    }
                )
                + "\n",
            )
            result = run([sys.executable, str(TOOL), "--root", str(root), "status"], root, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("adoption must not carry", result.stdout)

    def test_status_rejects_reviewed_adoption_with_dangling_template_origin_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root, ".agents/template-sync.json", json.dumps(reviewed_sync_metadata()) + "\n")
            (root / ".agents/template-origin.json").symlink_to("missing-origin.json")
            result = run([sys.executable, str(TOOL), "--root", str(root), "status"], root, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("adoption must not carry", result.stdout)

    def test_status_and_record_origin_reject_symlinked_sync_metadata(self) -> None:
        for dangling in (False, True):
            with self.subTest(dangling=dangling), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                git(root, "remote", "add", "origin", "git@github.com:a-green-hand-jack/example-paper.git")
                sync_path = root / ".agents/template-sync.json"
                sync_text = sync_path.read_text(encoding="utf-8")
                sync_path.unlink()
                target = "missing-sync.json"
                if not dangling:
                    target = "linked-sync.json"
                    write(root, ".agents/linked-sync.json", sync_text)
                sync_path.symlink_to(target)
                commit_all(root, "record unsafe sync metadata")

                status = run(
                    [sys.executable, str(TOOL), "--root", str(root), "status"],
                    root,
                    check=False,
                )
                self.assertNotEqual(status.returncode, 0)
                self.assertIn("malformed adoption metadata", status.stdout)
                with fake_gh() as env:
                    recorded = run(
                        [
                            sys.executable,
                            str(TOOL),
                            "--root",
                            str(root),
                            "record-template-origin",
                            "--commit",
                        ],
                        root,
                        check=False,
                        env=env,
                    )
                self.assertNotEqual(recorded.returncode, 0)
                self.assertIn("template adoption metadata is invalid", recorded.stderr)

    def test_status_rejects_malformed_reviewed_adoption_metadata(self) -> None:
        cases = (
            {"last_synced_at": "invalid"},
            {"adoption": {"prior_sync_history": [{}], "reviewed_at": "2026-08-25T12:00:00+00:00", "status": "reviewed", "target_commit": "a" * 40, "verification_repository_fingerprint": "b" * 64}},
            {"adoption": {"prior_sync_history": [], "reviewed_at": "invalid", "status": "reviewed", "target_commit": "a" * 40, "verification_repository_fingerprint": "b" * 64}},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                write(root, ".agents/template-sync.json", json.dumps(reviewed_sync_metadata(**overrides)) + "\n")
                result = run([sys.executable, str(TOOL), "--root", str(root), "status"], root, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("malformed adoption", result.stdout)

    def test_status_rejects_malformed_in_progress_adoption(self) -> None:
        invalid_adoptions = (
            {"status": "in_progress", "target_commit": "invalid"},
            {"status": "in_progress", "target_commit": "a" * 40},
            {
                "status": "in_progress",
                "target_commit": "a" * 40,
                "prior_sync_history": [{}],
            },
        )
        for adoption in invalid_adoptions:
            with self.subTest(adoption=adoption), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                metadata = reviewed_sync_metadata(
                    adoption=adoption,
                    last_synced_at=None,
                    last_synced_commit=None,
                )
                write(root, ".agents/template-sync.json", json.dumps(metadata) + "\n")
                result = run(
                    [sys.executable, str(TOOL), "--root", str(root), "status"],
                    root,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("malformed adoption", result.stdout)

    def test_status_rejects_adoption_with_invalid_top_level_sync_fields(self) -> None:
        invalid_fields = (
            {"reference_integrity": {"adopted": "yes"}},
            {"ignored_paths": ["../outside"]},
        )
        for reviewed in (False, True):
            for fields in invalid_fields:
                with self.subTest(reviewed=reviewed, fields=fields), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    fixture(root)
                    if reviewed:
                        metadata = reviewed_sync_metadata(**fields)
                    else:
                        metadata = {
                            "adoption": {
                                "prior_sync_history": [],
                                "status": "in_progress",
                                "target_commit": "a" * 40,
                            },
                            "last_synced_at": None,
                            "last_synced_commit": None,
                            "schema_version": "paper-template-sync-v1",
                            "upstream": {
                                "branch": "main",
                                "remote": "template",
                                "url": "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
                            },
                            **fields,
                        }
                    write(root, ".agents/template-sync.json", json.dumps(metadata) + "\n")
                    result = run(
                        [sys.executable, str(TOOL), "--root", str(root), "status"],
                        root,
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("malformed adoption", result.stdout)

    def test_record_template_origin_uses_github_and_commits_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            git(root, "remote", "add", "origin", "git@github.com:a-green-hand-jack/example-paper.git")
            with fake_gh() as env:
                result = run(
                    [
                        sys.executable,
                        str(TOOL),
                        "--root",
                        str(root),
                        "record-template-origin",
                        "--commit",
                    ],
                    root,
                    check=False,
                    env=env,
                )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("template_origin_committed", result.stdout)
            self.assertEqual(
                git(root, "ls-files", ".agents/template-origin.json").stdout.strip(),
                ".agents/template-origin.json",
            )

    def test_record_template_origin_refuses_adoption_and_marker_conflicts(self) -> None:
        cases = (
            ("in_progress", ".agents/template-origin.json", False),
            ("reviewed", ".agents/init-state.json", False),
            ("reviewed", ".agents/template-origin.json", True),
            ("in_progress", ".agents/init-state.json", True),
        )
        for adoption_kind, marker, dangling in cases:
            with self.subTest(adoption_kind=adoption_kind, marker=marker, dangling=dangling), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                git(root, "remote", "add", "origin", "git@github.com:a-green-hand-jack/example-paper.git")
                metadata = reviewed_sync_metadata() if adoption_kind == "reviewed" else {
                    "adoption": {
                        "prior_sync_history": [],
                        "status": "in_progress",
                        "target_commit": "a" * 40,
                    },
                    "last_synced_at": None,
                    "last_synced_commit": None,
                    "schema_version": "paper-template-sync-v1",
                    "upstream": {
                        "branch": "main",
                        "remote": "template",
                        "url": "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
                    },
                }
                write(root, ".agents/template-sync.json", json.dumps(metadata) + "\n")
                marker_path = root / marker
                if dangling:
                    marker_path.symlink_to("missing-marker.json")
                elif marker == ".agents/template-origin.json":
                    write(
                        root,
                        marker,
                        json.dumps(
                            {
                                "schema_version": "paper-template-origin-v1",
                                "template_repository": "a-green-hand-jack/ccfa-writing-paper-template",
                            }
                        )
                        + "\n",
                    )
                else:
                    write(root, marker, valid_marker(root))
                commit_all(root, "record conflicting lifecycle state")
                with fake_gh() as env:
                    result = run(
                        [
                            sys.executable,
                            str(TOOL),
                            "--root",
                            str(root),
                            "record-template-origin",
                            "--commit",
                        ],
                        root,
                        check=False,
                        env=env,
                    )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("template adoption metadata is", result.stderr)

    def test_record_template_origin_refuses_existing_init_marker_without_adoption(self) -> None:
        for dangling in (False, True):
            with self.subTest(dangling=dangling), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                git(root, "remote", "add", "origin", "git@github.com:a-green-hand-jack/example-paper.git")
                marker = root / ".agents/init-state.json"
                if dangling:
                    marker.symlink_to("missing-init-state.json")
                else:
                    write(root, ".agents/init-state.json", valid_marker(root))
                commit_all(root, "record existing init marker")
                with fake_gh() as env:
                    result = run(
                        [
                            sys.executable,
                            str(TOOL),
                            "--root",
                            str(root),
                            "record-template-origin",
                            "--commit",
                        ],
                        root,
                        check=False,
                        env=env,
                    )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("initialization marker exists", result.stderr)

    def test_record_template_origin_refuses_existing_provenance_without_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            with fake_gh() as env:
                result = run(
                    [
                        sys.executable,
                        str(TOOL),
                        "--root",
                        str(root),
                        "record-template-origin",
                        "--commit",
                    ],
                    root,
                    check=False,
                    env=env,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template provenance path already exists", result.stderr)

    def test_status_and_record_origin_reject_symlinked_agents_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            git(root, "remote", "add", "origin", "git@github.com:a-green-hand-jack/example-paper.git")
            agents = root / ".agents"
            real_agents = root / "agents-real"
            agents.rename(real_agents)
            agents.symlink_to(real_agents.name, target_is_directory=True)
            status = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(status.returncode, 0)
            self.assertIn("repository-local directory", status.stdout)
            with fake_gh() as env:
                recorded = run(
                    [
                        sys.executable,
                        str(TOOL),
                        "--root",
                        str(root),
                        "record-template-origin",
                        "--commit",
                    ],
                    root,
                    check=False,
                    env=env,
                )
            self.assertNotEqual(recorded.returncode, 0)
            self.assertIn("symlinked or non-directory", recorded.stderr)

    def test_initialized_status_rejects_sync_metadata_template_sync_would_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            write(root, ".agents/init-state.json", valid_marker(root))
            sync = json.loads((root / ".agents/template-sync.json").read_text(encoding="utf-8"))
            sync["last_synced_at"] = "invalid"
            write(root, ".agents/template-sync.json", json.dumps(sync) + "\n")
            commit_all(root, "record invalid initialized sync metadata")
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid template-sync metadata", result.stdout)

    def test_clean_rechecks_committed_attestation_against_github(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            with fake_gh("another-owner/another-template") as env:
                result = run(
                    [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                    root,
                    check=False,
                    env=env,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("did not identify", result.stderr)
            self.assertFalse((root / ".agents/init-state.json").exists())

    def test_clean_refuses_external_initialization_marker_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.NamedTemporaryFile(
            mode="w", delete=False
        ) as victim:
            root = Path(directory)
            victim_path = Path(victim.name)
            victim.write("do not overwrite\n")
            victim.flush()
            fixture(root)
            set_template_origin(root)
            marker = root / ".agents/init-state.json"
            marker.symlink_to(victim_path)
            commit_all(root, "record unsafe initialization marker")
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(victim_path.read_text(encoding="utf-8"), "do not overwrite\n")
            victim_path.unlink(missing_ok=True)

    def test_clean_refuses_external_initialization_marker_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.NamedTemporaryFile(
            mode="w", delete=False
        ) as victim:
            root = Path(directory)
            victim_path = Path(victim.name)
            victim.write("do not overwrite\n")
            victim.flush()
            fixture(root)
            set_template_origin(root)
            marker = root / ".agents/init-state.json"
            os.link(victim_path, marker)
            commit_all(root, "record hardlinked initialization marker")
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--commit"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(victim_path.read_text(encoding="utf-8"), "do not overwrite\n")
            victim_path.unlink(missing_ok=True)

    def test_clean_rejects_untracked_template_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            repository = "a-green-hand-jack/example-paper"
            git(root, "remote", "add", "origin", f"git@github.com:{repository}.git")
            write(
                root,
                ".agents/template-origin.json",
                json.dumps(
                    {
                        "downstream_repository": repository,
                        "git_head": git(root, "rev-parse", "HEAD").stdout.strip(),
                        "schema_version": "paper-template-origin-v1",
                        "template_repository": "a-green-hand-jack/ccfa-writing-paper-template",
                        "verification": "github_api_template_repository",
                        "verified_at": "2026-08-09T12:00:00+00:00",
                    }
                )
                + "\n",
            )
            with fake_gh() as env:
                result = run(
                    [sys.executable, str(TOOL), "--root", str(root), "clean"],
                    root,
                    check=False,
                    env=env,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("valid GitHub Template provenance", result.stderr)

    def test_in_progress_adoption_takes_precedence_over_initialized_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            write(root, ".agents/init-state.json", valid_marker(root))
            write(
                root,
                ".agents/template-sync.json",
                json.dumps(
                    {
                        "adoption": {
                            "prior_sync_history": [],
                            "status": "in_progress",
                            "target_commit": "a" * 40,
                        },
                        "last_synced_at": None,
                        "last_synced_commit": None,
                        "schema_version": "paper-template-sync-v1",
                        "upstream": {
                            "branch": "main",
                            "remote": "template",
                            "url": "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git",
                        },
                    }
                )
                + "\n",
            )
            commit_all(root, "record conflicting lifecycle state")
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("adoption must not carry", result.stdout)

    def test_initialized_marker_requires_template_sync_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            write(root, ".agents/init-state.json", valid_marker(root))
            (root / ".agents/template-sync.json").unlink()
            commit_all(root, "record incomplete initialized state")
            result = run(
                [sys.executable, str(TOOL), "--root", str(root), "status"],
                root,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid template-sync metadata", result.stdout)

    def test_same_origin_requires_template_provenance_even_with_override(self) -> None:
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
            self.assertNotEqual(overridden.returncode, 0)
            self.assertIn("provenance", overridden.stderr)
            self.assertFalse((root / ".agents/init-state.json").exists())

    def test_same_origin_commit_downstream_requires_template_provenance(self) -> None:
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("provenance", result.stderr)
            self.assertFalse((root / ".agents/init-state.json").exists())

    def test_initialized_marker_takes_precedence_over_same_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            set_template_origin(root)
            write(root, ".agents/init-state.json", valid_marker(root))
            commit_all(root, "record initialization marker")
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

    def test_invalid_markers_fail_closed_without_template_provenance(self) -> None:
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
                    [sys.executable, str(TOOL), "--root", str(root), "clean", "--downstream"],
                    root,
                    check=False,
                )
                self.assertNotEqual(overridden.returncode, 0)
                self.assertIn("provenance", overridden.stderr)
                self.assertIn("case/arxiv-2505-22954", (root / "AGENTS.md").read_text(encoding="utf-8"))

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
                [sys.executable, str(TOOL), "--root", str(root), "clean", "--downstream"],
                root,
                check=False,
            )
            self.assertNotEqual(overridden.returncode, 0)
            self.assertIn("provenance", overridden.stderr)
            self.assertIn("case/arxiv-2505-22954", (root / "AGENTS.md").read_text(encoding="utf-8"))

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
