from __future__ import annotations

import unittest

import numpy as np

from gaugegap.models.z2_plaquette import hamiltonian_dense, model_metadata, pauli_terms


class Z2PlaquetteTests(unittest.TestCase):
    def test_hamiltonian_shape_and_hermitian(self) -> None:
        matrix = hamiltonian_dense(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.2)
        self.assertEqual(matrix.shape, (16, 16))
        self.assertTrue(np.allclose(matrix, matrix.T.conj()))

    def test_pauli_terms_are_explicit(self) -> None:
        terms = pauli_terms(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.2)
        labels = [label for label, _ in terms]
        self.assertIn("ZZZZ", labels)
        self.assertEqual(len(terms), 5)

    def test_metadata_claim_boundary(self) -> None:
        metadata = model_metadata()
        self.assertIn("no continuum Yang-Mills", metadata["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
