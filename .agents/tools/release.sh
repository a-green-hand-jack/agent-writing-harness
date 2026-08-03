#!/usr/bin/env bash
# Stable Agent-facing release entrypoint. The factory template is intentionally
# unresolved, so this script fails at the contract gate until the paper is ready.
set -euo pipefail
cd "$(dirname "$0")/../.."

python3 .agents/tools/check-paper-contracts.py --profile release
python3 .agents/tools/check-paper-state.py
python3 .agents/tools/check-paper-interfaces.py
bash scripts/check-latex.sh --compile
bash scripts/export-tex-release.sh
python3 scripts/check-release-package.py
python3 scripts/check-release-freshness.py
python3 scripts/check-arxiv-portability.py
bash scripts/check-latex.sh --compile-release arxiv

echo "OK agent release"
