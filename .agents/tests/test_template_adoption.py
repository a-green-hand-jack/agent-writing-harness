from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/template-adoption.py"
PAPER_INIT_TOOL = ROOT / ".agents/tools/paper-init.py"
TEMPLATE_SYNC_TOOL = ROOT / ".agents/tools/template-sync.py"
SKILL = ROOT / ".agents/skills/template-adoption/SKILL.md"


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root, check=check)


def write(root: Path, relative: str, text: str, *, executable: bool = False) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@example.com")


def commit_all(root: Path, message: str) -> str:
    git(root, "add", "-A")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD").stdout.strip()


class TemplateAdoptionTests(unittest.TestCase):
    def test_current_repository_installation_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(ROOT), "validate"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_inspect_reports_journal_document_class(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repo(root)
            write(
                root,
                "manuscript.tex",
                "\\documentclass[review]{elsarticle}\n\\begin{document}Paper\\end{document}\n",
            )
            commit_all(root, "journal fixture")
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--root",
                    str(root),
                    "inspect",
                    "--output",
                    "inspection.json",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            inspection = json.loads((root / "inspection.json").read_text(encoding="utf-8"))
            self.assertEqual(inspection["selected_document_class"], "elsarticle")
            self.assertEqual(
                inspection["main_candidates"][0]["document_class_options"], ["review"]
            )

    def test_inspect_reports_journal_style_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repo(root)
            write(
                root,
                "manuscript.tex",
                "\\documentclass[twoside,11pt]{article}\n"
                "\\usepackage{jmlr2e}\n\\begin{document}Paper\\end{document}\n",
            )
            commit_all(root, "journal style fixture")
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--root",
                    str(root),
                    "inspect",
                    "--output",
                    "inspection.json",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            inspection = json.loads((root / "inspection.json").read_text(encoding="utf-8"))
            self.assertEqual(inspection["selected_document_class"], "article")
            self.assertIn("jmlr2e", inspection["selected_latex_packages"])

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.upstream = base / "upstream"
        self.downstream = base / "downstream"
        init_repo(self.upstream)

        tool_target = self.upstream / ".agents/tools/template-adoption.py"
        tool_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TOOL, tool_target)
        skill_target = self.upstream / ".agents/skills/template-adoption/SKILL.md"
        skill_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SKILL, skill_target)
        for relative in (
            ".agents/template-inheritance.json",
            ".agents/tools/_template_inheritance.py",
            ".agents/tools/_paper_profile.py",
            ".agents/tools/check-paper-profile.py",
        ):
            source = ROOT / relative
            target = self.upstream / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        write(
            self.upstream,
            ".agents/tools/template-sync.py",
            """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

if sys.argv[1:] != ["validate"]:
    raise SystemExit(2)
path = Path(".agents/template-sync.json")
if not path.is_file():
    print("missing sync config", file=sys.stderr)
    raise SystemExit(1)
data = json.loads(path.read_text())
if data.get("schema_version") != "paper-template-sync-v1":
    raise SystemExit(1)
print("OK fixture template_sync configuration")
""",
            executable=True,
        )
        write(
            self.upstream,
            ".agents/skills/template-sync/SKILL.md",
            "# Template Sync\n\n## Trigger\nX\n\n## Minimum context\nX\n\n## Procedure\nX\n\n## Safety boundary\nX\n",
        )
        write(
            self.upstream,
            ".agents/tools/verify.sh",
            """#!/usr/bin/env bash
set -euo pipefail
python3 .agents/tools/template-adoption.py validate
python3 .agents/tools/template-sync.py validate
python3 -m unittest discover -s .agents/tests -p 'test_*.py'
echo fixture-verify-ok
""",
            executable=True,
        )
        for checker in (
            "check-structure.py",
            "paper-init.py",
            "check-documentation.py",
            "check-venue-knowledge.py",
            "check-paper-contracts.py",
            "check-paper-interfaces.py",
            "check-reference-integrity.py",
            "check-publication.py",
            "check-release-records.py",
            "overleaf-sync.py",
        ):
            write(self.upstream, f".agents/tools/{checker}", "raise SystemExit(0)\n")
        write(
            self.upstream,
            ".agents/tests/test_fixture.py",
            """import unittest


class FixtureTest(unittest.TestCase):
    def test_fixture(self) -> None:
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
""",
        )
        write(self.upstream, ".agents/tools/helper.py", "UPSTREAM = True\n")
        write(
            self.upstream,
            ".agents/tools/mode-sensitive.py",
            "print('same content')\n",
            executable=True,
        )
        write(self.upstream, ".agents/knowledge/README.md", "# Knowledge\n")
        write(self.upstream, ".agents/ANATOMY.md", "# Agent Sidecar Anatomy\n")
        write(self.upstream, ".agents/runtime/.gitignore", "*\n!.gitignore\n")
        write(self.upstream, ".agents/vendor/README.md", "# Vendored skills\n")
        write(self.upstream, ".agents/vendor/ccfa-skills/LICENSE", "MIT\n")
        write(self.upstream, ".agents/vendor/ccfa-skills/ccf-common/SKILL.md", "# common\n")
        write(self.upstream, ".agents/vendor/ccfa-skills/ccf-paper-writer/SKILL.md", "# writer\n")
        write(self.upstream, ".agents/vendor/writing-dna-skill/LICENSE", "MIT\n")
        write(self.upstream, ".agents/vendor/writing-dna-skill/SKILL.md", "# writing dna\n")
        write(
            self.upstream,
            ".agents/template-sync.json",
            json.dumps(
                {
                    "schema_version": "paper-template-sync-v1",
                    "upstream": {
                        "url": str(self.upstream),
                        "remote": "template",
                        "branch": "main",
                    },
                    "last_synced_commit": None,
                    "always_manual": [],
                    "ignored_paths": [],
                },
                indent=2,
            )
            + "\n",
        )
        write(self.upstream, "README.md", "# Template README\n")
        write(self.upstream, "CONTRIBUTING.md", "# Template Contributing\n")
        write(self.upstream, "PAPER.md", "# Paper contract template\n")
        write(self.upstream, "Makefile", "pdf:\n\t@echo template\n")
        write(
            self.upstream,
            "paper/main.tex",
            "\\documentclass{article}\n\\begin{document}\nTemplate\n\\end{document}\n",
        )
        write(self.upstream, "paper/refs.bib", "@misc{template}\n")
        write(self.upstream, "paper/sections/01_intro.tex", "Template intro\n")
        write(
            self.upstream,
            ".github/workflows/pr-validation.yml",
            "name: template-ci\n",
        )
        self.target = commit_all(self.upstream, "template target")

        init_repo(self.downstream)
        write(
            self.downstream,
            "main.tex",
            """\\documentclass{article}
\\usepackage{conference}
\\begin{document}
\\input{sections/intro}
\\includegraphics{figures/result}
\\bibliography{references}
\\end{document}
""",
        )
        write(
            self.downstream,
            "sections/intro.tex",
            "Existing scientific introduction\n\\input{../tables/results}\n",
        )
        write(
            self.downstream,
            "tables/results.tex",
            "\\begin{tabular}{cc}\nA & B \\\\n\\end{tabular}\n",
        )
        write(self.downstream, "references.bib", "@article{existing}\n")
        figure = self.downstream / "figures/result.pdf"
        figure.parent.mkdir(parents=True, exist_ok=True)
        figure.write_bytes(b"%PDF-1.4 fixture\n")
        write(self.downstream, "conference.sty", "% venue style\n")
        write(self.downstream, "Makefile", "pdf:\n\t@echo existing\n")
        write(
            self.downstream,
            ".agents/paper-build.json",
            json.dumps(
                {
                    "schema_version": "paper-build-profile-v1",
                    "layout": "external-latex",
                    "source_root": ".",
                    "entrypoint": "main.tex",
                    "bibliography": "references.bib",
                    "builds": [
                        {"name": variant, "command": ["make", "pdf", f"VARIANT={variant}"]}
                        for variant in ("draft", "anonymous", "camera-ready", "arxiv")
                    ],
                }
            )
            + "\n",
        )
        write(self.downstream, "experiments/run.py", "print('run experiment')\n")
        write(self.downstream, "experiments/config.yaml", "seed: 1\n")
        write(self.downstream, ".github/workflows/existing.yml", "name: existing-ci\n")
        write(self.downstream, "CLAUDE.md", "# Existing Agent Guidance\n")
        write(self.downstream, "README.md", "# Template README\n")
        write(self.downstream, ".agents/tools/helper.py", "DOWNSTREAM = True\n")
        write(
            self.downstream,
            ".agents/tools/mode-sensitive.py",
            "print('same content')\n",
        )
        self.start_head = commit_all(self.downstream, "existing paper")
        git(self.downstream, "switch", "-c", "chore/template-adoption")
        git(self.downstream, "remote", "add", "template", str(self.upstream))
        git(self.downstream, "fetch", "template", "main")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def tool(self, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        return run(
            [
                sys.executable,
                str(TOOL),
                "--root",
                str(self.downstream),
                "--upstream-url",
                str(self.upstream),
                *args,
            ],
            self.downstream,
            check=check,
        )

    def plan(self) -> dict[str, object]:
        result = self.tool("plan")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        path = self.downstream / ".agents/runtime/template-adoption/plan.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def complete_semantic_migration(self) -> None:
        for contract in (
            "PAPER.md",
            "EXPERIMENTS.md",
            "PAPER_INTERFACES.md",
            "PUBLICATION.md",
            "DECISIONS.md",
        ):
            write(self.downstream, contract, f"# Reviewed {contract}\n")

    def write_external_build_profile(self, *, creates_output: bool) -> None:
        command = "printf '%s' '%PDF fixture' > manuscript.pdf" if creates_output else ":"
        write(self.downstream, "scripts/build-manuscript.sh", f"#!/bin/sh\n{command}\n", executable=True)
        write(self.downstream, ".gitignore", "manuscript.pdf\n")
        write(
            self.downstream,
            ".agents/paper-build.json",
            json.dumps(
                {
                    "schema_version": "paper-build-profile-v1",
                    "layout": "external-latex",
                    "source_root": ".",
                    "entrypoint": "main.tex",
                    "bibliography": "references.bib",
                    "builds": [
                        {
                            "name": "journal",
                            "command": ["sh", "scripts/build-manuscript.sh"],
                            "output": "manuscript.pdf",
                        }
                    ],
                }
            )
            + "\n",
        )

    def test_inspection_detects_existing_repository_surfaces(self) -> None:
        result = self.tool("inspect")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        inspection = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/inspection.json").read_text()
        )
        self.assertEqual(inspection["selected_main"], "main.tex")
        self.assertEqual(inspection["selected_bibliography"], "references.bib")
        mappings = {item["template_surface"]: item for item in inspection["mappings"]}
        self.assertEqual(mappings["paper/sections/"]["candidate"], "sections")
        self.assertEqual(mappings["paper/figures/"]["candidate"], "figures")
        self.assertEqual(mappings["paper/tables/"]["candidate"], "tables")
        self.assertEqual(mappings["EXPERIMENTS.md"]["candidate"], "experiments")
        self.assertEqual(mappings["Makefile"]["candidate"], "Makefile")
        self.assertEqual(mappings[".github/workflows/"]["candidate"], ".github/workflows/existing.yml")
        self.assertEqual(mappings["AGENTS.md"]["candidate"], "CLAUDE.md")

    def test_verify_runs_declared_external_build_and_checks_output(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.write_external_build_profile(creates_output=True)
        verified = self.tool("verify", "--builds")
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/verification.json").read_text()
        )
        self.assertEqual(
            [check["command"] for check in report["checks"]],
            ["bash .agents/tools/verify.sh", "sh scripts/build-manuscript.sh"],
        )
        self.assertTrue(report["checks"][1]["output_ready"])

    def test_verify_fails_when_declared_output_is_missing(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.write_external_build_profile(creates_output=False)
        verified = self.tool("verify", "--builds")
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("expected non-empty build output", verified.stderr)

    def test_verify_rejects_stale_declared_output_and_restores_it(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.write_external_build_profile(creates_output=False)
        (self.downstream / "manuscript.pdf").write_bytes(b"old output")
        verified = self.tool("verify", "--builds")
        self.assertNotEqual(verified.returncode, 0)
        self.assertEqual((self.downstream / "manuscript.pdf").read_bytes(), b"old output")

    def test_verify_rejects_declared_build_that_mutates_repository_state(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.write_external_build_profile(creates_output=True)
        write(
            self.downstream,
            "scripts/build-manuscript.sh",
            "#!/bin/sh\nprintf 'mutation\\n' >> main.tex\nprintf '%s' '%PDF fixture' > manuscript.pdf\n",
            executable=True,
        )
        verified = self.tool("verify", "--builds")
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("changed tracked or non-runtime untracked", verified.stderr)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/verification.json").read_text()
        )
        self.assertFalse(report["repository_unchanged"])

    def test_verify_rejects_declared_build_that_mutates_ignored_authored_input(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.write_external_build_profile(creates_output=True)
        style = self.downstream / "results.out"
        style.write_text("original\n", encoding="utf-8")
        with (self.downstream / ".gitignore").open("a", encoding="utf-8") as ignore:
            ignore.write("results.out\n")
        write(
            self.downstream,
            "scripts/build-manuscript.sh",
            "#!/bin/sh\nprintf 'changed\\n' > results.out\nprintf '%s' '%PDF fixture' > manuscript.pdf\n",
            executable=True,
        )
        verified = self.tool("verify", "--builds")
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("changed tracked or non-runtime untracked", verified.stderr)

    def test_assessment_records_unsafe_declared_output_and_continues(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        write(
            self.downstream,
            ".agents/paper-build.json",
            json.dumps(
                {
                    "schema_version": "paper-build-profile-v1",
                    "layout": "external-latex",
                    "source_root": ".",
                    "entrypoint": "main.tex",
                    "bibliography": "references.bib",
                    "builds": [
                        {
                            "name": "unsafe-output",
                            "command": ["sh", "scripts/build-manuscript.sh"],
                            "output": "conference.sty",
                        }
                    ],
                }
            )
            + "\n",
        )
        assessed = self.tool("assess")
        self.assertNotEqual(assessed.returncode, 0)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/assessment.json").read_text()
        )
        self.assertFalse(report["checks"][-1]["success"])
        self.assertEqual(report["checks"][-1]["returncode"], 125)
        self.assertIn("tracked file", report["checks"][-1]["stderr"])
        self.assertFalse(report["success"])

    def test_verify_records_command_start_failure_without_traceback(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        write(
            self.downstream,
            ".agents/paper-build.json",
            json.dumps(
                {
                    "schema_version": "paper-build-profile-v1",
                    "layout": "external-latex",
                    "source_root": ".",
                    "entrypoint": "main.tex",
                    "bibliography": "references.bib",
                    "builds": [
                        {
                            "name": "missing-tool",
                            "command": ["definitely-missing-paper-build-command"],
                        }
                    ],
                }
            )
            + "\n",
        )
        verified = self.tool("verify", "--builds")
        self.assertNotEqual(verified.returncode, 0)
        self.assertNotIn("Traceback", verified.stderr)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/verification.json").read_text()
        )
        self.assertEqual(report["checks"][-1]["returncode"], 127)
        self.assertIn("cannot start command", report["checks"][-1]["stderr"])

    def test_assessment_skips_canonical_checks_for_external_profile(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.write_external_build_profile(creates_output=True)
        assessed = self.tool("assess")
        self.assertEqual(assessed.returncode, 0, assessed.stdout + assessed.stderr)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/assessment.json").read_text()
        )
        commands = [check["command"] for check in report["checks"]]
        self.assertIn("python3 .agents/tools/check-paper-contracts.py --profile draft", commands)
        self.assertNotIn("python3 .agents/tools/check-paper-interfaces.py", commands)
        self.assertIn("python3 .agents/tools/check-release-records.py", commands)
        self.assertIn("sh scripts/build-manuscript.sh", commands)

    def test_inspection_keeps_all_entrypoint_candidates(self) -> None:
        (self.downstream / ".agents/paper-build.json").unlink()
        for index in range(12):
            write(
                self.downstream,
                f"alternatives/manuscript-{index:02d}.tex",
                "\\documentclass{article}\n\\begin{document}Paper\\end{document}\n",
            )
        result = self.tool("inspect")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        inspection = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/inspection.json").read_text()
        )
        self.assertGreater(len(inspection["main_candidates"]), 10)
        self.assertIn(
            "alternatives/manuscript-11.tex",
            {candidate["path"] for candidate in inspection["main_candidates"]},
        )

    def test_inspection_uses_declared_profile_entrypoint(self) -> None:
        write(
            self.downstream,
            "paper.tex",
            "\\documentclass{article}\n\\begin{document}Declared paper\\end{document}\n",
        )
        profile = json.loads(
            (self.downstream / ".agents/paper-build.json").read_text(encoding="utf-8")
        )
        profile["entrypoint"] = "paper.tex"
        write(self.downstream, "paper/refs.bib", "@misc{alternative}\n")
        (self.downstream / ".agents/paper-build.json").write_text(
            json.dumps(profile) + "\n", encoding="utf-8"
        )

        result = self.tool("inspect")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        inspection = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/inspection.json").read_text()
        )
        self.assertEqual(inspection["selected_main"], "paper.tex")
        self.assertEqual(inspection["selected_bibliography"], "references.bib")
        self.assertEqual(inspection["main_candidates"][0]["path"], "paper.tex")
        self.assertIn(
            "main.tex",
            {candidate["path"] for candidate in inspection["main_candidates"]},
        )

    def test_verify_detects_index_only_mutation_by_verification_command(self) -> None:
        write(
            self.downstream,
            ".agents/tools/verify.sh",
            "#!/usr/bin/env bash\n"
            "printf 'index mutation\\n' > .agents/tools/base.txt\n"
            "git add .agents/tools/base.txt\n"
            "printf 'base-v1\\n' > .agents/tools/base.txt\n",
            executable=True,
        )
        commit_all(self.downstream, "add mutating verifier fixture")
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.write_external_build_profile(creates_output=True)
        verified = self.tool("verify", "--builds")
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("changed tracked or non-runtime untracked", verified.stderr)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/verification.json").read_text()
        )
        self.assertFalse(report["repository_unchanged"])

    def test_verify_rejects_plan_changed_after_apply(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        plan_path = self.downstream / ".agents/runtime/template-adoption/plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["counts"]["manual"] += 1
        plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        refused = self.tool("verify", "--builds")

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("plan no longer matches the applied state", refused.stderr)

    def test_verify_rejects_safe_file_changed_after_apply(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        write(self.downstream, ".agents/tools/template-adoption.py", "changed after apply\n")
        refused = self.tool("verify", "--builds")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("safe adoption changes are not fully applied", refused.stderr)

    def test_verify_rejects_untracked_entries_for_deleted_safe_target(self) -> None:
        module_spec = importlib.util.spec_from_file_location("template_adoption", TOOL)
        self.assertIsNotNone(module_spec)
        self.assertIsNotNone(module_spec.loader)
        sys.path.insert(0, str(TOOL.parent))
        try:
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        paths = (
            ".agents/tools/deleted-safe-file.txt",
            ".agents/tools/deleted-safe-link",
            ".agents/tools/deleted-safe-directory",
        )
        write(self.downstream, paths[0], "recreated after deletion\n")
        (self.downstream / paths[1]).symlink_to("missing-target")
        (self.downstream / paths[2]).mkdir()

        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(module.AdoptionError) as context:
                    module.require_applied_safe_state(
                        self.downstream,
                        {
                            "target_commit": self.target,
                            "items": [{"category": "safe", "path": path}],
                        },
                    )

                self.assertIn(path, str(context.exception))

    def test_verify_rejects_downstream_head_changed_after_apply(self) -> None:
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        commit_all(self.downstream, "checkpoint after adoption apply")

        refused = self.tool("verify", "--builds")

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("HEAD changed after adoption apply", refused.stderr)

    def test_inspection_recursively_resolves_nested_tex_from_main_directory(self) -> None:
        write(
            self.downstream,
            "paper/main.tex",
            "\\documentclass{article}\n\\begin{document}\n\\input{sections/intro}\n\\end{document}\n",
        )
        write(self.downstream, "paper/sections/intro.tex", "\\input{figures/result}\n")
        write(
            self.downstream,
            "paper/figures/result.tex",
            "\\includegraphics{result}\n",
        )
        (self.downstream / "paper/figures/result.pdf").write_bytes(b"%PDF nested fixture\n")
        profile_path = self.downstream / ".agents/paper-build.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["entrypoint"] = "paper/main.tex"
        profile_path.write_text(json.dumps(profile) + "\n", encoding="utf-8")

        result = self.tool("inspect")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        inspection = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/inspection.json").read_text()
        )
        self.assertEqual(inspection["selected_main"], "paper/main.tex")
        self.assertIn("paper/figures/result.tex", inspection["tex_graph"]["files"])
        self.assertIn("paper/figures/result.pdf", inspection["graphics"]["resolved"])
        mappings = {item["template_surface"]: item for item in inspection["mappings"]}
        self.assertEqual(mappings["paper/figures/"]["candidate"], "paper/figures")

    def test_inspection_recognizes_evidenced_custom_build_entrypoint(self) -> None:
        (self.downstream / "Makefile").unlink()
        write(
            self.downstream,
            "README.md",
            "# Existing Paper\n\nBuild with `scripts/build-paper.sh`.\n",
        )
        write(self.downstream, "scripts/build-paper.sh", "#!/usr/bin/env bash\nexit 99\n")
        write(
            self.downstream,
            ".github/workflows/existing.yml",
            "name: existing-ci\nrun: scripts/build-paper.sh\n",
        )

        result = self.tool("inspect")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        inspection = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/inspection.json").read_text()
        )
        self.assertIn("scripts/build-paper.sh", inspection["build_files"])
        mappings = {item["template_surface"]: item for item in inspection["mappings"]}
        self.assertEqual(mappings["Makefile"]["candidate"], "scripts/build-paper.sh")

    def test_inspection_uses_parsed_command_paths_without_name_or_suffix_heuristics(self) -> None:
        (self.downstream / "Makefile").unlink()
        write(self.downstream, "scripts/run.sh", "#!/bin/sh\nexit 91\n")
        write(self.downstream, "tools/render", "#!/bin/sh\nexit 92\n")
        write(self.downstream, "scripts/build-looking.sh", "#!/bin/sh\nexit 93\n")
        write(
            self.downstream,
            "README.md",
            "Build with `scripts/run.sh --release`. The scripts/build-looking.sh file is unrelated.\n",
        )
        write(
            self.downstream,
            ".github/workflows/existing.yml",
            "steps:\n  - run: sh tools/render --paper\n",
        )

        result = self.tool("inspect")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        inspection = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/inspection.json").read_text()
        )
        self.assertIn("scripts/run.sh", inspection["build_files"])
        self.assertIn("tools/render", inspection["build_files"])
        self.assertNotIn("scripts/build-looking.sh", inspection["build_files"])

    def test_plan_classifies_safe_manual_conflict_and_ignored(self) -> None:
        plan = self.plan()
        by_path = {item["path"]: item for item in plan["items"]}
        self.assertEqual(by_path[".agents/tools/template-adoption.py"]["category"], "safe")
        self.assertEqual(by_path[".agents/tools/template-sync.py"]["category"], "safe")
        self.assertEqual(by_path[".agents/template-inheritance.json"]["category"], "safe")
        self.assertEqual(by_path[".agents/tests/test_fixture.py"]["category"], "safe")
        self.assertEqual(by_path[".agents/tools/helper.py"]["category"], "conflict")
        self.assertEqual(by_path[".agents/tools/mode-sensitive.py"]["category"], "conflict")
        self.assertIn("executable mode", by_path[".agents/tools/mode-sensitive.py"]["reason"])
        self.assertEqual(by_path["PAPER.md"]["category"], "manual")
        self.assertEqual(by_path["CONTRIBUTING.md"]["category"], "manual")
        self.assertEqual(by_path["README.md"]["category"], "manual")
        self.assertEqual(by_path["paper/main.tex"]["category"], "manual")
        self.assertEqual(by_path["Makefile"]["category"], "manual")
        self.assertEqual(by_path[".github/workflows/pr-validation.yml"]["category"], "manual")
        self.assertEqual(by_path[".agents/template-sync.json"]["category"], "ignored")

    def test_apply_stages_only_safe_sidecar_and_exports_review_bundle(self) -> None:
        self.plan()
        result = self.tool("apply")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.downstream / ".agents/tools/template-adoption.py").is_file())
        self.assertTrue((self.downstream / ".agents/tools/template-sync.py").is_file())
        self.assertTrue((self.downstream / ".agents/template-inheritance.json").is_file())
        self.assertTrue((self.downstream / ".agents/tests/test_fixture.py").is_file())
        self.assertEqual(
            (self.downstream / ".agents/tools/helper.py").read_text(),
            "DOWNSTREAM = True\n",
        )
        self.assertFalse(
            (self.downstream / ".agents/tools/mode-sensitive.py").stat().st_mode & 0o111
        )
        self.assertFalse((self.downstream / "PAPER.md").exists())
        self.assertFalse((self.downstream / "CONTRIBUTING.md").exists())
        pending = json.loads(
            (self.downstream / ".agents/template-sync.json").read_text(encoding="utf-8")
        )
        self.assertIsNone(pending["last_synced_commit"])
        self.assertIn(self.target, pending["last_sync_note"])
        staged = git(self.downstream, "diff", "--cached", "--name-only").stdout.splitlines()
        self.assertIn(".agents/tools/template-adoption.py", staged)
        self.assertIn(".agents/tests/test_fixture.py", staged)
        self.assertIn(".agents/template-sync.json", staged)
        self.assertNotIn("PAPER.md", staged)
        bundle = self.downstream / ".agents/runtime/template-adoption/merge-bundle"
        self.assertEqual(
            (bundle / "upstream/PAPER.md").read_text(),
            "# Paper contract template\n",
        )
        self.assertTrue((bundle / "downstream/PAPER.md.missing").is_file())
        self.assertEqual(
            (bundle / "downstream/.agents/tools/helper.py").read_text(),
            "DOWNSTREAM = True\n",
        )

    def test_plan_refuses_non_regular_template_entry(self) -> None:
        link = self.upstream / ".agents/tools/unsafe-link"
        link.symlink_to("/tmp/template-adoption-external-target")
        commit_all(self.upstream, "template symlink")
        git(self.downstream, "fetch", "template", "main")

        refused = self.tool("plan")

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("unsupported non-regular entry", refused.stderr)
        self.assertFalse((self.downstream / ".agents/tools/unsafe-link").exists())

    def test_apply_refuses_default_branch_and_dirty_worktree(self) -> None:
        self.plan()
        git(self.downstream, "switch", "main")
        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("default branch", refused.stderr)

        git(self.downstream, "switch", "chore/template-adoption")
        write(self.downstream, "dirty.txt", "dirty\n")
        refused_dirty = self.tool("apply")
        self.assertNotEqual(refused_dirty.returncode, 0)
        self.assertIn("dirty worktree", refused_dirty.stderr)

    def test_apply_refuses_a_different_non_default_branch(self) -> None:
        self.plan()
        git(self.downstream, "switch", "-c", "chore/other-adoption")
        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("branch changed", refused.stderr)

    def test_apply_revalidates_plan_classification_before_writing(self) -> None:
        plan = self.plan()
        for item in plan["items"]:
            if item["path"] == "PAPER.md":
                item["category"] = "safe"
                item["reason"] = "tampered"
                break
        path = self.downstream / ".agents/runtime/template-adoption/plan.json"
        path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("classification no longer matches", refused.stderr)
        self.assertFalse((self.downstream / "PAPER.md").exists())

    def test_plan_refuses_template_target_without_adoption_prerequisites(self) -> None:
        git(self.upstream, "rm", ".agents/skills/template-adoption/SKILL.md")
        commit_all(self.upstream, "remove adoption skill")
        git(self.downstream, "fetch", "template", "main")
        refused = self.tool("plan")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("does not contain adoption prerequisites", refused.stderr)

    def test_apply_refuses_repository_with_reviewed_template_baseline(self) -> None:
        write(
            self.downstream,
            ".agents/template-sync.json",
            json.dumps(
                {
                    "schema_version": "paper-template-sync-v1",
                    "upstream": {
                        "url": str(self.upstream),
                        "remote": "template",
                        "branch": "main",
                    },
                    "last_synced_commit": self.target,
                    "last_synced_at": "2026-08-03T00:00:00+00:00",
                    "last_sync_note": "Already reviewed.",
                    "adoption": {
                        "status": "reviewed",
                        "target_commit": self.target,
                        "reviewed_at": "2026-08-03T00:00:00+00:00",
                        "verification_repository_fingerprint": "a" * 64,
                        "prior_sync_history": [],
                    },
                    "always_manual": [],
                    "ignored_paths": [],
                },
                indent=2,
            )
            + "\n",
        )
        commit_all(self.downstream, "record existing template baseline")
        self.plan()
        refused = self.tool("apply", "--recover-reviewed")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("use template-sync", refused.stderr)

    def test_apply_recovers_invalid_reviewed_provenance_and_preserves_all_metadata(self) -> None:
        prior = {
            "schema_version": "paper-template-sync-v1",
            "upstream": {
                "url": str(self.upstream),
                "remote": "template",
                "branch": "main",
            },
            "last_synced_commit": self.start_head,
            "last_synced_at": "2026-08-03T00:00:00+00:00",
            "last_sync_note": "Trapped reviewed state.",
            "adoption": {
                "status": "reviewed",
                "target_commit": self.target,
                "reviewed_at": "2026-08-03T00:00:00+00:00",
                "verification_repository_fingerprint": "a" * 64,
                "prior_sync_history": [],
            },
            "reference_integrity": {"adopted": True},
            "always_manual": ["local-policy.md"],
            "ignored_paths": ["local-output/"],
            "downstream_extension": {"preserve": True},
        }
        write(
            self.downstream,
            ".agents/template-sync.json",
            json.dumps(prior, indent=2, sort_keys=True) + "\n",
        )
        commit_all(self.downstream, "record invalid reviewed provenance")
        self.plan()

        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--recover-reviewed", refused.stderr)

        recovered = self.tool("apply", "--recover-reviewed")
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        pending = json.loads(
            (self.downstream / ".agents/template-sync.json").read_text(encoding="utf-8")
        )
        history_entry = pending["adoption"]["prior_sync_history"][-1]
        self.assertEqual(history_entry["last_synced_commit"], prior["last_synced_commit"])
        self.assertEqual(history_entry["last_sync_note"], prior["last_sync_note"])
        self.assertEqual(history_entry["reference_integrity"], prior["reference_integrity"])
        self.assertEqual(history_entry["upstream"], prior["upstream"])
        self.assertEqual(history_entry["adoption"], prior["adoption"])

    def test_apply_recovers_reachable_reviewed_baseline_with_invalid_local_metadata(self) -> None:
        prior = {
            "schema_version": "paper-template-sync-v1",
            "upstream": {
                "url": str(self.upstream),
                "remote": "template",
                "branch": "main",
            },
            "last_synced_commit": self.target,
            "last_synced_at": "invalid",
            "last_sync_note": "Malformed reviewed state.",
            "adoption": {
                "status": "reviewed",
                "target_commit": self.target,
                "reviewed_at": "2026-08-03T00:00:00+00:00",
                "verification_repository_fingerprint": "a" * 64,
                "prior_sync_history": [],
            },
            "reference_integrity": {"adopted": True},
            "always_manual": [],
            "ignored_paths": [],
        }
        write(
            self.downstream,
            ".agents/template-sync.json",
            json.dumps(prior, indent=2, sort_keys=True) + "\n",
        )
        commit_all(self.downstream, "record malformed reachable reviewed baseline")
        self.plan()

        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--recover-reviewed", refused.stderr)
        recovered = self.tool("apply", "--recover-reviewed")
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        pending = json.loads(
            (self.downstream / ".agents/template-sync.json").read_text(encoding="utf-8")
        )
        history = pending["adoption"]["prior_sync_history"][-1]
        self.assertIsNone(history["last_synced_commit"])
        self.assertIsNone(history["last_synced_at"])
        self.assertEqual(history["recovery_original_fields"]["last_synced_at"], "invalid")

    def test_apply_requires_reviewed_recovery_for_stale_baseline_metadata(self) -> None:
        write(
            self.downstream,
            ".agents/template-sync.json",
            json.dumps(
                {
                    "schema_version": "paper-template-sync-v1",
                    "upstream": {
                        "url": "https://example.invalid/another-template.git",
                        "remote": "another-template",
                        "branch": "stable",
                    },
                    "last_synced_commit": self.start_head,
                    "last_synced_at": "2026-08-01T00:00:00+00:00",
                    "last_sync_note": "Premature baseline.",
                    "adoption": {
                        "status": "in_progress",
                        "target_commit": self.target,
                        "prior_sync_history": [
                            {
                                "last_synced_at": "invalid",
                                "recovery_original_fields": {"older": "evidence"},
                                "reference_integrity": {"adopted": "unknown"},
                                "upstream": {},
                            }
                        ],
                    },
                    "always_manual": [],
                    "ignored_paths": [],
                },
                indent=2,
            )
            + "\n",
        )
        commit_all(self.downstream, "add stale incomplete-adoption metadata")
        self.plan()
        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--recover-reviewed", refused.stderr)

        recovered = self.tool("apply", "--recover-reviewed")
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        pending = json.loads(
            (self.downstream / ".agents/template-sync.json").read_text(encoding="utf-8")
        )
        self.assertIsNone(pending["last_synced_commit"])
        self.assertEqual(pending["adoption"]["status"], "in_progress")
        self.assertEqual(
            pending["adoption"]["prior_sync_history"][-1]["last_synced_commit"],
            self.start_head,
        )
        self.assertTrue(
            {
                "adoption",
                "last_synced_commit",
                "last_synced_at",
                "last_sync_note",
                "reference_integrity",
                "upstream",
            }.issubset(pending["adoption"]["prior_sync_history"][-1])
        )
        repaired_history = pending["adoption"]["prior_sync_history"][0]
        self.assertIsNone(repaired_history["last_synced_at"])
        self.assertIsNone(repaired_history["reference_integrity"])
        self.assertEqual(repaired_history["upstream"]["remote"], "another-template")
        self.assertEqual(
            repaired_history["recovery_original_fields"]["previous"],
            {"older": "evidence"},
        )
        self.assertEqual(
            repaired_history["recovery_original_fields"]["current"]["upstream"],
            {},
        )
        self.complete_semantic_migration()
        verified = self.tool("verify", "--variants")
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        finalized = self.tool("finalize", "--reviewed")
        self.assertEqual(finalized.returncode, 0, finalized.stdout + finalized.stderr)
        paper_status = run(
            [sys.executable, str(PAPER_INIT_TOOL), "--root", str(self.downstream), "status"],
            self.downstream,
            check=False,
        )
        self.assertEqual(paper_status.returncode, 0, paper_status.stdout + paper_status.stderr)
        self.assertIn("adoption_reviewed", paper_status.stdout)
        sync_status = run(
            [sys.executable, str(TEMPLATE_SYNC_TOOL), "--root", str(self.downstream), "validate"],
            self.downstream,
            check=False,
        )
        self.assertEqual(sync_status.returncode, 0, sync_status.stdout + sync_status.stderr)

    def test_in_progress_contradictions_require_recovery_and_preserve_adoption(self) -> None:
        contradictions = (
            {"last_synced_commit": self.target},
            {"last_synced_at": "2026-08-01T00:00:00+00:00"},
            {"target_commit": "a" * 40},
            {"reviewed_at": "2026-08-01T00:00:00+00:00"},
            {"upstream_url": "https://example.invalid/wrong-template.git"},
        )
        for index, contradiction in enumerate(contradictions):
            with self.subTest(contradiction=contradiction):
                adoption = {
                    "status": "in_progress",
                    "target_commit": contradiction.get("target_commit", self.target),
                    "prior_sync_history": [],
                }
                if "reviewed_at" in contradiction:
                    adoption["reviewed_at"] = contradiction["reviewed_at"]
                config = {
                    "schema_version": "paper-template-sync-v1",
                    "upstream": {
                        "url": contradiction.get("upstream_url", str(self.upstream)),
                        "remote": "template",
                        "branch": "main",
                    },
                    "last_synced_commit": contradiction.get("last_synced_commit"),
                    "last_synced_at": contradiction.get("last_synced_at"),
                    "last_sync_note": "Contradictory pending state.",
                    "adoption": adoption,
                    "always_manual": [],
                    "ignored_paths": [],
                }
                write(
                    self.downstream,
                    ".agents/template-sync.json",
                    json.dumps(config, indent=2) + "\n",
                )
                commit_all(self.downstream, f"contradictory state {index}")
                self.plan()
                refused = self.tool("apply")
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn("--recover-reviewed", refused.stderr)
                recovered = self.tool("apply", "--recover-reviewed")
                self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
                pending = json.loads(
                    (self.downstream / ".agents/template-sync.json").read_text()
                )
                history = pending["adoption"]["prior_sync_history"]
                self.assertEqual(history[-1]["adoption"], adoption)
                git(self.downstream, "reset", "--hard", "HEAD")

    def test_invalid_pending_metadata_requires_explicit_recovery(self) -> None:
        config = {
            "schema_version": "paper-template-sync-v1",
            "upstream": {
                "url": str(self.upstream),
                "remote": "template",
                "branch": "main",
            },
            "last_synced_commit": None,
            "last_synced_at": None,
            "last_sync_note": 123,
            "adoption": {
                "status": "in_progress",
                "target_commit": "invalid",
                "prior_sync_history": [{}],
            },
            "reference_integrity": {"adopted": "unknown"},
            "always_manual": [],
            "ignored_paths": [],
        }
        config.pop("upstream")
        write(
            self.downstream,
            ".agents/template-sync.json",
            json.dumps(config, indent=2, sort_keys=True) + "\n",
        )
        commit_all(self.downstream, "record malformed pending adoption")
        self.plan()

        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--recover-reviewed", refused.stderr)
        recovered = self.tool("apply", "--recover-reviewed")
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        pending = json.loads(
            (self.downstream / ".agents/template-sync.json").read_text(encoding="utf-8")
        )
        history = pending["adoption"]["prior_sync_history"]
        self.assertEqual(history[-1]["recovery_original_fields"]["last_sync_note"], 123)
        self.assertIsNone(history[-1]["recovery_original_fields"]["upstream"])
        self.assertEqual(
            history[-1]["recovery_original_fields"]["reference_integrity"],
            {"adopted": "unknown"},
        )

    def test_recovery_preserves_non_object_history_entries(self) -> None:
        config = {
            "schema_version": "paper-template-sync-v1",
            "upstream": {
                "url": str(self.upstream),
                "remote": "template",
                "branch": "main",
            },
            "last_synced_commit": None,
            "last_synced_at": None,
            "adoption": {
                "status": "in_progress",
                "target_commit": self.target,
                "prior_sync_history": ["raw legacy history"],
            },
            "always_manual": [],
            "ignored_paths": [],
        }
        write(
            self.downstream,
            ".agents/template-sync.json",
            json.dumps(config, indent=2, sort_keys=True) + "\n",
        )
        commit_all(self.downstream, "record non-object history entry")
        self.plan()
        recovered = self.tool("apply", "--recover-reviewed")
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        pending = json.loads(
            (self.downstream / ".agents/template-sync.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            pending["adoption"]["prior_sync_history"][0]["recovery_original_fields"]["raw_entry"],
            "raw legacy history",
        )

    def test_apply_refuses_template_created_marker_before_writing_adoption_state(self) -> None:
        write(self.downstream, ".agents/template-origin.json", "{}\n")
        commit_all(self.downstream, "record template-created marker")
        self.plan()
        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("template adoption must not carry", refused.stderr)
        self.assertFalse((self.downstream / ".agents/template-sync.json").exists())

    def test_reviewed_adoption_remains_valid_after_sync_baseline_advances(self) -> None:
        config = {
            "schema_version": "paper-template-sync-v1",
            "upstream": {"url": str(self.upstream), "remote": "template", "branch": "main"},
            "last_synced_commit": self.start_head,
            "last_synced_at": "2026-08-04T00:00:00+00:00",
            "last_sync_note": "Later reviewed synchronization.",
            "adoption": {
                "status": "reviewed",
                "target_commit": self.target,
                "reviewed_at": "2026-08-03T00:00:00+00:00",
                "verification_repository_fingerprint": "b" * 64,
                "prior_sync_history": [],
            },
            "always_manual": [],
            "ignored_paths": [],
        }
        write(self.downstream, ".agents/template-sync.json", json.dumps(config, indent=2) + "\n")
        commit_all(self.downstream, "advance baseline after reviewed adoption")
        status = self.tool("status")
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn(self.start_head, status.stdout)

    def test_equal_unreviewed_baseline_is_not_adoption_proof(self) -> None:
        write(
            self.downstream,
            ".agents/template-sync.json",
            json.dumps(
                {
                    "schema_version": "paper-template-sync-v1",
                    "upstream": {
                        "url": str(self.upstream),
                        "remote": "template",
                        "branch": "main",
                    },
                    "last_synced_commit": self.target,
                    "always_manual": [],
                    "ignored_paths": [],
                },
                indent=2,
            )
            + "\n",
        )
        commit_all(self.downstream, "add unreviewed equal baseline")
        self.plan()
        refused = self.tool("apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("not trustworthy evidence", refused.stderr)

    def test_plan_refuses_symlinked_agent_control_directory(self) -> None:
        shutil.rmtree(self.downstream / ".agents")
        escaped = Path(self.tmp.name) / "escaped-agent-directory"
        escaped.mkdir()
        (self.downstream / ".agents").symlink_to(escaped, target_is_directory=True)
        commit_all(self.downstream, "replace agent control directory with symlink")

        refused = self.tool("plan")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("symlinked control directory", refused.stderr)
        self.assertFalse((escaped / "runtime/template-adoption/plan.json").exists())

    def test_finalize_reruns_current_full_variant_verification(self) -> None:
        run_log = self.downstream / ".agents/runtime/template-adoption/finalize-runs"
        verify = self.downstream / ".agents/tools/verify.sh"
        verify.write_text(
            "#!/usr/bin/env bash\n"
            "printf 'run\\n' >> .agents/runtime/template-adoption/finalize-runs\n",
            encoding="utf-8",
        )
        commit_all(self.downstream, "add finalize verifier fixture")
        self.plan()
        applied = self.tool("apply")
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.complete_semantic_migration()
        verified = self.tool("verify", "--variants")
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

        finalized = self.tool("finalize", "--reviewed")
        self.assertEqual(finalized.returncode, 0, finalized.stdout + finalized.stderr)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/verification.json").read_text()
        )
        self.assertEqual(len(report["checks"]), 5)
        self.assertTrue(all(check["returncode"] == 0 for check in report["checks"]))
        self.assertEqual(run_log.read_text().splitlines(), ["run", "run"])

    def test_finalize_rejects_coherent_forged_report_when_fresh_commands_fail(self) -> None:
        verify = self.downstream / ".agents/tools/verify.sh"
        verify.write_text(
            "#!/usr/bin/env bash\n"
            "test ! -e .agents/runtime/template-adoption/fail-finalize\n",
            encoding="utf-8",
        )
        commit_all(self.downstream, "add failing verifier fixture")
        self.plan()
        self.assertEqual(self.tool("apply").returncode, 0)
        self.complete_semantic_migration()
        marker = self.downstream / ".agents/runtime/template-adoption/fail-finalize"
        marker.touch()
        failed = self.tool("verify", "--variants")
        self.assertNotEqual(failed.returncode, 0)
        report_path = self.downstream / ".agents/runtime/template-adoption/verification.json"
        self.assertTrue(report_path.is_file())
        report = json.loads(report_path.read_text())
        report["success"] = True
        for check in report["checks"]:
            check["returncode"] = 0
            check["success"] = True
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        refused = self.tool("finalize", "--reviewed")

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("failed during finalize", refused.stderr)

    def test_assessment_collects_multiple_failures_and_cannot_authorize_finalize(self) -> None:
        self.plan()
        applied = self.tool("apply")
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.complete_semantic_migration()
        write(self.downstream, ".agents/tools/check-documentation.py", "raise SystemExit(7)\n")
        write(self.downstream, ".agents/tools/check-publication.py", "raise SystemExit(9)\n")

        assessed = self.tool("assess")
        self.assertNotEqual(assessed.returncode, 0)
        self.assertFalse(any(self.downstream.rglob("__pycache__")))
        self.assertFalse(any(self.downstream.rglob("*.pyc")))
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/assessment.json").read_text()
        )
        self.assertFalse(report["authorizes_finalize"])
        self.assertEqual(len(report["checks"]), 16)
        self.assertEqual(
            report["checks"][0]["command"],
            "python3 -m compileall -q .agents/tools .agents/tests",
        )
        failures = {check["command"]: check["returncode"] for check in report["checks"] if not check["success"]}
        self.assertEqual(failures["python3 .agents/tools/check-documentation.py"], 7)
        self.assertEqual(failures["python3 .agents/tools/check-publication.py"], 9)
        checks = {check["command"]: check for check in report["checks"]}
        compile_check = checks["python3 -m compileall -q .agents/tools .agents/tests"]
        self.assertTrue(compile_check["success"])
        self.assertEqual(compile_check["returncode"], 0)
        self.assertTrue(report["checks"][-1]["command"].endswith("VARIANT=arxiv"))
        self.assertFalse(
            (self.downstream / ".agents/runtime/template-adoption/verification.json").exists()
        )
        refused = self.tool("finalize", "--reviewed")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("verify --variants", refused.stderr)

    def test_custom_plan_is_bound_to_verification_and_finalize(self) -> None:
        relative = ".agents/runtime/template-adoption/custom-plan.json"
        planned = self.tool("plan", "--output", relative)
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertFalse(
            (self.downstream / ".agents/runtime/template-adoption/plan.json").exists()
        )

        applied = self.tool("apply", "--plan", relative)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        verified = self.tool("verify", "--plan", relative, "--variants")
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

        path = self.downstream / relative
        plan = json.loads(path.read_text(encoding="utf-8"))
        plan["inspection"]["mappings"][0]["recommendation"] += " Tampered."
        path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        refused = self.tool("finalize", "--plan", relative, "--reviewed")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("plan no longer matches the applied state", refused.stderr)

    def test_verify_refuses_missing_declared_entrypoint(self) -> None:
        (self.downstream / "main.tex").unlink()
        commit_all(self.downstream, "remove paper entrypoint")
        self.plan()
        applied = self.tool("apply")
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        verified = self.tool("verify", "--variants")
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("entrypoint does not name an existing file", verified.stderr)

    def test_verify_and_finalize_record_first_template_baseline(self) -> None:
        self.plan()
        applied = self.tool("apply")
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.complete_semantic_migration()

        verified = self.tool("verify", "--variants")
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        report = json.loads(
            (self.downstream / ".agents/runtime/template-adoption/verification.json").read_text()
        )
        self.assertTrue(report["success"])
        self.assertTrue(report["variants_verified"])
        self.assertEqual(report["target_commit"], self.target)
        self.assertEqual(len(report["repository_fingerprint"]), 64)

        unreviewed = self.tool("finalize")
        self.assertNotEqual(unreviewed.returncode, 0)
        self.assertIn("--reviewed", unreviewed.stderr)

        finalized = self.tool("finalize", "--reviewed")
        self.assertEqual(finalized.returncode, 0, finalized.stdout + finalized.stderr)
        config = json.loads(
            (self.downstream / ".agents/template-sync.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["last_synced_commit"], self.target)
        self.assertEqual(config["adoption"]["status"], "reviewed")
        self.assertEqual(config["upstream"]["url"], str(self.upstream))
        staged = git(self.downstream, "diff", "--cached", "--name-only").stdout.splitlines()
        self.assertIn(".agents/template-sync.json", staged)


if __name__ == "__main__":
    unittest.main()
