#!/usr/bin/env bash
# Fidelity gate: compare the selected paper PDF against an original source PDF.
#
# The paper root defaults to the caller's current working directory, not the
# repository containing this script copy. This matters when a newer script is
# invoked from an older worktree: the comparison must stay attached to the
# caller's paper unless --paper-root explicitly selects another checkout.
#
# Usage:
#   scripts/compare-original-pdf.sh <original> [compiled] [options]
#
# Options:
#   --paper-root PATH              Paper checkout to compile/read (default: cwd).
#   --compiled PATH                Compiled PDF; relative paths resolve from cwd.
#   --threshold N                  Allowed differing lines per side (default: 5).
#   --allow-suspicious-page-gap    Continue when page counts strongly suggest a
#                                  wrong paper root or incomplete compilation.
#
# <original> may be an arXiv id, PDF URL, or local PDF path. Existing positional
# [compiled] usage remains supported.
#
# Exit codes: 0 = within threshold, 1 = content drift, 2 = setup/identity error.
set -euo pipefail

INVOCATION_ROOT="$(pwd -P)"
PAPER_ROOT="$INVOCATION_ROOT"
ORIGINAL=""
COMPILED=""
THRESHOLD=5
ALLOW_SUSPICIOUS_PAGE_GAP=false

usage() {
  cat >&2 <<'EOF'
usage: scripts/compare-original-pdf.sh <arxiv-id|url|path> [compiled.pdf]
       [--paper-root PATH] [--compiled PATH] [--threshold N]
       [--allow-suspicious-page-gap]
EOF
}

while (($#)); do
  case "$1" in
    --paper-root)
      (($# >= 2)) || { echo "ERROR --paper-root requires a path" >&2; exit 2; }
      PAPER_ROOT="$2"
      shift 2
      ;;
    --compiled)
      (($# >= 2)) || { echo "ERROR --compiled requires a path" >&2; exit 2; }
      COMPILED="$2"
      shift 2
      ;;
    --threshold)
      (($# >= 2)) || { echo "ERROR --threshold requires an integer" >&2; exit 2; }
      THRESHOLD="$2"
      shift 2
      ;;
    --allow-suspicious-page-gap)
      ALLOW_SUSPICIOUS_PAGE_GAP=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "ERROR unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      if [ -z "$ORIGINAL" ]; then
        ORIGINAL="$1"
      elif [ -z "$COMPILED" ]; then
        COMPILED="$1"
      else
        echo "ERROR unexpected positional argument: $1" >&2
        usage
        exit 2
      fi
      shift
      ;;
  esac
done

if [ -z "$ORIGINAL" ]; then
  usage
  exit 2
fi
if ! [[ "$THRESHOLD" =~ ^[0-9]+$ ]]; then
  echo "ERROR --threshold must be a non-negative integer: $THRESHOLD" >&2
  exit 2
fi

PAPER_ROOT="$(cd "$PAPER_ROOT" 2>/dev/null && pwd -P)" \
  || { echo "ERROR paper root does not exist: $PAPER_ROOT" >&2; exit 2; }
if [ ! -d "$PAPER_ROOT/paper" ]; then
  echo "ERROR selected paper root has no paper/ directory: $PAPER_ROOT" >&2
  exit 2
fi

if [ -z "$COMPILED" ]; then
  COMPILED="$PAPER_ROOT/paper/main.pdf"
elif [[ "$COMPILED" != /* ]]; then
  COMPILED="$INVOCATION_ROOT/$COMPILED"
fi

for bin in pdftotext pdfinfo; do
  command -v "$bin" >/dev/null 2>&1 \
    || { echo "ERROR $bin is required (poppler-utils)" >&2; exit 2; }
done

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- Resolve the original PDF -------------------------------------------------
ORIG_PDF="$WORK/original.pdf"
if [ -f "$ORIGINAL" ]; then
  cp "$ORIGINAL" "$ORIG_PDF"
elif [[ "$ORIGINAL" =~ ^https?:// ]]; then
  command -v curl >/dev/null 2>&1 || { echo "ERROR curl is required for URL input" >&2; exit 2; }
  curl -fsSL "$ORIGINAL" -o "$ORIG_PDF"
elif [[ "$ORIGINAL" =~ ^[0-9]{4}\.[0-9]{4,5}(v[0-9]+)?$ ]]; then
  command -v curl >/dev/null 2>&1 || { echo "ERROR curl is required for arXiv input" >&2; exit 2; }
  curl -fsSL "https://arxiv.org/pdf/${ORIGINAL}" -o "$ORIG_PDF"
else
  echo "ERROR could not resolve original '$ORIGINAL' (not a file, URL, or arXiv id)" >&2
  exit 2
fi
if ! head -c 5 "$ORIG_PDF" | grep -q '%PDF'; then
  echo "ERROR resolved original is not a PDF (got $(file -b "$ORIG_PDF" 2>/dev/null))" >&2
  exit 2
fi

# --- Resolve the compiled PDF -------------------------------------------------
if [ ! -f "$COMPILED" ]; then
  echo "INFO $COMPILED not found; compiling $PAPER_ROOT/paper/main.tex" >&2
  command -v latexmk >/dev/null 2>&1 \
    || { echo "ERROR latexmk required to build $COMPILED" >&2; exit 2; }
  [ -f "$PAPER_ROOT/paper/main.tex" ] \
    || { echo "ERROR missing $PAPER_ROOT/paper/main.tex" >&2; exit 2; }
  (cd "$PAPER_ROOT/paper" && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex >"$WORK/latexmk.log" 2>&1) \
    || { echo "ERROR compile failed; see log tail:" >&2; tail -20 "$WORK/latexmk.log" >&2; exit 2; }
  COMPILED="$PAPER_ROOT/paper/main.pdf"
fi
COMPILED="$(cd "$(dirname "$COMPILED")" 2>/dev/null && pwd -P)/$(basename "$COMPILED")" \
  || { echo "ERROR cannot resolve compiled PDF path: $COMPILED" >&2; exit 2; }
if ! head -c 5 "$COMPILED" | grep -q '%PDF'; then
  echo "ERROR compiled target is not a PDF: $COMPILED" >&2
  exit 2
fi

# --- Normalize text for order-insensitive comparison --------------------------
normalize() {
  pdftotext -nopgbrk "$1" - 2>/dev/null \
    | grep -vE '^arXiv:[0-9]{4}\.[0-9]{4,5}' \
    | grep -vE '^[0-9]+[[:space:]]*$' \
    | tr -s ' ' \
    | sed '/^[[:space:]]*$/d' \
    | sort -u
}
normalize "$COMPILED" >"$WORK/ours.norm"
normalize "$ORIG_PDF" >"$WORK/orig.norm"
if [ ! -s "$WORK/ours.norm" ] || [ ! -s "$WORK/orig.norm" ]; then
  echo "ERROR PDF text extraction produced an empty document; verify the selected files" >&2
  exit 2
fi

OURS_ONLY="$WORK/ours_only.txt"
ORIG_ONLY="$WORK/orig_only.txt"
comm -23 "$WORK/ours.norm" "$WORK/orig.norm" >"$OURS_ONLY"
comm -13 "$WORK/ours.norm" "$WORK/orig.norm" >"$ORIG_ONLY"

n_ours=$(wc -l <"$OURS_ONLY")
n_orig=$(wc -l <"$ORIG_ONLY")
shared=$(comm -12 "$WORK/ours.norm" "$WORK/orig.norm" | wc -l)

# --- Page-count and identity sanity -------------------------------------------
pages_ours=$(pdfinfo "$COMPILED" 2>/dev/null | awk '/^Pages:/{print $2}')
pages_orig=$(pdfinfo "$ORIG_PDF" 2>/dev/null | awk '/^Pages:/{print $2}')
if ! [[ "$pages_ours" =~ ^[0-9]+$ && "$pages_orig" =~ ^[0-9]+$ ]]; then
  echo "ERROR could not determine PDF page counts" >&2
  exit 2
fi

page_gap=$((pages_ours > pages_orig ? pages_ours - pages_orig : pages_orig - pages_ours))
min_pages=$((pages_ours < pages_orig ? pages_ours : pages_orig))
max_pages=$((pages_ours > pages_orig ? pages_ours : pages_orig))
suspicious_page_gap=false
if ((page_gap >= 5 && min_pages > 0 && max_pages >= 2 * min_pages)); then
  suspicious_page_gap=true
fi

echo "=== PDF fidelity vs original ==="
echo "paper root: $PAPER_ROOT"
echo "compiled : $COMPILED ($pages_ours pages)"
echo "original : $ORIGINAL ($pages_orig pages)"
echo "shared content lines : $shared"
echo "only in compiled     : $n_ours (invented / misplaced / reworded)"
echo "only in original     : $n_orig (dropped / reworded; arXiv stamp already ignored)"
echo "threshold per side   : $THRESHOLD"

if $suspicious_page_gap && ! $ALLOW_SUSPICIOUS_PAGE_GAP; then
  echo "ERROR suspicious page-count mismatch ($pages_ours vs $pages_orig): possible wrong paper root or incomplete compilation" >&2
  echo "Use --paper-root/--compiled to select the intended paper, or --allow-suspicious-page-gap after reviewing the mismatch." >&2
  exit 2
elif [ "$pages_ours" != "$pages_orig" ]; then
  echo "WARN page count differs ($pages_ours vs $pages_orig)"
fi

status=0
if [ "$n_ours" -gt "$THRESHOLD" ] || [ "$n_orig" -gt "$THRESHOLD" ]; then
  status=1
  echo
  echo "--- content only in COMPILED (first 40) ---"
  head -40 "$OURS_ONLY"
  echo "--- content only in ORIGINAL (first 40) ---"
  head -40 "$ORIG_ONLY"
fi

if [ "$status" -eq 0 ]; then
  echo "OK pdf-fidelity: within threshold"
else
  echo "FAIL pdf-fidelity: content drift exceeds threshold — reconcile the selected paper with the original, then re-run"
fi
exit "$status"
