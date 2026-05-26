from __future__ import annotations

import unittest

import numpy as np

from gaugegap.models.z2_plaquette import hamiltonian_dense, pauli_terms
from gaugegap.quantum.pauli_export import (
    pauli_terms_to_dense,
    qiskit_available,
    qiskit_matrix,
    z2_plaquette_pauli_dense,
)


class PauliExportTests(unittest.TestCase):
    def test_dense_replica_equals_direct_hamiltonian(self) -> None:
        direct = hamiltonian_dense(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.2)
        replica = z2_plaquette_pauli_dense(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.2)
        self.assertTrue(np.allclose(direct, replica, atol=1e-12))

    def test_ordering_sensitive_two_plaquette_replica(self) -> None:
        direct = hamiltonian_dense(n_plaquettes=2, plaquette_coupling=0.9, transverse_field=0.15)
        replica = pauli_terms_to_dense(pauli_terms(n_plaquettes=2, plaquette_coupling=0.9, transverse_field=0.15))
        self.assertTrue(np.allclose(direct, replica, atol=1e-12))

    def test_rejects_malformed_terms(self) -> None:
        with self.assertRaises(ValueError):
            pauli_terms_to_dense([])
        with self.assertRaises(ValueError):
            pauli_terms_to_dense([("X", 1.0), ("II", 1.0)])
        with self.assertRaises(ValueError):
            pauli_terms_to_dense([("A", 1.0)])
        with self.assertRaises(ValueError):
            pauli_terms_to_dense([("X", float("inf"))])
        with self.assertRaises(ValueError):
            pauli_terms_to_dense([("X" * 13, 1.0)])

    def test_qiskit_matrix_preserves_dense_ordering_when_available(self) -> None:
        if not qiskit_available():
            self.skipTest("Qiskit is not installed")
        direct = hamiltonian_dense(n_plaquettes=2, plaquette_coupling=0.9, transverse_field=0.15)
        qiskit_dense = qiskit_matrix(n_plaquettes=2, plaquette_coupling=0.9, transverse_field=0.15)
        self.assertTrue(np.allclose(direct, qiskit_dense, atol=1e-12))


if __name__ == "__main__":
    unittest.main()
