#!/usr/bin/env python3
"""Public release CLI with clean-package policy over the release core."""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import _release_core as _core

# Re-export the core API used by tests and focused Agent tooling.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


def deterministic_zip(source: Path, output: Path) -> None:
    """Create a deterministic source ZIP without TeX build by-products."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative_path = path.relative_to(source)
            if not _core.source_file_allowed(relative_path):
                continue
            relative = relative_path.as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


# Core build functions resolve this name from their defining module.
_core.deterministic_zip = deterministic_zip


def main() -> int:
    return _core.main()


if __name__ == "__main__":
    sys.exit(main())
