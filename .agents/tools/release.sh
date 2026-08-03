#!/usr/bin/env bash
# Validate a release-ready publication variant. Immutable packaging is handled
# by the release-instance workflow.
set -euo pipefail
cd "$(dirname "$0")/../.."

VARIANT="${VARIANT:-draft}"
python3 .agents/tools/check-structure.py
python3 .agents/tools/check-paper-contracts.py --profile release
python3 .agents/tools/check-paper-interfaces.py
python3 .agents/tools/check-publication.py
make pdf VARIANT="$VARIANT"

echo "OK release-ready publication variant: $VARIANT"
