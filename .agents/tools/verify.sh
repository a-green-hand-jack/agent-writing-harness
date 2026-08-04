#!/usr/bin/env bash
# Stable Agent-facing verification entrypoint for the paper-first repository.
set -euo pipefail
cd "$(dirname "$0")/../.."

python3 -m compileall -q .agents/tools .agents/tests
python3 .agents/tools/check-structure.py
python3 .agents/tools/check-paper-contracts.py --profile draft
python3 .agents/tools/check-paper-interfaces.py
python3 .agents/tools/check-publication.py
python3 .agents/tools/check-release-records.py
python3 .agents/tools/template-adoption.py validate
python3 .agents/tools/template-sync.py validate
python3 -m unittest discover -s .agents/tests -p 'test_*.py'

echo "OK agent verify"
