#!/usr/bin/env bash
# Regression for the lightweight stable paper-interface surface.
set -euo pipefail
cd "$(dirname "$0")/.."

TOOL=".agents/tools/check-paper-interfaces.py"
python3 "$TOOL" --root . >/dev/null

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.agents/tools"
cp -R paper "$TMP/paper"
cp PAPER_INTERFACES.md "$TMP/PAPER_INTERFACES.md"
cp "$TOOL" "$TMP/.agents/tools/check-paper-interfaces.py"

# Missing definition must fail.
cp "$TMP/paper/macros.tex" "$TMP/paper/macros.good"
sed -i '/\\providecommand{\\MethodName}/d' "$TMP/paper/macros.tex"
set +e
python3 "$TOOL" --root "$TMP" > "$TMP/missing-definition.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR missing MethodName definition unexpectedly passed" >&2
  exit 1
fi
grep -F "missing interface definition: \\MethodName" "$TMP/missing-definition.out" >/dev/null
mv "$TMP/paper/macros.good" "$TMP/paper/macros.tex"

# Dead interface with no active consumer must fail.
find "$TMP/paper" -path "$TMP/paper/macros.tex" -prune -o -name '*.tex' -type f -print0 \
  | xargs -0 sed -i 's/\\MethodName{}//g'
set +e
python3 "$TOOL" --root "$TMP" > "$TMP/no-consumer.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR MethodName without an active consumer unexpectedly passed" >&2
  exit 1
fi
grep -F "has no active paper consumer: \\MethodName" "$TMP/no-consumer.out" >/dev/null

# Missing generated-results hook must fail.
cp -R paper "$TMP/paper"
sed -i '/generated\/results-macros.tex/d' "$TMP/paper/macros.tex"
set +e
python3 "$TOOL" --root "$TMP" > "$TMP/no-generated-hook.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR missing generated-results hook unexpectedly passed" >&2
  exit 1
fi
grep -F "generated results-macros override hook" "$TMP/no-generated-hook.out" >/dev/null

echo "OK test-paper-interfaces-negative: definitions, consumers, and generated override hook are enforced"
