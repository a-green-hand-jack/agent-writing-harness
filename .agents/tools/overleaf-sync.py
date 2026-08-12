#!/usr/bin/env python3
"""Synchronize only the canonical paper tree with an Overleaf Git project."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

CONFIG_RELATIVE = Path(".agents/overleaf-sync.json")
DEFAULT_BRANCHES = {"main", "master", "trunk"}
CANONICAL_CASE_PREFIX = "case/"
MARKER = "ccfa-Overleaf-Sync: export"
CREDENTIAL_RE = re.compile(r"://[^/@]+:[^/@]+@", re.I)
REMOTE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class SyncError(RuntimeError):
    pass


def run(
    root: Path,
    *command: str,
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        cwd=root,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise SyncError(
            f"command failed ({result.returncode}): {' '.join(command)}"
            f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def git(
    root: Path,
    *args: str,
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(root, "git", *args, check=check, input_text=input_text)


def read_config(root: Path) -> dict[str, Any] | None:
    path = root / CONFIG_RELATIVE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"invalid Overleaf sync config: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "paper-overleaf-sync-v1":
        raise SyncError("unsupported Overleaf sync configuration")

    prefix = data.get("source_prefix")
    if not isinstance(prefix, str) or not prefix:
        raise SyncError("source_prefix must be a non-empty string")
    prefix_path = PurePosixPath(prefix)
    if prefix_path.is_absolute() or ".." in prefix_path.parts:
        raise SyncError("source_prefix must be a safe relative path")

    remote = data.get("remote")
    if not isinstance(remote, dict):
        raise SyncError("remote configuration must be an object")
    for key in ("name", "url", "branch"):
        if not isinstance(remote.get(key), str) or not remote[key].strip():
            raise SyncError(f"remote.{key} must be a non-empty string")
    if not REMOTE_NAME_RE.fullmatch(remote["name"]):
        raise SyncError(f"invalid Git remote name: {remote['name']}")
    if "/" in remote["branch"] or remote["branch"] in {".", ".."}:
        raise SyncError(f"invalid Git branch name: {remote['branch']}")
    if CREDENTIAL_RE.search(remote["url"]):
        raise SyncError("remote URL must not contain embedded credentials")
    if "token=" in remote["url"].lower() or "password=" in remote["url"].lower():
        raise SyncError("remote URL must not contain credential query parameters")
    return data


def repository_root(root: Path) -> None:
    result = git(root, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0 or Path(result.stdout.strip()).resolve() != root.resolve():
        raise SyncError(f"--root must be the Git repository root: {root}")


def worktree_clean(root: Path) -> bool:
    return not git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout.strip()


def branch(root: Path) -> str:
    value = git(root, "branch", "--show-current").stdout.strip()
    if not value:
        raise SyncError("a named branch is required")
    return value


def ensure_remote(root: Path, config: dict[str, Any]) -> tuple[str, str]:
    remote = config["remote"]
    name = remote["name"]
    expected = remote["url"]
    actual = git(root, "remote", "get-url", name, check=False)
    if actual.returncode != 0:
        raise SyncError(f"missing Git remote: {name}")
    if actual.stdout.strip() != expected:
        raise SyncError(
            f"remote URL mismatch for {name}: expected {expected}, got {actual.stdout.strip()}"
        )
    return name, remote["branch"]


def validate(root: Path, config: dict[str, Any] | None) -> None:
    if config is None:
        print("OK overleaf_sync unconfigured")
        return
    prefix = config["source_prefix"]
    source = root / prefix
    if not source.is_dir() or not (source / "main.tex").is_file():
        raise SyncError(f"canonical paper source is missing: {prefix}/main.tex")
    tracked = [line for line in git(root, "ls-files", prefix).stdout.splitlines() if line]
    if not tracked:
        raise SyncError(f"no tracked files under {prefix}/")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise SyncError(f"Overleaf source cannot contain symlinks: {path.relative_to(root)}")
    remote = config["remote"]
    actual = git(root, "remote", "get-url", remote["name"], check=False)
    if actual.returncode == 0 and actual.stdout.strip() != remote["url"]:
        raise SyncError(
            f"remote URL mismatch for {remote['name']}: "
            f"expected {remote['url']}, got {actual.stdout.strip()}"
        )
    print(f"OK overleaf_sync source={prefix}/ tracked_files={len(tracked)}")


def fetch(root: Path, config: dict[str, Any]) -> str:
    name, remote_branch = ensure_remote(root, config)
    git(root, "fetch", "--prune", name, remote_branch)
    ref = f"refs/remotes/{name}/{remote_branch}"
    result = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
    if result.returncode != 0:
        raise SyncError(f"cannot resolve fetched Overleaf branch: {name}/{remote_branch}")
    return result.stdout.strip()


def split(root: Path, prefix: str) -> str:
    result = git(root, "subtree", "split", f"--prefix={prefix}", "HEAD")
    value = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if len(value) != 40:
        raise SyncError("git subtree split did not produce a commit")
    return value


def tree(root: Path, commit: str) -> str:
    return git(root, "rev-parse", f"{commit}^{{tree}}").stdout.strip()


def is_export_commit(root: Path, commit: str) -> bool:
    return MARKER in git(root, "show", "-s", "--format=%B", commit).stdout


def remote_was_imported(root: Path, remote_commit: str) -> bool:
    needle = f"git-subtree-split: {remote_commit}"
    result = git(root, "log", "HEAD", "--fixed-strings", f"--grep={needle}", "-1", "--format=%H")
    return bool(result.stdout.strip())


def make_export_commit(root: Path, remote_commit: str, split_commit: str) -> str:
    source_commit = git(root, "rev-parse", "HEAD").stdout.strip()
    message = (
        "Sync canonical paper to Overleaf\n\n"
        f"{MARKER}\n"
        f"Source-Commit: {source_commit}\n"
        f"Source-Split: {split_commit}\n"
    )
    result = git(
        root,
        "commit-tree",
        f"{split_commit}^{{tree}}",
        "-p",
        remote_commit,
        "-p",
        split_commit,
        input_text=message,
    )
    return result.stdout.strip()


def is_canonical_branch(name: str) -> bool:
    if name in DEFAULT_BRANCHES:
        return True
    if not name.startswith(CANONICAL_CASE_PREFIX):
        return False
    stem = name[len(CANONICAL_CASE_PREFIX) :]
    return bool(stem) and "/" not in stem and stem not in {".", ".."}


def push(root: Path, config: dict[str, Any], bootstrap: bool) -> None:
    current = branch(root)
    if not is_canonical_branch(current):
        raise SyncError(
            "Overleaf export must run from a canonical branch "
            "(main, master, trunk, or case/<name>)"
        )
    if not worktree_clean(root):
        raise SyncError("Overleaf export requires a clean worktree")
    remote_commit = fetch(root, config)
    split_commit = split(root, config["source_prefix"])
    same_tree = tree(root, remote_commit) == tree(root, split_commit)
    safe_lineage = is_export_commit(root, remote_commit) or remote_was_imported(
        root, remote_commit
    )
    if not (bootstrap or same_tree or safe_lineage):
        raise SyncError(
            "Overleaf contains changes not acknowledged by the canonical branch; "
            "run pull from a sync/overleaf-* branch before exporting"
        )
    if bootstrap and is_export_commit(root, remote_commit):
        raise SyncError("--bootstrap is only for the first canonical export")
    export_commit = make_export_commit(root, remote_commit, split_commit)
    name, remote_branch = ensure_remote(root, config)
    git(root, "push", name, f"{export_commit}:refs/heads/{remote_branch}")
    print(
        f"OK overleaf_push remote={name}/{remote_branch} commit={export_commit} "
        f"source={config['source_prefix']}/"
    )


def pull(root: Path, config: dict[str, Any]) -> None:
    current = branch(root)
    if current in DEFAULT_BRANCHES or not current.startswith("sync/overleaf-"):
        raise SyncError("Overleaf import requires a dedicated sync/overleaf-* branch")
    if not worktree_clean(root):
        raise SyncError("Overleaf import requires a clean worktree")
    remote_commit = fetch(root, config)
    name, remote_branch = ensure_remote(root, config)
    split_commit = split(root, config["source_prefix"])
    prefix = config["source_prefix"].rstrip("/") + "/"
    patch = git(
        root,
        "diff",
        "--binary",
        f"--src-prefix=a/{prefix}",
        f"--dst-prefix=b/{prefix}",
        split_commit,
        remote_commit,
    ).stdout
    if patch:
        git(root, "apply", "--index", "--whitespace=nowarn", input_text=patch)
    message = (
        "Import reviewed Overleaf working copy\n\n"
        "ccfa-Overleaf-Sync: import\n"
        f"git-subtree-dir: {config['source_prefix']}\n"
        f"git-subtree-split: {remote_commit}\n"
    )
    git(root, "commit", "--allow-empty", "-F", "-", input_text=message)
    print(
        f"OK overleaf_pull remote={name}/{remote_branch} commit={remote_commit} "
        f"target={config['source_prefix']}/"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    subcommands = result.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate")
    subcommands.add_parser("fetch")
    push_parser = subcommands.add_parser("push")
    push_parser.add_argument("--bootstrap", action="store_true")
    subcommands.add_parser("pull")
    return result


def main() -> int:
    args = parser().parse_args()
    root = args.root.resolve()
    try:
        repository_root(root)
        config = read_config(root)
        validate(root, config)
        if config is None and args.command != "validate":
            raise SyncError(
                "Overleaf sync is not configured; add .agents/overleaf-sync.json with "
                "source_prefix and remote name/url/branch"
            )
        if args.command == "fetch":
            assert config is not None
            print(f"OK overleaf_fetch commit={fetch(root, config)}")
        elif args.command == "push":
            assert config is not None
            push(root, config, args.bootstrap)
        elif args.command == "pull":
            assert config is not None
            pull(root, config)
    except SyncError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
