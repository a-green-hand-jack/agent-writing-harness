#!/usr/bin/env python3
"""Plan and apply safe upstream template updates in a downstream paper repository.

The downstream repository may have an unrelated Git history. Synchronization is
therefore path-level and three-way: the last recorded upstream template commit,
the requested upstream target, and the current downstream working tree.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from _template_inheritance import (
    POLICY_RELATIVE,
    combine_inheritance_policies,
    load_inheritance_policy,
    parse_inheritance_policy,
)

CONFIG_RELATIVE = Path(".agents/template-sync.json")
RUNTIME_RELATIVE = Path(".agents/runtime/template-sync")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DEFAULT_BRANCHES = {"main", "master", "trunk"}
PLAN_SCHEMA = "paper-template-sync-plan-v2"
APPLICATION_SCHEMA = "paper-template-sync-application-v1"
VERIFICATION_SCHEMA = "paper-template-sync-verification-v1"
REGULAR_FILE_MODES = {"100644", "100755"}


class SyncError(RuntimeError):
    pass


def inheritance_policy(root: Path) -> dict[str, Any]:
    try:
        return load_inheritance_policy(root)
    except ValueError as exc:
        raise SyncError(str(exc)) from exc


def ensure_directory_path(root: Path, relative: Path, *, create: bool) -> Path:
    candidate = PurePosixPath(relative.as_posix())
    if candidate.is_absolute() or ".." in candidate.parts:
        raise SyncError(f"unsafe template sync directory path: {relative.as_posix()}")
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise SyncError(
                f"refusing to use symlinked template sync directory: {current.relative_to(root)}"
            )
        if current.exists() and not current.is_dir():
            raise SyncError(
                f"template sync directory path is not a directory: {current.relative_to(root)}"
            )
        if create and not current.exists():
            current.mkdir()
    return current


def ensure_regular_file(path: Path, label: str, *, required: bool = False) -> None:
    if path.is_symlink():
        raise SyncError(f"refusing to use symlinked template sync {label}: {path}")
    if path.exists() and not path.is_file():
        raise SyncError(f"template sync {label} is not a regular file: {path}")
    if required and not path.is_file():
        raise SyncError(f"missing template sync {label}: {path}")


def runtime_directory(root: Path, *, create: bool) -> Path:
    return ensure_directory_path(root, RUNTIME_RELATIVE, create=create)


def repository_file_path(
    root: Path,
    value: Path | None,
    default_name: str,
    *,
    create_parent: bool,
    required: bool,
) -> Path:
    if value is None:
        path = runtime_directory(root, create=create_parent) / default_name
    else:
        if value.is_absolute():
            try:
                relative = value.relative_to(root)
            except ValueError as exc:
                raise SyncError("template sync runtime files must remain inside the repository") from exc
        else:
            relative = value
        candidate = PurePosixPath(relative.as_posix())
        if candidate.is_absolute() or ".." in candidate.parts or not candidate.name:
            raise SyncError(f"unsafe template sync file path: {value}")
        parent_relative = Path(*candidate.parts[:-1]) if len(candidate.parts) > 1 else Path(".")
        parent = ensure_directory_path(root, parent_relative, create=create_parent)
        path = parent / candidate.name
    ensure_regular_file(path, default_name, required=required)
    return path


def run(
    command: list[str],
    *,
    cwd: Path,
    capture: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=False,
    )
    if check and result.returncode != 0:
        detail = ""
        if capture:
            detail = f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        raise SyncError(f"command failed ({result.returncode}): {' '.join(command)}{detail}")
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=root, check=check)


def ensure_git_repository(root: Path) -> None:
    result = git(root, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        raise SyncError(f"not a Git repository: {root}")
    actual = Path(result.stdout.strip()).resolve()
    if actual != root.resolve():
        raise SyncError(f"--root must be repository root: expected {actual}, got {root.resolve()}")


def read_config(root: Path) -> dict[str, Any]:
    path = ensure_directory_path(root, CONFIG_RELATIVE.parent, create=False) / CONFIG_RELATIVE.name
    ensure_regular_file(path, "metadata", required=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SyncError(f"invalid template sync metadata: {exc}") from exc
    if not isinstance(data, dict):
        raise SyncError("template sync metadata must be a JSON object")
    return data


def validate_config_data(data: dict[str, Any]) -> None:
    if data.get("schema_version") != "paper-template-sync-v1":
        raise SyncError("unsupported template sync schema_version")
    upstream = data.get("upstream")
    if not isinstance(upstream, dict):
        raise SyncError("template sync metadata requires upstream object")
    for key in ("url", "remote", "branch"):
        value = upstream.get(key)
        if not isinstance(value, str) or not value.strip():
            raise SyncError(f"template sync upstream.{key} must be a non-empty string")
    baseline = data.get("last_synced_commit")
    if baseline is not None and (
        not isinstance(baseline, str) or len(baseline) != 40 or any(ch not in "0123456789abcdef" for ch in baseline)
    ):
        raise SyncError("last_synced_commit must be null or a 40-character lowercase Git SHA")
    synced_at = data.get("last_synced_at")
    if synced_at is not None:
        require_timestamp(synced_at, "last_synced_at")
    if (baseline is None) != (synced_at is None):
        raise SyncError("last_synced_commit and last_synced_at must be both null or both recorded")
    note = data.get("last_sync_note")
    if note is not None and not isinstance(note, str):
        raise SyncError("last_sync_note must be null or a string")
    reference_integrity = data.get("reference_integrity")
    if reference_integrity is not None and (
        not isinstance(reference_integrity, dict)
        or not isinstance(reference_integrity.get("adopted"), bool)
    ):
        raise SyncError("template sync reference_integrity.adopted must be boolean")
    adoption = data.get("adoption")
    if adoption is not None:
        if not isinstance(adoption, dict) or adoption.get("status") not in {
            "in_progress",
            "reviewed",
        }:
            raise SyncError("template sync adoption.status must be in_progress or reviewed")
        if adoption["status"] == "reviewed":
            validate_reviewed_adoption_shape(adoption)
            if synced_at is None:
                raise SyncError("reviewed adoption requires a recorded last_synced_at")
        else:
            validate_in_progress_adoption_shape(data, adoption)
    for key in ("always_manual", "ignored_paths"):
        values = data.get(key, [])
        if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
            raise SyncError(f"{key} must be a list of non-empty path strings")
        for value in values:
            path = PurePosixPath(value)
            if path.is_absolute() or ".." in path.parts:
                raise SyncError(f"unsafe path in {key}: {value}")


def is_lower_sha(value: Any, length: int) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def require_timestamp(value: Any, label: str) -> None:
    if not isinstance(value, str):
        raise SyncError(f"{label} must be a timezone-aware ISO timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise SyncError(f"{label} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SyncError(f"{label} must be a timezone-aware ISO timestamp")


def validate_prior_sync_history(history: Any, *, label: str = "reviewed adoption") -> None:
    if not isinstance(history, list):
        raise SyncError(f"{label} prior_sync_history must be a list")
    required = {
        "adoption",
        "last_synced_commit",
        "last_synced_at",
        "last_sync_note",
        "reference_integrity",
        "upstream",
    }
    for index, entry in enumerate(history):
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise SyncError(f"{label} history entry {index} is incomplete")
        commit = entry["last_synced_commit"]
        if commit is not None and not is_lower_sha(commit, 40):
            raise SyncError(f"{label} history entry {index} has an invalid baseline")
        synced_at = entry["last_synced_at"]
        if synced_at is not None:
            require_timestamp(synced_at, f"{label} history entry {index} last_synced_at")
        if (commit is None) != (synced_at is None):
            raise SyncError(f"{label} history entry {index} has an inconsistent baseline pair")
        if entry["last_sync_note"] is not None and not isinstance(entry["last_sync_note"], str):
            raise SyncError(f"{label} history entry {index} has an invalid note")
        if entry["adoption"] is not None and not isinstance(entry["adoption"], dict):
            raise SyncError(f"{label} history entry {index} has invalid adoption metadata")
        integrity = entry["reference_integrity"]
        if integrity is not None and (
            not isinstance(integrity, dict) or not isinstance(integrity.get("adopted"), bool)
        ):
            raise SyncError(f"{label} history entry {index} has invalid reference integrity")
        upstream = entry["upstream"]
        if not isinstance(upstream, dict) or not all(
            isinstance(upstream.get(key), str) and upstream[key].strip()
            for key in ("url", "remote", "branch")
        ):
            raise SyncError(f"{label} history entry {index} has invalid upstream metadata")


def validate_reviewed_adoption_shape(adoption: dict[str, Any]) -> None:
    if not is_lower_sha(adoption.get("target_commit"), 40):
        raise SyncError("reviewed adoption target_commit must be a lowercase 40-character SHA")
    require_timestamp(adoption.get("reviewed_at"), "reviewed adoption reviewed_at")
    if not is_lower_sha(adoption.get("verification_repository_fingerprint"), 64):
        raise SyncError(
            "reviewed adoption verification_repository_fingerprint must be a lowercase SHA-256"
        )
    if "prior_sync_history" not in adoption:
        raise SyncError("reviewed adoption prior_sync_history is required")
    validate_prior_sync_history(adoption["prior_sync_history"])


def validate_in_progress_adoption_shape(data: dict[str, Any], adoption: dict[str, Any]) -> None:
    if not is_lower_sha(adoption.get("target_commit"), 40):
        raise SyncError("in-progress adoption target_commit must be a lowercase 40-character SHA")
    if "prior_sync_history" not in adoption:
        raise SyncError("in-progress adoption prior_sync_history is required")
    validate_prior_sync_history(
        adoption["prior_sync_history"], label="in-progress adoption"
    )
    if data.get("last_synced_commit") is not None or data.get("last_synced_at") is not None:
        raise SyncError("in-progress adoption must not have a recorded template baseline")
    if "reviewed_at" in adoption or "verification_repository_fingerprint" in adoption:
        raise SyncError("in-progress adoption must not contain reviewed metadata")


def validate_repository(root: Path) -> None:
    inheritance_policy(root)
    data = read_config(root)
    validate_config_data(data)
    validate_reviewed_adoption_provenance(root, data)
    skill_relative = Path(".agents/skills/template-sync/SKILL.md")
    skill = ensure_directory_path(root, skill_relative.parent, create=False) / skill_relative.name
    ensure_regular_file(skill, "skill", required=True)
    text = skill.read_text(encoding="utf-8")
    for heading in ("## Trigger", "## Minimum context", "## Procedure", "## Safety boundary"):
        if heading not in text:
            raise SyncError(f"template sync skill missing heading: {heading}")
    print("OK template_sync configuration")


def validate_lifecycle_markers(root: Path, config: dict[str, Any]) -> None:
    adoption = config.get("adoption")
    if not isinstance(adoption, dict) or adoption.get("status") not in {
        "in_progress",
        "reviewed",
    }:
        return
    for relative in (Path(".agents/template-origin.json"), Path(".agents/init-state.json")):
        path = root / relative
        if path.is_symlink() or path.exists():
            raise SyncError(
                "template adoption must not carry GitHub Template provenance or an "
                f"initialization marker: {relative.as_posix()}"
            )


def require_operation_lifecycle(root: Path, config: dict[str, Any], command: str) -> None:
    adoption = config.get("adoption")
    if isinstance(adoption, dict) and adoption.get("status") in {"in_progress", "reviewed"}:
        return
    paper_init = root / ".agents/tools/paper-init.py"
    if paper_init.is_symlink() or not paper_init.is_file():
        raise SyncError(
            f"refusing template sync {command} without reviewed adoption or template-created provenance"
        )
    result = subprocess.run(
        [sys.executable, str(paper_init), "--root", str(root), "status"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not any(
        line in result.stdout
        for line in ("OK paper_init initialized",)
    ):
        detail = result.stdout.strip() or result.stderr.strip()
        raise SyncError(
            f"refusing template sync {command} without valid template-created provenance: {detail}"
        )


def normalize_path(path: str) -> str:
    return PurePosixPath(path).as_posix()


def path_matches(path: str, patterns: tuple[str, ...] | list[str]) -> bool:
    normalized = normalize_path(path)
    for pattern in patterns:
        prefix = pattern.endswith("/")
        candidate = normalize_path(pattern.rstrip("/"))
        if prefix:
            if normalized == candidate or normalized.startswith(candidate + "/"):
                return True
        elif normalized == candidate:
            return True
    return False


def has_unsafe_parent(root: Path, path: str) -> bool:
    current = root
    for part in PurePosixPath(path).parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return True
    return False


def object_exists(root: Path, ref: str) -> bool:
    return git(root, "cat-file", "-e", f"{ref}^{{object}}", check=False).returncode == 0


def resolve_commit(root: Path, ref: str) -> str:
    result = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
    if result.returncode != 0:
        raise SyncError(f"cannot resolve upstream commit: {ref}; run template-sync.py fetch first")
    return result.stdout.strip()


def current_branch(root: Path) -> str:
    result = git(root, "branch", "--show-current")
    branch = result.stdout.strip()
    if not branch:
        raise SyncError("template synchronization requires a named branch, not detached HEAD")
    return branch


def head_commit(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").stdout.strip()


def head_tree(root: Path) -> str:
    return git(root, "rev-parse", "HEAD^{tree}").stdout.strip()


def repository_id(root: Path) -> str:
    git_dir = git(root, "rev-parse", "--absolute-git-dir").stdout.strip()
    payload = f"paper-template-sync-repository-v1\0{root.resolve()}\0{Path(git_dir).resolve()}"
    return hashlib.sha256(payload.encode("utf-8", errors="surrogateescape")).hexdigest()


def worktree_changes(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SyncError("cannot inspect downstream worktree")
    changes: list[str] = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        if len(record) < 4:
            continue
        path = record[3:].decode("utf-8", errors="surrogateescape")
        normalized = normalize_path(path)
        if path_matches(normalized, [RUNTIME_RELATIVE.as_posix() + "/"]):
            continue
        changes.append(normalized)
    return changes


def worktree_clean(root: Path) -> bool:
    return not worktree_changes(root)


def repository_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(b"paper-template-sync-worktree-v1\0")
    digest.update(head_commit(root).encode("ascii"))
    digest.update(b"\0")
    diff = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff", "HEAD", "--"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if diff.returncode != 0:
        raise SyncError("cannot fingerprint tracked downstream changes")
    digest.update(diff.stdout)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if untracked.returncode != 0:
        raise SyncError("cannot fingerprint untracked downstream files")
    paths = sorted(
        normalize_path(raw.decode("utf-8", errors="surrogateescape"))
        for raw in untracked.stdout.split(b"\0")
        if raw
    )
    for relative in paths:
        if path_matches(relative, [RUNTIME_RELATIVE.as_posix() + "/"]):
            continue
        candidate = root / relative
        digest.update(b"\0path\0")
        digest.update(relative.encode("utf-8", errors="surrogateescape"))
        if has_unsafe_parent(root, relative):
            digest.update(b"\0unsafe-parent\0")
        elif candidate.is_symlink():
            digest.update(b"\0symlink\0")
            digest.update(os.fsencode(os.readlink(candidate)))
        elif candidate.is_file():
            digest.update(b"\0file\0")
            digest.update(str(candidate.stat().st_mode & 0o777).encode("ascii"))
            with candidate.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
        else:
            digest.update(b"\0other\0")
    return digest.hexdigest()


def json_digest(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def plan_digest(plan: dict[str, Any]) -> str:
    bound = dict(plan)
    bound.pop("created_at", None)
    bound.pop("plan_digest", None)
    # The resolved commit, not the movable ref spelling, is the security boundary.
    bound.pop("target_ref", None)
    return json_digest(bound)


def ensure_safe_apply_context(root: Path) -> None:
    branch = current_branch(root)
    if branch in DEFAULT_BRANCHES:
        raise SyncError(f"refusing template sync apply on default branch: {branch}")
    if not worktree_clean(root):
        raise SyncError("refusing template sync apply with a dirty worktree")


def ensure_remote(root: Path, config: dict[str, Any]) -> tuple[str, str, str]:
    upstream = config["upstream"]
    remote = upstream["remote"]
    url = upstream["url"]
    branch = upstream["branch"]
    existing = git(root, "remote", "get-url", remote, check=False)
    if existing.returncode != 0:
        git(root, "remote", "add", remote, url)
    elif existing.stdout.strip() != url:
        raise SyncError(
            f"remote {remote} points to {existing.stdout.strip()}, expected {url}; review before changing it"
        )
    return remote, url, branch


def configured_remote(root: Path, config: dict[str, Any]) -> tuple[str, str, str]:
    upstream = config["upstream"]
    remote = upstream["remote"]
    url = upstream["url"]
    branch = upstream["branch"]
    existing = git(root, "remote", "get-url", remote, check=False)
    if existing.returncode != 0:
        raise SyncError(
            f"configured upstream remote {remote} is missing; run template sync fetch first"
        )
    if existing.stdout.strip() != url:
        raise SyncError(
            f"remote {remote} points to {existing.stdout.strip()}, expected {url}; review before changing it"
        )
    return remote, url, branch


def require_configured_upstream_target(
    root: Path,
    config: dict[str, Any],
    target: str,
) -> None:
    remote, _, branch = configured_remote(root, config)
    branch_ref = f"refs/remotes/{remote}/{branch}"
    branch_tip = resolve_commit(root, branch_ref)
    result = git(root, "merge-base", "--is-ancestor", target, branch_tip, check=False)
    if result.returncode != 0:
        raise SyncError(
            f"target commit {target} is not reachable from configured upstream {remote}/{branch}"
        )


def validate_reviewed_adoption_provenance(root: Path, config: dict[str, Any]) -> None:
    adoption = config.get("adoption")
    if not isinstance(adoption, dict) or adoption.get("status") != "reviewed":
        baseline = config.get("last_synced_commit")
        if baseline is not None:
            require_configured_upstream_target(root, config, str(baseline))
        return
    baseline = config.get("last_synced_commit")
    if not is_lower_sha(baseline, 40):
        raise SyncError("reviewed adoption requires a recorded template baseline")
    target = str(adoption["target_commit"])
    require_configured_upstream_target(root, config, target)
    require_configured_upstream_target(root, config, str(baseline))
    relationship = git(root, "merge-base", "--is-ancestor", target, str(baseline), check=False)
    if relationship.returncode != 0:
        raise SyncError(
            "reviewed adoption target must be equal to or an ancestor of the current template baseline"
        )


def refuse_in_progress_adoption(config: dict[str, Any], command: str) -> None:
    adoption = config.get("adoption")
    if isinstance(adoption, dict) and adoption.get("status") == "in_progress":
        raise SyncError(
            f"refusing template sync {command} while template adoption is in_progress; "
            "finish reviewed adoption first"
        )


def fetch_upstream(root: Path, config: dict[str, Any]) -> str:
    remote, _, branch = ensure_remote(root, config)
    git(root, "fetch", "--prune", remote, branch)
    commit = resolve_commit(root, f"{remote}/{branch}")
    validate_reviewed_adoption_provenance(root, config)
    print(f"OK template_sync fetched {remote}/{branch} -> {commit}")
    return commit


def blob_at(root: Path, ref: str, path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def local_entry(root: Path, path: str) -> tuple[str, bytes | None, str | None]:
    target = root / path
    if has_unsafe_parent(root, path) or target.is_symlink():
        return "other", None, None
    if target.is_file():
        mode = "100755" if target.stat().st_mode & 0o111 else "100644"
        return "file", target.read_bytes(), mode
    if target.exists():
        return "other", None, None
    return "missing", None, None


def entry_at(root: Path, ref: str, path: str) -> tuple[str, bytes | None, str | None]:
    if ref == EMPTY_TREE:
        return "missing", None, None
    result = subprocess.run(
        ["git", "ls-tree", "-z", ref, "--", path],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return "missing", None, None
    record = result.stdout.split(b"\0", 1)[0]
    try:
        metadata, _ = record.split(b"\t", 1)
        mode, kind, _ = metadata.decode("ascii").split()
    except (ValueError, UnicodeDecodeError) as exc:
        raise SyncError(f"cannot parse template entry metadata for {path}") from exc
    if kind != "blob" or mode not in REGULAR_FILE_MODES:
        return "other", None, mode
    return "file", blob_at(root, ref, path), mode


def target_inheritance_policy(root: Path, target: str) -> dict[str, Any]:
    kind, payload, _ = entry_at(root, target, POLICY_RELATIVE.as_posix())
    if kind != "file" or payload is None:
        raise SyncError(
            f"template target requires a regular {POLICY_RELATIVE.as_posix()}"
        )
    try:
        target_policy = parse_inheritance_policy(payload)
    except ValueError as exc:
        raise SyncError(f"invalid target template inheritance policy: {exc}") from exc
    return combine_inheritance_policies(inheritance_policy(root), target_policy)


def changed_paths(root: Path, baseline: str, target: str) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "diff", "--no-renames", "--name-status", "-z", baseline, target],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SyncError(
            f"cannot compare template baseline {baseline} to target {target}: {result.stderr.decode(errors='replace')}"
        )
    tokens = result.stdout.split(b"\0")
    entries: list[tuple[str, str]] = []
    index = 0
    while index < len(tokens) and tokens[index]:
        status = tokens[index].decode("utf-8", errors="replace")
        if index + 1 >= len(tokens):
            raise SyncError("unexpected git diff output while planning template sync")
        path = tokens[index + 1].decode("utf-8", errors="surrogateescape")
        normalized = normalize_path(path)
        candidate = PurePosixPath(normalized)
        if candidate.is_absolute() or ".." in candidate.parts or normalized == ".git" or normalized.startswith(".git/"):
            raise SyncError(f"unsafe path reported by upstream template: {path}")
        entries.append((status[0], normalized))
        index += 2
    return entries


def classify_path(
    *,
    path: str,
    upstream_status: str,
    baseline_blob: bytes | None,
    baseline_mode: str | None,
    target_blob: bytes | None,
    target_mode: str | None,
    downstream_blob: bytes | None,
    downstream_mode: str | None,
    downstream_kind: str,
    manual_paths: list[str],
    ignored_paths: list[str],
) -> tuple[str, str]:
    if downstream_kind == "other":
        return "conflict", "downstream path is a symlink or non-file entry"
    if downstream_blob == target_blob and downstream_mode == target_mode:
        return "already", "downstream already matches upstream target"
    if path_matches(path, manual_paths):
        return "manual", "protected Human-authored or project-specific surface"
    if path_matches(path, ignored_paths):
        return "ignored", "downstream-local metadata or generated runtime"
    if downstream_blob == baseline_blob and downstream_mode == baseline_mode:
        return "safe", "downstream did not modify the upstream baseline"
    if baseline_blob is None and downstream_blob is None and target_blob is not None:
        return "safe", "new upstream file does not exist downstream"
    return "conflict", "upstream and downstream both changed or path identities differ"


def plan_sync(
    root: Path,
    config: dict[str, Any],
    *,
    target_ref: str | None,
    bootstrap: bool,
    fetch: bool,
) -> dict[str, Any]:
    if fetch:
        fetch_upstream(root, config)
    upstream = config["upstream"]
    target_name = target_ref or f"{upstream['remote']}/{upstream['branch']}"
    target = resolve_commit(root, target_name)
    require_configured_upstream_target(root, config, target)
    policy = target_inheritance_policy(root, target)
    configured_baseline = config.get("last_synced_commit")
    if configured_baseline is None:
        if not bootstrap:
            raise SyncError(
                "no last_synced_commit is recorded; use plan --bootstrap for the first reviewed synchronization"
            )
        baseline = EMPTY_TREE
    else:
        baseline = configured_baseline
        if not object_exists(root, baseline):
            raise SyncError(
                f"recorded baseline commit is not available locally: {baseline}; fetch upstream history first"
            )

    manual_paths = list(policy["sync"]["manual_paths"]) + list(
        config.get("always_manual", [])
    )
    ignored_paths = list(policy["sync"]["ignored_paths"]) + list(
        config.get("ignored_paths", [])
    )
    items: list[dict[str, Any]] = []
    for upstream_status, path in changed_paths(root, baseline, target):
        baseline_kind, baseline_value, baseline_mode = entry_at(root, baseline, path)
        target_kind, target_value, target_mode = entry_at(root, target, path)
        if baseline_kind == "other" or target_kind == "other":
            raise SyncError(
                f"template sync refuses non-regular upstream entry: {path}"
            )
        downstream_kind, downstream_value, downstream_mode = local_entry(root, path)
        category, reason = classify_path(
            path=path,
            upstream_status=upstream_status,
            baseline_blob=baseline_value,
            baseline_mode=baseline_mode,
            target_blob=target_value,
            target_mode=target_mode,
            downstream_blob=downstream_value,
            downstream_mode=downstream_mode,
            downstream_kind=downstream_kind,
            manual_paths=manual_paths,
            ignored_paths=ignored_paths,
        )
        action = "delete" if target_value is None else ("add" if baseline_value is None else "update")
        items.append(
            {
                "path": path,
                "upstream_status": upstream_status,
                "action": action,
                "baseline_mode": baseline_mode,
                "target_mode": target_mode,
                "category": category,
                "reason": reason,
            }
        )

    counts = {category: 0 for category in ("safe", "already", "manual", "conflict", "ignored")}
    for item in items:
        counts[item["category"]] += 1
    return {
        "schema_version": PLAN_SCHEMA,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "bootstrap": baseline == EMPTY_TREE,
        "baseline": baseline,
        "target_ref": target_name,
        "target_commit": target,
        "repository_id": repository_id(root),
        "downstream_head": head_commit(root),
        "downstream_tree": head_tree(root),
        "downstream_branch": current_branch(root),
        "worktree_clean": worktree_clean(root),
        "counts": counts,
        "items": items,
    }


def render_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Template Sync Plan",
        "",
        f"- Baseline: `{plan['baseline']}`",
        f"- Target: `{plan['target_commit']}` via `{plan['target_ref']}`",
        f"- Downstream head: `{plan['downstream_head']}`",
        f"- Downstream branch: `{plan['downstream_branch']}`",
        f"- Bootstrap: `{str(plan['bootstrap']).lower()}`",
        "",
        "## Summary",
        "",
    ]
    for category in ("safe", "already", "manual", "conflict", "ignored"):
        lines.append(f"- {category}: {plan['counts'][category]}")
    lines.extend(["", "## Paths", "", "| Category | Action | Path | Reason |", "|---|---|---|---|"])
    for item in plan["items"]:
        reason = str(item["reason"]).replace("|", "\\|")
        lines.append(
            f"| {item['category']} | {item['action']} | `{item['path']}` | {reason} |"
        )
    lines.extend(
        [
            "",
            "Safe paths may be applied mechanically. Manual and conflict paths require Agent review; protected paper meaning must remain downstream-owned.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_plan(root: Path, plan: dict[str, Any]) -> Path:
    plan["plan_digest"] = plan_digest(plan)
    runtime = runtime_directory(root, create=True)
    path = runtime / "plan.json"
    markdown = runtime / "plan.md"
    ensure_regular_file(path, "plan JSON")
    ensure_regular_file(markdown, "plan Markdown")
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown.write_text(render_plan(plan), encoding="utf-8")
    return path


def read_plan(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"cannot read template sync plan: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != PLAN_SCHEMA:
        raise SyncError("unsupported template sync plan schema")
    if data.get("plan_digest") != plan_digest(data):
        raise SyncError("template sync plan digest is invalid; regenerate the plan")
    return data


def require_plan_context(root: Path, config: dict[str, Any], plan: dict[str, Any]) -> None:
    if plan.get("repository_id") != repository_id(root):
        raise SyncError("template sync plan belongs to a different repository")
    if plan.get("downstream_branch") != current_branch(root):
        raise SyncError("downstream branch changed after plan creation; regenerate the template sync plan")
    if plan.get("downstream_head") != head_commit(root):
        raise SyncError("downstream HEAD moved after plan creation; regenerate the template sync plan")
    if plan.get("downstream_tree") != head_tree(root):
        raise SyncError("downstream HEAD tree changed after plan creation; regenerate the template sync plan")
    expected_baseline = config.get("last_synced_commit") or EMPTY_TREE
    if plan.get("baseline") != expected_baseline:
        raise SyncError("recorded template baseline changed after plan creation; regenerate the plan")
    target = plan.get("target_commit")
    if not isinstance(target, str) or resolve_commit(root, target) != target:
        raise SyncError("planned upstream target is unavailable or invalid")
    require_configured_upstream_target(root, config, target)


def require_untampered_plan(root: Path, config: dict[str, Any], plan: dict[str, Any]) -> None:
    require_plan_context(root, config, plan)
    expected = plan_sync(
        root,
        config,
        target_ref=str(plan["target_commit"]),
        bootstrap=bool(plan.get("bootstrap")),
        fetch=False,
    )
    if plan_digest(expected) != plan.get("plan_digest"):
        raise SyncError("template sync plan does not match current policy and classification; regenerate it")


def require_original_plan_policy(root: Path, config: dict[str, Any], plan: dict[str, Any]) -> None:
    baseline = str(plan["baseline"])
    target = str(plan["target_commit"])
    policy = target_inheritance_policy(root, target)
    downstream_head = str(plan["downstream_head"])
    manual_paths = list(policy["sync"]["manual_paths"]) + list(
        config.get("always_manual", [])
    )
    ignored_paths = list(policy["sync"]["ignored_paths"]) + list(
        config.get("ignored_paths", [])
    )
    expected_items: list[dict[str, Any]] = []
    for upstream_status, path in changed_paths(root, baseline, target):
        baseline_kind, baseline_value, baseline_mode = entry_at(root, baseline, path)
        target_kind, target_value, target_mode = entry_at(root, target, path)
        if baseline_kind == "other" or target_kind == "other":
            raise SyncError(
                f"template sync refuses non-regular upstream entry: {path}"
            )
        downstream_kind, downstream_value, downstream_mode = entry_at(
            root, downstream_head, path
        )
        category, reason = classify_path(
            path=path,
            upstream_status=upstream_status,
            baseline_blob=baseline_value,
            baseline_mode=baseline_mode,
            target_blob=target_value,
            target_mode=target_mode,
            downstream_blob=downstream_value,
            downstream_mode=downstream_mode,
            downstream_kind=downstream_kind,
            manual_paths=manual_paths,
            ignored_paths=ignored_paths,
        )
        expected_items.append({
            "path": path,
            "upstream_status": upstream_status,
            "action": "delete" if target_value is None else ("add" if baseline_value is None else "update"),
            "baseline_mode": baseline_mode,
            "target_mode": target_mode,
            "category": category,
            "reason": reason,
        })
    counts = {category: 0 for category in ("safe", "already", "manual", "conflict", "ignored")}
    for item in expected_items:
        counts[item["category"]] += 1
    if plan.get("items") != expected_items or plan.get("counts") != counts:
        raise SyncError("template sync plan does not match original policy and classification")


def export_blob(root: Path, ref: str, path: str, destination: Path) -> None:
    data = blob_at(root, ref, path)
    if data is None:
        marker = destination.with_suffix(destination.suffix + ".deleted")
        ensure_directory_path(root, marker.relative_to(root).parent, create=True)
        ensure_regular_file(marker, "merge-bundle deletion marker")
        marker.write_text("This path does not exist in this template revision.\n", encoding="utf-8")
        return
    ensure_directory_path(root, destination.relative_to(root).parent, create=True)
    ensure_regular_file(destination, "merge-bundle file")
    destination.write_bytes(data)


def apply_plan(root: Path, config: dict[str, Any], plan_path: Path) -> None:
    ensure_safe_apply_context(root)
    plan = read_plan(plan_path)
    require_untampered_plan(root, config, plan)
    target = str(plan["target_commit"])

    runtime = runtime_directory(root, create=True)
    stale_paths = (
        runtime / "application.json",
        runtime / "verification.json",
        runtime / "verification.md",
    )
    for stale in stale_paths:
        ensure_regular_file(stale, "runtime cleanup file")
    bundle = runtime / "merge-bundle"
    if bundle.is_symlink():
        raise SyncError("refusing to replace symlinked template sync merge bundle")
    if bundle.exists() and not bundle.is_dir():
        raise SyncError("template sync merge-bundle path is not a directory")
    for stale in stale_paths:
        stale.unlink(missing_ok=True)
    if bundle.exists():
        shutil.rmtree(bundle)
    safe_count = 0
    review_count = 0
    for item in plan["items"]:
        path = item["path"]
        category = item["category"]
        if category == "safe":
            if item["action"] == "delete":
                git(root, "rm", "-f", "--ignore-unmatch", "--", path)
            else:
                git(root, "restore", "--source", target, "--staged", "--worktree", "--", path)
            safe_count += 1
        elif category in {"manual", "conflict"}:
            export_blob(root, plan["baseline"], path, bundle / "baseline" / path)
            export_blob(root, target, path, bundle / "upstream" / path)
            review_count += 1

    if review_count:
        readme = bundle / "README.md"
        ensure_directory_path(root, readme.relative_to(root).parent, create=True)
        ensure_regular_file(readme, "merge-bundle README")
        readme.write_text(
            "# Template Sync Merge Bundle\n\n"
            "`baseline/` contains the last recorded upstream version and `upstream/` contains the requested target. "
            "Compare both with the current downstream file. Preserve Human contracts and scientific meaning.\n",
            encoding="utf-8",
        )
    application = {
        "schema_version": APPLICATION_SCHEMA,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "repository_id": repository_id(root),
        "downstream_branch": current_branch(root),
        "downstream_head": head_commit(root),
        "downstream_tree": head_tree(root),
        "baseline": plan["baseline"],
        "target_commit": target,
        "plan_digest": plan["plan_digest"],
        "repository_fingerprint": repository_fingerprint(root),
    }
    application_path = runtime / "application.json"
    ensure_regular_file(application_path, "application receipt")
    application_path.write_text(
        json.dumps(application, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"OK template_sync applied_safe={safe_count} review_bundle={review_count}")


def read_runtime_json(path: Path, schema: str, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"cannot read template sync {label}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != schema:
        raise SyncError(f"unsupported template sync {label} schema")
    return data


def require_application(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    path = runtime_directory(root, create=False) / "application.json"
    if not path.exists() and not path.is_symlink():
        raise SyncError("missing template sync application receipt; run apply before verification")
    ensure_regular_file(path, "application receipt", required=True)
    application = read_runtime_json(path, APPLICATION_SCHEMA, "application receipt")
    for key in (
        "repository_id", "downstream_branch", "downstream_head", "downstream_tree",
        "baseline", "target_commit", "plan_digest",
    ):
        expected = plan["repository_id"] if key == "repository_id" else plan[key]
        if application.get(key) != expected:
            raise SyncError(f"template sync application receipt has a stale {key}")
    return application


def ensure_only_planned_changes(root: Path, plan: dict[str, Any]) -> None:
    planned = {item.get("path") for item in plan.get("items", []) if isinstance(item, dict)}
    unrelated = [path for path in worktree_changes(root) if path not in planned]
    if unrelated:
        raise SyncError("refusing template sync with unrelated dirty state: " + ", ".join(unrelated[:8]))


def require_applied_safe_state(root: Path, plan: dict[str, Any]) -> None:
    target = str(plan["target_commit"])
    failures: list[str] = []
    for item in plan.get("items", []):
        if not isinstance(item, dict) or item.get("category") != "safe":
            continue
        path = str(item["path"])
        staged = git(root, "diff", "--quiet", "--cached", target, "--", path, check=False)
        worktree = git(root, "diff", "--quiet", "--", path, check=False)
        target_deleted = blob_at(root, target, path) is None
        unexpectedly_present = target_deleted and os.path.lexists(root / path)
        if staged.returncode != 0 or worktree.returncode != 0 or unexpectedly_present:
            failures.append(path)
    if failures:
        raise SyncError(
            "safe template changes are not fully applied and staged against the target: "
            + ", ".join(failures[:8])
        )


def expected_verification_commands() -> list[list[str]]:
    commands = [["bash", ".agents/tools/verify.sh"]]
    for variant in ("draft", "anonymous", "camera-ready", "arxiv"):
        commands.append(["make", "pdf", f"VARIANT={variant}"])
    return commands


def verify_sync(root: Path, config: dict[str, Any], plan_path: Path, *, reviewed: bool) -> int:
    if not reviewed:
        raise SyncError("template sync verification requires --reviewed after manual merge review")
    plan = read_plan(plan_path)
    require_plan_context(root, config, plan)
    require_original_plan_policy(root, config, plan)
    require_application(root, plan)
    ensure_only_planned_changes(root, plan)
    require_applied_safe_state(root, plan)
    runtime = runtime_directory(root, create=True)
    verification_json = runtime / "verification.json"
    verification_markdown = runtime / "verification.md"
    ensure_regular_file(verification_json, "verification JSON")
    ensure_regular_file(verification_markdown, "verification Markdown")
    commands = expected_verification_commands()
    checks: list[dict[str, Any]] = []
    for command in commands:
        result = run(command, cwd=root, check=False)
        checks.append({
            "command": shlex.join(command),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        })
        print(f"{'OK' if result.returncode == 0 else 'FAILED'} template_sync verify: {shlex.join(command)}")
    ensure_only_planned_changes(root, plan)
    require_applied_safe_state(root, plan)
    report = {
        "schema_version": VERIFICATION_SCHEMA,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "reviewed": True,
        "repository_id": repository_id(root),
        "downstream_branch": current_branch(root),
        "downstream_head": head_commit(root),
        "downstream_tree": head_tree(root),
        "baseline": plan["baseline"],
        "target_commit": plan["target_commit"],
        "plan_digest": plan["plan_digest"],
        "repository_fingerprint": repository_fingerprint(root),
        "success": all(check["success"] for check in checks),
        "checks": checks,
    }
    verification_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = ["# Template Sync Verification", ""]
    lines.extend(f"- {'PASS' if check['success'] else 'FAIL'}: `{check['command']}`" for check in checks)
    lines.extend(["", "Reviewed: `true`", f"Overall success: `{str(report['success']).lower()}`"])
    verification_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if report["success"] else 1


def require_current_verification(root: Path, plan: dict[str, Any]) -> None:
    path = runtime_directory(root, create=False) / "verification.json"
    if not path.exists() and not path.is_symlink():
        raise SyncError("missing reviewed template sync verification report; run verify --reviewed")
    ensure_regular_file(path, "verification report", required=True)
    report = read_runtime_json(path, VERIFICATION_SCHEMA, "verification report")
    if not report.get("reviewed") or not report.get("success"):
        raise SyncError("the latest template sync verification report is not reviewed and successful")
    expected_commands = [shlex.join(command) for command in expected_verification_commands()]
    checks = report.get("checks")
    if not isinstance(checks, list) or [check.get("command") for check in checks if isinstance(check, dict)] != expected_commands:
        raise SyncError("template sync verification report has an incomplete command set")
    if not all(
        isinstance(check, dict) and check.get("success") and check.get("returncode") == 0
        for check in checks
    ):
        raise SyncError("template sync verification report contains a failed or malformed check")
    for key in (
        "repository_id", "downstream_branch", "downstream_head", "downstream_tree",
        "baseline", "target_commit", "plan_digest",
    ):
        expected = plan["repository_id"] if key == "repository_id" else plan[key]
        if report.get(key) != expected:
            raise SyncError(f"template sync verification report has a stale {key}")
    if report.get("repository_fingerprint") != repository_fingerprint(root):
        raise SyncError("downstream repository changed since template sync verification; rerun verify --reviewed")


def write_config(root: Path, config: dict[str, Any]) -> None:
    path = ensure_directory_path(root, CONFIG_RELATIVE.parent, create=True) / CONFIG_RELATIVE.name
    ensure_regular_file(path, "metadata")
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record_baseline(
    root: Path,
    config: dict[str, Any],
    *,
    plan_path: Path,
    target_ref: str | None,
    reviewed: bool,
    note: str | None,
) -> None:
    if not reviewed:
        raise SyncError("record requires --reviewed after manual merges and repository verification")
    branch = current_branch(root)
    if branch in DEFAULT_BRANCHES:
        raise SyncError(f"refusing template sync record on default branch: {branch}")
    plan = read_plan(plan_path)
    require_plan_context(root, config, plan)
    require_original_plan_policy(root, config, plan)
    require_application(root, plan)
    ensure_only_planned_changes(root, plan)
    require_applied_safe_state(root, plan)
    require_current_verification(root, plan)
    if verify_sync(root, config, plan_path, reviewed=True) != 0:
        raise SyncError("mandatory template sync verification failed during record")
    target = str(plan["target_commit"])
    if target_ref is not None and resolve_commit(root, target_ref) != target:
        raise SyncError("record target does not match the reviewed template sync plan")
    config["last_synced_commit"] = target
    config["last_synced_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    config["last_sync_note"] = note or "Reviewed Agent-assisted template synchronization."
    write_config(root, config)
    print(f"OK template_sync recorded {target}")


def show_status(root: Path, config: dict[str, Any]) -> None:
    upstream = config["upstream"]
    print(f"upstream_url: {upstream['url']}")
    print(f"remote: {upstream['remote']}")
    print(f"branch: {upstream['branch']}")
    print(f"last_synced_commit: {config.get('last_synced_commit') or 'uninitialized'}")
    print(f"downstream_branch: {current_branch(root)}")
    print(f"worktree_clean: {str(worktree_clean(root)).lower()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")
    subparsers.add_parser("status")
    subparsers.add_parser("fetch")

    plan = subparsers.add_parser("plan")
    plan.add_argument("--target-ref")
    plan.add_argument("--bootstrap", action="store_true")
    plan.add_argument("--fetch", action="store_true")
    plan.add_argument("--output", type=Path)

    apply = subparsers.add_parser("apply")
    apply.add_argument("--plan", type=Path)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--plan", type=Path)
    verify.add_argument("--reviewed", action="store_true")

    record = subparsers.add_parser("record")
    record.add_argument("--plan", type=Path)
    record.add_argument("--target-ref")
    record.add_argument("--reviewed", action="store_true")
    record.add_argument("--note")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.expanduser().resolve()
    try:
        ensure_git_repository(root)
        config = read_config(root)
        validate_config_data(config)
        validate_lifecycle_markers(root, config)
        if args.command != "fetch" and not (args.command == "plan" and args.fetch):
            validate_reviewed_adoption_provenance(root, config)
        if args.command in {"fetch", "plan", "apply", "verify", "record"}:
            require_operation_lifecycle(root, config, args.command)
            if args.command != "fetch":
                refuse_in_progress_adoption(config, args.command)
        if args.command == "validate":
            validate_repository(root)
        elif args.command == "status":
            show_status(root, config)
        elif args.command == "fetch":
            fetch_upstream(root, config)
        elif args.command == "plan":
            plan = plan_sync(
                root,
                config,
                target_ref=args.target_ref,
                bootstrap=args.bootstrap,
                fetch=args.fetch,
            )
            plan["plan_digest"] = plan_digest(plan)
            output = args.output
            if output is None:
                output = write_plan(root, plan)
            else:
                output = repository_file_path(
                    root,
                    output,
                    "plan.json",
                    create_parent=True,
                    required=False,
                )
                markdown = output.with_suffix(".md")
                ensure_regular_file(markdown, "plan Markdown")
                output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                markdown.write_text(render_plan(plan), encoding="utf-8")
            print(render_plan(plan), end="")
            print(f"Plan written to {output.relative_to(root) if output.is_relative_to(root) else output}")
        elif args.command == "apply":
            plan_path = repository_file_path(
                root, args.plan, "plan.json", create_parent=False, required=True
            )
            apply_plan(root, config, plan_path)
        elif args.command == "verify":
            plan_path = repository_file_path(
                root, args.plan, "plan.json", create_parent=False, required=True
            )
            return verify_sync(root, config, plan_path, reviewed=args.reviewed)
        elif args.command == "record":
            branch = current_branch(root)
            if branch in DEFAULT_BRANCHES:
                raise SyncError(f"refusing template sync record on default branch: {branch}")
            plan_path = repository_file_path(
                root, args.plan, "plan.json", create_parent=False, required=True
            )
            record_baseline(
                root,
                config,
                plan_path=plan_path,
                target_ref=args.target_ref,
                reviewed=args.reviewed,
                note=args.note,
            )
        return 0
    except SyncError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
