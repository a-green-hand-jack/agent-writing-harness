#!/usr/bin/env bash
# Stable Agent-facing release entrypoint. The factory template is intentionally
# unresolved, so this script fails at the contract gate until the paper is ready.
set -euo pipefail
cd "$(dirname "$0")/../.."

RUNNER=(python3 .agents/tools/paper-harness.py)
python3 .agents/tools/check-paper-contracts.py --profile release
python3 .agents/tools/check-paper-state.py
python3 .agents/tools/check-paper-interfaces.py
bash scripts/check-latex.sh --compile
"${RUNNER[@]}" export_release
"${RUNNER[@]}" release_package
"${RUNNER[@]}" release_freshness
"${RUNNER[@]}" arxiv_portability
bash scripts/check-latex.sh --compile-release arxiv

echo "OK agent release"
