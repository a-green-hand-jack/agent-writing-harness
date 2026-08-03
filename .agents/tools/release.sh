#!/usr/bin/env bash
# Build and verify one strict immutable release instance.
set -euo pipefail
cd "$(dirname "$0")/../.."

: "${RELEASE_ID:?Set RELEASE_ID, for example iclr2027-submission-r1}"
VARIANT="${VARIANT:-anonymous}"
TARGETS="${TARGETS:-pdf,source-zip,arxiv-flat,overleaf-zip}"

python3 .agents/tools/release.py build \
  --id "$RELEASE_ID" \
  --variant "$VARIANT" \
  --profile release \
  --targets "$TARGETS" \
  --verify-tex
python3 .agents/tools/check-release.py "dist/$RELEASE_ID"

echo "OK strict release instance: $RELEASE_ID"
