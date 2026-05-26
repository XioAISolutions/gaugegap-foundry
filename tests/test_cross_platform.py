from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    import qiskit  # noqa: F401
    import braket  # noqa: F401
    import pyqpanda  # noqa: F401
    ALL_BACKENDS = True
except ImportError:
    ALL_BACKENDS = False


@unittest.skipUnless(ALL_BACKENDS, "requires qiskit + braket + pyqpanda")
class TestCrossPlatformValidation(unittest.TestCase):
    def test_all_simulators_agree(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_cross_platform import run_validation

        result = run_validation(
            n_sites=4, times=[0.0, 0.5], initial_states=["domain_wall"],
            shots=512, steps=2,
        )
        summary = result["summary"]
        self.assertGreater(summary["total_comparisons"], 0)
        self.assertEqual(summary["fail_count"], 0, f"Failures: {summary}")
        self.assertIn("originq-cpuqvm", summary["backends_tested"])
        self.assertIn("braket-local", summary["backends_tested"])
        self.assertIn("aer-sampler", summary["backends_tested"])


if __name__ == "__main__":
    unittest.main()
