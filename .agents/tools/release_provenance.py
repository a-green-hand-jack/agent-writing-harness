#!/usr/bin/env python3
"""Squash-stable release provenance for the legacy harness backend.

The authoritative source identity is a synthetic Git tree built from exactly the
`paper/` paths exported by the release harness. It reflects working-tree content,
ignores unrelated repository changes, and remains identical across squash/rebase.
The current commit is retained only as an audit hint.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from types import ModuleType

HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


class ProvenanceError(RuntimeError):
    pass


def git(root: Path, *args: str, input_text: str | None = None) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        message = process.stderr.strip() or process.stdout.strip() or "git command failed"
        raise ProvenanceError(message)
    return process.stdout.strip()


def blob_sha(root: Path, path: Path) -> str:
    # `mktree` validates referenced objects. `-w` stores a working-tree blob so
    # uncommitted authored paper changes can participate in the synthetic tree.
    process = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=root,
        input=path.read_bytes(),
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ProvenanceError(process.stderr.decode(errors="replace").strip())
    return process.stdout.decode().strip()


def tree_sha(root: Path, path: Path) -> str:
    entries: list[str] = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        if child.is_symlink():
            raise ProvenanceError(f"paper source contains symlink: {child.relative_to(root)}")
        if child.is_dir():
            sha = tree_sha(root, child)
            entries.append(f"040000 tree {sha}\t{child.name}\n")
        elif child.is_file():
            sha = blob_sha(root, child)
            executable = child.stat().st_mode & 0o111
            mode = "100755" if executable else "100644"
            entries.append(f"{mode} blob {sha}\t{child.name}\n")
    return git(root, "mktree", input_text="".join(entries))


def paper_source_tree(root: Path, release_items: list[str] | tuple[str, ...]) -> str:
    paper = root / "paper"
    if not paper.is_dir():
        raise ProvenanceError("missing paper/ source directory")

    entries: list[str] = []
    for name in release_items:
        path = paper / name
        if not path.exists():
            continue
        if path.is_symlink():
            raise ProvenanceError(f"paper source contains symlink: paper/{name}")
        if path.is_dir():
            sha = tree_sha(root, path)
            entries.append(f"040000 tree {sha}\t{name}\n")
        else:
            sha = blob_sha(root, path)
            executable = path.stat().st_mode & 0o111
            mode = "100755" if executable else "100644"
            entries.append(f"{mode} blob {sha}\t{name}\n")
    return git(root, "mktree", input_text="".join(sorted(entries)))


def install(ph: ModuleType) -> None:
    """Install paper-tree provenance into `paper_harness_checks`."""

    def current_tree() -> str:
        return paper_source_tree(ph.ROOT, ph.RELEASE_ITEMS)

    def source_revision() -> dict:
        try:
            tree = current_tree()
        except (OSError, ProvenanceError) as exc:
            ph.error(f"cannot build paper source tree: {exc}")
            return {}
        commit = ph.git_value("rev-parse", "--verify", "HEAD")
        revision = {
            "scope": "paper",
            "treeish": "paper/",
            "tree": tree,
        }
        if commit and HEX40_RE.fullmatch(commit.lower()):
            revision["commit"] = commit.lower()
        return revision

    def validate_revision(manifest: dict, *, label: str) -> int:
        revision = manifest.get("source_revision", {})
        if not ph.meaningful(revision):
            return 0
        if not isinstance(revision, dict):
            return ph.error("release manifest source_revision must be a mapping")

        scope = str(revision.get("scope", "")).strip().lower()
        recorded_tree = str(revision.get("tree", "")).strip().lower()
        if scope != "paper":
            return ph.error(
                "release manifest uses legacy commit-bound provenance; rerun the release exporter"
            )
        if not HEX40_RE.fullmatch(recorded_tree):
            return ph.error("release manifest source_revision has invalid paper tree")

        try:
            actual_tree = current_tree()
        except (OSError, ProvenanceError) as exc:
            return ph.error(f"cannot build current paper source tree: {exc}")
        if recorded_tree != actual_tree:
            return ph.error(
                f"release manifest paper source tree is stale: {recorded_tree[:12]} != {actual_tree[:12]}"
            )

        commit = str(revision.get("commit", "")).strip().lower()
        if commit and not HEX40_RE.fullmatch(commit):
            return ph.error("release manifest source_revision has invalid audit commit")
        return 0

    def check_source_revision_matches_release_source(manifest: dict) -> int:
        return validate_revision(manifest, label="export")

    def check_source_revision_freshness(manifest: dict) -> int:
        return validate_revision(manifest, label="freshness")

    ph.source_revision = source_revision
    ph.check_source_revision_matches_release_source = check_source_revision_matches_release_source
    ph.check_source_revision_freshness = check_source_revision_freshness
