from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agents/tools/release.py"

spec = importlib.util.spec_from_file_location("release_public", TOOL)
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class CleanPackageTests(unittest.TestCase):
    def test_deterministic_zip_excludes_tex_build_products(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "main.tex").write_text("main\n", encoding="utf-8")
            (source / "main.pdf").write_bytes(b"pdf")
            (source / "main.aux").write_text("aux\n", encoding="utf-8")
            figures = source / "figures"
            figures.mkdir()
            (figures / "plot.pdf").write_bytes(b"figure")
            output = root / "source.zip"

            release.deterministic_zip(source, output)

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("main.tex", names)
            self.assertIn("figures/plot.pdf", names)
            self.assertNotIn("main.pdf", names)
            self.assertNotIn("main.aux", names)


if __name__ == "__main__":
    unittest.main()
