#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONDONTWRITEBYTECODE=1 python3 .agents/tools/paper-harness.py export_release
