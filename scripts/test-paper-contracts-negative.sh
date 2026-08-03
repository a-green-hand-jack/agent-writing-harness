#!/usr/bin/env bash
# Positive/negative regression for the lightweight Human–Agent paper contracts.
set -euo pipefail
cd "$(dirname "$0")/.."

TOOL=".agents/tools/check-paper-contracts.py"
python3 "$TOOL" --profile draft --root . >/dev/null

# The factory template is intentionally unresolved and must not release.
set +e
python3 "$TOOL" --profile release --root . > /tmp/paper-contract-release-template.out 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR unresolved factory template unexpectedly passed release check" >&2
  cat /tmp/paper-contract-release-template.out >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP" /tmp/paper-contract-release-template.out' EXIT
mkdir -p "$TMP/paper/sections" "$TMP/.agents/skills" "$TMP/.agents/runtime"
cp AGENTS.md "$TMP/AGENTS.md"
cp -R .agents/skills/* "$TMP/.agents/skills/"
printf '*\n!.gitignore\n' > "$TMP/.agents/runtime/.gitignore"

cat > "$TMP/PAPER.md" <<'EOF'
# Paper Contract

The collaboration cues are locked, bounded, free, and unresolved; the current release decisions below are complete.

## Paper identity

- Working title: Verified Paper
- Target venue: Generic submission
- Paper type: method
- Intended readers: researchers
- One-sentence positioning: A verified example.

## What readers should believe

### Central thesis

The example supports its stated conclusion.

### Contributions

1. **C1:** A verified contribution.

## What must not change silently

- Central claim meaning is locked.

## What may evolve

- Local wording is free within the approved claim.

## Unresolved

None.

## Story and structure

### Narrative arc

Problem to evidence.

### Section responsibilities

| Section | Reader task | Must preserve | Flexible elements |
|---|---|---|---|
| Introduction | Explain the problem | Claim meaning | wording |

## Writing style

### Current style

- Positioning and voice: direct and evidence-aware.

## Human decisions required

- The Human approves final release.
EOF

cat > "$TMP/EXPERIMENTS.md" <<'EOF'
# Experiment Contract

The current experiment contract is complete.

## Experiment overview

| ID | Paper question | Supports | Current state |
|---|---|---|---|
| E1 | Does the method support C1? | C1 | complete |

## Result interpretation

- The result supports only the approved setting.

## Relationship to the code repository

The data exchange interface is outside this contract.
EOF

cat > "$TMP/PAPER_INTERFACES.md" <<'EOF'
# Paper Interfaces

## Keep the implementation light

Use paper macros and readable comments.

## Interface categories

Identity, terminology, notation, and results.

## Flexible control

Meaning is locked; presentation can be bounded or free.

## Change workflow

Search consumers and request Human review for semantic changes.

## Draft and release

Required interfaces contain final values before release.
EOF

cat > "$TMP/paper/main.tex" <<'EOF'
\documentclass{article}
\begin{document}
Verified paper.
\end{document}
EOF

python3 "$TOOL" --profile release --root "$TMP" >/dev/null

# Removing a stable contract anchor must fail Draft.
cp "$TMP/PAPER.md" "$TMP/PAPER.good"
sed -i '/## Writing style/d' "$TMP/PAPER.md"
set +e
python3 "$TOOL" --profile draft --root "$TMP" > "$TMP/missing-heading.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR missing required contract heading unexpectedly passed Draft" >&2
  exit 1
fi
mv "$TMP/PAPER.good" "$TMP/PAPER.md"

# An active TeX placeholder must fail Release.
printf '\\PaperTODO{result}\n' >> "$TMP/paper/main.tex"
set +e
python3 "$TOOL" --profile release --root "$TMP" > "$TMP/tex-placeholder.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "ERROR active TeX placeholder unexpectedly passed Release" >&2
  exit 1
fi
grep -F "active release placeholder" "$TMP/tex-placeholder.out" >/dev/null

echo "OK test-paper-contracts-negative: Draft stays flexible; Release rejects unresolved and active placeholders"
