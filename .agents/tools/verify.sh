#!/usr/bin/env bash
# Stable Agent-facing deterministic verification entrypoint.
set -euo pipefail
cd "$(dirname "$0")/../.."

RUNNER=(python3 .agents/tools/paper-harness.py)
"${RUNNER[@]}" capability_parity
"${RUNNER[@]}" writing_harness
"${RUNNER[@]}" anatomy_drift
"${RUNNER[@]}" paper_surface
"${RUNNER[@]}" conference_template
"${RUNNER[@]}" release_package
"${RUNNER[@]}" release_freshness
"${RUNNER[@]}" arxiv_portability
"${RUNNER[@]}" bridge_chassis_preflight
python3 .agents/tools/check-paper-contracts.py --profile draft
python3 .agents/tools/check-paper-state.py
python3 .agents/tools/check-paper-interfaces.py

echo "OK agent verify"
