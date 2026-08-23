from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-vendored-skill-evals.py"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def fixture(root: Path) -> tuple[Path, Path, Path]:
    scenarios_path = root / ".agents/evals/vendored-skills/scenarios.json"
    fixtures_path = root / ".agents/evals/vendored-skills/fixtures.json"
    provenance_path = root / ".agents/dependencies/vendored-skills/provenance.json"
    scenarios_path.parent.mkdir(parents=True)
    provenance_path.parent.mkdir(parents=True)
    scenarios_path.write_bytes(
        (ROOT / ".agents/evals/vendored-skills/scenarios.json").read_bytes()
    )
    fixtures_path.write_bytes(
        (ROOT / ".agents/evals/vendored-skills/fixtures.json").read_bytes()
    )
    provenance_path.write_bytes(
        (ROOT / ".agents/dependencies/vendored-skills/provenance.json").read_bytes()
    )
    shutil.copytree(ROOT / ".agents/skills", root / ".agents/skills")
    return scenarios_path, fixtures_path, provenance_path


class VendoredSkillEvaluationTests(unittest.TestCase):
    def test_repository_scenarios_pass(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_optimizer_no_selection_boundary_is_locked(self) -> None:
        wrapper = (ROOT / ".agents/skills/ccf-idea-optimizer/SKILL.md").read_text(
            encoding="utf-8"
        )
        frontmatter, _, body = wrapper.partition("\n---\n")
        scenarios = json.loads(
            (ROOT / ".agents/evals/vendored-skills/scenarios.json").read_text(
                encoding="utf-8"
            )
        )
        scenario = next(
            item for item in scenarios["scenarios"] if item["id"] == "idea-routes-unsearched"
        )
        override_marker = "## Mandatory local override (before canonical content)"
        self.assertIn("Binding local protocol:", frontmatter)
        self.assertIn("conflicting upstream selection and output instructions are disabled", frontmatter)
        self.assertIn("neutral peer candidates only", frontmatter)
        self.assertIn("primary, lead, focus, default, fallback, recommendation, pivot, recommended-next, preferred ordering", frontmatter)
        self.assertIn("same fields and comparable depth for every candidate", frontmatter)
        self.assertIn("selection and output instructions are disabled even when upstream is read", frontmatter)
        self.assertIn(override_marker, body)
        self.assertLess(body.index(override_marker), body.index("## Canonical content"))
        self.assertIn("binding local contract, not advisory guidance", body)
        self.assertIn("Conflicting upstream selection and output instructions are disabled", body)
        self.assertIn("Best development candidate", body)
        self.assertIn("ccf-idea-reviewer", body)
        self.assertIn("Human decision through `decision-packet`", body)
        self.assertIn("more than one candidate, route, or concretization", frontmatter)
        self.assertIn("even when they came from one Human seed", body)
        self.assertIn("## Complete local workflow", body)
        self.assertIn("## Exact peer-candidate output schema", body)
        self.assertIn("exact same fields and comparable depth", body)
        for field in (
            "Candidate ID:",
            "Parent seed and operation:",
            "Target problem:",
            "Gap and root challenge:",
            "Core insight:",
            "Method mechanism:",
            "Innovation type and boundary:",
            "Discriminating evidence sketch:",
            "Novelty and closest-work status:",
            "Assumptions, limitations, and missing inputs:",
            "Candidate-specific tradeoffs:",
        ):
            self.assertIn(field, body)
        self.assertIn("strongest-route core text", body)
        self.assertIn("references/idea-intake.md", body)
        self.assertIn("references/frontier-ideation.md", body)
        self.assertIn("references/literature-grounded-evolution.md", body)
        self.assertIn("never authorizes the optimizer to compare or select", body)
        self.assertIn("neutral peer candidates", body)
        self.assertIn("primary, lead, focus, default, fallback, pivot, recommendation", body)
        self.assertIn("### Complete local workflow", body)
        self.assertIn("same fields and comparable depth", body)
        self.assertIn("thesis, method blueprint, innovation boundary, evidence package, or action plan", body)
        self.assertIn("Those references are inactive reference material", body)
        self.assertIn("Lead Route", body)
        self.assertIn("Structurally Different Fallback", body)
        self.assertIn("Run the pre-return forbidden-output audit", body)
        self.assertIn("remove any selection-bearing label, ordering, recommendation, pivot, or asymmetric expansion", body)
        self.assertIn("End with the neutral handoff below and stop", body)
        self.assertIn("comparison and selection are deferred to `ccf-idea-reviewer`", body)
        self.assertIn("Human decision through `decision-packet`", body)
        must = " ".join(scenario["must"])
        must_not = " ".join(scenario["must_not"])
        self.assertIn("ccf-idea-reviewer only on explicit Human request", must)
        self.assertIn("Human decision through decision-packet", must)
        for phrase in (
            "strongest, best, preferred, winning, recommended, or fallback",
            "emit a lead or primary route",
            "emit a pivot or recommended-next route",
            "order candidates by quality",
            "asymmetrically expand one candidate",
            "compare, rank, recommend, or select among routes",
            "Best development candidate",
        ):
            self.assertIn(phrase, must_not)

    def test_missing_wrapper_scenario_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenarios_path, _, _ = fixture(root)
            scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
            scenarios["scenarios"] = scenarios["scenarios"][1:]
            scenarios_path.write_text(json.dumps(scenarios), encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing vendored skill scenarios", result.stdout)

    def test_empty_forbidden_behavior_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenarios_path, _, _ = fixture(root)
            scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
            scenarios["scenarios"][0]["must_not"] = []
            scenarios_path.write_text(json.dumps(scenarios), encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires non-empty must_not", result.stdout)

    def test_provenance_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, provenance_path = fixture(root)
            provenance_path.write_bytes(provenance_path.read_bytes() + b"\n")

            result = run(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("provenance hash mismatch", result.stdout)

    def test_required_exact_output_cannot_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenarios_path, fixtures_path, _ = fixture(root)
            scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
            scenario_id = next(
                item["id"]
                for item in scenarios["scenarios"]
                if item.get("requires_exact_output")
            )
            fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
            fixtures["fixtures"][scenario_id].pop("expected_output")
            fixture_bytes = (json.dumps(fixtures) + "\n").encode("utf-8")
            fixtures_path.write_bytes(fixture_bytes)
            scenarios["fixture_bundle"]["sha256"] = hashlib.sha256(
                fixture_bytes
            ).hexdigest()
            scenarios_path.write_text(json.dumps(scenarios), encoding="utf-8")

            result = run(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires exact expected_output", result.stdout)

    def test_removing_wrapper_from_all_registries_still_fails_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenarios_path, fixtures_path, provenance_path = fixture(root)
            removed = "ccf-common"
            shutil.rmtree(root / ".agents/skills" / removed)

            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            provenance["wrappers"].remove(removed)
            provenance_bytes = (json.dumps(provenance) + "\n").encode("utf-8")
            provenance_path.write_bytes(provenance_bytes)

            scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
            removed_scenario = next(
                item for item in scenarios["scenarios"] if item["skill"] == removed
            )
            scenarios["scenarios"].remove(removed_scenario)
            scenarios["provenance_sha256"] = hashlib.sha256(
                provenance_bytes
            ).hexdigest()
            fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
            fixtures["fixtures"].pop(removed_scenario["id"])
            fixture_bytes = (json.dumps(fixtures) + "\n").encode("utf-8")
            fixtures_path.write_bytes(fixture_bytes)
            scenarios["fixture_bundle"]["sha256"] = hashlib.sha256(
                fixture_bytes
            ).hexdigest()
            scenarios_path.write_text(json.dumps(scenarios), encoding="utf-8")

            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected 19 vendored wrapper directories", result.stdout)


if __name__ == "__main__":
    unittest.main()
