#!/usr/bin/env bash
# Regression for the paper-first public interfaces.
set -euo pipefail
cd "$(dirname "$0")/.."

bash -n .agents/tools/verify.sh
bash -n .agents/tools/release.sh
make -n pdf | grep -F 'cd paper' >/dev/null
make -n clean | grep -F 'cd paper' >/dev/null

# The deterministic Agent entrypoint must work on the factory tree.
bash .agents/tools/verify.sh >/dev/null

# The unresolved factory template must stop at the Release contract before any
# export or release mutation occurs.
before="$(sha256sum release/manifest.yaml | awk '{print $1}')"
set +e
bash .agents/tools/release.sh > /tmp/agent-release-entrypoint.out 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR unresolved factory template unexpectedly passed Agent release" >&2
  exit 1
fi
after="$(sha256sum release/manifest.yaml | awk '{print $1}')"
if [ "$before" != "$after" ]; then
  echo "ERROR Agent release mutated the manifest before the contract gate" >&2
  exit 1
fi
grep -E 'release placeholder|remains unresolved' /tmp/agent-release-entrypoint.out >/dev/null
rm -f /tmp/agent-release-entrypoint.out

echo "OK test-public-entrypoints-negative: Human build targets and Agent verify/release boundaries hold"
