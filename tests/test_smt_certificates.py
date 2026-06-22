"""z3 independently verifies every certified-inequality schema."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    import z3  # noqa: F401
    _HAVE_Z3 = True
except Exception:
    _HAVE_Z3 = False


@unittest.skipUnless(_HAVE_Z3, "z3-solver not installed (optional [smt] extra)")
class TestSMTCertificates(unittest.TestCase):
    def test_all_schemas_machine_verified(self):
        from gaugegap.rigorous.smt_certificates import verify_all
        results = verify_all()
        self.assertGreaterEqual(len(results), 8)
        for r in results:
            self.assertTrue(r.valid, f"z3 failed to verify schema: {r.name}")

    def test_expected_schemas_present(self):
        from gaugegap.rigorous.smt_certificates import verify_all
        names = {r.name for r in verify_all()}
        for expected in ("speed_limit", "time_bandwidth", "ergotropy", "branching",
                         "landauer", "bekenstein", "warp_energy_condition"):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
