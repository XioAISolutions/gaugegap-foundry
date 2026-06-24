"""Test the physical-limits capstone runner (all members pass on one report)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestPhysicalLimitsCapstone(unittest.TestCase):
    def test_capstone_all_checks_pass(self):
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "run_physical_limits.py"),
                 "--output-dir", d, "--skip-audit"],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads((Path(d) / "physical-limits.json").read_text())
            self.assertTrue(payload["all_checks_pass"])
            # all six currency members present and passing
            for name in ("speed_limit_respected", "time_frequency_duality",
                         "ergotropy_no_free_energy", "branch_count_bracketed",
                         "landauer_cost_positive", "bekenstein_respected",
                         "warp_needs_negative_energy", "cherenkov_cone_valid",
                         "lieb_robinson_lightcone",
                         "compton_schwarzschild_planck_floor",
                         "quantum_zeno_freezes"):
                self.assertTrue(payload["checks"][name], name)
            # every certificate is hole-free
            for k, cert in payload["certificates"].items():
                self.assertNotIn("sorry", cert, k)
                self.assertNotIn("Admitted", cert, k)
            # no operator bridge unless requested
            self.assertIsNone(payload["operator_bridge"])

    def test_operator_registry_bridge(self):
        # --operator ties the certified-spectral registry to the QSL web member
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "run_physical_limits.py"),
                 "--operator", "berry_keating_xp", "--operator-size", "6",
                 "--output-dir", d, "--skip-audit"],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads((Path(d) / "physical-limits.json").read_text())
            self.assertTrue(payload["all_checks_pass"])
            self.assertTrue(payload["checks"]["operator_qsl_respected"])
            bridge = payload["operator_bridge"]
            self.assertEqual(bridge["operator"], "berry_keating_xp")
            self.assertTrue(bridge["respects_qsl"])
            self.assertGreaterEqual(bridge["evolution_time"], bridge["tau_qsl"])
            self.assertNotIn("Admitted", bridge["coq"])


if __name__ == "__main__":
    unittest.main()
