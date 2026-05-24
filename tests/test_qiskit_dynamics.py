from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.qiskit_backend import qiskit_available
from gaugegap.qiskit_dynamics import aer_sample_z_observables, build_tfim_trotter_circuit, statevector_z_observables


@unittest.skipUnless(qiskit_available(), "Qiskit optional dependency is not installed")
class QiskitDynamicsTests(unittest.TestCase):
    def test_zero_state_time_zero_observables(self) -> None:
        circuit = build_tfim_trotter_circuit(4, 1.0, 0.8, time=0.0, steps=1, initial_state="zeros")
        observed = statevector_z_observables(circuit, n_sites=4)
        self.assertTrue(np.allclose(observed["z"], [1.0, 1.0, 1.0, 1.0]))
        self.assertTrue(np.allclose(observed["zz"], [1.0, 1.0, 1.0]))

    def test_domain_wall_time_zero_observables(self) -> None:
        circuit = build_tfim_trotter_circuit(4, 1.0, 0.8, time=0.0, steps=1, initial_state="domain_wall")
        observed = statevector_z_observables(circuit, n_sites=4)
        self.assertTrue(np.allclose(observed["z"], [1.0, 1.0, -1.0, -1.0]))
        self.assertTrue(np.allclose(observed["zz"], [1.0, -1.0, 1.0]))

    def test_aer_sampler_zero_state_time_zero_observables(self) -> None:
        circuit = build_tfim_trotter_circuit(4, 1.0, 0.8, time=0.0, steps=1, initial_state="zeros", measure=True)
        observed = aer_sample_z_observables(circuit, n_sites=4, shots=128)
        self.assertTrue(np.allclose(observed["z"], [1.0, 1.0, 1.0, 1.0]))
        self.assertTrue(np.allclose(observed["zz"], [1.0, 1.0, 1.0]))


if __name__ == "__main__":
    unittest.main()
