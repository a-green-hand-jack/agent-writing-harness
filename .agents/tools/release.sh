#!/usr/bin/env bash
# Validate a release-ready canonical paper. Packaging is handled by the
# publication/release workflow introduced in the next architecture stage.
set -euo pipefail
cd "$(dirname "$0")/../.."

python3 .agents/tools/check-structure.py
python3 .agents/tools/check-paper-contracts.py --profile release
python3 .agents/tools/check-paper-interfaces.py
make pdf

echo "OK release-ready canonical paper"
