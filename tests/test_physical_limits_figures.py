"""Test the physical-limits figure/gallery generator (deterministic, well-formed)."""
import os
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom as minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestPhysicalLimitsFigures(unittest.TestCase):
    def test_generates_wellformed_figures_and_gallery(self):
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "generate_physical_limits_figures.py"),
                 "--output-dir", d],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = Path(d)
            for name in ("web.svg", "ladder.svg", "index.html"):
                self.assertTrue((out / name).exists(), name)
            # SVGs are well-formed XML
            minidom.parse(str(out / "web.svg"))
            minidom.parse(str(out / "ladder.svg"))
            # the gallery references the web diagram and pulls in module figures
            html = (out / "index.html").read_text()
            self.assertIn("web.svg", html)
            self.assertIn("ladder.svg", html)
            self.assertGreaterEqual(len(list(out.glob("*__*.svg"))), 1)

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            for d in (d1, d2):
                subprocess.run(
                    [sys.executable,
                     str(ROOT / "scripts" / "generate_physical_limits_figures.py"),
                     "--output-dir", d], check=True, capture_output=True)
            self.assertEqual((Path(d1) / "web.svg").read_text(),
                             (Path(d2) / "web.svg").read_text())
            self.assertEqual((Path(d1) / "ladder.svg").read_text(),
                             (Path(d2) / "ladder.svg").read_text())


if __name__ == "__main__":
    unittest.main()
