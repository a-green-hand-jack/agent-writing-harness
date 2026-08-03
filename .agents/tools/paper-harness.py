#!/usr/bin/env python3
"""Run the legacy harness with current Agent-side compatibility adapters."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
TOOLS = ROOT / ".agents" / "tools"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(TOOLS))

import paper_harness_checks as harness  # noqa: E402
from release_provenance import install  # noqa: E402

install(harness)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: paper-harness.py <check-name>", file=sys.stderr)
        return 2
    return harness.run(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
