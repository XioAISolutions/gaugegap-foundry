from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from gaugegap.braket_runner import (
        braket_counts_to_z_observables,
        braket_readiness,
        build_tfim_trotter_braket,
        run_local_simulator,
        CLOUD_DEVICES,
    )
    BRAKET_AVAILABLE = True
except ImportError:
    BRAKET_AVAILABLE = False


@unittest.skipUnless(BRAKET_AVAILABLE, "amazon-braket-sdk not installed")
class TestBraketLocalSimulator(unittest.TestCase):
    def test_bell_state_counts(self):
        from braket.circuits import Circuit
        c = Circuit().h(0).cnot(0, 1)
        result = run_local_simulator(c, shots=200)
        self.assertEqual(result["provider"], "braket-local")
        self.assertEqual(result["status"], "completed")
        self.assertIn("00", result["counts"])
        self.assertIn("11", result["counts"])
        total = sum(result["counts"].values())
        self.assertEqual(total, 200)

    def test_tfim_trotter_braket_runs(self):
        circuit = build_tfim_trotter_braket(
            n_sites=4, exchange_coupling=1.0, transverse_field=0.8,
            time=0.5, steps=2, initial_state="domain_wall",
        )
        result = run_local_simulator(circuit, shots=100)
        self.assertEqual(result["status"], "completed")
        self.assertGreater(len(result["counts"]), 0)

    def test_z_observables_from_counts(self):
        counts = {"0000": 50, "1111": 50}
        obs = braket_counts_to_z_observables(counts, n_sites=4)
        self.assertEqual(len(obs["z"]), 4)
        self.assertEqual(len(obs["zz"]), 3)
        for z_val in obs["z"]:
            self.assertAlmostEqual(z_val, 0.0, places=10)
        for zz_val in obs["zz"]:
            self.assertAlmostEqual(zz_val, 1.0, places=10)

    def test_initial_states(self):
        for state in ["zeros", "ones", "domain_wall"]:
            circuit = build_tfim_trotter_braket(
                n_sites=4, exchange_coupling=1.0, transverse_field=0.0,
                time=0.0, steps=1, initial_state=state,
            )
            result = run_local_simulator(circuit, shots=50)
            self.assertEqual(result["status"], "completed")


@unittest.skipUnless(BRAKET_AVAILABLE, "amazon-braket-sdk not installed")
class TestBraketReadiness(unittest.TestCase):
    def test_readiness_without_probe(self):
        r = braket_readiness(probe=False)
        self.assertTrue(r["dependency_present"])
        self.assertTrue(r["local_simulator_available"])
        self.assertEqual(r["status"], "not_probed")

    def test_readiness_with_local_probe(self):
        r = braket_readiness(probe=True)
        self.assertIn(r["status"], ["local_ok", "cloud_ok", "cloud_probe_failed"])


@unittest.skipUnless(BRAKET_AVAILABLE, "amazon-braket-sdk not installed")
class TestCloudDeviceRegistry(unittest.TestCase):
    def test_known_devices(self):
        self.assertIn("ionq-aria1", CLOUD_DEVICES)
        self.assertIn("ionq-forte1", CLOUD_DEVICES)
        self.assertIn("rigetti-ankaa2", CLOUD_DEVICES)
        self.assertIn("quera-aquila", CLOUD_DEVICES)
        self.assertIn("sv1", CLOUD_DEVICES)
        for name, arn in CLOUD_DEVICES.items():
            self.assertTrue(arn.startswith("arn:aws:braket"))


if __name__ == "__main__":
    unittest.main()
