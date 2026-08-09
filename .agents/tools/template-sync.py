#!/usr/bin/env python3
"""Plan and apply safe upstream template updates in a downstream paper repository.

The downstream repository may have an unrelated Git history. Synchronization is
therefore path-level and three-way: the last recorded upstream template commit,
the requested upstream target, and the current downstream working tree.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

CONFIG_RELATIVE = Path(".agents/template-sync.json")
RUNTIME_RELATIVE = Path(".agents/runtime/template-sync")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DEFAULT_BRANCHES = {"main", "master", "trunk"}
DEFAULT_MANUAL_PATHS = (
    ".gitignore",
    ".github/",
    "README.md",
    "REFERENCES.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "Makefile",
    "PAPER.md",
    "EXPERIMENTS.md",
    "PAPER_INTERFACES.md",
    "PUBLICATION.md",
    "DECISIONS.md",
    "paper/main.tex",
    "paper/macros.tex",
    "paper/venue_preamble.tex",
    "paper/refs.bib",
    "paper/sections/",
    "paper/figures/",
    "paper/tables/",
    "paper/generated/",
    "paper/supplementary/",
    "paper/style/",
    "references/",
    ".agents/dependencies/",
    ".agents/knowledge/",
)
DEFAULT_IGNORED_PATHS = (
    ".agents/template-sync.json",
    ".agents/overleaf-sync.json",
    ".agents/documentation-consistency.json",
    ".agents/init-state.json",
    ".agents/runtime/",
    "dist/",
)


class SyncError(RuntimeError):
    pass


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
    path = root / CONFIG_RELATIVE
    if not path.is_file():
        raise SyncError(f"missing template sync metadata: {CONFIG_RELATIVE.as_posix()}")
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
    reference_integrity = data.get("reference_integrity")
    if reference_integrity is not None and (
        not isinstance(reference_integrity, dict)
        or not isinstance(reference_integrity.get("adopted"), bool)
    ):
        raise SyncError("template sync reference_integrity.adopted must be boolean")
    for key in ("always_manual", "ignored_paths"):
        values = data.get(key, [])
        if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
            raise SyncError(f"{key} must be a list of non-empty path strings")
        for value in values:
            path = PurePosixPath(value)
            if path.is_absolute() or ".." in path.parts:
                raise SyncError(f"unsafe path in {key}: {value}")


def validate_repository(root: Path) -> None:
    data = read_config(root)
    validate_config_data(data)
    skill = root / ".agents/skills/template-sync/SKILL.md"
    if not skill.is_file():
        raise SyncError("missing template sync skill: .agents/skills/template-sync/SKILL.md")
    text = skill.read_text(encoding="utf-8")
    for heading in ("## Trigger", "## Minimum context", "## Procedure", "## Safety boundary"):
        if heading not in text:
            raise SyncError(f"template sync skill missing heading: {heading}")
    print("OK template_sync configuration")


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


def fetch_upstream(root: Path, config: dict[str, Any]) -> str:
    remote, _, branch = ensure_remote(root, config)
    git(root, "fetch", "--prune", remote, branch)
    commit = resolve_commit(root, f"{remote}/{branch}")
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


def local_entry(root: Path, path: str) -> tuple[str, bytes | None]:
    target = root / path
    if target.is_symlink():
        return "other", None
    if target.is_file():
        return "file", target.read_bytes()
    if target.exists():
        return "other", None
    return "missing", None


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
    target_blob: bytes | None,
    downstream_blob: bytes | None,
    downstream_kind: str,
    manual_paths: list[str],
    ignored_paths: list[str],
) -> tuple[str, str]:
    if path_matches(path, ignored_paths):
        return "ignored", "downstream-local metadata or generated runtime"
    if downstream_kind == "other":
        return "conflict", "downstream path is a symlink or non-file entry"
    if downstream_blob == target_blob:
        return "already", "downstream already matches upstream target"
    if path_matches(path, manual_paths):
        return "manual", "protected Human-authored or project-specific surface"
    if downstream_blob == baseline_blob:
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

    manual_paths = list(DEFAULT_MANUAL_PATHS) + list(config.get("always_manual", []))
    ignored_paths = list(DEFAULT_IGNORED_PATHS) + list(config.get("ignored_paths", []))
    items: list[dict[str, Any]] = []
    for upstream_status, path in changed_paths(root, baseline, target):
        baseline_value = blob_at(root, baseline, path) if baseline != EMPTY_TREE else None
        target_value = blob_at(root, target, path)
        downstream_kind, downstream_value = local_entry(root, path)
        category, reason = classify_path(
            path=path,
            upstream_status=upstream_status,
            baseline_blob=baseline_value,
            target_blob=target_value,
            downstream_blob=downstream_value,
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
                "category": category,
                "reason": reason,
            }
        )

    counts = {category: 0 for category in ("safe", "already", "manual", "conflict", "ignored")}
    for item in items:
        counts[item["category"]] += 1
    return {
        "schema_version": "paper-template-sync-plan-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "bootstrap": baseline == EMPTY_TREE,
        "baseline": baseline,
        "target_ref": target_name,
        "target_commit": target,
        "downstream_head": git(root, "rev-parse", "HEAD").stdout.strip(),
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
    runtime = root / RUNTIME_RELATIVE
    runtime.mkdir(parents=True, exist_ok=True)
    path = runtime / "plan.json"
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (runtime / "plan.md").write_text(render_plan(plan), encoding="utf-8")
    return path


def read_plan(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"cannot read template sync plan: {exc}") from exc
    if data.get("schema_version") != "paper-template-sync-plan-v1":
        raise SyncError("unsupported template sync plan schema")
    return data


def export_blob(root: Path, ref: str, path: str, destination: Path) -> None:
    data = blob_at(root, ref, path)
    if data is None:
        marker = destination.with_suffix(destination.suffix + ".deleted")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("This path does not exist in this template revision.\n", encoding="utf-8")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def apply_plan(root: Path, plan_path: Path) -> None:
    ensure_safe_apply_context(root)
    plan = read_plan(plan_path)
    current_head = git(root, "rev-parse", "HEAD").stdout.strip()
    if current_head != plan["downstream_head"]:
        raise SyncError("downstream HEAD moved after plan creation; regenerate the template sync plan")
    target = resolve_commit(root, plan["target_commit"])
    if target != plan["target_commit"]:
        raise SyncError("upstream target no longer resolves to the planned commit")

    runtime = root / RUNTIME_RELATIVE
    bundle = runtime / "merge-bundle"
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
        (bundle / "README.md").write_text(
            "# Template Sync Merge Bundle\n\n"
            "`baseline/` contains the last recorded upstream version and `upstream/` contains the requested target. "
            "Compare both with the current downstream file. Preserve Human contracts and scientific meaning.\n",
            encoding="utf-8",
        )
    print(f"OK template_sync applied_safe={safe_count} review_bundle={review_count}")


def write_config(root: Path, config: dict[str, Any]) -> None:
    path = root / CONFIG_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record_baseline(
    root: Path,
    config: dict[str, Any],
    *,
    target_ref: str | None,
    reviewed: bool,
    note: str | None,
) -> None:
    if not reviewed:
        raise SyncError("record requires --reviewed after manual merges and repository verification")
    upstream = config["upstream"]
    ref = target_ref or f"{upstream['remote']}/{upstream['branch']}"
    target = resolve_commit(root, ref)
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

    record = subparsers.add_parser("record")
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
            output = args.output
            if output is None:
                output = write_plan(root, plan)
            else:
                if not output.is_absolute():
                    output = root / output
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                output.with_suffix(".md").write_text(render_plan(plan), encoding="utf-8")
            print(render_plan(plan), end="")
            print(f"Plan written to {output.relative_to(root) if output.is_relative_to(root) else output}")
        elif args.command == "apply":
            plan_path = args.plan or (root / RUNTIME_RELATIVE / "plan.json")
            if not plan_path.is_absolute():
                plan_path = root / plan_path
            apply_plan(root, plan_path)
        elif args.command == "record":
            record_baseline(
                root,
                config,
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
