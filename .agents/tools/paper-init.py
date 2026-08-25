#!/usr/bin/env python3
"""Initialize a downstream paper repository by removing template governance residue."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

INIT_STATE_RELATIVE = Path(".agents/init-state.json")
TEMPLATE_ORIGIN_RELATIVE = Path(".agents/template-origin.json")
DOCUMENTATION_CONFIG_RELATIVE = Path(".agents/documentation-consistency.json")
OVERLEAF_CONFIG_RELATIVE = Path(".agents/overleaf-sync.json")
PUBLICATION_RELATIVE = Path("PUBLICATION.md")
INVALID_SYNC_METADATA = object()
COMMIT_MESSAGE = "chore: initialize paper repository and remove template governance residue"
ORIGIN_COMMIT_MESSAGE = "chore: record GitHub Template provenance"
UPSTREAM_REPOSITORY = "a-green-hand-jack/ccfa-writing-paper-template"
TEMPLATE_OVERLEAF_PROJECT = "6a71e37eeb498fef8922f370"
AGENTS_PROTECTED_BRANCHES_LINE = (
    "- Never propose or perform deletion of the protected case branches "
    "(`case/arxiv-2505-22954`, `case/arxiv-2604-01658`, `case/arxiv-2605-03042`), "
    "their case issues (#23, #24, #30), or the standing verification trackers "
    "(#21, #31); do not include them in routine cleanup or deletion reports.\n"
)
DECISION_UPSTREAM_HEADING = "## DEC-0014: Case branches and verification trackers are protected evidence"
DECISION_DOWNSTREAM_HEADING = "## DEC-0014: Downstream paper initialization"
DECISION_RECORDING_HEADING = "## Recording future decisions"
DOWNSTREAM_DECISION = (
    "## DEC-0014: Downstream paper initialization\n"
    "\n"
    "Decision: this repository is a downstream paper initialized from the template. "
    "Upstream template-specific governance IDs were removed during initialization. "
    "This repository owns its own protected case branches and verification issues.\n"
    "\n"
)
PUBLICATION_UPSTREAM_TRACKERS = (
    "This venue planning input is distinct from capability authenticity (#21) and "
    "real environment availability (#31), but strict venue planning depends on the "
    "same honest source and freshness rules."
)
PUBLICATION_DOWNSTREAM_TEXT = (
    "Venue planning is distinct from capability authenticity and real environment "
    "availability, but all three depend on honest source and freshness rules."
)


class InitError(RuntimeError):
    pass


def run(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise InitError(
            f"git {' '.join(args)} failed: {result.stdout.strip()} {result.stderr.strip()}"
        )
    return result


def origin_url(root: Path) -> str:
    result = run(root, "remote", "get-url", "origin", check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def github_repository_identity(url: str) -> str | None:
    value = url.strip()
    if not value:
        return None

    scp_match = re.fullmatch(r"[^/@\s]+@github\.com:(?P<path>.+)", value, flags=re.IGNORECASE)
    if scp_match:
        path = scp_match.group("path")
    else:
        parsed = urlparse(value)
        if (parsed.hostname or "").lower() != "github.com":
            return None
        path = parsed.path.lstrip("/")

    path = path.rstrip("/")
    if path.lower().endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return "/".join(parts).lower()


def is_upstream_template(root: Path) -> bool:
    return github_repository_identity(origin_url(root)) == UPSTREAM_REPOSITORY.lower()


def template_origin_path(root: Path) -> Path:
    return root / TEMPLATE_ORIGIN_RELATIVE


def agents_directory_is_safe(root: Path) -> bool:
    path = root / ".agents"
    return not path.is_symlink() and (not path.exists() or path.is_dir())


def tracked_unchanged(root: Path, relative: Path) -> bool:
    path = relative.as_posix()
    return bool(
        run(root, "ls-files", "--error-unmatch", "--", path, check=False).returncode == 0
        and run(root, "diff", "--quiet", "HEAD", "--", path, check=False).returncode == 0
    )


def valid_template_origin(root: Path) -> bool:
    if not agents_directory_is_safe(root):
        return False
    path = template_origin_path(root)
    if (
        path.is_symlink()
        or not path.is_file()
        or not tracked_unchanged(root, TEMPLATE_ORIGIN_RELATIVE)
    ):
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    if data.get("schema_version") != "paper-template-origin-v1":
        return False
    if data.get("template_repository") != UPSTREAM_REPOSITORY.lower():
        return False
    if data.get("verification") != "github_api_template_repository":
        return False
    downstream_repository = data.get("downstream_repository")
    if not isinstance(downstream_repository, str) or not downstream_repository:
        return False
    if github_repository_identity(origin_url(root)) != downstream_repository.lower():
        return False
    verified_at = data.get("verified_at")
    if not isinstance(verified_at, str):
        return False
    try:
        timestamp = dt.datetime.fromisoformat(verified_at)
    except ValueError:
        return False
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return False
    git_head = data.get("git_head")
    if not isinstance(git_head, str) or not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", git_head):
        return False
    return run(root, "merge-base", "--is-ancestor", git_head, "HEAD", check=False).returncode == 0


def init_state(root: Path) -> Path:
    return root / INIT_STATE_RELATIVE


def valid_init_state(root: Path) -> bool:
    if not agents_directory_is_safe(root):
        return False
    if not valid_template_origin(root):
        return False
    path = init_state(root)
    if path.is_symlink() or not path.is_file() or not tracked_unchanged(root, INIT_STATE_RELATIVE):
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    if (
        data.get("schema_version") != "paper-init-v1"
        or data.get("mode") != "downstream"
        or data.get("template_cleanup") is not True
    ):
        return False
    initialized_at = data.get("initialized_at")
    if not isinstance(initialized_at, str):
        return False
    try:
        timestamp = dt.datetime.fromisoformat(initialized_at)
    except ValueError:
        return False
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return False
    git_head = data.get("git_head")
    if not isinstance(git_head, str) or not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", git_head):
        return False
    return run(root, "merge-base", "--is-ancestor", git_head, "HEAD", check=False).returncode == 0


def worktree_clean(root: Path) -> bool:
    result = run(root, "status", "--porcelain=v1", "--untracked-files=all", check=False)
    return not result.stdout.strip()


def sync_metadata(root: Path) -> dict[str, Any] | None | object:
    if not agents_directory_is_safe(root):
        return INVALID_SYNC_METADATA
    path = root / ".agents/template-sync.json"
    if not path.is_symlink() and not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        return INVALID_SYNC_METADATA
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return INVALID_SYNC_METADATA
    return data if isinstance(data, dict) else INVALID_SYNC_METADATA


def valid_sync_metadata_shape(data: dict[str, Any]) -> bool:
    upstream = data.get("upstream")
    return bool(
        data.get("schema_version") == "paper-template-sync-v1"
        and isinstance(upstream, dict)
        and all(
            isinstance(upstream.get(key), str) and upstream[key].strip()
            for key in ("url", "remote", "branch")
        )
    )


def valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def valid_prior_sync_history(history: Any) -> bool:
    if not isinstance(history, list):
        return False
    required = {
        "adoption",
        "last_synced_commit",
        "last_synced_at",
        "last_sync_note",
        "reference_integrity",
        "upstream",
    }
    for entry in history:
        if not isinstance(entry, dict) or not required.issubset(entry):
            return False
        commit = entry["last_synced_commit"]
        if commit is not None and (
            not isinstance(commit, str)
            or not re.fullmatch(r"[0-9a-f]{40}", commit)
        ):
            return False
        if entry["last_synced_at"] is not None and not valid_timestamp(entry["last_synced_at"]):
            return False
        if (commit is None) != (entry["last_synced_at"] is None):
            return False
        if entry["last_sync_note"] is not None and not isinstance(entry["last_sync_note"], str):
            return False
        if entry["adoption"] is not None and not isinstance(entry["adoption"], dict):
            return False
        integrity = entry["reference_integrity"]
        if integrity is not None and (
            not isinstance(integrity, dict) or not isinstance(integrity.get("adopted"), bool)
        ):
            return False
        upstream = entry["upstream"]
        if not isinstance(upstream, dict) or not all(
            isinstance(upstream.get(key), str) and upstream[key].strip()
            for key in ("url", "remote", "branch")
        ):
            return False
    return True


def valid_sync_metadata_fields(data: dict[str, Any]) -> bool:
    if not valid_sync_metadata_shape(data):
        return False
    baseline = data.get("last_synced_commit")
    if baseline is not None and not (
        isinstance(baseline, str) and re.fullmatch(r"[0-9a-f]{40}", baseline)
    ):
        return False
    synced_at = data.get("last_synced_at")
    if synced_at is not None and not valid_timestamp(synced_at):
        return False
    if (baseline is None) != (synced_at is None):
        return False
    note = data.get("last_sync_note")
    if note is not None and not isinstance(note, str):
        return False
    integrity = data.get("reference_integrity")
    if integrity is not None and (
        not isinstance(integrity, dict) or not isinstance(integrity.get("adopted"), bool)
    ):
        return False
    for key in ("always_manual", "ignored_paths"):
        values = data.get(key, [])
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            return False
        for value in values:
            candidate = Path(value)
            if candidate.is_absolute() or ".." in candidate.parts:
                return False
    return True


def valid_reviewed_adoption_shape(data: dict[str, Any]) -> bool:
    adoption = data.get("adoption")
    baseline = data.get("last_synced_commit")
    if not isinstance(adoption, dict) or adoption.get("status") != "reviewed":
        return False
    return bool(
        valid_sync_metadata_fields(data)
        and isinstance(baseline, str)
        and re.fullmatch(r"[0-9a-f]{40}", baseline)
        and valid_timestamp(data.get("last_synced_at"))
        and isinstance(adoption.get("target_commit"), str)
        and re.fullmatch(r"[0-9a-f]{40}", adoption["target_commit"])
        and valid_timestamp(adoption.get("reviewed_at"))
        and isinstance(adoption.get("verification_repository_fingerprint"), str)
        and re.fullmatch(
            r"[0-9a-f]{64}", adoption["verification_repository_fingerprint"]
        )
        and valid_prior_sync_history(adoption.get("prior_sync_history"))
    )


def adoption_state(root: Path) -> str:
    data = sync_metadata(root)
    if data is None:
        return "none"
    if data is INVALID_SYNC_METADATA or not isinstance(data, dict):
        return "invalid"
    adoption = data.get("adoption")
    if adoption is None:
        return "none" if valid_sync_metadata_fields(data) else "invalid_sync"
    if not isinstance(adoption, dict):
        return "invalid"
    target = adoption.get("target_commit")
    history = adoption.get("prior_sync_history")
    common_valid = bool(
        valid_sync_metadata_fields(data)
        and isinstance(target, str)
        and re.fullmatch(r"[0-9a-f]{40}", target)
        and "prior_sync_history" in adoption
        and valid_prior_sync_history(history)
    )
    if adoption.get("status") == "in_progress":
        valid = bool(
            common_valid
            and data.get("last_synced_commit") is None
            and data.get("last_synced_at") is None
            and "reviewed_at" not in adoption
            and "verification_repository_fingerprint" not in adoption
        )
        return "in_progress" if valid else "invalid"
    if adoption.get("status") == "reviewed":
        return "reviewed" if valid_reviewed_adoption_shape(data) else "invalid"
    return "invalid"


def valid_initialized_sync(root: Path) -> bool:
    data = sync_metadata(root)
    if not isinstance(data, dict) or not valid_sync_metadata_fields(data):
        return False
    adoption = data.get("adoption")
    if adoption is None:
        return True
    return valid_reviewed_adoption_shape(data)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_agents_file(root: Path, name: str, text: str) -> None:
    agents = root / ".agents"
    agents.mkdir(parents=True, exist_ok=True)
    directory_fd = -1
    file_fd = -1
    try:
        directory_fd = os.open(
            agents,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        file_fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o644,
            dir_fd=directory_fd,
        )
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise InitError(f"refusing to write non-regular lifecycle file: {agents / name}")
        with os.fdopen(file_fd, "w", encoding="utf-8") as stream:
            file_fd = -1
            stream.write(text)
    except OSError as exc:
        raise InitError(f"refusing unsafe lifecycle file write: {agents / name}: {exc}") from exc
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if directory_fd >= 0:
            os.close(directory_fd)


def status(root: Path) -> int:
    if not agents_directory_is_safe(root):
        print("UNINITIALIZED paper_init conflict: .agents must be a repository-local directory")
        return 1
    marker_path = init_state(root)
    origin_path = template_origin_path(root)
    marker_exists = marker_path.is_symlink() or marker_path.exists()
    origin_exists = origin_path.is_symlink() or origin_path.exists()
    adoption = adoption_state(root)
    if adoption == "in_progress":
        if marker_exists or origin_exists:
            print(
                "UNINITIALIZED paper_init conflict: adoption must not carry "
                "GitHub Template provenance or an initialization marker"
            )
            return 1
        print("OK paper_init adoption_in_progress")
        return 0
    if adoption == "reviewed":
        if marker_exists or origin_exists:
            print(
                "UNINITIALIZED paper_init conflict: adoption must not carry "
                "GitHub Template provenance or an initialization marker"
            )
            return 1
        print("OK paper_init adoption_reviewed")
        return 0
    if adoption == "invalid":
        print("UNINITIALIZED paper_init conflict: malformed adoption metadata")
        return 1
    if adoption == "invalid_sync":
        print("UNINITIALIZED paper_init conflict: invalid template-sync metadata")
        return 1
    if valid_init_state(root):
        if not valid_initialized_sync(root):
            print("UNINITIALIZED paper_init conflict: initialized marker has invalid template-sync metadata")
            return 1
        print("OK paper_init initialized")
        return 0
    if not marker_exists and is_upstream_template(root):
        print("OK paper_init upstream_template")
        return 0
    if valid_template_origin(root):
        print(
            "UNINITIALIZED paper_init template_created; run "
            "`python3 .agents/tools/paper-init.py clean --commit`"
        )
        return 1
    if marker_exists:
        print(
            "UNINITIALIZED paper_init invalid marker; run "
            "`python3 .agents/tools/paper-init.py clean --commit`"
        )
        return 1
    print(
        "UNINITIALIZED paper_init; positive GitHub Template provenance is "
        "required before initialization"
    )
    return 1


def clean_agents(root: Path, changes: list[str]) -> None:
    path = root / "AGENTS.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if AGENTS_PROTECTED_BRANCHES_LINE in text:
        text = text.replace(AGENTS_PROTECTED_BRANCHES_LINE, "")
        write_text(path, text)
        changes.append("AGENTS.md")


def clean_decisions(root: Path, changes: list[str]) -> None:
    path = root / "DECISIONS.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if DECISION_DOWNSTREAM_HEADING in text:
        return
    start = text.find(DECISION_UPSTREAM_HEADING)
    end = text.find(DECISION_RECORDING_HEADING, start)
    if start != -1 and end != -1:
        text = text[:start] + DOWNSTREAM_DECISION + text[end:]
        write_text(path, text)
        changes.append("DECISIONS.md")


def reset_documentation_config(root: Path, changes: list[str]) -> None:
    path = root / DOCUMENTATION_CONFIG_RELATIVE
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(data, dict) or data.get("schema_version") != "paper-documentation-consistency-v1":
        return
    if data.get("required_facts") == {} and data.get("stale_patterns", {}) == {}:
        return
    data["required_facts"] = {}
    data["stale_patterns"] = {}
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    changes.append(DOCUMENTATION_CONFIG_RELATIVE.as_posix())


def clean_publication(root: Path, changes: list[str]) -> None:
    path = root / PUBLICATION_RELATIVE
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if PUBLICATION_UPSTREAM_TRACKERS in text:
        write_text(path, text.replace(PUBLICATION_UPSTREAM_TRACKERS, PUBLICATION_DOWNSTREAM_TEXT))
        changes.append(PUBLICATION_RELATIVE.as_posix())


def delete_template_overleaf_config(root: Path, changes: list[str]) -> None:
    path = root / OVERLEAF_CONFIG_RELATIVE
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if TEMPLATE_OVERLEAF_PROJECT not in text:
        return
    path.unlink()
    changes.append(OVERLEAF_CONFIG_RELATIVE.as_posix())


def write_init_state(root: Path, changes: list[str]) -> None:
    data: dict[str, Any] = {
        "schema_version": "paper-init-v1",
        "initialized_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "downstream",
        "template_cleanup": True,
        "git_head": run(root, "rev-parse", "HEAD").stdout.strip(),
    }
    path = init_state(root)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise InitError(f"refusing to replace unsafe initialization marker: {path}")
    write_agents_file(root, "init-state.json", json.dumps(data, indent=2, sort_keys=True) + "\n")
    changes.append(INIT_STATE_RELATIVE.as_posix())


def run_gh_template_check(root: Path, repository: str) -> None:
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repository}", "--jq", ".template_repository.full_name // empty"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise InitError(f"GitHub Template provenance check could not start: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise InitError(f"GitHub Template provenance check failed: {detail}")
    observed = result.stdout.strip().lower()
    if observed != UPSTREAM_REPOSITORY.lower():
        raise InitError(
            "GitHub API did not identify "
            f"{UPSTREAM_REPOSITORY} as the template repository for {repository}"
        )


def record_template_origin(root: Path, commit: bool) -> int:
    if not commit:
        raise InitError("record-template-origin requires --commit for durable provenance")
    if not agents_directory_is_safe(root):
        raise InitError("refusing to use a symlinked or non-directory .agents path")
    adoption = adoption_state(root)
    if adoption != "none":
        raise InitError(
            "refusing to record GitHub Template provenance while template adoption metadata is "
            + adoption
        )
    marker = init_state(root)
    if marker.is_symlink() or marker.exists():
        raise InitError(
            "refusing to record GitHub Template provenance while an initialization marker exists"
        )
    if not worktree_clean(root):
        raise InitError("record-template-origin requires a clean worktree")
    path = template_origin_path(root)
    if path.is_symlink() or path.exists():
        raise InitError(f"template provenance path already exists: {path}")
    repository = github_repository_identity(origin_url(root))
    if repository is None or repository == UPSTREAM_REPOSITORY.lower():
        raise InitError("record-template-origin requires a distinct GitHub repository origin")
    run_gh_template_check(root, repository)
    data = {
        "downstream_repository": repository,
        "git_head": run(root, "rev-parse", "HEAD").stdout.strip(),
        "schema_version": "paper-template-origin-v1",
        "template_repository": UPSTREAM_REPOSITORY.lower(),
        "verification": "github_api_template_repository",
        "verified_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    write_agents_file(root, "template-origin.json", json.dumps(data, indent=2, sort_keys=True) + "\n")
    if commit:
        run(root, "add", "--", TEMPLATE_ORIGIN_RELATIVE.as_posix())
        run(root, "commit", "-m", ORIGIN_COMMIT_MESSAGE)
        print("OK paper_init template_origin_committed")
    else:
        print("OK paper_init template_origin_recorded")
    return 0


def clean(root: Path, commit: bool, downstream: bool) -> int:
    marker_path = init_state(root)
    if marker_path.is_symlink() or (marker_path.exists() and not marker_path.is_file()):
        raise InitError(f"refusing to clean with an unsafe initialization marker: {marker_path}")
    marker_exists = marker_path.is_file()
    adoption = adoption_state(root)
    if adoption != "none":
        raise InitError(
            "refusing paper initialization while template adoption metadata is " + adoption
        )
    if valid_init_state(root):
        if not valid_initialized_sync(root):
            raise InitError(
                "refusing to accept initialization without valid .agents/template-sync.json; "
                "restore the template sync metadata before running clean"
            )
        print("OK paper_init already_initialized")
        return 0
    if not downstream and is_upstream_template(root):
        if marker_exists:
            raise InitError(
                "refusing to clean upstream template with an invalid initialization marker; "
                "use --downstream only after confirming this repository is a downstream paper"
            )
        print("OK paper_init upstream_template")
        return 0
    if not valid_template_origin(root):
        raise InitError(
            "refusing to initialize without a valid GitHub Template provenance record; "
            "run `python3 .agents/tools/paper-init.py record-template-origin --commit` "
            "from the verified template-create workflow"
        )
    if not valid_initialized_sync(root):
        raise InitError(
            "refusing to initialize without valid .agents/template-sync.json; "
            "restore the template sync metadata before running clean"
        )
    if marker_exists:
        raise InitError(f"refusing to replace existing initialization marker: {marker_path}")
    repository = github_repository_identity(origin_url(root))
    if repository is None:
        raise InitError("template provenance requires a GitHub repository origin")
    run_gh_template_check(root, repository)
    if commit and not worktree_clean(root):
        raise InitError("clean --commit requires a clean worktree")

    changes: list[str] = []
    clean_agents(root, changes)
    clean_decisions(root, changes)
    reset_documentation_config(root, changes)
    clean_publication(root, changes)
    delete_template_overleaf_config(root, changes)
    write_init_state(root, changes)

    if not changes:
        print("OK paper_init clean_no_changes")
        return 0

    print("OK paper_init cleaned " + ", ".join(changes))
    if commit:
        run(root, "add", "-A")
        run(root, "commit", "-m", COMMIT_MESSAGE)
        print("OK paper_init committed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    origin_parser = subparsers.add_parser("record-template-origin")
    origin_parser.add_argument("--commit", action="store_true")
    clean_parser = subparsers.add_parser("clean")
    clean_parser.add_argument("--commit", action="store_true")
    clean_parser.add_argument(
        "--downstream",
        action="store_true",
        help="legacy explicit override; it cannot bypass template provenance verification",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.expanduser().resolve()
    try:
        if args.command == "status":
            return status(root)
        if args.command == "record-template-origin":
            return record_template_origin(root, args.commit)
        if args.command == "clean":
            return clean(root, args.commit, args.downstream)
        raise InitError(f"unknown command: {args.command}")
    except InitError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
