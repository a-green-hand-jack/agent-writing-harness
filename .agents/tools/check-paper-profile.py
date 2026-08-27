#!/usr/bin/env python3
"""Validate the repository-local LaTeX source and build profile."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _paper_profile import ProfileError, ensure_profile_paths, load_profile


def check(root: Path, *, print_layout: bool) -> int:
    try:
        profile = load_profile(root)
    except ProfileError as exc:
        print(f"ERROR paper_build_profile: {exc}")
        return 1

    try:
        ensure_profile_paths(root, profile)
    except ProfileError as exc:
        print(f"ERROR paper_build_profile: {exc}")
        return 1
    if print_layout:
        print(profile["layout"])
    else:
        print("OK paper_build_profile")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--print-layout", action="store_true")
    args = parser.parse_args()
    return check(args.root.expanduser().resolve(), print_layout=args.print_layout)


if __name__ == "__main__":
    sys.exit(main())
