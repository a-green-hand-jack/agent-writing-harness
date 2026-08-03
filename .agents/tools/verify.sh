#!/usr/bin/env bash
# Stable Agent-facing deterministic verification entrypoint.
set -euo pipefail
cd "$(dirname "$0")/../.."

python3 scripts/check-capability-parity.py
python3 scripts/check-writing-harness.py
python3 scripts/check-anatomy-drift.py
python3 scripts/check-paper-surface.py
python3 scripts/check-conference-template.py
python3 scripts/check-release-package.py
python3 scripts/check-release-freshness.py
python3 scripts/check-arxiv-portability.py
python3 scripts/check-bridge-chassis.py
python3 .agents/tools/check-paper-contracts.py --profile draft
python3 .agents/tools/check-paper-state.py
python3 .agents/tools/check-paper-interfaces.py

echo "OK agent verify"
