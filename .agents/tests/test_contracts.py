from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-paper-contracts.py"


def run(root: Path, profile: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), "--profile", profile],
        text=True,
        capture_output=True,
        check=False,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def completed_fixture(root: Path) -> None:
    write(
        root / "PAPER.md",
        """# Paper Contract
The collaboration cues locked, bounded, free, and unresolved remain available as guidance.
## Paper identity
The paper has an approved identity.
## What readers should believe
The central thesis is approved.
## What must not change silently
The central claim is protected.
## What may evolve
Local wording may evolve.
## Unresolved
There are no open release blockers.
## Story and structure
The narrative is approved.
## Writing style
The style is approved.
## Human decisions required
Final approval belongs to the Human.
""",
    )
    write(
        root / "EXPERIMENTS.md",
        """# Experiment Contract
## Experiment overview
The release uses the reviewed experiment interpretation.
## Result interpretation
The result meaning is approved.
## Relationship to the code repository
No run lifecycle is duplicated here.
""",
    )
    write(
        root / "PAPER_INTERFACES.md",
        """# Paper Interfaces
## Keep the implementation light
Interfaces are Human-readable.
## Interface categories
Identity, terminology, notation, and results.
## Flexible control
Meaning changes require review.
## Change workflow
Consumers are updated together.
## Draft and release
Release interfaces are approved.
""",
    )
    write(
        root / "PUBLICATION.md",
        """# Publication Contract
## Canonical paper
One source.
## Active variants
The approved release variant is active.
## Allowed differences
Presentation only.
## Must not diverge silently
Scientific meaning is shared.
## Human review triggers
Publication requires Human review.
## Build interface
Use the build command.
## Release instances
The release instance is approved.
""",
    )
    write(root / "AGENTS.md", "# Agent Entry\nLoad only relevant context.\n")
    write(root / "DECISIONS.md", "# Decisions\n")
    write(
        root / ".agents/skills/paper-orientation/SKILL.md",
        "# Paper Orientation Skill\n## Reading order\nRead contracts.\n## Context hygiene\nLoad selectively.\n",
    )
    for skill in (
        "control-review",
        "decision-packet",
        "section-writing",
        "style-alignment",
        "manuscript-consistency-review",
        "paper-interface-maintenance",
        "publication-planning",
        "release-review",
    ):
        write(
            root / f".agents/skills/{skill}/SKILL.md",
            f"# {skill}\n## Trigger\nRelevant task.\n## Minimum context\nCurrent contract.\n## Procedure\nReview and act.\n",
        )
    write(
        root / ".agents/skills/section-writing/SKILL.md",
        "# section-writing\n## Trigger\nDraft a section.\n## Minimum context\nCurrent contract.\n## Procedure\nDraft.\nDo not invoke a reviewer persona.\n",
    )
    write(
        root / ".agents/skills/manuscript-consistency-review/SKILL.md",
        "# manuscript-consistency-review\n## Trigger\nUse after the Human identifies a manuscript version as ready.\n## Minimum context\nRead the complete paper.\n## Procedure\nReport findings only. Do not edit files.\n",
    )
    write(root / ".agents/runtime/.gitignore", "*\n!.gitignore\n")
    write(
        root / "paper/main.tex",
        "\\documentclass{article}\n\\begin{document}\nReady.\n\\end{document}\n",
    )
    write(root / "paper/macros.tex", "% approved interfaces\n")


class ContractChecks(unittest.TestCase):
    def test_factory_draft_passes(self) -> None:
        result = run(ROOT, "draft")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_factory_release_blocks_visible_placeholders(self) -> None:
        result = run(ROOT, "release")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release placeholder", result.stdout)

    def test_completed_fixture_passes_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            completed_fixture(fixture)
            result = run(fixture, "release")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_section_writing_requires_no_reviewer_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            completed_fixture(fixture)
            path = fixture / ".agents/skills/section-writing/SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace(
                "Do not invoke a reviewer persona.", "Review the manuscript."
            ), encoding="utf-8")
            result = run(fixture, "draft")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must prohibit reviewer passes during drafting", result.stdout)

    def test_consistency_review_requires_findings_only_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            completed_fixture(fixture)
            path = fixture / ".agents/skills/manuscript-consistency-review/SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace(
                "Report findings only.", "Rewrite the manuscript."
            ), encoding="utf-8")
            result = run(fixture, "draft")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required boundary: Report findings only", result.stdout)


if __name__ == "__main__":
    unittest.main()
