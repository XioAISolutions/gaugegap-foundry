from __future__ import annotations

import unittest

import numpy as np

from gaugegap.models.z2_plaquette import hamiltonian_dense
from gaugegap.quantum.vqe_gap import ansatz_state, estimate_gap_statevector


class VQEGAPTests(unittest.TestCase):
    def test_statevector_result_is_finite_and_nonnegative(self) -> None:
        matrix = hamiltonian_dense()
        result = estimate_gap_statevector(matrix, n_qubits=4, layers=2, samples=8, seed=1)
        self.assertTrue(np.isfinite(result.gap))
        self.assertGreaterEqual(result.gap, 0.0)
        self.assertEqual(result.backend, "local_numpy_statevector_vqe_style")

    def test_ansatz_state_is_normalized(self) -> None:
        state = ansatz_state(np.zeros(4), n_qubits=2, layers=2)
        self.assertAlmostEqual(float(np.linalg.norm(state)), 1.0)

    def test_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            estimate_gap_statevector(np.eye(2), n_qubits=0)
        with self.assertRaises(ValueError):
            estimate_gap_statevector(np.eye(2), n_qubits=1, samples=3)
        with self.assertRaises(ValueError):
            estimate_gap_statevector(np.array([[0.0, 1.0], [0.0, 0.0]]), n_qubits=1)


if __name__ == "__main__":
    unittest.main()
