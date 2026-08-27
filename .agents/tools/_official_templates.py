#!/usr/bin/env python3
"""Download, stage, and smoke-test official LaTeX templates."""
from __future__ import annotations

import hashlib
import json
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
    sha256: str | None = None


@dataclass(frozen=True)
class OfficialTemplate:
    name: str
    venue: str
    identity: str
    authority_url: str
    files: tuple[RemoteFile, ...]
    archive: str | None
    sample_root: str | None
    entrypoint: str
    output: str
    latexmk_mode: str = "-pdf"


OFFICIAL_TEMPLATES: tuple[OfficialTemplate, ...] = (
    OfficialTemplate(
        name="springer-nature",
        venue="Springer Nature journals",
        identity="v12 (December 2024)",
        authority_url="https://www.springernature.com/gp/authors/campaigns/latex-author-support",
        files=(
            RemoteFile(
                name="springer-v12",
                url=(
                    "https://cms-resources.apps.public.k8s.springernature.io/"
                    "springer-cms/rest/v1/content/18782940/data/v12"
                ),
            ),
        ),
        archive="springer-v12",
        sample_root="sn-article-template",
        entrypoint="sn-article.tex",
        output="sn-article.pdf",
        latexmk_mode="-pdfps",
    ),
    OfficialTemplate(
        name="aas",
        venue="AAS journals",
        identity="AASTeX 7.0.2",
        authority_url="https://journals.aas.org/aastex-package-for-manuscript-preparation/",
        files=(
            RemoteFile(
                name="aastex702.zip",
                url="https://journals.aas.org/wp-content/uploads/2026/06/aastex702.zip",
            ),
        ),
        archive="aastex702.zip",
        sample_root=None,
        entrypoint="sample702.tex",
        output="sample702.pdf",
    ),
    OfficialTemplate(
        name="iop",
        venue="IOP journals",
        identity="July 2025 package",
        authority_url="https://publishingsupport.iopscience.iop.org/questions/latex-template/",
        files=(
            RemoteFile(
                name="ioplatextemplate.zip",
                url="https://publishingsupport.iopscience.iop.org/wp-content/uploads/2025/07/ioplatextemplate.zip",
            ),
        ),
        archive="ioplatextemplate.zip",
        sample_root=None,
        entrypoint="iopjournal-template.tex",
        output="iopjournal-template.pdf",
    ),
    OfficialTemplate(
        name="jmlr",
        venue="JMLR",
        identity="current official master branch",
        authority_url="https://www.jmlr.org/format/format.html",
        files=(
            RemoteFile(
                name="jmlr-style-file-master.zip",
                url=(
                    "https://github.com/JmlrOrg/jmlr-style-file/"
                    "archive/refs/heads/master.zip"
                ),
            ),
        ),
        archive="jmlr-style-file-master.zip",
        sample_root="jmlr-style-file-master",
        entrypoint="sample.tex",
        output="sample.pdf",
    ),
    OfficialTemplate(
        name="plos-one",
        venue="PLOS ONE",
        identity="current PLOS ONE package",
        authority_url="https://journals.plos.org/plosone/s/latex",
        files=(
            RemoteFile(
                name="PLOS_latex_template.zip",
                url="https://journals.plos.org/plosone/s/file?id=1457/PLOS_latex_template.zip",
            ),
        ),
        archive="PLOS_latex_template.zip",
        sample_root=None,
        entrypoint="plos_latex_template.tex",
        output="plos_latex_template.pdf",
    ),
    OfficialTemplate(
        name="icml-2026",
        venue="ICML",
        identity="2026",
        authority_url="https://icml.cc/Conferences/2026/AuthorInstructions",
        files=(
            RemoteFile(
                name="icml2026.zip",
                url="https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip",
            ),
        ),
        archive="icml2026.zip",
        sample_root=None,
        entrypoint="example_paper.tex",
        output="example_paper.pdf",
    ),
    OfficialTemplate(
        name="iclr-2026",
        venue="ICLR",
        identity="2026",
        authority_url="https://iclr.cc/Conferences/2026/AuthorGuide",
        files=(
            RemoteFile(
                name="iclr2026.zip",
                url="https://github.com/ICLR/Master-Template/raw/master/iclr2026.zip",
            ),
        ),
        archive="iclr2026.zip",
        sample_root="iclr2026",
        entrypoint="iclr2026_conference.tex",
        output="iclr2026_conference.pdf",
    ),
    OfficialTemplate(
        name="neurips-2026",
        venue="NeurIPS",
        identity="2026",
        authority_url="https://neurips.cc/Conferences/2026/CallForPapers",
        files=(
            RemoteFile(
                name="Formatting_Instructions_For_NeurIPS_2026.zip",
                url=(
                    "https://media.neurips.cc/Conferences/NeurIPS2026/"
                    "Formatting_Instructions_For_NeurIPS_2026.zip"
                ),
            ),
        ),
        archive="Formatting_Instructions_For_NeurIPS_2026.zip",
        sample_root=None,
        entrypoint="neurips_2026.tex",
        output="neurips_2026.pdf",
    ),
    OfficialTemplate(
        name="acl-2026",
        venue="ACL",
        identity="2026 using the current official rolling files",
        authority_url="https://2026.aclweb.org/calls/main_conference_papers/",
        files=(
            RemoteFile(
                name="acl-style-files-master.zip",
                url="https://github.com/acl-org/acl-style-files/archive/refs/heads/master.zip",
            ),
        ),
        archive="acl-style-files-master.zip",
        sample_root="acl-style-files-master",
        entrypoint="acl_latex.tex",
        output="acl_latex.pdf",
    ),
    OfficialTemplate(
        name="aaai-2026",
        venue="AAAI",
        identity="Author Kit 2026.1",
        authority_url="https://aaai.org/conference/aaai/aaai-26/submission-instructions/",
        files=(
            RemoteFile(
                name="AuthorKit26-1.zip",
                url="https://aaai.org/wp-content/uploads/2025/07/AuthorKit26-1.zip",
            ),
        ),
        archive="AuthorKit26-1.zip",
        sample_root="AuthorKit26/AnonymousSubmission/LaTeX",
        entrypoint="anonymous-submission-latex-2026.tex",
        output="anonymous-submission-latex-2026.pdf",
    ),
)


class OfficialTemplateError(RuntimeError):
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
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise OfficialTemplateError(
            f"official template cache path is not a regular file: {destination}"
        )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{remote.name}.", dir=cache_dir
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        request = urllib.request.Request(
            remote.url,
            headers={
                "User-Agent": "ccfa-writing-paper-template official template smoke test"
            },
        )
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open(
            "wb"
        ) as handle:
            shutil.copyfileobj(response, handle)
        actual = _sha256(temporary)
        if remote.sha256 is not None and actual != remote.sha256:
            raise OfficialTemplateError(
                f"SHA-256 mismatch for {remote.name}: expected {remote.sha256}, got {actual}"
            )
        temporary.replace(destination)
        _record_digest(remote, destination, actual)
        print(f"OK official_template_source {remote.name} sha256={actual} url={remote.url}")
        return destination
    finally:
        if temporary.exists():
            temporary.unlink()


def _record_digest(remote: RemoteFile, path: Path, actual: str) -> None:
    record = path.with_name(path.name + ".sha256.json")
    payload = {
        "schema_version": "official-template-download-v1",
        "name": remote.name,
        "url": remote.url,
        "sha256": actual,
    }
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{record.name}.", dir=record.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary.replace(record)
    finally:
        if temporary.exists():
            temporary.unlink()


def _safe_member_path(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise OfficialTemplateError(f"unsafe path in official package: {name}")
    target = (root / Path(*relative.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise OfficialTemplateError(f"unsafe path in official package: {name}")
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
                    raise OfficialTemplateError(
                        f"symlink in official package is not supported: {member.filename}"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    except zipfile.BadZipFile as exc:
        raise OfficialTemplateError(
            f"official package is not a ZIP archive: {archive.name}"
        ) from exc


def _copy_tree_contents(source: Path, destination: Path) -> None:
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def _stage(template: OfficialTemplate, cache_dir: Path, destination: Path) -> None:
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
        raise OfficialTemplateError(
            f"official package {template.name} has no sample directory: {template.sample_root}"
        )
    _copy_tree_contents(source, destination)
    if template.name == "springer-nature":
        bst_directory = destination / "bst"
        if bst_directory.is_dir():
            for style in bst_directory.glob("*.bst"):
                shutil.copy2(style, destination / style.name)


def smoke_test(template: OfficialTemplate, cache_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix=f"ccfa-{template.name}-") as directory:
        stage = Path(directory)
        _stage(template, cache_dir, stage)
        packaged_output = stage / template.output
        if packaged_output.is_symlink() or packaged_output.is_file():
            packaged_output.unlink()
        command = [
            "latexmk",
            "-norc",
            template.latexmk_mode,
            "-no-shell-escape",
            "-interaction=nonstopmode",
            "-halt-on-error",
            template.entrypoint,
        ]
        result, _ = run_profile_command(stage, command, timeout_seconds=180)
        if result.returncode == 124:
            raise OfficialTemplateError(f"{template.name} smoke test timed out")
        if result.returncode != 0:
            raise OfficialTemplateError(
                f"{template.name} smoke test failed (exit {result.returncode})\n"
                f"{result.stdout}\n{result.stderr}"
            )
        output = stage / template.output
        if not output.is_file() or output.stat().st_size == 0:
            raise OfficialTemplateError(
                f"{template.name} smoke test did not create a non-empty {template.output}"
            )
        if output.read_bytes()[:5] != b"%PDF-":
            raise OfficialTemplateError(
                f"{template.name} output is not a PDF: {template.output}"
            )


def run_smoke_matrix(
    cache_dir: Path, templates: Iterable[OfficialTemplate] = OFFICIAL_TEMPLATES
) -> dict[str, str]:
    failures: dict[str, str] = {}
    for template in templates:
        try:
            smoke_test(template, cache_dir)
        except (OfficialTemplateError, OSError, subprocess.SubprocessError) as exc:
            failures[template.name] = str(exc)
    return failures
