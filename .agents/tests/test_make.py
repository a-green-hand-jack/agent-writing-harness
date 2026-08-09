from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fixture(root: Path) -> None:
    shutil.copy2(ROOT / "Makefile", root / "Makefile")
    (root / "paper").mkdir()


class MakeChecks(unittest.TestCase):
    def test_clean_removes_only_owned_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            owned = (
                root / "paper/main.pdf",
                root / "paper/main-anonymous.aux",
                root / "paper/main-camera-ready.log",
                root / "paper/main-arxiv.synctex.gz",
            )
            preserved = (
                root / "paper/main-source.pdf",
                root / "paper/main-analysis.log",
                root / "paper/keep.pdf",
            )
            for path in owned + preserved:
                path.write_bytes(b"sentinel")

            result = subprocess.run(
                ["make", "clean"], cwd=root, text=True, capture_output=True, check=False
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(all(not path.exists() for path in owned))
            self.assertTrue(all(path.is_file() for path in preserved))

    def test_unknown_variant_is_rejected_before_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)

            result = subprocess.run(
                ["make", "pdf", "VARIANT=unknown"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported VARIANT=unknown", result.stderr)


if __name__ == "__main__":
    unittest.main()
