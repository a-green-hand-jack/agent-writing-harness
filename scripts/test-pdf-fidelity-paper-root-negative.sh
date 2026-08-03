#!/usr/bin/env bash
# Regression for #29: calling a script copy from worktree B while standing in
# worktree A must compare A/paper/main.pdf, not B/paper/main.pdf. Also proves an
# extreme page-count mismatch is reported as a setup/identity error.
set -euo pipefail
cd "$(dirname "$0")/.."

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
A="$TMP/worktree-a"
B="$TMP/worktree-b"
FAKEBIN="$TMP/fakebin"
mkdir -p "$A/paper" "$B/paper" "$B/scripts" "$FAKEBIN"
cp scripts/compare-original-pdf.sh "$B/scripts/compare-original-pdf.sh"
chmod +x "$B/scripts/compare-original-pdf.sh"

# The files only need a PDF header because pdftotext/pdfinfo are controlled
# fakes in this regression. A's compiled text matches the original; B's does not.
printf '%%PDF-1.4\nA\n' >"$A/paper/main.pdf"
printf '%%PDF-1.4\nB\n' >"$B/paper/main.pdf"
printf '%%PDF-1.4\nORIGINAL-SAME\n' >"$A/original-same.pdf"
printf '%%PDF-1.4\nORIGINAL-LARGE\n' >"$A/original-large.pdf"
printf '%%PDF-1.4\nBAD\n' >"$A/paper/bad.pdf"

cat >"$FAKEBIN/pdftotext" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
pdf=""
for arg in "$@"; do
  case "$arg" in *.pdf) pdf="$arg" ;; esac
done
case "$pdf" in
  */worktree-b/paper/main.pdf) echo "WRONG-WORKTREE" ;;
  *) echo "MATCHED-CONTENT" ;;
esac
EOF

cat >"$FAKEBIN/pdfinfo" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
pdf="${1:-}"
if grep -q 'ORIGINAL-LARGE' "$pdf"; then
  echo "Pages:          21"
else
  echo "Pages:          2"
fi
EOF
chmod +x "$FAKEBIN/pdftotext" "$FAKEBIN/pdfinfo"

OUT="$TMP/root.out"
(
  cd "$A"
  PATH="$FAKEBIN:$PATH" bash "$B/scripts/compare-original-pdf.sh" original-same.pdf --threshold 0
) >"$OUT" 2>&1

grep -F "paper root: $A" "$OUT" >/dev/null
grep -F "compiled : $A/paper/main.pdf" "$OUT" >/dev/null
if grep -F "$B/paper/main.pdf" "$OUT" >/dev/null; then
  echo "ERROR fidelity gate selected the script copy's paper instead of the caller paper" >&2
  cat "$OUT" >&2
  exit 1
fi
grep -F "OK pdf-fidelity" "$OUT" >/dev/null

set +e
(
  cd "$A"
  PATH="$FAKEBIN:$PATH" bash "$B/scripts/compare-original-pdf.sh" original-large.pdf paper/bad.pdf --threshold 0
) >"$TMP/gap.out" 2>&1
rc=$?
set -e
if [ "$rc" -ne 2 ]; then
  echo "ERROR suspicious page gap should exit 2, got $rc" >&2
  cat "$TMP/gap.out" >&2
  exit 1
fi
grep -F "possible wrong paper root or incomplete compilation" "$TMP/gap.out" >/dev/null

echo "OK test-pdf-fidelity-paper-root-negative: caller root wins; suspicious page mismatch is explicit"
