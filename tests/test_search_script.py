from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class SearchScriptSmokeTests(unittest.TestCase):
    def test_search_gap_candidates_script_smoke(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "search_gap_candidates.py"),
                    "--output-dir",
                    tmp,
                    "--n-plaquettes",
                    "1",
                    "--plaquette-couplings",
                    "1.0",
                    "--field-points",
                    "2",
                    "--max-candidates",
                    "1",
                    "--run-id",
                    "test-run",
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"stdout={proc.stdout}\nstderr={proc.stderr}")
            self.assertTrue((Path(tmp) / "gaugegap-search-0001-candidates.jsonl").exists())
            self.assertTrue((Path(tmp) / "gaugegap-search-0001-ranking.md").exists())
            self.assertTrue((Path(tmp) / "dossiers").exists())


if __name__ == "__main__":
    unittest.main()
