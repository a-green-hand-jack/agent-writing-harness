from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORRECTIONS = ROOT / ".agents/tools/check-reference-corrections.py"
INTEGRITY = ROOT / ".agents/tools/check-reference-integrity.py"
ENV_HELPER = ROOT / ".agents/tools/_reference_env.py"
FORMAT_HELPER = ROOT / ".agents/tools/_validate-bibtex-with-pybtex.py"
CORRECTION_HELPER = ROOT / ".agents/tools/_validate-bibtex-correction.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prepare(root: Path, bib: str = "") -> None:
    write(root / ".agents/tools/check-reference-integrity.py", INTEGRITY.read_text(encoding="utf-8"))
    write(root / ".agents/tools/_reference_env.py", ENV_HELPER.read_text(encoding="utf-8"))
    write(root / ".agents/tools/_validate-bibtex-with-pybtex.py", FORMAT_HELPER.read_text(encoding="utf-8"))
    write(root / ".agents/tools/_validate-bibtex-correction.py", CORRECTION_HELPER.read_text(encoding="utf-8"))
    write(root / ".agents/dependencies/reference-integrity/uv.lock", "fixture lock\n")
    write(root / ".agents/template-sync.json", '{"reference_integrity":{"adopted":true}}\n')
    write(
        root / "PUBLICATION.md",
        """<!-- REFERENCE-INTEGRITY:START -->
```json
{"schema_version":"paper-reference-integrity-policy-v1","enforcement":"enforced","ledger":"references/ledger.json","bibliography":"paper/refs.bib"}
```
<!-- REFERENCE-INTEGRITY:END -->
""",
    )
    write(root / "paper/refs.bib", "% REFERENCE_INTEGRITY_REQUIRED: references/ledger.json\n" + bib)
    keys = ["real"] if bib else []
    references = [{
        "citation_key": key,
        "status": "verified",
        "identifiers": {"doi": "10.0000/example"},
        "verification": {"sources": ["crossref"], "checked_at": "2026-08-08"},
        "human_review": {"state": "human-confirmed", "rationale": "fixture"},
    } for key in keys]
    write(root / "references/ledger.json", json.dumps({
        "schema_version": "paper-reference-ledger-v1",
        "references": references,
        "citation_usages": [],
        "claim_evidence": [],
    }))


def run(root: Path, uv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CORRECTIONS), "--root", str(root), "--uv", uv, "--timeout", "5"],
        text=True, capture_output=True, check=False,
    )


def fake_uv(root: Path, action: str = "unchanged", mutate: bool = False) -> Path:
    runner = root / "fake-uv"
    write(
        runner,
        f"""#!/usr/bin/env python3
import json, pathlib, shutil, sys
if 'bibtex-update' in sys.argv:
    assert '--in-place' not in sys.argv and '--dedupe' not in sys.argv and '--rekey' not in sys.argv
    assert '--use-scholarly' not in sys.argv and '--zotero' not in sys.argv
    assert sys.argv[sys.argv.index('--max-workers') + 1] == '1'
    source = pathlib.Path(sys.argv[sys.argv.index('bibtex-update') + 1])
    candidate = pathlib.Path(sys.argv[sys.argv.index('--output') + 1])
    report = pathlib.Path(sys.argv[sys.argv.index('--report') + 1])
    candidate.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, candidate)
    report.write_text(json.dumps({{
        'file': str(source), 'key_old': 'real', 'key_new': 'real',
        'doi_old': None, 'doi_new': None, 'action': {action!r},
        'method': None, 'confidence': 0.0, 'title_old': 'T', 'title_new': 'T'
    }}) + '\\n')
    {"pathlib.Path('paper/refs.bib').write_text('mutated')" if mutate else "pass"}
elif any('_validate-bibtex-correction.py' in arg for arg in sys.argv):
    target = pathlib.Path(sys.argv[-1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({{
        'schema_version': 'paper-reference-correction-validation-v1',
        'passed': True,
        'changed_keys': {"['real']" if action in {"upgraded", "field_filled"} else "[]"},
        'incomplete_keys': {"['real']" if action == "failed" else "[]"},
        'errors': []
    }}) + '\\n')
else:
    target = pathlib.Path(sys.argv[-1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{{}}\\n')
""",
    )
    runner.chmod(0o755)
    return runner


class ReferenceCorrectionTests(unittest.TestCase):
    def test_empty_bibliography_skips_without_uv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(root)
            result = run(root, "missing-uv")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/corrections/run.json").read_text())
            self.assertEqual(summary["outcome"], "skipped")
            self.assertFalse(summary["rewrites_bibliography"])

    def test_candidate_is_generated_without_changing_canonical_bibliography(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bib = "@article{real, author={A}, title={T}, journal={J}, year={2026}}\n"
            prepare(root, bib)
            before = (root / "paper/refs.bib").read_bytes()
            result = run(root, str(fake_uv(root, "upgraded")))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((root / "paper/refs.bib").read_bytes(), before)
            summary = json.loads((root / "dist/reference-integrity/corrections/run.json").read_text())
            self.assertEqual(summary["outcome"], "candidates_found")
            self.assertEqual(summary["changed_keys"], ["real"])
            self.assertFalse(summary["approves_bibliography_changes"])
            self.assertFalse(summary["approves_claim_support"])

    def test_canonical_mutation_is_a_safety_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(root, "@article{real, author={A}, title={T}, journal={J}, year={2026}}\n")
            result = run(root, str(fake_uv(root, mutate=True)))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            summary = json.loads((root / "dist/reference-integrity/corrections/run.json").read_text())
            self.assertEqual(summary["outcome"], "unsafe_output")

    def test_local_env_is_allowlisted_and_does_not_override_exported_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root / ".env", "OPENALEX_API_KEY=local\nS2_API_KEY=semantic\n")
            spec = importlib.util.spec_from_file_location("test_reference_env", ENV_HELPER)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with mock.patch.dict(os.environ, {"OPENALEX_API_KEY": "exported"}, clear=False):
                loaded = module.load_reference_env(root)
                self.assertEqual(os.environ["OPENALEX_API_KEY"], "exported")
                self.assertEqual(os.environ["S2_API_KEY"], "semantic")
                self.assertEqual(loaded, ["S2_API_KEY"])

            write(root / ".env", "UNSAFE=value\n")
            with self.assertRaisesRegex(ValueError, "unsupported key"):
                module.load_reference_env(root)


if __name__ == "__main__":
    unittest.main()
