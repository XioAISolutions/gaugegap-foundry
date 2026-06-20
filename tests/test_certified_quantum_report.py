"""Test the certified-quantum capstone report (all primitives, one operator)."""
from __future__ import annotations
import importlib.util, sys, tempfile, warnings
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")


def _load():
    p = ROOT / "scripts" / "run_certified_quantum_report.py"
    spec = importlib.util.spec_from_file_location("cqr", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


class TestCertifiedQuantumReport(unittest.TestCase):
    def test_all_checks_pass_xp(self):
        m = _load()
        with tempfile.TemporaryDirectory() as d:
            argv = ["prog", "--operator", "berry_keating_xp", "--n-basis", "8",
                    "--output-dir", d, "--skip-audit"]
            old = sys.argv; sys.argv = argv
            try:
                rc = m.main()
            finally:
                sys.argv = old
            self.assertEqual(rc, 0)
            import json
            data = json.loads((Path(d) / "certified-quantum.json").read_text())
            self.assertTrue(data["all_checks_pass"])
            # every primitive's check is present and True
            for name in ("interval_bracket_contains_E0", "temple_bracket_contains_E0",
                         "validation_esprit_krylov_certified", "qsvt_transform_certified",
                         "open_system_valid_steady_state"):
                self.assertTrue(data["checks"][name], msg=name)


if __name__ == "__main__":
    unittest.main()
