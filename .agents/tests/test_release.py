from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE_TOOL = ROOT / ".agents/tools/release.py"
CHECK_TOOL = ROOT / ".agents/tools/check-release.py"

spec = importlib.util.spec_from_file_location("paper_release", RELEASE_TOOL)
assert spec and spec.loader
paper_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper_release)


def run_release(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RELEASE_TOOL), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_check(instance: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_TOOL), str(instance)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def fake_instance(root: Path, release_id: str = "test-release-r1") -> Path:
    instance = root / release_id
    artifacts = instance / "artifacts"
    artifacts.mkdir(parents=True)
    artifact = artifacts / "paper.pdf"
    artifact.write_bytes(b"%PDF-test\n")
    sha = paper_release.sha256_file(artifact)
    manifest = {
        "schema_version": "paper-release-instance-v1",
        "release_id": release_id,
        "variant": "anonymous",
        "profile": "draft",
        "release_ready": False,
        "source": {
            "fingerprint_sha256": "a" * 64,
            "git_audit_commit": None,
            "git_dirty": False,
            "paper_interfaces_sha256": "b" * 64,
            "publication_contract_sha256": "c" * 64,
            "variant_config_sha256": "d" * 64,
        },
        "targets": ["pdf"],
        "checks": {"profile_checks": True},
        "artifacts": [
            {
                "target": "pdf",
                "path": "artifacts/paper.pdf",
                "sha256": sha,
                "size": artifact.stat().st_size,
            }
        ],
    }
    (instance / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (instance / "build-report.md").write_text("# Build report\n", encoding="utf-8")
    return instance


class ReleaseInstanceTests(unittest.TestCase):
    def test_reference_evidence_is_release_provenance(self) -> None:
        provenance = paper_release.reference_provenance(ROOT, "release")
        self.assertEqual(provenance["offline_profile"], "release")
        self.assertTrue(provenance["offline_gate_passed"])
        self.assertFalse(provenance["online_metadata_required"])
        self.assertEqual(provenance["ledger_sha256"], paper_release.sha256_file(ROOT / "references/ledger.json"))
        self.assertIn("REFERENCES.md", paper_release.REFERENCE_CONTRACTS)
        self.assertIn("references/ledger.json", paper_release.REFERENCE_CONTRACTS)

    def test_legacy_downstream_release_provenance_remains_inert(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper").mkdir()
            (root / "paper/refs.bib").write_text("@article{legacy, title={Legacy}}\n", encoding="utf-8")
            provenance = paper_release.reference_provenance(root, "draft")
            self.assertEqual(provenance["enforcement"], "not-adopted")
            self.assertEqual(provenance["online_metadata_outcome"], "not-applicable")

    def test_adopted_provenance_does_not_downgrade_after_marker_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".agents").mkdir()
            (root / "paper").mkdir()
            (root / ".agents/template-sync.json").write_text(
                '{"reference_integrity":{"adopted":true}}\n', encoding="utf-8"
            )
            (root / "paper/refs.bib").write_text("", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                paper_release.reference_provenance(root, "release")

    def test_invalid_release_id_fails_before_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_release(
                "build",
                "--id",
                "../bad",
                "--variant",
                "draft",
                "--profile",
                "draft",
                "--targets",
                "pdf",
                "--dist",
                directory,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid release id", result.stderr)

    def test_existing_release_id_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "existing-r1"
            existing.mkdir()
            result = run_release(
                "build",
                "--id",
                "existing-r1",
                "--variant",
                "draft",
                "--profile",
                "draft",
                "--targets",
                "pdf",
                "--dist",
                directory,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("will not be overwritten", result.stderr)

    def test_checksum_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            instance = fake_instance(Path(directory))
            baseline = run_check(instance)
            self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)
            (instance / "artifacts/paper.pdf").write_bytes(b"changed")
            drift = run_check(instance)
            self.assertNotEqual(drift.returncode, 0)
            self.assertIn("checksum drift", drift.stdout)

    def test_record_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance = fake_instance(root)
            record = root / "record.md"
            first = run_release(
                "record",
                "--instance",
                str(instance),
                "--output",
                str(record),
                "--status",
                "candidate",
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = run_release(
                "record",
                "--instance",
                str(instance),
                "--output",
                str(record),
                "--status",
                "candidate",
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("will not be overwritten", second.stderr)

    def test_deterministic_zip_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "b.txt").write_text("b\n", encoding="utf-8")
            (source / "a.txt").write_text("a\n", encoding="utf-8")
            first = root / "first.zip"
            second = root / "second.zip"
            paper_release.deterministic_zip(source, first)
            paper_release.deterministic_zip(source, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_forbidden_zip_surface_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance = fake_instance(root, "zip-boundary-r1")
            zip_path = instance / "artifacts/source.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("main.tex", "main")
                archive.writestr("canonical.tex", "canonical")
                archive.writestr("macros.tex", "macros")
                archive.writestr("refs.bib", "refs")
                archive.writestr(".agents/private.txt", "leak")
            manifest_path = instance / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["targets"] = ["source-zip"]
            manifest["artifacts"] = [
                {
                    "target": "source-zip",
                    "path": "artifacts/source.zip",
                    "sha256": paper_release.sha256_file(zip_path),
                    "size": zip_path.stat().st_size,
                }
            ]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            result = run_check(instance)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden repository surface", result.stdout)


if __name__ == "__main__":
    unittest.main()
