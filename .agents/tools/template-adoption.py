#!/usr/bin/env python3
"""Inspect and safely adopt the paper template in an existing Git repository.

The adoption workflow is intentionally separate from ongoing template sync. It
can be run from a template checkout against an unrelated downstream repository,
installs only missing Agent-sidecar infrastructure mechanically, and leaves
scientific content, build logic, CI, venue configuration, and project contracts
for evidence-backed semantic migration.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from _template_inheritance import (
    POLICY_RELATIVE,
    combine_inheritance_policies,
    load_inheritance_policy,
    parse_inheritance_policy,
)

RUNTIME_RELATIVE = Path(".agents/runtime/template-adoption")
SYNC_CONFIG_RELATIVE = Path(".agents/template-sync.json")
ADOPTION_SKILL_RELATIVE = Path(".agents/skills/template-adoption/SKILL.md")
ADOPTION_TOOL_RELATIVE = Path(".agents/tools/template-adoption.py")
DEFAULT_UPSTREAM_URL = "https://github.com/a-green-hand-jack/ccfa-writing-paper-template.git"
DEFAULT_REMOTE = "template"
DEFAULT_UPSTREAM_BRANCH = "main"
DEFAULT_BRANCHES = {"main", "master", "trunk"}
REGULAR_FILE_MODES = {"100644", "100755"}
SCAN_SKIP_PREFIXES = (
    ".git/",
    ".agents/runtime/",
    "dist/",
    "build/",
    "out/",
    "node_modules/",
    ".venv/",
    "venv/",
)
TEXT_LIMIT = 2 * 1024 * 1024
IMAGE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps"}
BUILD_CANDIDATES = (
    "Makefile",
    "makefile",
    "GNUmakefile",
    ".latexmkrc",
    "latexmkrc",
    "build.sh",
    "compile.sh",
    "justfile",
    "Justfile",
    "Dockerfile",
    "pyproject.toml",
)
COMMAND_INTERPRETERS = {
    "bash",
    "dash",
    "perl",
    "python",
    "python3",
    "ruby",
    "sh",
    "zsh",
}
ASSESSMENT_COMMANDS = (
    ("python3", "-m", "compileall", "-q", ".agents/tools", ".agents/tests"),
    ("python3", ".agents/tools/check-structure.py"),
    ("python3", ".agents/tools/paper-init.py", "status"),
    ("python3", ".agents/tools/check-documentation.py"),
    ("python3", ".agents/tools/check-venue-knowledge.py"),
    ("python3", ".agents/tools/check-paper-contracts.py", "--profile", "draft"),
    ("python3", ".agents/tools/check-paper-interfaces.py"),
    ("python3", ".agents/tools/check-reference-integrity.py", "--profile", "draft"),
    ("python3", ".agents/tools/check-publication.py"),
    ("python3", ".agents/tools/check-release-records.py"),
    ("python3", ".agents/tools/template-adoption.py", "validate"),
    ("python3", ".agents/tools/template-sync.py", "validate"),
    ("python3", ".agents/tools/overleaf-sync.py", "validate"),
    ("python3", "-m", "unittest", "discover", "-s", ".agents/tests", "-p", "test_*.py"),
    ("make", "pdf", "VARIANT=draft"),
    ("make", "pdf", "VARIANT=anonymous"),
    ("make", "pdf", "VARIANT=camera-ready"),
    ("make", "pdf", "VARIANT=arxiv"),
)
AGENT_CANDIDATES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    ".cursorrules",
    ".windsurfrules",
)
CONTRACT_PATHS = (
    "PAPER.md",
    "EXPERIMENTS.md",
    "PAPER_INTERFACES.md",
    "PUBLICATION.md",
    "DECISIONS.md",
)
EXPERIMENT_DIRECTORY_NAMES = {
    "analysis",
    "analyses",
    "benchmark",
    "benchmarks",
    "eval",
    "evals",
    "evaluation",
    "evaluations",
    "experiment",
    "experiments",
    "notebook",
    "notebooks",
    "result",
    "results",
}
EXPERIMENT_FILE_TOKENS = (
    "ablation",
    "benchmark",
    "eval",
    "evaluation",
    "experiment",
)

DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{[^}]+\}")
BEGIN_DOCUMENT_RE = re.compile(r"\\begin\{document\}")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
GRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
BIBLIOGRAPHY_RE = re.compile(r"\\bibliography\{([^}]+)\}")
ADD_BIBRESOURCE_RE = re.compile(r"\\addbibresource(?:\[[^\]]*\])?\{([^}]+)\}")
TABLE_RE = re.compile(r"\\begin\{(?:table\*?|tabular\*?|longtable)\}")


class AdoptionError(RuntimeError):
    pass


def inheritance_policy(root: Path) -> dict[str, Any]:
    try:
        return load_inheritance_policy(root)
    except ValueError as exc:
        raise AdoptionError(str(exc)) from exc


def tool_inheritance_policy() -> dict[str, Any]:
    return inheritance_policy(Path(__file__).resolve().parents[2])


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
        raise AdoptionError(f"command failed ({result.returncode}): {' '.join(command)}{detail}")
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=root, check=check)


def ensure_git_repository(root: Path) -> None:
    result = git(root, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        raise AdoptionError(f"not a Git repository: {root}")
    actual = Path(result.stdout.strip()).resolve()
    if actual != root.resolve():
        raise AdoptionError(f"--root must be repository root: expected {actual}, got {root.resolve()}")


def normalize_path(path: str) -> str:
    return PurePosixPath(path).as_posix()


def path_matches(path: str, patterns: Iterable[str]) -> bool:
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


def ensure_directory_path(root: Path, relative: Path, *, create: bool) -> Path:
    candidate = PurePosixPath(relative.as_posix())
    if candidate.is_absolute() or ".." in candidate.parts:
        raise AdoptionError(f"unsafe control directory path: {relative.as_posix()}")
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise AdoptionError(
                f"refusing to use symlinked control directory: {current.relative_to(root)}"
            )
        if current.exists() and not current.is_dir():
            raise AdoptionError(
                f"control directory path is not a directory: {current.relative_to(root)}"
            )
        if create and not current.exists():
            current.mkdir()
    return current


def runtime_directory(root: Path, *, create: bool) -> Path:
    return ensure_directory_path(root, RUNTIME_RELATIVE, create=create)


def ensure_writable_file(path: Path) -> None:
    if path.is_symlink():
        raise AdoptionError(f"refusing to overwrite symlinked output file: {path}")
    if path.exists() and not path.is_file():
        raise AdoptionError(f"output path is not a regular file: {path}")


def prepare_output_path(root: Path, value: Path | None, default_name: str) -> Path:
    if value is None:
        path = runtime_directory(root, create=True) / default_name
    elif value.is_absolute():
        path = value
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        candidate = PurePosixPath(value.as_posix())
        if ".." in candidate.parts:
            raise AdoptionError(f"unsafe relative output path: {value}")
        parent_relative = Path(*candidate.parts[:-1]) if len(candidate.parts) > 1 else Path(".")
        parent = ensure_directory_path(root, parent_relative, create=True)
        path = parent / candidate.name
    ensure_writable_file(path)
    return path


def has_unsafe_parent(root: Path, path: str) -> bool:
    candidate = PurePosixPath(path)
    current = root
    for part in candidate.parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return True
    return False


def current_branch(root: Path) -> str:
    result = git(root, "branch", "--show-current")
    branch = result.stdout.strip()
    if not branch:
        raise AdoptionError("template adoption requires a named branch, not detached HEAD")
    return branch


def head_commit(root: Path) -> str | None:
    result = git(root, "rev-parse", "HEAD", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def worktree_changes(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AdoptionError("cannot inspect downstream worktree")
    changes: list[str] = []
    for record in result.stdout.split(b"\0"):
        if not record or len(record) < 4:
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
    head = head_commit(root)
    if head is None:
        raise AdoptionError("template adoption verification requires a checkpoint commit")
    digest = hashlib.sha256()
    digest.update(b"paper-template-adoption-worktree-v1\0")
    digest.update(head.encode("ascii"))
    digest.update(b"\0")

    diff = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff", "HEAD", "--"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if diff.returncode != 0:
        raise AdoptionError("cannot fingerprint tracked downstream changes")
    digest.update(diff.stdout)

    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if untracked.returncode != 0:
        raise AdoptionError("cannot fingerprint untracked downstream files")
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
        if candidate.is_symlink():
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


def json_fingerprint(data: dict[str, Any]) -> str:
    payload = json.dumps(
        data,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def inspection_fingerprint(inspection: dict[str, Any]) -> str:
    comparable = json.loads(json.dumps(inspection))
    comparable.pop("created_at", None)
    return json_fingerprint(comparable)


def ensure_safe_apply_context(root: Path) -> None:
    branch = current_branch(root)
    if branch in DEFAULT_BRANCHES:
        raise AdoptionError(f"refusing template adoption apply on default branch: {branch}")
    if head_commit(root) is None:
        raise AdoptionError("template adoption apply requires a checkpoint commit")
    changes = worktree_changes(root)
    if changes:
        raise AdoptionError(
            "refusing template adoption apply with a dirty worktree: " + ", ".join(changes[:8])
        )


def ensure_non_default_branch(root: Path) -> None:
    branch = current_branch(root)
    if branch in DEFAULT_BRANCHES:
        raise AdoptionError(f"refusing template adoption finalization on default branch: {branch}")


def ensure_remote(root: Path, *, remote: str, url: str) -> None:
    existing = git(root, "remote", "get-url", remote, check=False)
    if existing.returncode != 0:
        git(root, "remote", "add", remote, url)
    elif existing.stdout.strip() != url:
        raise AdoptionError(
            f"remote {remote} points to {existing.stdout.strip()}, expected {url}; review before changing it"
        )


def resolve_commit(root: Path, ref: str) -> str:
    result = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
    if result.returncode != 0:
        raise AdoptionError(f"cannot resolve template commit: {ref}; run fetch first")
    return result.stdout.strip()


def fetch_upstream(root: Path, *, remote: str, url: str, branch: str) -> str:
    ensure_remote(root, remote=remote, url=url)
    git(root, "fetch", "--prune", remote, branch)
    target = resolve_commit(root, f"{remote}/{branch}")
    print(f"OK template_adoption fetched {remote}/{branch} -> {target}")
    return target


def target_entries(root: Path, target: str) -> list[dict[str, str]]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", target],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AdoptionError(f"cannot list template tree: {target}")
    entries: list[dict[str, str]] = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, sha = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        normalized = normalize_path(path)
        candidate = PurePosixPath(normalized)
        if candidate.is_absolute() or ".." in candidate.parts or path_matches(normalized, [".git/"]):
            raise AdoptionError(f"unsafe path reported by template: {path}")
        if kind != "blob":
            raise AdoptionError(
                f"unsupported non-file entry in template target: {normalized} ({kind})"
            )
        if mode not in REGULAR_FILE_MODES:
            raise AdoptionError(
                f"unsupported non-regular entry in template target: {normalized} ({mode})"
            )
        entries.append({"mode": mode, "sha": sha, "path": normalized})
    return entries


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


def target_inheritance_policy(root: Path, target: str) -> dict[str, Any]:
    payload = blob_at(root, target, POLICY_RELATIVE.as_posix())
    if payload is None:
        raise AdoptionError(
            f"selected template target is missing {POLICY_RELATIVE.as_posix()}"
        )
    try:
        target_policy = parse_inheritance_policy(payload)
    except ValueError as exc:
        raise AdoptionError(f"invalid target template inheritance policy: {exc}") from exc
    return combine_inheritance_policies(tool_inheritance_policy(), target_policy)


def local_entry(root: Path, path: str) -> tuple[str, bytes | None, str | None]:
    if has_unsafe_parent(root, path):
        return "other", None, None
    target = root / path
    if target.is_symlink():
        return "other", None, "120000"
    if target.is_file():
        mode = "100755" if target.stat().st_mode & 0o111 else "100644"
        return "file", target.read_bytes(), mode
    if target.exists():
        return "other", None, None
    return "missing", None, None


def tracked_and_untracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AdoptionError("cannot enumerate repository files")
    paths: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = normalize_path(raw.decode("utf-8", errors="surrogateescape"))
        if path_matches(path, SCAN_SKIP_PREFIXES):
            continue
        candidate = root / path
        if candidate.is_file() and not candidate.is_symlink():
            paths.append(path)
    return sorted(set(paths))


def is_build_candidate(path: str) -> bool:
    pure = PurePosixPath(path)
    return path in BUILD_CANDIDATES or pure.name in BUILD_CANDIDATES


def is_workflow_candidate(path: str) -> bool:
    return (
        path.startswith(".github/workflows/")
        and PurePosixPath(path).suffix.lower() in {".yml", ".yaml"}
    ) or path == ".gitlab-ci.yml"


def ranked_agent_files(paths: Iterable[str]) -> list[str]:
    scores: dict[str, int] = {}
    for path in paths:
        score = 10
        if path == "AGENTS.md":
            score = 100
        elif path == "CLAUDE.md":
            score = 85
        elif path == ".github/copilot-instructions.md":
            score = 70
        elif path.startswith(".github/instructions/"):
            score = 60
        elif path.startswith(".cursor/rules/") or path == ".cursorrules":
            score = 55
        scores[path] = score
    return sorted(scores, key=lambda item: (-scores[item], item))


def read_text(root: Path, path: str) -> str | None:
    candidate = root / path
    try:
        if candidate.stat().st_size > TEXT_LIMIT:
            return None
        return candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def active_tex(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        match = re.search(r"(?<!\\)%", line)
        lines.append(line[: match.start()] if match else line)
    return "\n".join(lines)


def inside_root(root: Path, candidate: Path) -> Path | None:
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root.resolve())
        return resolved
    except (OSError, ValueError):
        return None


def relative_posix(root: Path, candidate: Path) -> str | None:
    resolved = inside_root(root, candidate)
    if resolved is None:
        return None
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def resolve_tex_reference(
    root: Path,
    source: str,
    reference: str,
    main_path: str,
) -> str | None:
    value = reference.strip()
    if not value or any(token in value for token in ("\\", "#", "$")):
        return None
    candidate = Path(value)
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".tex")
    for base in ((root / source).parent, (root / main_path).parent, root):
        resolved = relative_posix(root, base / candidate)
        if resolved and (root / resolved).is_file():
            return resolved
    return None


def discover_tex_graph(root: Path, main_path: str | None) -> tuple[list[str], list[dict[str, str]]]:
    if not main_path:
        return [], []
    queue = [main_path]
    visited: list[str] = []
    edges: list[dict[str, str]] = []
    seen: set[str] = set()
    while queue:
        source = queue.pop(0)
        if source in seen:
            continue
        seen.add(source)
        visited.append(source)
        text = read_text(root, source)
        if text is None:
            continue
        for reference in INPUT_RE.findall(active_tex(text)):
            resolved = resolve_tex_reference(root, source, reference, main_path)
            edges.append(
                {
                    "source": source,
                    "reference": reference,
                    "resolved": resolved or "",
                }
            )
            if resolved and resolved not in seen:
                queue.append(resolved)
    return visited, edges


def confidence_for(scores: list[int]) -> str:
    if not scores:
        return "none"
    top = scores[0]
    gap = top - scores[1] if len(scores) > 1 else top
    if top >= 90 and gap >= 15:
        return "high"
    if top >= 55:
        return "medium"
    return "low"


def main_candidates(
    root: Path,
    paths: list[str],
    build_files: list[str],
) -> list[dict[str, Any]]:
    hint_paths = build_files + [path for path in paths if is_workflow_candidate(path)]
    hint_text = "\n".join(
        text for path in hint_paths if (text := read_text(root, path)) is not None
    )
    candidates: list[dict[str, Any]] = []
    for path in paths:
        if not path.lower().endswith(".tex"):
            continue
        text = read_text(root, path)
        if text is None:
            continue
        active = active_tex(text)
        if not DOCUMENTCLASS_RE.search(active) or not BEGIN_DOCUMENT_RE.search(active):
            continue
        pure = PurePosixPath(path)
        score = 0
        reasons: list[str] = []
        if path == "paper/main.tex":
            score += 150
            reasons.append("already uses the template canonical entrypoint")
        if pure.name == "main.tex":
            score += 75
            reasons.append("conventional main.tex name")
        elif pure.stem.lower() in {"paper", "manuscript", "submission", "article"}:
            score += 45
            reasons.append("paper-like entrypoint name")
        depth = len(pure.parts) - 1
        score += max(0, 30 - depth * 8)
        if depth == 0:
            reasons.append("repository-root entrypoint")
        if INPUT_RE.search(active):
            score += 12
            reasons.append("includes subordinate TeX files")
        if BIBLIOGRAPHY_RE.search(active) or ADD_BIBRESOURCE_RE.search(active):
            score += 10
            reasons.append("declares bibliography input")
        if path in hint_text or pure.name in hint_text:
            score += 35
            reasons.append("referenced by existing build or CI configuration")
        candidates.append({"path": path, "score": score, "evidence": reasons})
    return sorted(candidates, key=lambda item: (-int(item["score"]), str(item["path"])))


def bibliography_candidates(
    root: Path,
    paths: list[str],
    tex_paths: list[str],
    main_path: str | None,
) -> list[dict[str, Any]]:
    referenced: set[str] = set()
    reference_names: set[str] = set()
    for tex_path in tex_paths:
        text = read_text(root, tex_path)
        if text is None:
            continue
        active = active_tex(text)
        values: list[str] = []
        for group in BIBLIOGRAPHY_RE.findall(active):
            values.extend(part.strip() for part in group.split(","))
        values.extend(value.strip() for value in ADD_BIBRESOURCE_RE.findall(active))
        for value in values:
            if not value or any(token in value for token in ("\\", "#", "$")):
                continue
            candidate = Path(value)
            if candidate.suffix == "":
                candidate = candidate.with_suffix(".bib")
            reference_names.add(candidate.name)
            bases = [(root / tex_path).parent]
            if main_path:
                bases.append((root / main_path).parent)
            bases.append(root)
            for base in bases:
                resolved = relative_posix(root, base / candidate)
                if resolved and (root / resolved).is_file():
                    referenced.add(resolved)
    candidates: list[dict[str, Any]] = []
    for path in paths:
        if not path.lower().endswith(".bib"):
            continue
        pure = PurePosixPath(path)
        score = 0
        evidence: list[str] = []
        if path == "paper/refs.bib":
            score += 140
            evidence.append("already uses the template bibliography path")
        if path in referenced:
            score += 100
            evidence.append("referenced by the inferred TeX graph")
        elif pure.name in reference_names:
            score += 70
            evidence.append("filename referenced by TeX")
        if pure.name == "refs.bib":
            score += 45
            evidence.append("template-compatible refs.bib name")
        elif pure.name.lower() in {"references.bib", "bibliography.bib", "main.bib"}:
            score += 35
            evidence.append("conventional bibliography name")
        score += max(0, 15 - (len(pure.parts) - 1) * 3)
        candidates.append({"path": path, "score": score, "evidence": evidence})
    return sorted(candidates, key=lambda item: (-int(item["score"]), str(item["path"])))


def ranked_directories(paths: Iterable[str]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for path in paths:
        parent = PurePosixPath(path).parent.as_posix()
        counter[parent if parent != "." else "(root)"] += 1
    return [
        {"path": path, "count": count}
        for path, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def discover_experiment_surfaces(paths: Iterable[str]) -> list[dict[str, Any]]:
    """Rank conventional experiment/evaluation directories and explicit runner files."""
    counter: Counter[str] = Counter()
    for path in paths:
        pure = PurePosixPath(path)
        if not pure.parts or pure.parts[0] in {".agents", ".git", "dist", "paper", "releases"}:
            continue
        selected: str | None = None
        for index, part in enumerate(pure.parts[:-1]):
            if part.lower() in EXPERIMENT_DIRECTORY_NAMES:
                selected = PurePosixPath(*pure.parts[: index + 1]).as_posix()
                break
        if selected is None:
            stem = pure.stem.lower()
            if any(token in stem for token in EXPERIMENT_FILE_TOKENS):
                selected = path
        if selected is not None:
            counter[selected] += 1
    return [
        {"path": path, "count": count}
        for path, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def discover_table_files(root: Path, tex_paths: list[str], main_path: str | None) -> list[str]:
    tables: list[str] = []
    for path in tex_paths:
        if path == main_path:
            continue
        pure = PurePosixPath(path)
        text = read_text(root, path)
        active = active_tex(text) if text is not None else ""
        parent_parts = {part.lower() for part in pure.parts[:-1]}
        stem = pure.stem.lower()
        named_table_surface = bool(parent_parts & {"table", "tables"})
        generated_table = "generated" in parent_parts and TABLE_RE.search(active)
        table_like_name = (
            stem.startswith(("table_", "tab_")) or stem.endswith(("_table", "_tabular"))
        ) and TABLE_RE.search(active)
        if named_table_surface or generated_table or table_like_name:
            tables.append(path)
    return sorted(set(tables))


def discover_graphics(
    root: Path,
    tex_paths: list[str],
    main_path: str | None,
) -> tuple[list[str], list[str]]:
    resolved: list[str] = []
    unresolved: list[str] = []
    for tex_path in tex_paths:
        text = read_text(root, tex_path)
        if text is None:
            continue
        for value in GRAPHICS_RE.findall(active_tex(text)):
            reference = value.strip()
            if not reference or any(token in reference for token in ("\\", "#", "$")):
                continue
            candidate = Path(reference)
            variants = [candidate]
            if candidate.suffix == "":
                variants = [candidate.with_suffix(extension) for extension in sorted(IMAGE_EXTENSIONS)]
            found = False
            bases = [(root / tex_path).parent]
            if main_path:
                bases.append((root / main_path).parent)
            bases.append(root)
            for base in bases:
                for variant in variants:
                    relative = relative_posix(root, base / variant)
                    if relative and (root / relative).is_file():
                        resolved.append(relative)
                        found = True
                        break
                if found:
                    break
            if not found:
                unresolved.append(reference)
    return sorted(set(resolved)), sorted(set(unresolved))


def command_entrypoint(command: str) -> str | None:
    try:
        tokens = shlex.split(command, comments=True, posix=True)
    except ValueError:
        return None
    while tokens and "=" in tokens[0] and not tokens[0].startswith(("/", "./", "../")):
        tokens.pop(0)
    while tokens and PurePosixPath(tokens[0]).name in {"command", "env", "sudo"}:
        tokens.pop(0)
        while tokens and tokens[0].startswith("-"):
            tokens.pop(0)
        while tokens and "=" in tokens[0]:
            tokens.pop(0)
    if not tokens:
        return None
    executable = PurePosixPath(tokens[0]).name
    if executable in COMMAND_INTERPRETERS:
        return next((token for token in tokens[1:] if not token.startswith("-")), None)
    if executable == "make":
        for index, token in enumerate(tokens[1:], 1):
            if token in {"-f", "--file", "--makefile"} and index + 1 < len(tokens):
                return tokens[index + 1]
            if token.startswith(("--file=", "--makefile=")):
                return token.split("=", 1)[1]
        return None
    return tokens[0]


def readme_commands(text: str) -> list[str]:
    commands = re.findall(r"`([^`\n]+)`", text)
    commands.extend(
        line.strip()
        for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
        for line in block.splitlines()
        if line.strip()
    )
    return commands


def workflow_commands(text: str) -> list[str]:
    commands: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)(?:-\s*)?run:\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent, value = len(match.group(1)), match.group(2).strip()
        if value not in {"|", ">", "|-", ">-"}:
            commands.append(value.strip("'\""))
            index += 1
            continue
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                break
            if line.strip():
                commands.append(line.strip())
            index += 1
    return commands


def evidenced_command_paths(root: Path, paths: list[str]) -> set[str]:
    known = set(paths)
    evidenced: set[str] = set()
    for path in paths:
        is_readme = PurePosixPath(path).name.lower().startswith("readme")
        if not is_readme and not is_workflow_candidate(path):
            continue
        text = read_text(root, path)
        if text is None:
            continue
        commands = readme_commands(text) if is_readme else workflow_commands(text)
        for command in commands:
            for segment in re.split(r"(?:&&|\|\||;)", command):
                entrypoint = command_entrypoint(segment.strip())
                if not entrypoint or any(marker in entrypoint for marker in ("$", "{", "}")):
                    continue
                normalized = PurePosixPath(entrypoint.removeprefix("./")).as_posix()
                if normalized in known and (root / normalized).is_file():
                    evidenced.add(normalized)
    return evidenced


def discover_build_files(root: Path, paths: list[str]) -> list[str]:
    build_files = {path for path in paths if is_build_candidate(path)}
    build_files.update(evidenced_command_paths(root, paths))
    return sorted(build_files)


def inspect_repository(root: Path) -> dict[str, Any]:
    paths = tracked_and_untracked_paths(root)
    build_files = discover_build_files(root, paths)
    mains = main_candidates(root, paths, build_files)
    selected_main = str(mains[0]["path"]) if mains else None
    graph_paths, graph_edges = discover_tex_graph(root, selected_main)
    bibliography_scope = graph_paths if graph_paths else ([selected_main] if selected_main else [])
    bibliographies = bibliography_candidates(root, paths, bibliography_scope, selected_main)
    selected_bib = str(bibliographies[0]["path"]) if bibliographies else None
    table_paths = discover_table_files(root, graph_paths, selected_main)
    table_directories = ranked_directories(table_paths)
    section_paths = [
        path for path in graph_paths if path != selected_main and path not in set(table_paths)
    ]
    section_directories = ranked_directories(section_paths)
    graphics, unresolved_graphics = discover_graphics(root, graph_paths, selected_main)
    figure_directories = ranked_directories(graphics)
    style_paths = sorted(path for path in paths if PurePosixPath(path).suffix.lower() in {".sty", ".cls", ".bst"})
    style_directories = ranked_directories(style_paths)
    experiment_surfaces = discover_experiment_surfaces(paths)
    selected_experiment = (
        "EXPERIMENTS.md"
        if "EXPERIMENTS.md" in paths
        else (str(experiment_surfaces[0]["path"]) if experiment_surfaces else "")
    )
    workflows = sorted(path for path in paths if is_workflow_candidate(path))
    agent_files = ranked_agent_files(
        path
        for path in paths
        if path in AGENT_CANDIDATES
        or path.startswith(".cursor/rules/")
        or path.startswith(".github/instructions/")
    )
    selected_build = "Makefile" if "Makefile" in build_files else (build_files[0] if build_files else "")
    contracts = [
        {"path": path, "status": "present" if path in paths else "missing"}
        for path in CONTRACT_PATHS
    ]

    mappings = [
        {
            "template_surface": "paper/main.tex",
            "candidate": selected_main or "",
            "confidence": confidence_for([int(item["score"]) for item in mains]),
            "alternatives": [str(item["path"]) for item in mains[1:5]],
            "recommendation": (
                "Preserve the existing entrypoint first; prefer a thin paper/main.tex wrapper before moving authored files."
            ),
        },
        {
            "template_surface": "paper/refs.bib",
            "candidate": selected_bib or "",
            "confidence": confidence_for([int(item["score"]) for item in bibliographies]),
            "alternatives": [str(item["path"]) for item in bibliographies[1:5]],
            "recommendation": "Map the existing bibliography deliberately; do not duplicate or silently fork references.",
        },
        {
            "template_surface": "paper/sections/",
            "candidate": str(section_directories[0]["path"]) if section_directories else "",
            "confidence": "high" if section_directories and section_directories[0]["count"] >= 2 else ("medium" if section_directories else "none"),
            "alternatives": [str(item["path"]) for item in section_directories[1:5]],
            "recommendation": "Retain section identity and input order; rename or move only through reviewed, reversible steps.",
        },
        {
            "template_surface": "paper/figures/",
            "candidate": str(figure_directories[0]["path"]) if figure_directories else "",
            "confidence": "medium" if figure_directories else "none",
            "alternatives": [str(item["path"]) for item in figure_directories[1:5]],
            "recommendation": "Preserve source assets and wrapper relationships; do not infer missing figures from filenames alone.",
        },
        {
            "template_surface": "paper/tables/",
            "candidate": str(table_directories[0]["path"]) if table_directories else "",
            "confidence": "medium" if table_directories else "none",
            "alternatives": [str(item["path"]) for item in table_directories[1:5]],
            "recommendation": "Preserve table semantics and generation provenance; do not convert generated values into authored facts.",
        },
        {
            "template_surface": "paper/style/",
            "candidate": str(style_directories[0]["path"]) if style_directories else "",
            "confidence": "medium" if style_directories else "none",
            "alternatives": [str(item["path"]) for item in style_directories[1:5]],
            "recommendation": "Treat venue classes, styles, and bibliography styles as protected publication configuration.",
        },
        {
            "template_surface": "EXPERIMENTS.md",
            "candidate": selected_experiment,
            "confidence": (
                "high"
                if selected_experiment == "EXPERIMENTS.md"
                or (experiment_surfaces and int(experiment_surfaces[0]["count"]) >= 2)
                else ("medium" if experiment_surfaces else "none")
            ),
            "alternatives": (
                [str(item["path"]) for item in experiment_surfaces[:4]]
                if selected_experiment == "EXPERIMENTS.md"
                else [str(item["path"]) for item in experiment_surfaces[1:5]]
            ),
            "recommendation": (
                "Initialize the experiment contract from verified questions, conditions, artifacts, and interpretation boundaries; "
                "do not promote scripts or expected results into paper evidence."
            ),
        },
        {
            "template_surface": "Makefile",
            "candidate": selected_build,
            "confidence": "high" if "Makefile" in build_files else ("medium" if build_files else "none"),
            "alternatives": [path for path in build_files if path != selected_build][:4],
            "recommendation": "Merge template build targets into the existing build contract instead of replacing working commands.",
        },
        {
            "template_surface": ".github/workflows/",
            "candidate": workflows[0] if workflows else "",
            "confidence": "medium" if workflows else "none",
            "alternatives": workflows[1:5],
            "recommendation": "Integrate validation jobs with existing CI and branch protections; never replace CI wholesale.",
        },
        {
            "template_surface": "AGENTS.md",
            "candidate": agent_files[0] if agent_files else "",
            "confidence": "high" if "AGENTS.md" in agent_files else ("medium" if agent_files else "none"),
            "alternatives": agent_files[1:5],
            "recommendation": "Merge routing and safety rules with current Agent instructions; preserve project-specific knowledge.",
        },
    ]

    return {
        "schema_version": "paper-template-adoption-inspection-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "repository": {
            "root": str(root),
            "branch": current_branch(root),
            "head": head_commit(root),
            "worktree_clean": worktree_clean(root),
            "file_count": len(paths),
        },
        "main_candidates": mains[:10],
        "selected_main": selected_main,
        "tex_graph": {"files": graph_paths, "edges": graph_edges},
        "bibliography_candidates": bibliographies[:10],
        "selected_bibliography": selected_bib,
        "section_directories": section_directories[:10],
        "table_files": table_paths[:100],
        "table_directories": table_directories[:10],
        "graphics": {"resolved": graphics, "unresolved": unresolved_graphics},
        "figure_directories": figure_directories[:10],
        "style_files": style_paths[:100],
        "style_directories": style_directories[:10],
        "experiment_surfaces": experiment_surfaces[:20],
        "build_files": build_files,
        "workflows": workflows,
        "agent_instruction_files": agent_files,
        "contracts": contracts,
        "mappings": mappings,
    }


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_inspection(inspection: dict[str, Any]) -> str:
    repository = inspection["repository"]
    experiment_paths = [str(item["path"]) for item in inspection["experiment_surfaces"]]
    lines = [
        "# Template Adoption Inspection",
        "",
        f"- Repository root: `{repository['root']}`",
        f"- Branch: `{repository['branch']}`",
        f"- Head: `{repository['head'] or 'unborn'}`",
        f"- Worktree clean: `{str(repository['worktree_clean']).lower()}`",
        f"- Files considered: `{repository['file_count']}`",
        "",
        "## Inferred mappings",
        "",
        "| Template surface | Candidate | Confidence | Alternatives | Recommendation |",
        "|---|---|---|---|---|",
    ]
    for mapping in inspection["mappings"]:
        lines.append(
            "| {template_surface} | {candidate} | {confidence} | {alternatives} | {recommendation} |".format(
                template_surface=markdown_cell(mapping["template_surface"]),
                candidate=f"`{markdown_cell(mapping['candidate'])}`" if mapping["candidate"] else "—",
                confidence=markdown_cell(mapping["confidence"]),
                alternatives=(
                    ", ".join(
                        f"`{markdown_cell(path)}`" for path in mapping["alternatives"]
                    )
                    or "—"
                ),
                recommendation=markdown_cell(mapping["recommendation"]),
            )
        )
    lines.extend(["", "## Human contracts", ""])
    for contract in inspection["contracts"]:
        lines.append(f"- `{contract['path']}`: {contract['status']}")
    lines.extend(
        [
            "",
            "## Existing integration surfaces",
            "",
            f"- Build files: {', '.join(f'`{path}`' for path in inspection['build_files']) or 'none detected'}",
            f"- CI workflows: {', '.join(f'`{path}`' for path in inspection['workflows']) or 'none detected'}",
            f"- Agent instructions: {', '.join(f'`{path}`' for path in inspection['agent_instruction_files']) or 'none detected'}",
            f"- Experiment/evaluation surfaces: {', '.join(f'`{path}`' for path in experiment_paths) or 'none detected'}",
            "",
            "## Review boundary",
            "",
            "The inspection reports evidence and candidates. It does not authorize moving authored files, replacing build or CI logic, inventing Human contracts, or changing scientific meaning.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_inspection(root: Path, inspection: dict[str, Any], output: Path | None = None) -> Path:
    output = prepare_output_path(root, output, "inspection.json")
    markdown = output.with_suffix(".md")
    ensure_writable_file(markdown)
    output.write_text(json.dumps(inspection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown.write_text(render_inspection(inspection), encoding="utf-8")
    return output


def classify_path(
    *,
    path: str,
    target_mode: str,
    target_blob: bytes,
    downstream_kind: str,
    downstream_blob: bytes | None,
    downstream_mode: str | None,
    policy: dict[str, Any],
) -> tuple[str, str]:
    adoption = policy["adoption"]
    safe_paths = adoption["safe_paths"]
    safe_prefixes = adoption["safe_prefixes"]
    safe_sidecar = path_matches(path, safe_paths) or path_matches(path, safe_prefixes)
    if not path_matches(path, safe_paths) and path_matches(path, adoption["ignored_paths"]):
        return "ignored", "generated adoption/synchronization metadata or runtime output"
    if target_mode not in REGULAR_FILE_MODES:
        if safe_sidecar:
            return (
                "conflict",
                "template sidecar path is a symlink or non-regular file and cannot be installed mechanically",
            )
        return (
            "manual",
            "template path is a symlink or non-regular file and requires explicit review",
        )
    if downstream_kind == "other":
        return "conflict", "downstream path is a symlink or non-file entry"
    if safe_sidecar:
        if downstream_blob == target_blob and downstream_mode == target_mode:
            return "already", "downstream Agent-sidecar file already matches the template target"
        if downstream_kind == "missing":
            return "safe", "missing Agent-sidecar infrastructure may be installed mechanically"
        return (
            "conflict",
            "existing downstream Agent-sidecar content or executable mode differs from the template",
        )
    if path_matches(path, adoption["manual_paths"]):
        if downstream_blob == target_blob:
            return "manual", "protected surface matches the template bytes but still requires downstream semantic review"
        return "manual", "Human-authored, scientific, build, CI, publication, or project-specific surface"
    if downstream_blob == target_blob:
        return "manual", "matching unclassified template surface still requires explicit adoption review"
    return "manual", "unclassified template surface requires explicit semantic review"


def plan_adoption(
    root: Path,
    *,
    target_ref: str | None,
    fetch: bool,
    remote: str,
    url: str,
    branch: str,
) -> dict[str, Any]:
    if fetch:
        fetch_upstream(root, remote=remote, url=url, branch=branch)
    target_name = target_ref or f"{remote}/{branch}"
    target = resolve_commit(root, target_name)
    policy = target_inheritance_policy(root, target)
    entries = target_entries(root, target)
    entry_paths = {entry["path"] for entry in entries}
    missing_target_paths = sorted(set(policy["adoption"]["required_paths"]) - entry_paths)
    if missing_target_paths:
        raise AdoptionError(
            "selected template target does not contain adoption prerequisites: "
            + ", ".join(missing_target_paths)
        )
    inspection = inspect_repository(root)
    items: list[dict[str, Any]] = []
    for entry in entries:
        path = entry["path"]
        target_blob = blob_at(root, target, path)
        if target_blob is None:
            raise AdoptionError(f"cannot read template blob: {path}")
        downstream_kind, downstream_blob, downstream_mode = local_entry(root, path)
        category, reason = classify_path(
            path=path,
            target_mode=entry["mode"],
            target_blob=target_blob,
            downstream_kind=downstream_kind,
            downstream_blob=downstream_blob,
            downstream_mode=downstream_mode,
            policy=policy,
        )
        items.append(
            {
                "path": path,
                "mode": entry["mode"],
                "action": "add" if downstream_kind == "missing" else "review",
                "category": category,
                "reason": reason,
            }
        )
    counts = {category: 0 for category in ("safe", "already", "manual", "conflict", "ignored")}
    for item in items:
        counts[item["category"]] += 1
    return {
        "schema_version": "paper-template-adoption-plan-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "upstream": {"url": url, "remote": remote, "branch": branch},
        "target_ref": target_name,
        "target_commit": target,
        "downstream_head": head_commit(root),
        "downstream_branch": current_branch(root),
        "worktree_clean": worktree_clean(root),
        "counts": counts,
        "inspection": inspection,
        "items": items,
    }


def render_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Template Adoption Plan",
        "",
        f"- Template target: `{plan['target_commit']}` via `{plan['target_ref']}`",
        f"- Downstream head: `{plan['downstream_head'] or 'unborn'}`",
        f"- Downstream branch: `{plan['downstream_branch']}`",
        f"- Worktree clean: `{str(plan['worktree_clean']).lower()}`",
        "",
        "## Summary",
        "",
    ]
    for category in ("safe", "already", "manual", "conflict", "ignored"):
        lines.append(f"- {category}: {plan['counts'][category]}")
    lines.extend(
        [
            "",
            "## Inferred mappings",
            "",
            "| Template surface | Candidate | Confidence | Alternatives | Recommendation |",
            "|---|---|---|---|---|",
        ]
    )
    for mapping in plan["inspection"]["mappings"]:
        lines.append(
            "| {surface} | {candidate} | {confidence} | {alternatives} | {recommendation} |".format(
                surface=markdown_cell(mapping["template_surface"]),
                candidate=f"`{markdown_cell(mapping['candidate'])}`" if mapping["candidate"] else "—",
                confidence=markdown_cell(mapping["confidence"]),
                alternatives=(
                    ", ".join(
                        f"`{markdown_cell(path)}`" for path in mapping["alternatives"]
                    )
                    or "—"
                ),
                recommendation=markdown_cell(mapping["recommendation"]),
            )
        )
    lines.extend(
        [
            "",
            "## Template paths",
            "",
            "| Category | Action | Path | Reason |",
            "|---|---|---|---|",
        ]
    )
    for item in plan["items"]:
        lines.append(
            f"| {item['category']} | {item['action']} | `{markdown_cell(item['path'])}` | {markdown_cell(item['reason'])} |"
        )
    lines.extend(
        [
            "",
            "Only `safe` Agent-sidecar additions may be applied mechanically. Manual and conflict paths require repository-specific semantic migration; missing contracts must be initialized from evidence with unresolved questions left visible.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_plan(root: Path, plan: dict[str, Any], output: Path | None = None) -> Path:
    output = prepare_output_path(root, output, "plan.json")
    markdown = output.with_suffix(".md")
    inspection_path = output.parent / "inspection.json"
    inspection_markdown = inspection_path.with_suffix(".md")
    for path in (markdown, inspection_path, inspection_markdown):
        ensure_writable_file(path)
    output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown.write_text(render_plan(plan), encoding="utf-8")
    inspection_path.write_text(
        json.dumps(plan["inspection"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    inspection_markdown.write_text(render_inspection(plan["inspection"]), encoding="utf-8")
    return output


def read_json(path: Path, schema: str) -> dict[str, Any]:
    if path.is_symlink():
        raise AdoptionError(f"refusing to read symlinked control file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdoptionError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != schema:
        raise AdoptionError(f"unsupported or missing schema in {path}")
    return data


def validate_plan_upstream(root: Path, plan: dict[str, Any]) -> None:
    upstream = plan.get("upstream")
    if not isinstance(upstream, dict):
        raise AdoptionError("adoption plan requires an upstream object")
    values: dict[str, str] = {}
    for key in ("url", "remote", "branch"):
        value = upstream.get(key)
        if not isinstance(value, str) or not value.strip():
            raise AdoptionError(f"adoption plan upstream.{key} must be a non-empty string")
        values[key] = value

    configured = git(root, "remote", "get-url", values["remote"], check=False)
    if configured.returncode != 0:
        raise AdoptionError(
            f"missing planned template remote {values['remote']}; rerun plan --fetch"
        )
    if configured.stdout.strip() != values["url"]:
        raise AdoptionError(
            f"planned template remote {values['remote']} points to {configured.stdout.strip()}, "
            f"expected {values['url']}"
        )

    target = resolve_commit(root, str(plan.get("target_commit", "")))
    branch_target = resolve_commit(root, f"{values['remote']}/{values['branch']}")
    reachable = git(
        root,
        "merge-base",
        "--is-ancestor",
        target,
        branch_target,
        check=False,
    )
    if reachable.returncode != 0:
        raise AdoptionError(
            "planned template target is not reachable from the configured upstream branch"
        )


def validate_apply_plan_items(root: Path, plan: dict[str, Any], target: str) -> None:
    policy = target_inheritance_policy(root, target)
    inspection = plan.get("inspection")
    if not isinstance(inspection, dict):
        raise AdoptionError("adoption plan requires an inspection object")
    current_inspection = inspect_repository(root)
    if inspection_fingerprint(inspection) != inspection_fingerprint(current_inspection):
        raise AdoptionError(
            "adoption inspection no longer matches the repository; regenerate the plan"
        )

    entries = target_entries(root, target)
    entries_by_path = {entry["path"]: entry for entry in entries}
    missing_target_paths = sorted(
        set(policy["adoption"]["required_paths"]) - set(entries_by_path)
    )
    if missing_target_paths:
        raise AdoptionError(
            "selected template target does not contain adoption prerequisites: "
            + ", ".join(missing_target_paths)
        )
    raw_items = plan.get("items")
    if not isinstance(raw_items, list) or not all(isinstance(item, dict) for item in raw_items):
        raise AdoptionError("adoption plan items must be a list of objects")

    item_paths = [str(item.get("path", "")) for item in raw_items]
    if len(item_paths) != len(set(item_paths)):
        raise AdoptionError("adoption plan contains duplicate template paths")
    if set(item_paths) != set(entries_by_path):
        raise AdoptionError(
            "adoption plan path set no longer matches the selected template target; regenerate the plan"
        )

    recomputed_counts = {
        category: 0 for category in ("safe", "already", "manual", "conflict", "ignored")
    }
    for item in raw_items:
        path = str(item["path"])
        entry = entries_by_path[path]
        target_blob = blob_at(root, target, path)
        if target_blob is None:
            raise AdoptionError(f"cannot read template blob while validating plan: {path}")
        downstream_kind, downstream_blob, downstream_mode = local_entry(root, path)
        category, reason = classify_path(
            path=path,
            target_mode=entry["mode"],
            target_blob=target_blob,
            downstream_kind=downstream_kind,
            downstream_blob=downstream_blob,
            downstream_mode=downstream_mode,
            policy=policy,
        )
        action = "add" if downstream_kind == "missing" else "review"
        expected = {
            "path": path,
            "mode": entry["mode"],
            "action": action,
            "category": category,
            "reason": reason,
        }
        actual = {key: item.get(key) for key in expected}
        if actual != expected:
            raise AdoptionError(
                f"adoption plan classification no longer matches the repository for {path}; "
                "regenerate the plan"
            )
        recomputed_counts[category] += 1

    if plan.get("counts") != recomputed_counts:
        raise AdoptionError("adoption plan counts are inconsistent; regenerate the plan")


def export_bytes(destination: Path, data: bytes | None, *, deleted_message: str) -> None:
    if data is None:
        marker = destination.with_suffix(destination.suffix + ".missing")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(deleted_message + "\n", encoding="utf-8")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def sync_provenance(config: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(config)


def reviewed_provenance_is_compatible(root: Path, config: dict[str, Any]) -> bool:
    adoption = config["adoption"]
    upstream = config["upstream"]
    baseline = config.get("last_synced_commit")
    if not isinstance(baseline, str):
        return False
    configured = git(root, "remote", "get-url", upstream["remote"], check=False)
    if configured.returncode != 0 or configured.stdout.strip() != upstream["url"]:
        return False
    branch_tip = git(
        root,
        "rev-parse",
        "--verify",
        f"{upstream['remote']}/{upstream['branch']}^{{commit}}",
        check=False,
    )
    if branch_tip.returncode != 0:
        return False
    target = adoption["target_commit"]
    for candidate in (target, baseline):
        reachable = git(
            root,
            "merge-base",
            "--is-ancestor",
            candidate,
            branch_tip.stdout.strip(),
            check=False,
        )
        if reachable.returncode != 0:
            return False
    return git(root, "merge-base", "--is-ancestor", target, baseline, check=False).returncode == 0


def consistent_pending_adoption(
    existing: dict[str, Any],
    adoption: Any,
    upstream: dict[str, str],
    target: str,
) -> bool:
    return bool(
        isinstance(adoption, dict)
        and adoption.get("status") == "in_progress"
        and adoption.get("target_commit") == target
        and existing.get("last_synced_commit") is None
        and existing.get("last_synced_at") is None
        and not any(
            key in adoption
            for key in ("reviewed_at", "verification_repository_fingerprint")
        )
        and all(
            existing["upstream"][key] == upstream[key]
            for key in ("url", "remote", "branch")
        )
    )


def pending_sync_config(
    root: Path,
    plan: dict[str, Any],
    *,
    recover_reviewed: bool,
) -> dict[str, Any]:
    existing = read_existing_sync_config(root)
    adoption = existing.get("adoption") if existing else None
    if isinstance(adoption, dict) and adoption.get("status") == "reviewed":
        if reviewed_provenance_is_compatible(root, existing):
            raise AdoptionError(
                "a legitimate reviewed template baseline already exists; "
                "use template-sync instead of template adoption"
            )
        if not recover_reviewed:
            raise AdoptionError(
                "existing reviewed adoption provenance is invalid, unreachable, or incompatible; "
                "review its provenance and rerun apply with --recover-reviewed"
            )
    upstream = plan["upstream"]
    recovering = False
    if existing is not None:
        existing_upstream = existing["upstream"]
        same_pending = consistent_pending_adoption(
            existing, adoption, upstream, str(plan["target_commit"])
        )
        recovering = not same_pending and (
            existing.get("last_synced_commit") is not None
            or isinstance(adoption, dict)
            or any(existing_upstream[key] != upstream[key] for key in ("url", "remote", "branch"))
        )
        if recovering and not recover_reviewed:
            raise AdoptionError(
                "existing baseline or adoption metadata is not trustworthy evidence of completed adoption; "
                "review its provenance and rerun apply with --recover-reviewed"
            )
    always_manual = list(existing.get("always_manual", [])) if existing else []
    ignored_paths = list(existing.get("ignored_paths", [])) if existing else []
    prior_sync_history = []
    if isinstance(adoption, dict):
        prior_sync_history = list(adoption.get("prior_sync_history", []))
    if existing is not None and recovering:
        prior_sync_history.append(sync_provenance(existing))
    return {
        "adoption": {
            "prior_sync_history": prior_sync_history,
            "status": "in_progress",
            "target_commit": plan["target_commit"],
        },
        "always_manual": always_manual,
        "ignored_paths": ignored_paths,
        "last_sync_note": (
            "Template adoption is in progress against "
            f"{plan['target_commit']}; finalize only after semantic review and validation."
        ),
        "last_synced_at": None,
        "last_synced_commit": None,
        "reference_integrity": {"adopted": False},
        "schema_version": "paper-template-sync-v1",
        "upstream": {
            "branch": upstream["branch"],
            "remote": upstream["remote"],
            "url": upstream["url"],
        },
    }


def write_pending_sync_config(
    root: Path,
    plan: dict[str, Any],
    *,
    recover_reviewed: bool,
) -> None:
    config = pending_sync_config(root, plan, recover_reviewed=recover_reviewed)
    path = ensure_directory_path(root, Path(".agents"), create=True) / "template-sync.json"
    ensure_writable_file(path)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    git(root, "add", "--", SYNC_CONFIG_RELATIVE.as_posix())


def apply_plan(root: Path, plan_path: Path, *, recover_reviewed: bool) -> None:
    ensure_safe_apply_context(root)
    plan = read_json(plan_path, "paper-template-adoption-plan-v1")
    validate_plan_upstream(root, plan)
    if current_branch(root) != plan.get("downstream_branch"):
        raise AdoptionError(
            "downstream branch changed after plan creation; regenerate the adoption plan"
        )
    current = head_commit(root)
    if current != plan.get("downstream_head"):
        raise AdoptionError("downstream HEAD moved after plan creation; regenerate the adoption plan")
    target = resolve_commit(root, str(plan["target_commit"]))
    if target != plan["target_commit"]:
        raise AdoptionError("template target no longer resolves to the planned commit")
    validate_apply_plan_items(root, plan, target)
    pending_sync_config(root, plan, recover_reviewed=recover_reviewed)

    runtime = runtime_directory(root, create=True)
    bundle = runtime / "merge-bundle"
    if bundle.is_symlink():
        raise AdoptionError("refusing to replace symlinked adoption merge bundle")
    if bundle.exists() and not bundle.is_dir():
        raise AdoptionError("adoption merge-bundle path is not a directory")
    if bundle.exists():
        import shutil

        shutil.rmtree(bundle)
    safe_count = 0
    review_count = 0
    for item in plan["items"]:
        path = str(item["path"])
        category = str(item["category"])
        if category == "safe":
            git(root, "restore", "--source", target, "--staged", "--worktree", "--", path)
            safe_count += 1
        elif category in {"manual", "conflict"}:
            upstream = blob_at(root, target, path)
            downstream_kind, downstream, _ = local_entry(root, path)
            export_bytes(
                bundle / "upstream" / path,
                upstream,
                deleted_message="This path does not exist in the selected template revision.",
            )
            export_bytes(
                bundle / "downstream" / path,
                downstream,
                deleted_message=(
                    "This downstream path is not a regular file."
                    if downstream_kind == "other"
                    else "This path does not currently exist downstream."
                ),
            )
            review_count += 1
    if review_count:
        bundle.mkdir(parents=True, exist_ok=True)
        (bundle / "README.md").write_text(
            "# Template Adoption Merge Bundle\n\n"
            "`upstream/` contains the selected template surfaces and `downstream/` contains current files when present. "
            "Use the inspection mappings and preserve scientific meaning, build behavior, CI policy, venue configuration, and project-specific Agent knowledge.\n",
            encoding="utf-8",
        )
        (bundle / "mappings.md").write_text(
            render_inspection(plan["inspection"]), encoding="utf-8"
        )
    write_pending_sync_config(root, plan, recover_reviewed=recover_reviewed)
    print(
        f"OK template_adoption applied_safe={safe_count} "
        f"review_bundle={review_count} pending_sync_config=1"
    )


def validate_installation(root: Path) -> None:
    ensure_directory_path(root, Path(".agents"), create=False)
    policy = inheritance_policy(root)
    required = (
        ADOPTION_TOOL_RELATIVE,
        ADOPTION_SKILL_RELATIVE,
        Path(".agents/tools/template-sync.py"),
        Path(".agents/skills/template-sync/SKILL.md"),
        Path(".agents/runtime/.gitignore"),
    )
    for relative in required:
        path = root / relative
        if (
            has_unsafe_parent(root, relative.as_posix())
            or path.is_symlink()
            or not path.is_file()
        ):
            raise AdoptionError(f"missing adoption prerequisite: {relative.as_posix()}")
    for relative in policy["adoption"]["required_paths"]:
        path = root / relative
        if has_unsafe_parent(root, relative) or path.is_symlink() or not path.is_file():
            raise AdoptionError(f"missing adoption prerequisite: {relative}")
    text = (root / ADOPTION_SKILL_RELATIVE).read_text(encoding="utf-8")
    for heading in ("## Trigger", "## Minimum context", "## Procedure", "## Safety boundary"):
        if heading not in text:
            raise AdoptionError(f"template adoption skill missing heading: {heading}")
    print("OK template_adoption installation")


def command_record(command: list[str], result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "command": shlex.join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


def expected_verification_commands(*, variants: bool) -> list[list[str]]:
    commands = [["bash", ".agents/tools/verify.sh"]]
    if variants:
        for variant in ("draft", "anonymous", "camera-ready", "arxiv"):
            commands.append(["make", "pdf", f"VARIANT={variant}"])
    return commands


def verify_adoption(root: Path, *, plan_path: Path, variants: bool) -> int:
    if not plan_path.is_file():
        raise AdoptionError("missing adoption plan; run plan before verification")
    plan = read_json(plan_path, "paper-template-adoption-plan-v1")
    validate_plan_upstream(root, plan)
    if current_branch(root) != plan.get("downstream_branch"):
        raise AdoptionError(
            "downstream branch changed after plan creation; regenerate the adoption plan"
        )
    verify = root / ".agents/tools/verify.sh"
    if not verify.is_file():
        raise AdoptionError("missing .agents/tools/verify.sh; apply the safe sidecar set first")
    if variants:
        if not (root / "Makefile").is_file():
            raise AdoptionError("cannot verify variants without a downstream Makefile")
    commands = expected_verification_commands(variants=variants)

    checks: list[dict[str, Any]] = []
    for command in commands:
        result = run(command, cwd=root, check=False)
        checks.append(command_record(command, result))
        status = "OK" if result.returncode == 0 else "FAILED"
        print(f"{status} template_adoption verify: {shlex.join(command)}")
        if result.returncode != 0:
            if result.stdout:
                print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")

    inspection = inspect_repository(root)
    report = {
        "schema_version": "paper-template-adoption-verification-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "downstream_head": head_commit(root),
        "downstream_branch": current_branch(root),
        "target_commit": plan["target_commit"],
        "plan_fingerprint": json_fingerprint(plan),
        "inspection_fingerprint": inspection_fingerprint(inspection),
        "variants_verified": variants,
        "repository_fingerprint": repository_fingerprint(root),
        "success": all(check["success"] for check in checks),
        "checks": checks,
    }
    runtime = runtime_directory(root, create=True)
    verification_json = runtime / "verification.json"
    verification_markdown = runtime / "verification.md"
    ensure_writable_file(verification_json)
    ensure_writable_file(verification_markdown)
    verification_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = ["# Template Adoption Verification", ""]
    for check in checks:
        lines.append(f"- {'PASS' if check['success'] else 'FAIL'}: `{check['command']}`")
    lines.append("")
    lines.append(f"Publication variants verified: `{str(variants).lower()}`")
    lines.append(f"Repository fingerprint: `{report['repository_fingerprint']}`")
    lines.append(f"Overall success: `{str(report['success']).lower()}`")
    verification_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if report["success"] else 1


def assess_adoption(root: Path, *, plan_path: Path) -> int:
    if not plan_path.is_file():
        raise AdoptionError("missing adoption plan; run plan before assessment")
    plan = read_json(plan_path, "paper-template-adoption-plan-v1")
    validate_plan_upstream(root, plan)
    checks: list[dict[str, Any]] = []
    for raw_command in ASSESSMENT_COMMANDS:
        command = list(raw_command)
        result = run(command, cwd=root, check=False)
        checks.append(command_record(command, result))
        print(
            f"{'OK' if result.returncode == 0 else 'FAILED'} "
            f"template_adoption assess: {shlex.join(command)}"
        )
    report = {
        "schema_version": "paper-template-adoption-assessment-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "authorizes_finalize": False,
        "downstream_head": head_commit(root),
        "downstream_branch": current_branch(root),
        "target_commit": plan["target_commit"],
        "plan_fingerprint": json_fingerprint(plan),
        "repository_fingerprint": repository_fingerprint(root),
        "success": all(check["success"] for check in checks),
        "checks": checks,
    }
    runtime = runtime_directory(root, create=True)
    assessment_json = runtime / "assessment.json"
    assessment_markdown = runtime / "assessment.md"
    ensure_writable_file(assessment_json)
    ensure_writable_file(assessment_markdown)
    assessment_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Template Adoption Assessment",
        "",
        "This collect-all diagnostic report cannot authorize finalization.",
        "",
    ]
    lines.extend(
        f"- {'PASS' if check['success'] else 'FAIL'}: `{check['command']}`" for check in checks
    )
    lines.extend(["", f"Overall success: `{str(report['success']).lower()}`"])
    assessment_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if report["success"] else 1


def require_current_full_verification(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    path = runtime_directory(root, create=False) / "verification.json"
    if not path.is_file():
        raise AdoptionError("missing adoption verification report; run verify --variants before finalize")
    report = read_json(path, "paper-template-adoption-verification-v1")
    if not report.get("success"):
        raise AdoptionError("the latest adoption verification report is not successful")
    if not report.get("variants_verified"):
        raise AdoptionError("finalize requires successful verification of all publication variants")
    checks = report.get("checks")
    expected_commands = [
        shlex.join(command) for command in expected_verification_commands(variants=True)
    ]
    if not isinstance(checks, list) or [check.get("command") for check in checks if isinstance(check, dict)] != expected_commands:
        raise AdoptionError("verification report does not contain the complete expected command set")
    if not all(
        isinstance(check, dict)
        and check.get("success") is True
        and check.get("returncode") == 0
        for check in checks
    ):
        raise AdoptionError("verification report contains an unsuccessful or malformed command result")
    if report.get("target_commit") != plan.get("target_commit"):
        raise AdoptionError("verification report targets a different template commit; rerun verify --variants")
    if report.get("plan_fingerprint") != json_fingerprint(plan):
        raise AdoptionError("adoption plan changed since verification; rerun verify --variants")
    if current_branch(root) != plan.get("downstream_branch"):
        raise AdoptionError("downstream branch changed after planning; regenerate the adoption plan")
    if report.get("downstream_branch") != current_branch(root):
        raise AdoptionError("downstream branch changed since verification; rerun verify --variants")
    if report.get("downstream_head") != head_commit(root):
        raise AdoptionError("downstream HEAD changed since verification; rerun verify --variants")
    current = repository_fingerprint(root)
    if report.get("repository_fingerprint") != current:
        raise AdoptionError("downstream repository changed since verification; rerun verify --variants")
    inspection = inspect_repository(root)
    if report.get("inspection_fingerprint") != inspection_fingerprint(inspection):
        raise AdoptionError("downstream inspection changed since verification; rerun verify --variants")
    return report


def require_paper_ready_inspection(root: Path) -> dict[str, Any]:
    inspection = inspect_repository(root)
    missing_contracts = [
        str(contract["path"])
        for contract in inspection["contracts"]
        if contract["status"] != "present"
    ]
    missing: list[str] = []
    if not inspection.get("selected_main"):
        missing.append("a supported TeX paper entrypoint")
    if missing_contracts:
        missing.append("Human contracts: " + ", ".join(missing_contracts))
    if missing:
        raise AdoptionError(
            "adoption cannot finalize a materially non-paper-first repository; missing "
            + "; ".join(missing)
        )
    return inspection


def read_existing_sync_config(root: Path) -> dict[str, Any] | None:
    path = ensure_directory_path(root, Path(".agents"), create=False) / "template-sync.json"
    if path.is_symlink():
        raise AdoptionError("refusing to read symlinked .agents/template-sync.json")
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdoptionError(f"invalid existing template sync configuration: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "paper-template-sync-v1":
        raise AdoptionError("existing .agents/template-sync.json has an unsupported schema")
    baseline = data.get("last_synced_commit")
    if baseline is not None and (
        not isinstance(baseline, str)
        or len(baseline) != 40
        or any(character not in "0123456789abcdef" for character in baseline)
    ):
        raise AdoptionError("existing template sync baseline must be null or a lowercase 40-character SHA")
    for key in ("always_manual", "ignored_paths"):
        values = data.get(key, [])
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise AdoptionError(f"existing template sync {key} must be a list of path strings")
        for value in values:
            candidate = PurePosixPath(value)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise AdoptionError(f"unsafe path in existing template sync {key}: {value}")
    upstream = data.get("upstream")
    if not isinstance(upstream, dict):
        raise AdoptionError("existing template sync configuration requires an upstream object")
    for key in ("url", "remote", "branch"):
        value = upstream.get(key)
        if not isinstance(value, str) or not value.strip():
            raise AdoptionError(f"existing template sync upstream.{key} must be a non-empty string")
    adoption = data.get("adoption")
    if adoption is not None:
        if not isinstance(adoption, dict) or adoption.get("status") not in {
            "in_progress",
            "reviewed",
        }:
            raise AdoptionError("existing template sync adoption.status is invalid")
        target = adoption.get("target_commit")
        if not isinstance(target, str) or len(target) != 40 or any(
            character not in "0123456789abcdef" for character in target
        ):
            raise AdoptionError("existing template sync adoption target must be a lowercase 40-character SHA")
        history = adoption.get("prior_sync_history", [])
        if not isinstance(history, list) or not all(isinstance(item, dict) for item in history):
            raise AdoptionError("existing template sync adoption prior_sync_history must be a list of objects")
        if adoption["status"] == "reviewed":
            fingerprint = adoption.get("verification_repository_fingerprint")
            if (
                not isinstance(adoption.get("reviewed_at"), str)
                or not isinstance(fingerprint, str)
                or len(fingerprint) != 64
                or any(character not in "0123456789abcdef" for character in fingerprint)
            ):
                raise AdoptionError("existing reviewed adoption state is incomplete or inconsistent")
    return data


def finalize_adoption(
    root: Path,
    *,
    plan_path: Path,
    reviewed: bool,
    note: str | None,
) -> None:
    if not reviewed:
        raise AdoptionError("finalize requires --reviewed after semantic migration and validation")
    ensure_non_default_branch(root)
    validate_installation(root)
    plan = read_json(plan_path, "paper-template-adoption-plan-v1")
    validate_plan_upstream(root, plan)
    target = resolve_commit(root, str(plan["target_commit"]))
    existing = read_existing_sync_config(root)
    adoption = existing.get("adoption") if existing else None
    if existing is None or not consistent_pending_adoption(
        existing, adoption, plan["upstream"], target
    ):
        raise AdoptionError(
            "finalize requires consistent in-progress adoption state for the exact target; "
            "review contradictory provenance and rerun apply with --recover-reviewed"
        )
    require_current_full_verification(root, plan)
    require_paper_ready_inspection(root)
    if verify_adoption(root, plan_path=plan_path, variants=True) != 0:
        raise AdoptionError("mandatory full-variant verification failed during finalize")
    report = require_current_full_verification(root, plan)
    always_manual = list(existing.get("always_manual", [])) if existing else []
    ignored_paths = list(existing.get("ignored_paths", [])) if existing else []
    upstream = plan["upstream"]
    config = {
        "adoption": {
            "prior_sync_history": list(adoption.get("prior_sync_history", [])),
            "reviewed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "status": "reviewed",
            "target_commit": target,
            "verification_repository_fingerprint": report["repository_fingerprint"],
        },
        "always_manual": always_manual,
        "ignored_paths": ignored_paths,
        "last_sync_note": note or "Reviewed initial adoption from an existing paper repository.",
        "last_synced_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "last_synced_commit": target,
        "reference_integrity": (
            existing.get("reference_integrity", {"adopted": False})
            if existing
            else {"adopted": False}
        ),
        "schema_version": "paper-template-sync-v1",
        "upstream": {
            "branch": upstream["branch"],
            "remote": upstream["remote"],
            "url": upstream["url"],
        },
    }
    path = ensure_directory_path(root, Path(".agents"), create=True) / "template-sync.json"
    ensure_writable_file(path)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    git(root, "add", "--", SYNC_CONFIG_RELATIVE.as_posix())
    runtime = runtime_directory(root, create=True)
    finalization_path = runtime / "finalization.json"
    ensure_writable_file(finalization_path)
    finalization_path.write_text(
        json.dumps(
            {
                "schema_version": "paper-template-adoption-finalization-v1",
                "created_at": config["last_synced_at"],
                "target_commit": target,
                "downstream_head": head_commit(root),
                "downstream_branch": current_branch(root),
                "reviewed": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"OK template_adoption finalized baseline={target}")


def show_status(root: Path) -> None:
    print(f"downstream_branch: {current_branch(root)}")
    print(f"downstream_head: {head_commit(root) or 'unborn'}")
    print(f"worktree_clean: {str(worktree_clean(root)).lower()}")
    plan_path = runtime_directory(root, create=False) / "plan.json"
    if plan_path.is_file():
        plan = read_json(plan_path, "paper-template-adoption-plan-v1")
        print(f"planned_target: {plan['target_commit']}")
        for category in ("safe", "already", "manual", "conflict", "ignored"):
            print(f"planned_{category}: {plan['counts'][category]}")
    else:
        print("planned_target: none")
    config = read_existing_sync_config(root)
    print(
        "recorded_template_baseline: "
        + (str(config.get("last_synced_commit") or "uninitialized") if config else "absent")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--upstream-url", default=DEFAULT_UPSTREAM_URL)
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--branch", default=DEFAULT_UPSTREAM_BRANCH)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")
    subparsers.add_parser("status")
    subparsers.add_parser("fetch")

    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("--output", type=Path)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--target-ref")
    plan.add_argument("--fetch", action="store_true")
    plan.add_argument("--output", type=Path)

    apply = subparsers.add_parser("apply")
    apply.add_argument("--plan", type=Path)
    apply.add_argument(
        "--recover-reviewed",
        action="store_true",
        help="resume an incomplete adoption after reviewing stale baseline provenance",
    )

    verify = subparsers.add_parser("verify")
    verify.add_argument("--plan", type=Path)
    verify.add_argument("--variants", action="store_true")

    assess = subparsers.add_parser("assess")
    assess.add_argument("--plan", type=Path)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--plan", type=Path)
    finalize.add_argument("--reviewed", action="store_true")
    finalize.add_argument("--note")
    return parser


def resolve_runtime_path(root: Path, value: Path | None, default_name: str) -> Path:
    if value is None:
        return runtime_directory(root, create=False) / default_name
    if value.is_absolute():
        return value
    candidate = PurePosixPath(value.as_posix())
    if ".." in candidate.parts:
        raise AdoptionError(f"unsafe relative control-file path: {value}")
    normalized = candidate.as_posix()
    if has_unsafe_parent(root, normalized):
        raise AdoptionError(f"control-file path has a symlinked or non-directory parent: {value}")
    return root / normalized


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.expanduser().resolve()
    try:
        ensure_git_repository(root)
        if args.command == "validate":
            validate_installation(root)
        elif args.command == "status":
            show_status(root)
        elif args.command == "fetch":
            fetch_upstream(
                root,
                remote=args.remote,
                url=args.upstream_url,
                branch=args.branch,
            )
        elif args.command == "inspect":
            inspection = inspect_repository(root)
            output = write_inspection(root, inspection, args.output)
            print(render_inspection(inspection), end="")
            print(f"Inspection written to {output.relative_to(root) if output.is_relative_to(root) else output}")
        elif args.command == "plan":
            plan = plan_adoption(
                root,
                target_ref=args.target_ref,
                fetch=args.fetch,
                remote=args.remote,
                url=args.upstream_url,
                branch=args.branch,
            )
            output = write_plan(root, plan, args.output)
            print(render_plan(plan), end="")
            print(f"Plan written to {output.relative_to(root) if output.is_relative_to(root) else output}")
        elif args.command == "apply":
            plan_path = resolve_runtime_path(root, args.plan, "plan.json")
            apply_plan(root, plan_path, recover_reviewed=args.recover_reviewed)
        elif args.command == "verify":
            plan_path = resolve_runtime_path(root, args.plan, "plan.json")
            return verify_adoption(root, plan_path=plan_path, variants=args.variants)
        elif args.command == "assess":
            plan_path = resolve_runtime_path(root, args.plan, "plan.json")
            return assess_adoption(root, plan_path=plan_path)
        elif args.command == "finalize":
            plan_path = resolve_runtime_path(root, args.plan, "plan.json")
            finalize_adoption(
                root,
                plan_path=plan_path,
                reviewed=args.reviewed,
                note=args.note,
            )
        return 0
    except AdoptionError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
