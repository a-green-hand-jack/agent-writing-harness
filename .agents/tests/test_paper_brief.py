from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/paper-brief.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


FACTORY_PAPER = """# Paper Contract
The collaboration cues locked, bounded, free, and unresolved remain available as guidance.
## Paper identity
- Working title: TODO Paper Title
- Target venue: unresolved (verify current official rules before submission work)
- Paper type: unresolved
- Intended readers: TODO
- One-sentence positioning: TODO
## Operating mode
- Mode: unresolved (`collaborative` or `autonomous`)
## What readers should believe
### Central thesis — unresolved

TODO: state the single most important conclusion the paper wants readers to accept.
### Contributions
No contributions have been approved yet. Add one entry per contribution that
the current paper can defend; there is no required number of contributions.

For each contribution, record whether it is central, supporting, or optional and whether it may be weakened or removed if the evidence changes.
## What must not change silently
Current locked items:

- TODO
## What may evolve
- Local sentence wording: free unless it changes claim strength or scientific meaning.
- TODO
## Unresolved
- TODO: title candidates
- TODO: central thesis
- TODO: target audience and venue fit
## Story and structure
The narrative is approved.
## Writing style
### Current style — unresolved
- Positioning and voice: TODO
- Explanation density: TODO
- Claim-strength discipline: TODO
- Preferred paragraph moves: TODO
- Terms or expressions to avoid: TODO
- Venue-specific overlay: TODO; load only when the target venue is active and current rules have been verified.
## Human decisions required
Final approval belongs to the Human.
"""


def brief_fixture() -> str:
    return """# Paper Brief
## Paper identity
- Working title: A Study of X
- Target venue: ICLR 2026
- Paper type: conference
- Intended readers: ML researchers
- One-sentence positioning: We show that X works.
## What readers should believe
### Central thesis
X improves accuracy.
### Contributions
- Contribution: a new method for X
## Operating mode
- Mode: autonomous
## Evidence and materials
- Code / data / results: repo link
## What must not change silently
- the primary comparison
## What may evolve
- presentation order of experiments
## Target and delivery
- Venue / year / track and deadline: unresolved
## Authors and identity
- Author list: unresolved
## Constraints
- Language and length limits: English, 9 pages
## First deliverable
- outline
"""


class PaperBriefChecks(unittest.TestCase):
    def test_validate_passes_on_valid_brief(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "BRIEF.md"
            write(brief, brief_fixture())
            result = run(Path(directory), "validate", "--brief", str(brief))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OK paper_brief validated", result.stdout)

    def test_validate_rejects_missing_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "BRIEF.md"
            write(brief, brief_fixture().replace("## Constraints", "## Missing constraints"))
            result = run(Path(directory), "validate", "--brief", str(brief))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required sections: Constraints", result.stdout + result.stderr)

    def test_validate_rejects_invalid_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "BRIEF.md"
            write(brief, brief_fixture().replace("- Mode: autonomous", "- Mode: unsupervised"))
            result = run(Path(directory), "validate", "--brief", str(brief))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mode must be collaborative, autonomous, or unresolved", result.stdout + result.stderr)

    def test_validate_accepts_directory_brief(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            write(Path(directory) / "BRIEF.md", brief_fixture())
            result = run(Path(directory), "validate", "--brief", directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validate_rejects_missing_brief(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run(Path(directory), "validate", "--brief", str(Path(directory) / "nope.md"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not exist", result.stdout + result.stderr)

    def test_ingest_fills_decided_fields_and_leaves_missing_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "writing"
            write(repo / "PAPER.md", FACTORY_PAPER)
            brief = Path(directory) / "briefrepo" / "BRIEF.md"
            write(brief, brief_fixture())
            result = run(repo, "ingest", "--brief", str(brief))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            paper = (repo / "PAPER.md").read_text(encoding="utf-8")
            self.assertIn("Working title: A Study of X", paper)
            self.assertIn("Target venue: ICLR 2026", paper)
            self.assertIn("Mode: autonomous", paper)
            self.assertIn("### Central thesis\n\nX improves accuracy.", paper)
            self.assertIn("- Contribution: a new method for X", paper)
            self.assertIn("- the primary comparison", paper)
            self.assertIn("- presentation order of experiments", paper)
            # Fields not decided in the brief stay unresolved.
            self.assertIn("### Current style — unresolved", paper)
            self.assertIn("Explanation density: TODO", paper)
            brief_copy = (repo / "BRIEF.md").read_text(encoding="utf-8")
            self.assertIn("Paper Brief", brief_copy)

    def test_ingest_does_not_invent_from_empty_brief(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "writing"
            write(repo / "PAPER.md", FACTORY_PAPER)
            empty = """# Paper Brief
## Paper identity
- Working title: TODO
## What readers should believe
### Central thesis
TODO
### Contributions
- TODO
## Operating mode
- Mode: unresolved
## Evidence and materials
- Code / data / results: none yet
## What must not change silently
- TODO
## What may evolve
- TODO
## Target and delivery
- Venue / year / track and deadline: unresolved
## Authors and identity
- Author list: unresolved
## Constraints
- Language and length limits: TODO
## First deliverable
- TODO
"""
            brief = Path(directory) / "briefrepo" / "BRIEF.md"
            write(brief, empty)
            result = run(repo, "ingest", "--brief", str(brief))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            paper = (repo / "PAPER.md").read_text(encoding="utf-8")
            self.assertIn("Working title: TODO Paper Title", paper)
            self.assertIn("Mode: unresolved", paper)


if __name__ == "__main__":
    unittest.main()
