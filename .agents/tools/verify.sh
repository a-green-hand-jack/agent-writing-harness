#!/usr/bin/env bash
# Stable Agent-facing verification entrypoint for the paper-first repository.
set -euo pipefail
cd "$(dirname "$0")/../.."

pycache_dir="$(mktemp -d)"
trap 'rm -rf "$pycache_dir"' EXIT
PYTHONPYCACHEPREFIX="$pycache_dir" python3 -m compileall -q .agents/tools .agents/tests
layout="$(python3 .agents/tools/check-paper-profile.py --print-layout)"
python3 .agents/tools/check-structure.py
python3 .agents/tools/paper-init.py status
python3 .agents/tools/check-actions.py
python3 .agents/tools/check-skills.py
python3 .agents/tools/check-vendored-skills.py
python3 .agents/tools/check-vendored-skill-evals.py
for vendor_script in \
  .agents/vendor/ccfa-skills/ccf-common/scripts/check_markdown_links.py \
  .agents/vendor/ccfa-skills/ccf-common/scripts/check_path_privacy.py; do
  if [[ ! -f "$vendor_script" ]]; then
    echo "ERROR vendor snapshot changed: missing $vendor_script (re-sync after review)" >&2
    exit 1
  fi
done
python3 .agents/vendor/ccfa-skills/ccf-common/scripts/check_markdown_links.py
python3 .agents/vendor/ccfa-skills/ccf-common/scripts/check_path_privacy.py .agents/vendor/ccfa-skills
python3 .agents/tools/check-documentation.py
python3 .agents/tools/check-venue-knowledge.py
python3 .agents/tools/check-publication.py
python3 .agents/tools/check-paper-contracts.py --profile draft
python3 .agents/tools/check-release-records.py
if [[ "$layout" == "canonical-variants" ]]; then
  python3 .agents/tools/check-paper-interfaces.py
  python3 .agents/tools/check-reference-integrity.py --profile draft
  python3 .agents/tools/reference-evidence.py --offline status
  python3 .agents/tools/reference-evidence.py --offline inventory
fi
python3 .agents/tools/template-adoption.py validate
python3 .agents/tools/template-sync.py validate
python3 .agents/tools/overleaf-sync.py validate
python3 -m unittest discover -s .agents/tests -p 'test_*.py'

echo "OK agent verify"
