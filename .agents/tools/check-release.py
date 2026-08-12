#!/usr/bin/env python3
"""Public release-instance checker with clean-package enforcement."""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path, PurePosixPath

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import _check_release_core as _core

for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

_ORIGINAL_SAFE_ZIP_ENTRIES = _core.safe_zip_entries
_BUILD_SUFFIXES = {".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".log", ".out"}


def safe_zip_entries(path: Path, required: set[str]) -> int:
    code = _ORIGINAL_SAFE_ZIP_ENTRIES(path, required)
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                pure = PurePosixPath(info.filename)
                is_build_file = (
                    pure.name.endswith(".synctex.gz")
                    or pure.suffix.lower() in _BUILD_SUFFIXES
                    or (
                        pure.parent == PurePosixPath(".")
                        and pure.name.startswith("main")
                        and pure.suffix.lower() == ".pdf"
                    )
                )
                if is_build_file:
                    code |= _core.error(f"source package contains a TeX build by-product: {path.name}:{info.filename}")
    except (OSError, zipfile.BadZipFile):
        # The core checker already reports malformed ZIP files.
        pass
    return code


_core.safe_zip_entries = safe_zip_entries


def check(instance: Path) -> int:
    return _core.check(instance)


def main() -> int:
    return _core.main()


if __name__ == "__main__":
    sys.exit(main())
