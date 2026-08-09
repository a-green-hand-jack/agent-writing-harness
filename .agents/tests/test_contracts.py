from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-paper-contracts.py"
F7_REQUIREMENTS = (
    ("control-review", "F7-CR-001-v1", "independent semantic choices"),
    ("decision-packet", "F7-DP-001-v1", "neutral recommendation"),
    (
        "section-writing",
        "F7-SW-001-v1",
        "introduces, fabricates, removes, or materially changes",
    ),
    (
        "manuscript-consistency-review",
        "F7-MCR-001-v1",
        "every conflicting or affected surface found",
    ),
    ("reference-repair", "F7-RR-001-v1", "initial audit baseline"),
    ("template-sync", "F7-TS-001-v1", "state the review boundary"),
)


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
        root / ".agents/skills/control-review/SKILL.md",
        "# control-review\n## Trigger\nReview meaning.\n## Minimum context\nCurrent contract.\n## Procedure\n<!-- paper-skill-contract: F7-CR-001-v1 -->\nFor independent semantic choices, use a separate Human approval gate for each; approval of one choice does not approve another.\n",
    )
    write(
        root / ".agents/skills/decision-packet/SKILL.md",
        "# decision-packet\n## Trigger\nRequest a choice.\n## Minimum context\nCurrent contract.\n## Procedure\n<!-- paper-skill-contract: F7-DP-001-v1 -->\nUse a neutral recommendation with stated criteria and tradeoffs. Give each choice a separate focused packet and separate Human approval gate for each.\n",
    )
    write(
        root / ".agents/skills/section-writing/SKILL.md",
        "# section-writing\n## Trigger\nDraft a section.\n## Minimum context\nCurrent contract.\n## Procedure\n<!-- paper-skill-contract: F7-SW-001-v1 -->\nWhen a prompt introduces, fabricates, removes, or materially changes a citation or claim-support request, inspect `REFERENCES.md` and `references/ledger.json` before drafting.\nDo not invoke a reviewer persona.\n",
    )
    write(
        root / ".agents/skills/manuscript-consistency-review/SKILL.md",
        "# manuscript-consistency-review\n## Trigger\nUse after the Human identifies a manuscript version as ready.\n## Minimum context\nRead the complete paper.\n## Procedure\n<!-- paper-skill-contract: F7-MCR-001-v1 -->\nReport findings only. Do not edit files. Enumerate every conflicting or affected surface found with exact file and line references.\n",
    )
    write(
        root / ".agents/skills/reference-repair/SKILL.md",
        "# reference-repair\n## Trigger\nRepair a reference.\n## Minimum context\nCurrent entry.\n## Procedure\n<!-- paper-skill-contract: F7-RR-001-v1 -->\nBefore any edit, run and preserve checks as the initial audit baseline.\n",
    )
    write(
        root / ".agents/skills/template-sync/SKILL.md",
        "# template-sync\n## Trigger\nSync a template.\n## Minimum context\nCurrent plan.\n## Procedure\n<!-- paper-skill-contract: F7-TS-001-v1 -->\nBefore applying any safe change, explain why paths were classified and state the review boundary; no classification authorizes a semantic change.\n",
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

    def test_f7_valid_contract_declarations_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            completed_fixture(fixture)
            result = run(fixture, "draft")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_f7_missing_contract_declarations_fail(self) -> None:
        for skill, requirement_id, _ in F7_REQUIREMENTS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as directory:
                fixture = Path(directory)
                completed_fixture(fixture)
                path = fixture / f".agents/skills/{skill}/SKILL.md"
                declaration = f"<!-- paper-skill-contract: {requirement_id} -->"
                path.write_text(
                    path.read_text(encoding="utf-8").replace(declaration + "\n", ""),
                    encoding="utf-8",
                )
                result = run(fixture, "draft")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"missing exact contract declaration: {declaration}", result.stdout)

    def test_f7_malformed_contract_declarations_fail(self) -> None:
        for skill, requirement_id, _ in F7_REQUIREMENTS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as directory:
                fixture = Path(directory)
                completed_fixture(fixture)
                path = fixture / f".agents/skills/{skill}/SKILL.md"
                declaration = f"<!-- paper-skill-contract: {requirement_id} -->"
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        declaration, f"<!-- paper-skill-contract: {requirement_id}-malformed -->"
                    ),
                    encoding="utf-8",
                )
                result = run(fixture, "draft")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"missing exact contract declaration: {declaration}", result.stdout)

    def test_f7_declarations_in_fenced_examples_are_inactive(self) -> None:
        for skill, requirement_id, _ in F7_REQUIREMENTS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as directory:
                fixture = Path(directory)
                completed_fixture(fixture)
                path = fixture / f".agents/skills/{skill}/SKILL.md"
                declaration = f"<!-- paper-skill-contract: {requirement_id} -->"
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        declaration, f"```markdown\n{declaration}\n```"
                    ),
                    encoding="utf-8",
                )
                result = run(fixture, "draft")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"missing exact contract declaration: {declaration}", result.stdout)

    def test_f7_negated_old_prose_does_not_replace_contract_declarations(self) -> None:
        for skill, requirement_id, old_phrase in F7_REQUIREMENTS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as directory:
                fixture = Path(directory)
                completed_fixture(fixture)
                path = fixture / f".agents/skills/{skill}/SKILL.md"
                declaration = f"<!-- paper-skill-contract: {requirement_id} -->"
                text = path.read_text(encoding="utf-8").replace(declaration, "")
                text += f"\nThis skill must not satisfy {old_phrase}.\n"
                path.write_text(text, encoding="utf-8")
                result = run(fixture, "draft")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"missing exact contract declaration: {declaration}", result.stdout)


if __name__ == "__main__":
    unittest.main()
