#!/usr/bin/env python3
"""Load the repository-local LaTeX source and build profile."""
from __future__ import annotations

import copy
import ctypes
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

PROFILE_RELATIVE = Path(".agents/paper-build.json")
PROFILE_SCHEMA = "paper-build-profile-v1"
PROFILE_COMMAND_TIMEOUT_SECONDS = 30 * 60
LAYOUTS = {"canonical-variants", "external-latex"}
FORBIDDEN_SOURCE_ROOTS = {".agents", "dist", "release", "releases"}
BUILD_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

CANONICAL_BUILDS: list[dict[str, Any]] = [
    {
        "name": "draft",
        "command": ["make", "pdf", "VARIANT=draft"],
        "output": "paper/main.pdf",
    },
    {
        "name": "anonymous",
        "command": ["make", "pdf", "VARIANT=anonymous"],
        "output": "paper/main-anonymous.pdf",
    },
    {
        "name": "camera-ready",
        "command": ["make", "pdf", "VARIANT=camera-ready"],
        "output": "paper/main-camera-ready.pdf",
    },
    {
        "name": "arxiv",
        "command": ["make", "pdf", "VARIANT=arxiv"],
        "output": "paper/main-arxiv.pdf",
    },
]

LEGACY_PROFILE: dict[str, Any] = {
    "schema_version": PROFILE_SCHEMA,
    "layout": "canonical-variants",
    "source_root": "paper",
    "entrypoint": "paper/main.tex",
    "bibliography": "paper/refs.bib",
    "builds": copy.deepcopy(CANONICAL_BUILDS),
}


class ProfileError(ValueError):
    pass


def safe_path(value: Any, label: str, *, allow_dot: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ProfileError(f"{label} must be a non-empty relative path")
    normalized = PurePosixPath(value).as_posix()
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ProfileError(f"{label} must be a safe repository-relative path")
    if normalized == "." and not allow_dot:
        raise ProfileError(f"{label} must name a repository file")
    return normalized


def validate_profile(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != PROFILE_SCHEMA:
        raise ProfileError(f"unsupported {PROFILE_RELATIVE.as_posix()} schema_version")
    layout = data.get("layout")
    if layout not in LAYOUTS:
        raise ProfileError(
            f"paper build profile layout must be one of: {', '.join(sorted(LAYOUTS))}"
        )
    source_root = safe_path(data.get("source_root"), "source_root", allow_dot=True)
    entrypoint = safe_path(data.get("entrypoint"), "entrypoint")
    source = PurePosixPath(source_root)
    entry = PurePosixPath(entrypoint)
    if entry.suffix.lower() != ".tex":
        raise ProfileError("entrypoint must name a .tex source file")
    if source_root != "." and entry != source and source not in entry.parents:
        raise ProfileError("entrypoint must be inside source_root")

    bibliography_value = data.get("bibliography")
    bibliography = (
        None
        if bibliography_value is None
        else safe_path(bibliography_value, "bibliography")
    )
    if bibliography is not None:
        bib_path = PurePosixPath(bibliography)
        if bib_path.suffix.lower() != ".bib":
            raise ProfileError("bibliography must name a .bib file")
        if source_root != "." and bib_path != source and source not in bib_path.parents:
            raise ProfileError("bibliography must be inside source_root")
    for label, value in (
        ("source_root", source_root),
        ("entrypoint", entrypoint),
        ("bibliography", bibliography),
    ):
        parts = PurePosixPath(value).parts if value is not None else ()
        if parts and parts[0] in FORBIDDEN_SOURCE_ROOTS:
            raise ProfileError(f"{label} must not use a generated or Agent-control surface")

    builds = data.get("builds")
    if not isinstance(builds, list) or not builds:
        raise ProfileError("paper build profile requires at least one build")
    normalized_builds: list[dict[str, Any]] = []
    names: set[str] = set()
    outputs: set[str] = set()
    for index, build in enumerate(builds):
        if not isinstance(build, dict):
            raise ProfileError(f"builds[{index}] must be an object")
        name = build.get("name")
        if not isinstance(name, str) or not BUILD_NAME_RE.fullmatch(name):
            raise ProfileError(f"builds[{index}].name is invalid")
        if name in names:
            raise ProfileError(f"duplicate paper build name: {name}")
        names.add(name)
        command = build.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(argument, str) and argument and "\x00" not in argument for argument in command
        ):
            raise ProfileError(f"builds[{index}].command must be a non-empty argv list without NUL bytes")
        executable = PurePosixPath(command[0])
        if executable.is_absolute() or ".." in executable.parts:
            raise ProfileError(f"builds[{index}].command executable must be repository-local or on PATH")
        output_value = build.get("output")
        output = None if output_value is None else safe_path(output_value, f"builds[{index}].output")
        if output is not None and output in outputs:
            raise ProfileError(f"duplicate paper build output: {output}")
        if output is not None:
            protected = {
                entrypoint,
                bibliography,
                PROFILE_RELATIVE.as_posix(),
            }
            if (
                output in protected
                or output.startswith(".agents/")
                or PurePosixPath(output).parts[0] in {"release", "releases"}
            ):
                raise ProfileError(f"build output collides with a protected source path: {output}")
            outputs.add(output)
        normalized_builds.append(
            {
                "name": name,
                "command": list(command),
                **({"output": output} if output is not None else {}),
            }
        )

    normalized = {
        "schema_version": PROFILE_SCHEMA,
        "layout": layout,
        "source_root": source_root,
        "entrypoint": entrypoint,
        "bibliography": bibliography,
        "builds": normalized_builds,
    }
    if layout == "canonical-variants":
        expected = {
            "source_root": "paper",
            "entrypoint": "paper/main.tex",
            "bibliography": "paper/refs.bib",
            "builds": CANONICAL_BUILDS,
        }
        for key, value in expected.items():
            if normalized[key] != value:
                raise ProfileError(
                    f"canonical-variants profile must use the standard {key} declaration"
                )
    return normalized


def load_profile(root: Path) -> dict[str, Any]:
    path = root / PROFILE_RELATIVE
    if not path.exists() and not path.is_symlink():
        return copy.deepcopy(LEGACY_PROFILE)
    if path.is_symlink() or not path.is_file():
        raise ProfileError(f"{PROFILE_RELATIVE.as_posix()} must be a regular file")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileError(f"invalid {PROFILE_RELATIVE.as_posix()}: {exc}") from exc
    return validate_profile(data)


def has_symlink_component(root: Path, value: str) -> bool:
    current = root
    for part in PurePosixPath(value).parts:
        if part == ".":
            continue
        current = current / part
        if current.is_symlink():
            return True
    return False


def path_is_contained(root: Path, value: str) -> bool:
    try:
        return (root / value).resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def active_tex(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        comment_at = len(line)
        for index, character in enumerate(line):
            if character != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                comment_at = index
                break
        lines.append(line[:comment_at])
    return "\n".join(lines)


def ensure_profile_paths(root: Path, profile: dict[str, Any]) -> None:
    checks = [
        ("source_root", profile["source_root"], True),
        ("entrypoint", profile["entrypoint"], False),
    ]
    if profile["bibliography"] is not None:
        checks.append(("bibliography", profile["bibliography"], False))
    for label, value, directory in checks:
        path = root / value
        expected_type = path.is_dir() if directory else path.is_file()
        if has_symlink_component(root, value) or not path_is_contained(root, value):
            raise ProfileError(f"{label} must not traverse a symlink or leave the repository")
        if not expected_type:
            kind = "directory" if directory else "file"
            raise ProfileError(f"{label} does not name an existing {kind}: {value}")
    try:
        entrypoint_text = (root / profile["entrypoint"]).read_text(encoding="utf-8")
    except OSError as exc:
        raise ProfileError(f"cannot read entrypoint: {profile['entrypoint']}") from exc
    if not re.search(r"\\(?:documentclass|input|include)\b", active_tex(entrypoint_text)):
        raise ProfileError(
            "entrypoint must contain a document declaration or include another TeX source"
        )


def verification_steps(root: Path) -> list[dict[str, Any]]:
    profile = load_profile(root)
    ensure_profile_paths(root, profile)
    return [dict(build) for build in profile["builds"]]


def output_is_ready(root: Path, value: str) -> bool:
    artifact = root / value
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", value],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", "--", value],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return (
            not has_symlink_component(root, value)
            and path_is_contained(root, value)
            and tracked.returncode != 0
            and ignored.returncode == 0
            and artifact.is_file()
            and artifact.stat().st_size > 0
        )
    except OSError:
        return False


def isolate_output(root: Path, value: str) -> Path | None:
    artifact = root / value
    if has_symlink_component(root, value) or not path_is_contained(root, value):
        raise ProfileError("build output must not traverse a symlink or leave the repository")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", value],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if tracked.returncode == 0:
        raise ProfileError(f"build output must not be a tracked file: {value}")
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", value],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if ignored.returncode != 0:
        raise ProfileError(f"build output must be ignored by Git: {value}")
    if artifact.is_symlink():
        raise ProfileError(f"build output is not a regular file: {value}")
    if not artifact.exists():
        return None
    if not artifact.is_file():
        raise ProfileError(f"build output is not a regular file: {value}")
    backup_directory = Path(tempfile.mkdtemp(prefix="paper-build-backup-"))
    backup = backup_directory / artifact.name
    try:
        shutil.copy2(artifact, backup)
        artifact.unlink()
    except OSError:
        shutil.rmtree(backup_directory, ignore_errors=True)
        raise
    return backup


def finish_output(
    root: Path,
    value: str,
    backup: Path | None,
    *,
    command_succeeded: bool,
) -> bool:
    artifact = root / value
    parent_value = PurePosixPath(value).parent.as_posix()
    backup_directory = backup.parent if backup is not None else None
    try:
        if backup is not None:
            current = root
            for part in PurePosixPath(parent_value).parts:
                if part == ".":
                    continue
                current = current / part
                if current.is_symlink():
                    current.unlink()
                elif os.path.lexists(current) and not current.is_dir():
                    current.unlink()
                if not current.exists():
                    current.mkdir()
        if has_symlink_component(root, parent_value) or not path_is_contained(root, parent_value):
            raise ProfileError("build output path became unsafe after the command; refusing cleanup")
        ready = command_succeeded and output_is_ready(root, value)
        if ready:
            if backup_directory is not None:
                shutil.rmtree(backup_directory)
            return True

        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", value],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if tracked.returncode == 0:
            unstaged = subprocess.run(
                ["git", "rm", "--cached", "--quiet", "--ignore-unmatch", "--", value],
                cwd=root,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
            )
            if unstaged.returncode != 0:
                detail = unstaged.stderr.strip() or "unknown Git error"
                raise ProfileError(
                    f"cannot remove failed build output from Git index: {value}: {detail}"
                )
        if artifact.is_symlink() or artifact.is_file():
            artifact.unlink()
        elif artifact.is_dir():
            try:
                shutil.rmtree(artifact)
            except OSError as exc:
                raise ProfileError(
                    f"cannot clean failed build output directory: {value}"
                ) from exc
        elif os.path.lexists(artifact):
            artifact.unlink()
        if backup is not None:
            artifact.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(backup), artifact)
        return False
    except (OSError, ProfileError) as exc:
        if backup is not None and backup.exists():
            raise ProfileError(
                f"cannot restore previous build output; backup retained at {backup}"
            ) from exc
        raise
    finally:
        if backup_directory is not None and (backup is None or not backup.exists()):
            shutil.rmtree(backup_directory, ignore_errors=True)


def _run_profile_subprocess(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    if sys.platform != "linux":
        raise ProfileError("safe paper build process supervision currently requires Linux")
    previous_subreaper_state = _child_subreaper_enabled()
    if previous_subreaper_state is None:
        raise ProfileError("cannot inspect Linux child-subreaper state for paper build")
    result: subprocess.CompletedProcess[str] | None = None
    primary_error: BaseException | None = None
    primary_traceback = None
    restore_error: BaseException | None = None
    restored = True
    try:
        try:
            if not previous_subreaper_state and not _enable_child_subreaper():
                raise ProfileError(
                    "cannot enable Linux child-subreaper supervision for paper build"
                )
            result = _run_profile_subprocess_as_subreaper(
                command,
                cwd=cwd,
                env=env,
                timeout_seconds=timeout_seconds,
            )
        except BaseException as exc:
            primary_error = exc
            primary_traceback = exc.__traceback__
    finally:
        if not previous_subreaper_state:
            try:
                restored = _set_child_subreaper(False)
            except BaseException as exc:
                restored = False
                restore_error = exc

    if primary_error is not None:
        if not restored:
            if restore_error is None:
                restore_error = ProfileError(
                    "cannot restore Linux child-subreaper state after paper build"
                )
            raise primary_error.with_traceback(primary_traceback) from restore_error
        raise primary_error.with_traceback(primary_traceback)
    if not restored:
        if restore_error is not None:
            raise restore_error
        raise ProfileError("cannot restore Linux child-subreaper state after paper build")
    if result is None:
        raise ProfileError("paper build command ended without a result")
    return result


def _run_profile_subprocess_as_subreaper(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    baseline_descendants = _descendant_process_ids(os.getpid())
    if baseline_descendants:
        raise ProfileError(
            "cannot safely supervise a build while unrelated child processes are active"
        )
    with tempfile.TemporaryDirectory(prefix="paper-build-output-") as directory:
        stdout_path = Path(directory) / "stdout"
        stderr_path = Path(directory) / "stderr"
        with stdout_path.open("w+", encoding="utf-8") as stdout_file, stderr_path.open(
            "w+", encoding="utf-8"
        ) as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                text=True,
                stdout=stdout_file,
                stderr=stderr_file,
                env=env,
                start_new_session=True,
            )
            try:
                process.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired as exc:
                _terminate_profile_process_group(
                    process,
                    baseline_descendants=baseline_descendants,
                )
                process.wait()
                stdout_file.flush()
                stderr_file.flush()
                stdout = stdout_path.read_bytes().decode("utf-8", errors="replace")
                stderr = stderr_path.read_bytes().decode("utf-8", errors="replace")
                raise subprocess.TimeoutExpired(
                    command,
                    timeout_seconds,
                    output=stdout if stdout else exc.output,
                    stderr=stderr if stderr else exc.stderr,
                ) from exc
            except BaseException:
                _terminate_profile_process_group(
                    process,
                    baseline_descendants=baseline_descendants,
                )
                raise
            if _owned_profile_process_ids(process, baseline_descendants):
                _terminate_profile_process_group(
                    process,
                    baseline_descendants=baseline_descendants,
                )
            stdout_file.flush()
            stderr_file.flush()
            return subprocess.CompletedProcess(
                command,
                process.returncode,
                stdout_path.read_bytes().decode("utf-8", errors="replace"),
                stderr_path.read_bytes().decode("utf-8", errors="replace"),
            )


def _enable_child_subreaper() -> bool:
    return _set_child_subreaper(True)


def _set_child_subreaper(enabled: bool) -> bool:
    if sys.platform != "linux":
        return False
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        return libc.prctl(36, int(enabled), 0, 0, 0) == 0  # PR_SET_CHILD_SUBREAPER
    except (AttributeError, OSError):
        return False


def _child_subreaper_enabled() -> bool | None:
    if sys.platform != "linux":
        return None
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        enabled = ctypes.c_int()
        if libc.prctl(37, ctypes.byref(enabled), 0, 0, 0) != 0:  # PR_GET_CHILD_SUBREAPER
            return None
        return bool(enabled.value)
    except (AttributeError, OSError):
        return None


def _terminate_profile_process_group(
    process: subprocess.Popen[str],
    *,
    baseline_descendants: set[int] | None = None,
) -> None:
    if os.name != "posix":
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return

    descendants = _owned_profile_process_ids(process, baseline_descendants)
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    for pid in descendants:
        if pid == process.pid:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    try:
        process.wait(timeout=0.1)
    except subprocess.TimeoutExpired:
        pass
    new_descendants = _owned_profile_process_ids(process, baseline_descendants) - descendants
    descendants.update(new_descendants)
    for pid in new_descendants:
        if pid == process.pid:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    deadline = time.monotonic() + 1
    quiet_scans = 0
    cleaned = False
    while time.monotonic() < deadline:
        _reap_profile_children(descendants, process.pid)
        new_descendants = _owned_profile_process_ids(process, baseline_descendants) - descendants
        descendants.update(new_descendants)
        for pid in new_descendants:
            if pid == process.pid:
                continue
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        alive = {pid for pid in descendants if _process_exists(pid)}
        if process.poll() is not None and not alive:
            quiet_scans += 1
            if quiet_scans >= 2:
                cleaned = True
                break
        else:
            quiet_scans = 0
        time.sleep(0.05)

    if not cleaned:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.kill()
            except ProcessLookupError:
                pass

        deadline = time.monotonic() + 1
        quiet_scans = 0
        while time.monotonic() < deadline:
            descendants.update(_owned_profile_process_ids(process, baseline_descendants))
            for pid in descendants:
                if pid == process.pid:
                    continue
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            _reap_profile_children(descendants, process.pid)
            alive = {pid for pid in descendants if _process_exists(pid)}
            if process.poll() is not None and not alive:
                quiet_scans += 1
                if quiet_scans >= 2:
                    break
            else:
                quiet_scans = 0
            time.sleep(0.05)

    if process.poll() is None:
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    remaining = _owned_profile_process_ids(process, baseline_descendants)
    for pid in remaining:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if remaining:
        time.sleep(0.05)
        _reap_profile_children(remaining, process.pid)
    survivors = {
        pid
        for pid in _owned_profile_process_ids(process, baseline_descendants)
        if _process_exists(pid)
    }
    if survivors:
        raise ProfileError("paper build left descendant processes running after cleanup")


def _owned_profile_process_ids(
    process: subprocess.Popen[str], baseline_descendants: set[int] | None
) -> set[int]:
    owned = _descendant_process_ids(process.pid)
    if baseline_descendants is not None:
        owned.update(_descendant_process_ids(os.getpid()) - baseline_descendants)
    return owned


def _reap_profile_children(process_ids: set[int], root_pid: int) -> None:
    for pid in process_ids:
        if pid == root_pid:
            continue
        try:
            os.waitpid(pid, os.WNOHANG)
        except (ChildProcessError, OSError):
            pass


def _descendant_process_ids(parent_pid: int) -> set[int]:
    if sys.platform == "linux":
        return _proc_descendant_process_ids(parent_pid)
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,ppid="],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    children: dict[int, set[int]] = {}
    for line in result.stdout.splitlines():
        try:
            pid_text, parent_text = line.split()
            pid, parent = int(pid_text), int(parent_text)
        except ValueError:
            continue
        children.setdefault(parent, set()).add(pid)
    descendants: set[int] = set()
    pending = list(children.get(parent_pid, ()))
    while pending:
        pid = pending.pop()
        if pid in descendants:
            continue
        descendants.add(pid)
        pending.extend(children.get(pid, ()))
    return descendants


def _proc_descendant_process_ids(parent_pid: int) -> set[int]:
    descendants: set[int] = set()
    pending = list(_proc_child_process_ids(parent_pid))
    while pending:
        pid = pending.pop()
        if pid in descendants:
            continue
        descendants.add(pid)
        pending.extend(_proc_child_process_ids(pid))
    return descendants


def _proc_child_process_ids(parent_pid: int) -> set[int]:
    task_root = Path("/proc") / str(parent_pid) / "task"
    children: set[int] = set()
    try:
        tasks = list(task_root.iterdir())
    except OSError:
        return children
    for task in tasks:
        try:
            children.update(
                int(value)
                for value in (task / "children").read_text(encoding="ascii").split()
            )
        except (OSError, ValueError):
            continue
    return children


def _process_exists(pid: int) -> bool:
    if sys.platform == "linux":
        try:
            stat = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8")
            return stat.rsplit(")", 1)[1].split()[0] != "Z"
        except FileNotFoundError:
            return False
        except (OSError, IndexError):
            pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _timeout_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_profile_command(
    root: Path,
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    output: str | None = None,
    timeout_seconds: float = PROFILE_COMMAND_TIMEOUT_SECONDS,
) -> tuple[subprocess.CompletedProcess[str], bool]:
    backup = isolate_output(root, output) if output is not None else None
    result: subprocess.CompletedProcess[str] | None = None
    output_ready = True
    try:
        try:
            result = _run_profile_subprocess(
                command,
                cwd=root,
                env=env,
                timeout_seconds=timeout_seconds,
            )
        except OSError as exc:
            result = subprocess.CompletedProcess(
                command,
                127,
                stdout="",
                stderr=f"cannot start command: {exc}",
            )
        except subprocess.TimeoutExpired as exc:
            stderr = _timeout_stream(exc.stderr)
            timeout_detail = f"command timed out after {timeout_seconds:g} seconds"
            result = subprocess.CompletedProcess(
                command,
                124,
                stdout=_timeout_stream(exc.stdout),
                stderr=(stderr + "\n" + timeout_detail).lstrip("\n"),
            )
    finally:
        if output is not None:
            output_ready = finish_output(
                root,
                output,
                backup,
                command_succeeded=result is not None and result.returncode == 0,
            )
    if result is None:
        raise ProfileError("paper build command ended without a result")
    return result, output_ready


def is_canonical(profile: dict[str, Any]) -> bool:
    return profile["layout"] == "canonical-variants"
