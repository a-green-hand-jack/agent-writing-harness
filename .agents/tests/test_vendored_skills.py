from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-vendored-skills.py"

WRAPPERS = (
    "ccf-common",
    "ccf-experiment-designer",
    "ccf-humanization",
    "ccf-idea-optimizer",
    "ccf-idea-reviewer",
    "ccf-integrity-auditor",
    "ccf-literature-monitor",
    "ccf-literature-searcher",
    "ccf-paper-reviewer",
    "ccf-paper-to-exemplar",
    "ccf-paper-writer",
    "ccf-pipeline-orchestrator",
    "ccf-project-scaffolder",
    "ccf-rebuttal-writer",
    "ccf-skill-forger",
    "ccf-submission-checker",
    "ccf-visual-composer",
    "writing-dna-skill",
    "lieflat-less-ai-tone",
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(root: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
        env=merged,
    )


def fixture(root: Path) -> None:
    """Minimal valid vendor tree plus all 19 wrappers and a routing router."""
    vendor_files = {
        "ccfa-skills/LICENSE": "MIT\n",
        "ccfa-skills/ccf-common/SKILL.md": "# common\n",
        "ccfa-skills/ccf-common/scripts/check_markdown_links.py": "#!/usr/bin/env python3\n",
        "ccfa-skills/ccf-common/scripts/check_path_privacy.py": "#!/usr/bin/env python3\n",
        "ccfa-skills/ccf-experiment-designer/SKILL.md": "# experiment\n",
        "ccfa-skills/ccf-humanization/SKILL.md": "# humanization\n",
        "ccfa-skills/ccf-idea-optimizer/SKILL.md": "# idea optimizer\n",
        "ccfa-skills/ccf-idea-reviewer/SKILL.md": "# idea reviewer\n",
        "ccfa-skills/ccf-integrity-auditor/SKILL.md": "# integrity\n",
        "ccfa-skills/ccf-literature-monitor/SKILL.md": "# monitor\n",
        "ccfa-skills/ccf-literature-searcher/SKILL.md": "# searcher\n",
        "ccfa-skills/ccf-paper-reviewer/SKILL.md": "# reviewer\n",
        "ccfa-skills/ccf-paper-to-exemplar/SKILL.md": "# exemplar\n",
        "ccfa-skills/ccf-paper-writer/SKILL.md": "# writer\n",
        "ccfa-skills/ccf-pipeline-orchestrator/SKILL.md": "# pipeline\n",
        "ccfa-skills/ccf-project-scaffolder/SKILL.md": "# scaffolder\n",
        "ccfa-skills/ccf-rebuttal-writer/SKILL.md": "# rebuttal\n",
        "ccfa-skills/ccf-skill-forger/SKILL.md": "# forger\n",
        "ccfa-skills/ccf-submission-checker/SKILL.md": "# submission\n",
        "ccfa-skills/ccf-visual-composer/SKILL.md": "# visual\n",
        "writing-dna-skill/LICENSE": "MIT\n",
        "writing-dna-skill/SKILL.md": "# writing dna\n",
        "writing-dna-skill/skills/lieflat-less-ai-tone/SKILL.md": "# lieflat\n",
    }
    files: dict[str, dict[str, str]] = {}
    for rel, text in vendor_files.items():
        path = root / ".agents/vendor" / rel
        write(path, text)
        prefix, inner = rel.split("/", 1)
        files.setdefault(prefix, {})[inner] = hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "schema_version": "paper-vendored-skills-v1",
        "sources": [
            {
                "name": "CCFA-Skills",
                "url": "https://example.invalid/ccfa",
                "ref": "v0.0.0",
                "commit": "0" * 40,
                "license": "MIT",
                "license_file": "ccfa-skills/LICENSE",
            },
            {
                "name": "writing-dna-skill",
                "url": "https://example.invalid/writing-dna",
                "ref": None,
                "commit": "1" * 40,
                "license": "MIT",
                "license_file": "writing-dna-skill/LICENSE",
            },
        ],
        "excluded": [],
        "wrappers": list(WRAPPERS),
        "files": files,
    }
    write(
        root / ".agents/dependencies/vendored-skills/provenance.json",
        json.dumps(manifest) + "\n",
    )

    router_lines = ["# Router\n"]
    for name in WRAPPERS:
        vendor = (
            ".agents/vendor/ccfa-skills/" + name + "/SKILL.md"
            if name.startswith("ccf-")
            else ".agents/vendor/writing-dna-skill/skills/lieflat-less-ai-tone/SKILL.md"
            if name == "lieflat-less-ai-tone"
            else ".agents/vendor/writing-dna-skill/SKILL.md"
        )
        write(
            root / f".agents/skills/{name}/SKILL.md",
            f"---\nname: {name}\ndescription: Use for focused work.\n---\n\n# {name}\n\n"
            f"- Skill: `{vendor}`\n",
        )
        router_lines.append(f"- {name} -> `.agents/skills/{name}/SKILL.md`")
    write(root / "AGENTS.md", "\n".join(router_lines) + "\n")


class VendoredSkillsChecks(unittest.TestCase):
    def test_repository_vendor_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env = {"PYTHONPYCACHEPREFIX": str(Path(directory) / "pycache")}
            result = run(ROOT, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_modified_vendor_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            target = root / ".agents/vendor/ccfa-skills/ccf-common/SKILL.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nEDIT\n", encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hash mismatch", result.stdout)

    def test_missing_vendor_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / ".agents/vendor/ccfa-skills/ccf-common/SKILL.md").unlink()
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing from vendor tree", result.stdout)

    def test_unrecorded_vendor_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/vendor/ccfa-skills/ccf-common/references/extra.md", "x\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not recorded in the manifest", result.stdout)

    def test_vendor_symlink_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/vendor/ccfa-skills/ccf-common/references/target.md", "x\n")
            (root / ".agents/vendor/ccfa-skills/ccf-common/references/link.md").symlink_to(
                "target.md"
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink is forbidden", result.stdout)

    def test_forbidden_pdf_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/vendor/ccfa-skills/ccf-common/references/paper.pdf", "%PDF\n")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("violates exclusion boundary", result.stdout)

    def test_vendor_pycache_tolerated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(
                root / ".agents/vendor/ccfa-skills/ccf-common/__pycache__/x.cpython-312.pyc",
                "pyc",
            )
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_required_vendor_script_missing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            rel = "ccfa-skills/ccf-common/scripts/check_markdown_links.py"
            (root / ".agents/vendor" / rel).unlink()
            manifest = root / ".agents/dependencies/vendored-skills/provenance.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"]["ccfa-skills"].pop("ccf-common/scripts/check_markdown_links.py")
            manifest.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("verify.sh depends on vendored script", result.stdout)

    def test_required_vendor_script_unrecorded_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            manifest = root / ".agents/dependencies/vendored-skills/provenance.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"]["ccfa-skills"].pop("ccf-common/scripts/check_path_privacy.py")
            manifest.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("verify.sh depends on vendored script", result.stdout)

    def test_missing_license_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / ".agents/vendor/ccfa-skills/LICENSE").unlink()
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing license file", result.stdout)

    def test_missing_wrapper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / ".agents/skills/ccf-paper-writer/SKILL.md").unlink()
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing wrapper skill", result.stdout)

    def test_wrapper_with_missing_vendor_target_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            wrapper = root / ".agents/skills/ccf-paper-writer/SKILL.md"
            wrapper.write_text(
                wrapper.read_text(encoding="utf-8")
                + "\n- Skill: `.agents/vendor/ccfa-skills/ccf-paper-writer/missing.md`\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("vendor target missing", result.stdout)

    def test_wrapper_target_outside_vendor_tree_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            write(root / ".agents/outside.md", "outside\n")
            wrapper = root / ".agents/skills/ccf-paper-writer/SKILL.md"
            wrapper.write_text(
                wrapper.read_text(encoding="utf-8")
                + "\n- Skill: `.agents/outside.md`\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("vendor target outside vendor tree", result.stdout)

    def test_wrapper_target_mismatched_skill_name_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            wrapper = root / ".agents/skills/ccf-paper-writer/SKILL.md"
            wrapper.write_text(
                wrapper.read_text(encoding="utf-8")
                + "\n- Skill: `.agents/vendor/ccfa-skills/ccf-experiment-designer/SKILL.md`\n",
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match skill name", result.stdout)

    def test_unrouted_wrapper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            router = root / "AGENTS.md"
            router.write_text(
                router.read_text(encoding="utf-8").replace(
                    "- ccf-paper-writer -> `.agents/skills/ccf-paper-writer/SKILL.md`\n",
                    "",
                ),
                encoding="utf-8",
            )
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not route vendored skill", result.stdout)

    def test_unsupported_manifest_schema_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            manifest = root / ".agents/dependencies/vendored-skills/provenance.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["schema_version"] = "paper-vendored-skills-v999"
            manifest.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported vendored-skills manifest schema", result.stderr)


if __name__ == "__main__":
    unittest.main()
