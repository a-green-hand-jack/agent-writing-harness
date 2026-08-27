#!/usr/bin/env python3
"""Check the paper-first repository structure and generated-output boundaries."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _paper_profile import ProfileError, ensure_profile_paths, is_canonical, load_profile

CANONICAL_FORBIDDEN = (
    ".agent",
    ".claude",
    "state",
    "lab",
    "human",
    "memory",
    "PROJECT.md",
    # Template-development-only surface. These paths belong to the template's
    # template-dev branch and must never appear in a paper-facing repo.
    ".agents/evals",
    ".agents/tools/check-actions.py",
    ".agents/tools/check-skills.py",
    ".agents/tools/check-vendored-skills.py",
    ".agents/tools/check-vendored-skill-evals.py",
    ".agents/dependencies/vendored-skills",
)
UNIVERSAL_FORBIDDEN = ("release",)
REQUIRED = (
    "README.md",
    "AGENT_GUIDE.md",
    "WHY_THIS_TEMPLATE.md",
    "PAPER.md",
    "EXPERIMENTS.md",
    "PAPER_INTERFACES.md",
    "PUBLICATION.md",
    "DECISIONS.md",
    "AGENTS.md",
    "releases/README.md",
    "releases/records/README.md",
    ".agents/knowledge/README.md",
    ".agents/knowledge/writing/README.md",
    ".agents/knowledge/venues/README.md",
    ".agents/knowledge/venues/_template.md",
    ".agents/template-sync.json",
    ".agents/template-inheritance.json",
    ".agents/skills/paper-orientation/SKILL.md",
    ".agents/skills/template-adoption/SKILL.md",
    ".agents/skills/template-sync/SKILL.md",
    ".agents/vendor/README.md",
    ".agents/vendor/ccfa-skills/LICENSE",
    ".agents/vendor/ccfa-skills/ccf-common/SKILL.md",
    ".agents/vendor/ccfa-skills/ccf-paper-writer/SKILL.md",
    ".agents/vendor/writing-dna-skill/LICENSE",
    ".agents/vendor/writing-dna-skill/SKILL.md",
    ".agents/tools/_template_inheritance.py",
    ".agents/tools/_paper_profile.py",
    ".agents/tools/verify.sh",
    ".agents/tools/paper-init.py",
    ".agents/tools/paper-brief.py",
    ".agents/tools/check-documentation.py",
    ".agents/tools/check-venue-knowledge.py",
    ".agents/tools/check-publication.py",
    ".agents/tools/check-paper-profile.py",
    ".agents/tools/release.py",
    ".agents/tools/check-release.py",
    ".agents/tools/check-release-records.py",
    ".agents/tools/template-adoption.py",
    ".agents/tools/template-sync.py",
    ".agents/tools/overleaf-sync.py",
    ".agents/runtime/.gitignore",
)
CANONICAL_REQUIRED = (
    "Makefile",
    "paper/main.tex",
    "paper/macros.tex",
    "paper/venue_preamble.tex",
    "paper/refs.bib",
    "paper/sections/00_title.tex",
    "paper/sections/01_abstract.tex",
    "paper/sections/10_appendix.tex",
    "paper/variants/README.md",
    "paper/variants/common.tex",
    "paper/variants/draft.tex",
    "paper/variants/anonymous.tex",
    "paper/variants/camera_ready.tex",
    "paper/variants/arxiv.tex",
)
SECTION_RE = re.compile(r"^[01]\d_[a-z][a-z0-9_]*\.tex$")
INPUT_RE = re.compile(r"\\input\s*\{sections/([^}]+)\}")
ASSET_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
TEX_SOURCE_EXTENSIONS = {".tex", ".sty", ".cls"}
FORBIDDEN_DEPENDENCY_ROOTS = {".agents", "dist", "release", "releases"}
TEX_REFERENCE_PATTERNS = (
    ("input", re.compile(r"\\(?:input|include)\s*\{([^}]+)\}"), (".tex",), False),
    ("input", re.compile(r"\\InputIfFileExists\s*\{([^}]+)\}"), (".tex",), False),
    (
        "graphics",
        re.compile(r"\\includegraphics\*?\s*(?:\[[^\]]*\]\s*)?\{([^}]+)\}"),
        ("", ".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps"),
        False,
    ),
    ("bibliography", re.compile(r"\\bibliography\s*\{([^}]+)\}"), (".bib",), True),
    (
        "bibliography",
        re.compile(r"\\addbibresource\s*(?:\[[^\]]*\]\s*)?\{([^}]+)\}"),
        (".bib",),
        False,
    ),
    ("style", re.compile(r"\\bibliographystyle\s*\{([^}]+)\}"), (".bst",), False),
    (
        "package",
        re.compile(r"\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\]\s*)?\{([^}]+)\}"),
        (".sty",),
        True,
    ),
    (
        "class",
        re.compile(r"\\documentclass\s*(?:\[[^\]]*\]\s*)?\{([^}]+)\}"),
        (".cls",),
        False,
    ),
)
UNSUPPORTED_PATH_DIRECTIVE_RE = re.compile(r"\\(?:graphicspath|input@path)\b")
UNSUPPORTED_INPUT_SYNTAX_RE = re.compile(r"\\(?:input|include)\b\s*+(?!\{)")


def error(message: str) -> int:
    print(f"ERROR {message}")
    return 1


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


def check_required(root: Path, profile: dict[str, object]) -> int:
    code = 0
    required = REQUIRED + (CANONICAL_REQUIRED if is_canonical(profile) else ())
    for relative in required:
        if not (root / relative).is_file():
            code |= error(f"missing required paper-first file: {relative}")
    forbidden = UNIVERSAL_FORBIDDEN + (CANONICAL_FORBIDDEN if is_canonical(profile) else ())
    for relative in forbidden:
        if (root / relative).exists():
            code |= error(f"obsolete or generated repository surface must be removed: {relative}")
    return code


def check_sections(root: Path) -> int:
    main_path = root / "paper/main.tex"
    sections_root = root / "paper/sections"
    if not main_path.is_file() or not sections_root.is_dir():
        return error("missing paper/main.tex or paper/sections/")

    code = 0
    names = sorted(path.name for path in sections_root.glob("*.tex"))
    for name in names:
        if not SECTION_RE.fullmatch(name):
            code |= error(f"section file does not follow NN_name.tex: {name}")

    main = active_tex(main_path.read_text(encoding="utf-8"))
    inputs = INPUT_RE.findall(main)
    for anchor in ("00_title", "01_abstract", "10_appendix"):
        if anchor not in inputs:
            code |= error(f"paper/main.tex does not input sections/{anchor}.tex")
    for stem in inputs:
        if not (sections_root / f"{stem}.tex").is_file():
            code |= error(f"paper/main.tex has dangling section input: {stem}")

    appendix_index = main.find("\\appendix")
    body = [stem for stem in inputs if stem.startswith("0")]
    appendix = [stem for stem in inputs if stem.startswith("1")]
    if body != sorted(body):
        code |= error("body section inputs are not in ascending NN order")
    if appendix != sorted(appendix):
        code |= error("appendix section inputs are not in ascending NN order")
    for stem in body:
        if appendix_index >= 0 and re.search(
            rf"\\input\s*\{{sections/{re.escape(stem)}\}}", main[appendix_index:]
        ):
            code |= error(f"body section appears after appendix: {stem}")
    for stem in appendix:
        match = re.search(rf"\\input\s*\{{sections/{re.escape(stem)}\}}", main)
        if appendix_index < 0 or match is None or match.start() < appendix_index:
            code |= error(f"appendix section appears before \\appendix: {stem}")
    return code


def check_figures(root: Path, profile: dict[str, object]) -> int:
    wrappers = root / str(profile["source_root"]) / "figures"
    assets = wrappers / "srcs"
    if not wrappers.is_dir() or not assets.is_dir():
        return 0
    code = 0
    wrapper_stems = {path.stem for path in wrappers.glob("*.tex")}
    asset_stems = {
        path.stem
        for path in assets.iterdir()
        if path.is_file() and path.suffix.lower() in ASSET_EXTENSIONS
    }
    for stem in sorted(wrapper_stems - asset_stems):
        code |= error(f"figure wrapper has no matching source asset: {stem}")
    for stem in sorted(asset_stems - wrapper_stems):
        code |= error(f"figure source asset has no matching wrapper: {stem}")
    return code


def check_dependency_boundary(root: Path, profile: dict[str, object]) -> int:
    code = 0
    source_root = root / str(profile["source_root"])
    repository_root = root.resolve()
    entrypoint_root = (root / str(profile["entrypoint"])).parent
    forbidden_roots = [
        (root / relative).resolve()
        for relative in FORBIDDEN_DEPENDENCY_ROOTS
    ]

    def boundary_error(source: Path, label: str, reference: str, candidate: Path) -> int:
        resolved = candidate.resolve()
        try:
            relative_dependency = resolved.relative_to(repository_root)
        except ValueError:
            return error(
                f"paper source dependency leaves the repository: "
                f"{source.relative_to(root)} -> {label} {{{reference}}}"
            )
        if any(
            resolved == forbidden or forbidden in resolved.parents
            for forbidden in forbidden_roots
        ):
            return error(
                f"paper source depends on non-paper surface: "
                f"{source.relative_to(root)} -> {relative_dependency}"
            )
        return 0

    def candidates_for(
        source: Path,
        reference: str,
        extensions: tuple[str, ...],
    ) -> list[Path]:
        dynamic_at = min(
            (reference.find(token) for token in ("\\", "#", "$") if token in reference),
            default=-1,
        )
        static_reference = reference if dynamic_at < 0 else reference[:dynamic_at]
        static_reference = static_reference.rstrip()
        if not static_reference:
            return []
        raw = Path(static_reference)
        variants = [raw]
        if dynamic_at < 0 and raw.suffix == "":
            variants = [raw.with_suffix(extension) if extension else raw for extension in extensions]
        bases = tuple(dict.fromkeys((source.parent, entrypoint_root, source_root, root)))
        return [base / variant for base in bases for variant in variants]

    source_files = sorted(
        path
        for path in source_root.rglob("*")
        if path.suffix.lower() in TEX_SOURCE_EXTENSIONS
    )
    for path in source_files:
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in FORBIDDEN_DEPENDENCY_ROOTS:
            continue
        resolved_source = path.resolve()
        try:
            resolved_relative = resolved_source.relative_to(root.resolve())
        except ValueError:
            code |= error(f"paper source leaves the repository: {relative}")
            continue
        if resolved_relative.parts and resolved_relative.parts[0] in FORBIDDEN_DEPENDENCY_ROOTS:
            code |= error(f"paper source depends on non-paper surface: {relative} -> {resolved_relative}")
        text = active_tex(path.read_text(encoding="utf-8"))
        if UNSUPPORTED_PATH_DIRECTIVE_RE.search(text):
            code |= error(
                f"paper source uses unsupported TeX dependency search path directive: {relative}"
            )
        if UNSUPPORTED_INPUT_SYNTAX_RE.search(text):
            code |= error(
                f"paper source uses unsupported unbraced TeX input syntax: {relative}"
            )
        for label, pattern, extensions, comma_separated in TEX_REFERENCE_PATTERNS:
            for raw_reference in pattern.findall(text):
                references = raw_reference.split(",") if comma_separated else [raw_reference]
                for raw_value in references:
                    value = raw_value.strip()
                    if not value:
                        continue
                    if any(token in value for token in ("\\", "#", "$")):
                        code |= error(
                            f"paper source has unresolved dynamic {label} dependency: "
                            f"{path.relative_to(root)} -> {{{value}}}"
                        )
                        continue
                    candidates = candidates_for(path, value, extensions)
                    if not candidates:
                        continue
                    existing = [
                        candidate
                        for candidate in candidates
                        if candidate.is_file() or candidate.is_symlink()
                    ]
                    selected = existing or [candidates[0]]
                    for candidate in selected:
                        candidate_code = boundary_error(path, label, value, candidate)
                        code |= candidate_code
                        if candidate_code:
                            break
    return code


def check(root: Path) -> int:
    try:
        profile = load_profile(root)
        ensure_profile_paths(root, profile)
    except ProfileError as exc:
        return error(f"paper build profile is invalid: {exc}")
    code = (
        check_required(root, profile)
        | (check_sections(root) if is_canonical(profile) else 0)
        | (check_figures(root, profile) if is_canonical(profile) else 0)
        | check_dependency_boundary(root, profile)
    )
    if code == 0:
        print("OK paper_structure")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    return check(args.root.expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
