#!/usr/bin/env python3
"""Download, stage, and smoke-test official journal LaTeX templates."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from _paper_profile import run_profile_command


@dataclass(frozen=True)
class RemoteFile:
    name: str
    url: str
    sha256: str


@dataclass(frozen=True)
class JournalTemplate:
    name: str
    files: tuple[RemoteFile, ...]
    archive: str | None
    sample_root: str | None
    entrypoint: str
    output: str


SPRINGER_VERSION = "v12"
JMLR_COMMIT = "f413f638b407af76074813f8f88a82a7a5a81e9d"

JOURNAL_TEMPLATES: tuple[JournalTemplate, ...] = (
    JournalTemplate(
        name="springer-nature",
        files=(
            RemoteFile(
                name="springer-v12",
                url=(
                    "https://cms-resources.apps.public.k8s.springernature.io/"
                    "springer-cms/rest/v1/content/18782940/data/v12"
                ),
                sha256="812e76dcaa9c28dc1bff1fb6065d51729b67d4ea140552a05088317414a3ecae",
            ),
        ),
        archive="springer-v12",
        sample_root="sn-article-template",
        entrypoint="sn-article.tex",
        output="sn-article.pdf",
    ),
    JournalTemplate(
        name="aas",
        files=(
            RemoteFile(
                name="aastex702.zip",
                url="https://journals.aas.org/wp-content/uploads/2026/06/aastex702.zip",
                sha256="008ed27b62a3b1689a256a53893df05080cd01b754b206f4833f864cb16fc25f",
            ),
        ),
        archive="aastex702.zip",
        sample_root=None,
        entrypoint="sample702.tex",
        output="sample702.pdf",
    ),
    JournalTemplate(
        name="iop",
        files=(
            RemoteFile(
                name="ioplatextemplate.zip",
                url="https://publishingsupport.iopscience.iop.org/wp-content/uploads/2025/07/ioplatextemplate.zip",
                sha256="796c337cc2099a86e736bf86b5d5b17f66f1b29441bb5dfc3272ff3819ce7114",
            ),
        ),
        archive="ioplatextemplate.zip",
        sample_root=None,
        entrypoint="iopjournal-template.tex",
        output="iopjournal-template.pdf",
    ),
    JournalTemplate(
        name="jmlr",
        files=(
            RemoteFile(
                name="jmlr2e.sty",
                url=(
                    "https://raw.githubusercontent.com/JmlrOrg/jmlr-style-file/"
                    f"{JMLR_COMMIT}/jmlr2e.sty"
                ),
                sha256="a430a875d561235951800e4e21d2631e18ddf0b369646ec276f43ea5080f27c3",
            ),
            RemoteFile(
                name="sample.tex",
                url=(
                    "https://raw.githubusercontent.com/JmlrOrg/jmlr-style-file/"
                    f"{JMLR_COMMIT}/sample.tex"
                ),
                sha256="19f563441b9b288333851cc9f63be8d9e8bd6b10bd672271a598b74f6e2903e2",
            ),
            RemoteFile(
                name="sample.bib",
                url=(
                    "https://raw.githubusercontent.com/JmlrOrg/jmlr-style-file/"
                    f"{JMLR_COMMIT}/sample.bib"
                ),
                sha256="89e88007d9d80c206c103c1fe8cdaa4e3e56757b310fc28448a0763869036e1c",
            ),
        ),
        archive=None,
        sample_root=None,
        entrypoint="sample.tex",
        output="sample.pdf",
    ),
    JournalTemplate(
        name="plos-one",
        files=(
            RemoteFile(
                name="PLOS_latex_template.zip",
                url="https://journals.plos.org/plosone/s/file?id=1457/PLOS_latex_template.zip",
                sha256="ea3a8a0fdbac77f95de47639541b09ef1583e059ace6783367490af9fa0b9a60",
            ),
        ),
        archive="PLOS_latex_template.zip",
        sample_root=None,
        entrypoint="plos_latex_template.tex",
        output="plos_latex_template.pdf",
    ),
)


class JournalTemplateError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(remote: RemoteFile, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / remote.name
    if destination.is_file() and _sha256(destination) == remote.sha256:
        return destination
    if destination.exists():
        destination.unlink()

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{remote.name}.", dir=cache_dir)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        request = urllib.request.Request(
            remote.url,
            headers={"User-Agent": "ccfa-writing-paper-template journal smoke test"},
        )
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        actual = _sha256(temporary)
        if actual != remote.sha256:
            raise JournalTemplateError(
                f"SHA-256 mismatch for {remote.name}: expected {remote.sha256}, got {actual}"
            )
        temporary.replace(destination)
        return destination
    finally:
        if temporary.exists():
            temporary.unlink()


def _safe_member_path(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise JournalTemplateError(f"unsafe path in official package: {name}")
    target = (root / Path(*relative.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise JournalTemplateError(f"unsafe path in official package: {name}")
    return target


def _extract(archive: Path, destination: Path) -> None:
    try:
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                target = _safe_member_path(destination, member.filename)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if member.external_attr >> 16 & 0o170000 == 0o120000:
                    raise JournalTemplateError(
                        f"symlink in official package is not supported: {member.filename}"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    except zipfile.BadZipFile as exc:
        raise JournalTemplateError(f"official package is not a ZIP archive: {archive.name}") from exc


def _copy_tree_contents(source: Path, destination: Path) -> None:
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def _stage(template: JournalTemplate, cache_dir: Path, destination: Path) -> None:
    downloads = {remote.name: _download(remote, cache_dir) for remote in template.files}
    if template.archive is None:
        for remote in template.files:
            shutil.copy2(downloads[remote.name], destination / remote.name)
        return

    extracted = destination / ".package"
    extracted.mkdir()
    _extract(downloads[template.archive], extracted)
    source = extracted / template.sample_root if template.sample_root else extracted
    if not source.is_dir():
        raise JournalTemplateError(
            f"official package {template.name} has no sample directory: {template.sample_root}"
        )
    _copy_tree_contents(source, destination)
    if template.name == "springer-nature":
        bst_directory = destination / "bst"
        if bst_directory.is_dir():
            for style in bst_directory.glob("*.bst"):
                shutil.copy2(style, destination / style.name)


def smoke_test(template: JournalTemplate, cache_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix=f"ccfa-{template.name}-") as directory:
        stage = Path(directory)
        _stage(template, cache_dir, stage)
        packaged_output = stage / template.output
        if packaged_output.is_symlink() or packaged_output.is_file():
            packaged_output.unlink()
        command = [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            template.entrypoint,
        ]
        result, _ = run_profile_command(stage, command, timeout_seconds=180)
        if result.returncode == 124:
            raise JournalTemplateError(f"{template.name} smoke test timed out")
        if result.returncode != 0:
            raise JournalTemplateError(
                f"{template.name} smoke test failed (exit {result.returncode})\n"
                f"{result.stdout}\n{result.stderr}"
            )
        output = stage / template.output
        if not output.is_file() or output.stat().st_size == 0:
            raise JournalTemplateError(
                f"{template.name} smoke test did not create a non-empty {template.output}"
            )
        if output.read_bytes()[:5] != b"%PDF-":
            raise JournalTemplateError(f"{template.name} output is not a PDF: {template.output}")


def run_smoke_matrix(cache_dir: Path, templates: Iterable[JournalTemplate] = JOURNAL_TEMPLATES) -> dict[str, str]:
    failures: dict[str, str] = {}
    for template in templates:
        try:
            smoke_test(template, cache_dir)
        except (JournalTemplateError, OSError, subprocess.SubprocessError) as exc:
            failures[template.name] = str(exc)
    return failures
