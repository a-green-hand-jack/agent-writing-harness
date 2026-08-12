from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/check-release-records.py"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def fixture(root: Path, record: str | None = None) -> Path:
    records = root / "releases/records"
    records.mkdir(parents=True)
    (root / "releases/README.md").write_text("# Releases\n", encoding="utf-8")
    (records / "README.md").write_text("# Release Records\n", encoding="utf-8")
    if record is not None:
        (records / "test-release.md").write_text(record, encoding="utf-8")
    return records


def valid_record(**replacements: str) -> str:
    values = {
        "status": "candidate",
        "variant": "anonymous",
        "profile": "release",
        "release_ready": "true",
        "source": "a" * 64,
        "manifest": "b" * 64,
        "approval": "pending",
    }
    values.update(replacements)
    return f"""# Release test-release

- Status: `{values['status']}`
- Variant: `{values['variant']}`
- Profile: `{values['profile']}`
- Release ready: `{values['release_ready']}`
- Source fingerprint: `{values['source']}`
- Manifest SHA-256: `{values['manifest']}`
- Human approval: `{values['approval']}`

## Artifacts

None.

## Notes

Fixture.
"""


class ReleaseRecordChecks(unittest.TestCase):
    def test_repository_records_pass(self) -> None:
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_valid_candidate_approved_and_published_records_pass(self) -> None:
        records = (
            valid_record(),
            valid_record(status="approved", approval="Approved by Cher [id:@cher] on 2026-08-09"),
            valid_record(status="approved", approval="Approved by Ludwig van Beethoven [id:@lvb] on 2026-08-09"),
            valid_record(status="published", approval="Approved by José García [id:@jgarcia] on 2026-08-09"),
            valid_record(status="published", approval="Approved by [id:@reviewer-42] on 2026-08-09"),
        )
        for record in records:
            with self.subTest(status=record.splitlines()[2]):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    fixture(root, record)
                    result = run(root)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_malformed_required_values_fail_with_reasons(self) -> None:
        cases = (
            ("variant", "", "invalid variant value"),
            ("profile", "definitely-not-a-profile", "invalid profile"),
            ("release_ready", "perhaps", "invalid release ready value"),
            ("source", "", "invalid source fingerprint value"),
            ("manifest", "not-a-checksum", "invalid manifest sha-256"),
        )
        for field, value, reason in cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    fixture(root, valid_record(**{field: value}))
                    result = run(root)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(reason, result.stdout.lower())

    def test_free_form_negated_and_malformed_human_approval_fails(self) -> None:
        approvals = (
            "no human approved this",
            "Nobody approved this",
            "no reviewer available",
            "human unavailable",
            "approval is awaited",
            "A. Researcher approved this on 2026-08-09",
            "Approved by A. Researcher",
            "Approved by A. Researcher on 2026-02-30",
            "approved by A. Researcher on 2026-08-09",
            "Approved by  on 2026-08-09",
            "Approved by Nobody on 2026-08-09",
            "Approved by no one on 2026-08-09",
            "Approved by none on 2026-08-09",
            "Approved by pending on 2026-08-09",
            "Approved by todo on 2026-08-09",
            "Approved by unknown on 2026-08-09",
            "Approved by Nobody! on 2026-08-09",
            "Approved by none. on 2026-08-09",
            "Approved by (n/a) on 2026-08-09",
            "Approved by Ｎｏｂｏｄｙ！ on 2026-08-09",
            "Approved by no-human available on 2026-08-09",
            "Approved by not—approved on 2026-08-09",
            "Approved by without approval on 2026-08-09",
            "Approved by awaiting approval on 2026-08-09",
            "Approved by approval...pending on 2026-08-09",
            "Approved by `reviewer` on 2026-08-09",
            "Approved by reviewer\x07 on 2026-08-09",
            "Approved by A. Researcher on 2026-08-09 because nobody approved it",
            "Approved by A. Researcher [id:@reviewer] on 2026-02-30",
            "Approved by A. Researcher [id:reviewer] on 2026-08-09",
            "Approved by A. Researcher [id:@reviewer handle] on 2026-08-09",
            "Approved by A. Researcher [id:@-reviewer] on 2026-08-09",
            "Approved by A. [Researcher] [id:@reviewer] on 2026-08-09",
            "Approved by `A. Researcher` [id:@reviewer] on 2026-08-09",
            "Approved by A. Researcher [id:@reviewer] on 2026-08-09\x07",
        )
        for approval in approvals:
            with self.subTest(approval=approval), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root, valid_record(status="approved", approval=approval))
                result = run(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("lacks Human approval", result.stdout)

    def test_non_approved_status_may_remain_pending(self) -> None:
        for status in ("candidate", "superseded", "withdrawn"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root, valid_record(status=status, approval="pending"))
                result = run(root)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
