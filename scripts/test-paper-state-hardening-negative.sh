#!/usr/bin/env bash
# Regressions for real-case gaps: supporting claim numeric binding, broad numeric
# exceptions, and configured venue styles that are no longer used.
set -euo pipefail
cd "$(dirname "$0")/.."

TOOL=".agents/tools/check-paper-state.py"
python3 "$TOOL" --root . >/dev/null

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/state/numbers/groups" "$TMP/paper/style"

cat > "$TMP/state/numeric-registry.yaml" <<'EOF'
index: state/numbers/numeric-index.yaml
groups:
  - state/numbers/groups/main-results.yaml
EOF
printf 'numbers: []\n' > "$TMP/state/numbers/numeric-index.yaml"
cat > "$TMP/state/claim-evidence-map.yaml" <<'EOF'
claims:
  - claim_id: claim-supporting
    status: active
    claim_strength: supporting
    numeric_ids: [number-a]
  - claim_id: claim-other
    status: active
    claim_strength: core
    numeric_ids: [number-b]
EOF
cat > "$TMP/state/numbers/groups/main-results.yaml" <<'EOF'
numbers:
  - numeric_id: number-a
    status: verified
    value: 1.0
    claim_ids: [claim-other]
  - numeric_id: number-b
    status: verified
    value: 2.0
    claim_ids: [claim-other]
EOF
printf 'exceptions: []\n' > "$TMP/state/numbers/exceptions.yaml"
printf 'raw_template: TODO\n' > "$TMP/state/conference-template.yaml"
printf '\\documentclass{article}\n' > "$TMP/paper/main.tex"
printf '%% no venue yet\n' > "$TMP/paper/venue_preamble.tex"

set +e
python3 "$TOOL" --root "$TMP" > "$TMP/supporting.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR supporting-claim numeric rebind unexpectedly passed" >&2
  exit 1
fi
grep -F "claim-supporting (supporting)" "$TMP/supporting.out" >/dev/null

# Repair reciprocal binding before testing the next independent invariant.
cat > "$TMP/state/numbers/groups/main-results.yaml" <<'EOF'
numbers:
  - numeric_id: number-a
    status: verified
    value: 1.0
    claim_ids: [claim-supporting]
  - numeric_id: number-b
    status: verified
    value: 2.0
    claim_ids: [claim-other]
EOF
python3 "$TOOL" --root "$TMP" >/dev/null

cat > "$TMP/state/numbers/exceptions.yaml" <<'EOF'
exceptions:
  - pattern: "2026"
    match_scope: literal
    reason: year metadata
EOF
set +e
python3 "$TOOL" --root "$TMP" > "$TMP/exception.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR global numeric exception unexpectedly passed" >&2
  exit 1
fi
grep -F "has no path_pattern" "$TMP/exception.out" >/dev/null

cat > "$TMP/state/numbers/exceptions.yaml" <<'EOF'
exceptions:
  - pattern: "2026"
    match_scope: literal
    path_pattern: paper/sections/00_title.tex
    reason: title year metadata
EOF
python3 "$TOOL" --root "$TMP" >/dev/null

cat > "$TMP/state/conference-template.yaml" <<'EOF'
venue: iclr
year: 2026
raw_template: fixtures/iclr-2026
compat_shim: paper/style/compat.sty
human_verified_at: 2026-08-03
EOF
printf '%% shim\n' > "$TMP/paper/style/compat.sty"
printf '\\documentclass{article}\n' > "$TMP/paper/main.tex"
printf '%% \\usepackage{style/iclr2026_conference}\n' > "$TMP/paper/venue_preamble.tex"

set +e
python3 "$TOOL" --root "$TMP" > "$TMP/venue-input.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR configured venue without main input unexpectedly passed" >&2
  exit 1
fi
grep -F "must input venue_preamble" "$TMP/venue-input.out" >/dev/null

printf '\\documentclass{article}\n\\input{venue_preamble}\n' > "$TMP/paper/main.tex"
set +e
python3 "$TOOL" --root "$TMP" > "$TMP/venue-comment.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR comment-only venue preamble unexpectedly passed" >&2
  exit 1
fi
grep -F "no active class/package/input command" "$TMP/venue-comment.out" >/dev/null

printf '%% style\n' > "$TMP/paper/style/iclr2026_conference.sty"
printf '\\usepackage{style/iclr2026_conference}\n' > "$TMP/paper/venue_preamble.tex"
python3 "$TOOL" --root "$TMP" >/dev/null

echo "OK test-paper-state-hardening-negative: supporting bindings, exception scope, and venue use are enforced"
