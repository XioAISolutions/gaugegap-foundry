from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    import pyqpanda  # noqa: F401
    from gaugegap.originq_runner import (
        originq_counts_to_z_observables,
        originq_readiness,
        run_local_cpuqvm,
    )
    ORIGINQ_AVAILABLE = True
except ImportError:
    ORIGINQ_AVAILABLE = False


@unittest.skipUnless(ORIGINQ_AVAILABLE, "pyqpanda not installed")
class TestOriginQCPUQVM(unittest.TestCase):
    def test_domain_wall_time_zero(self):
        result = run_local_cpuqvm(
            n_sites=4, exchange_coupling=1.0, transverse_field=0.8,
            time=0.0, steps=1, initial_state="domain_wall", shots=200,
        )
        self.assertEqual(result["provider"], "originq-local")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(sum(result["counts"].values()), 200)

    def test_zeros_time_zero(self):
        result = run_local_cpuqvm(
            n_sites=4, exchange_coupling=1.0, transverse_field=0.0,
            time=0.0, steps=1, initial_state="zeros", shots=100,
        )
        self.assertIn("0000", result["counts"])
        self.assertEqual(result["counts"]["0000"], 100)

    def test_trotter_dynamics(self):
        result = run_local_cpuqvm(
            n_sites=4, exchange_coupling=1.0, transverse_field=0.8,
            time=0.5, steps=4, initial_state="domain_wall", shots=500,
        )
        self.assertGreater(len(result["counts"]), 0)
        self.assertEqual(sum(result["counts"].values()), 500)

    def test_initial_states(self):
        for state in ["zeros", "ones", "domain_wall"]:
            result = run_local_cpuqvm(
                n_sites=4, exchange_coupling=1.0, transverse_field=0.0,
                time=0.0, steps=1, initial_state=state, shots=50,
            )
            self.assertEqual(result["status"], "completed")


@unittest.skipUnless(ORIGINQ_AVAILABLE, "pyqpanda not installed")
class TestOriginQObservables(unittest.TestCase):
    def test_all_zeros_state(self):
        counts = {"0000": 100}
        obs = originq_counts_to_z_observables(counts, n_sites=4)
        self.assertEqual(len(obs["z"]), 4)
        self.assertEqual(len(obs["zz"]), 3)
        for z_val in obs["z"]:
            self.assertAlmostEqual(z_val, 1.0)
        for zz_val in obs["zz"]:
            self.assertAlmostEqual(zz_val, 1.0)

    def test_all_ones_state(self):
        counts = {"1111": 100}
        obs = originq_counts_to_z_observables(counts, n_sites=4)
        for z_val in obs["z"]:
            self.assertAlmostEqual(z_val, -1.0)
        for zz_val in obs["zz"]:
            self.assertAlmostEqual(zz_val, 1.0)

    def test_mixed_counts(self):
        counts = {"0000": 50, "1111": 50}
        obs = originq_counts_to_z_observables(counts, n_sites=4)
        for z_val in obs["z"]:
            self.assertAlmostEqual(z_val, 0.0)
        for zz_val in obs["zz"]:
            self.assertAlmostEqual(zz_val, 1.0)
        self.assertEqual(obs["shots"], 100)


@unittest.skipUnless(ORIGINQ_AVAILABLE, "pyqpanda not installed")
class TestOriginQReadiness(unittest.TestCase):
    def test_readiness_without_probe(self):
        r = originq_readiness(probe=False)
        self.assertTrue(r["dependency_present"])
        self.assertEqual(r["status"], "not_probed")

    def test_readiness_with_probe(self):
        r = originq_readiness(probe=True)
        self.assertEqual(r["status"], "local_ok")


if __name__ == "__main__":
    unittest.main()
