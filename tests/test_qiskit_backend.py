from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.qiskit_backend import qiskit_available, qiskit_mass_gap, qiskit_matrix
from gaugegap.z2_chain import hamiltonian_dense, mass_gap


@unittest.skipUnless(qiskit_available(), "Qiskit optional dependency is not installed")
class QiskitBackendTests(unittest.TestCase):
    def test_qiskit_operator_matches_dense_hamiltonian(self) -> None:
        exact = hamiltonian_dense(n_sites=3, exchange_coupling=1.0, transverse_field=0.7)
        qiskit = qiskit_matrix(n_sites=3, exchange_coupling=1.0, transverse_field=0.7)
        self.assertTrue(np.allclose(qiskit, exact))

    def test_qiskit_gap_matches_exact_gap(self) -> None:
        exact_gap = mass_gap(n_sites=4, exchange_coupling=1.0, transverse_field=0.8)
        qiskit_gap = qiskit_mass_gap(n_sites=4, exchange_coupling=1.0, transverse_field=0.8)
        self.assertTrue(np.allclose(qiskit_gap, exact_gap))


if __name__ == "__main__":
    unittest.main()
