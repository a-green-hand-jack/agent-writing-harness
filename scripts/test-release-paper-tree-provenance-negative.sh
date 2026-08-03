#!/usr/bin/env bash
# Regression for #53: release identity follows authored paper content, not a
# branch commit that disappears after squash/rebase.
set -euo pipefail
cd "$(dirname "$0")/.."
SOURCE_REPO="$(pwd)"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
mkdir -p "$REPO/paper"
cd "$REPO"
git init -q
git config user.email test@example.com
git config user.name test
printf '\\documentclass{article}\n' > paper/main.tex
git add paper/main.tex
git commit -qm source
SOURCE_COMMIT="$(git rev-parse HEAD)"
SOURCE_TREE="$(python3 - "$SOURCE_REPO" "$REPO" <<'PY'
import importlib.util
import sys
from pathlib import Path

tools = Path(sys.argv[1]) / ".agents/tools"
repo = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("release_provenance", tools / "release_provenance.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module.paper_source_tree(repo, ["main.tex"]))
PY
)"

# Simulate a squash result with identical paper content but unrelated history.
git checkout -q --orphan squash
rm -rf ./*
mkdir -p paper
printf '\\documentclass{article}\n' > paper/main.tex
git add paper/main.tex
git commit -qm squash

# Delete every non-squash branch (including the init default branch), expire all
# reflogs, and prune objects so the original source commit is genuinely absent.
while IFS= read -r branch; do
  [ "$branch" = "squash" ] || git branch -D "$branch" >/dev/null
done < <(git for-each-ref --format='%(refname:short)' refs/heads)
git reflog expire --expire=now --all
git gc --prune=now >/dev/null 2>&1

if git cat-file -e "$SOURCE_COMMIT^{commit}" 2>/dev/null; then
  echo "ERROR source commit is still reachable; squash fixture is invalid" >&2
  git show-ref >&2 || true
  exit 1
fi

python3 - "$SOURCE_REPO" "$REPO" "$SOURCE_COMMIT" "$SOURCE_TREE" <<'PY'
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

tools = Path(sys.argv[1]) / ".agents/tools"
repo = Path(sys.argv[2])
source_commit = sys.argv[3]
source_tree = sys.argv[4]
spec = importlib.util.spec_from_file_location("release_provenance", tools / "release_provenance.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

errors = []
def error(message):
    errors.append(message)
    return 1

def git_value(*args):
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else ""

ph = SimpleNamespace(
    ROOT=repo,
    RELEASE_ITEMS=["main.tex"],
    meaningful=lambda value: value not in (None, "", {}, []),
    error=error,
    git_value=git_value,
)
module.install(ph)
manifest = {
    "source_revision": {
        "scope": "paper",
        "treeish": "paper/",
        "commit": source_commit,
        "tree": source_tree,
    }
}
assert ph.check_source_revision_freshness(manifest) == 0, errors
assert ph.check_source_revision_matches_release_source(manifest) == 0, errors

# A docs-only commit must not invalidate the paper release identity.
(repo / "README.md").write_text("docs only\n", encoding="utf-8")
subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
subprocess.run(["git", "commit", "-qm", "docs"], cwd=repo, check=True)
assert ph.check_source_revision_freshness(manifest) == 0, errors

# Authored paper drift must invalidate it.
(repo / "paper/main.tex").write_text("\\documentclass{article}\nchanged\n", encoding="utf-8")
assert ph.check_source_revision_freshness(manifest) != 0
assert any("paper source tree is stale" in message for message in errors), errors

legacy = {"source_revision": {"treeish": "HEAD", "commit": source_commit, "tree": source_tree}}
assert ph.check_source_revision_freshness(legacy) != 0
assert any("legacy commit-bound provenance" in message for message in errors), errors
print("OK")
PY

echo "OK test-release-paper-tree-provenance-negative: squash/docs survive; paper drift fails"
