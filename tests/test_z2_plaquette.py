from __future__ import annotations

import unittest

import numpy as np

from gaugegap.models.z2_plaquette import (
    CLAIM_BOUNDARY,
    ground_state_observables,
    hamiltonian_dense,
    model_metadata,
    open_plaquette_chain_layout,
    pauli_label,
    pauli_terms,
    state_observables,
)
from gaugegap.quantum.pauli_export import pauli_terms_to_dense


class Z2PlaquetteTests(unittest.TestCase):
    def test_layout_shares_one_link_between_neighboring_plaquettes(self) -> None:
        layout = open_plaquette_chain_layout(2)
        self.assertEqual(layout.n_qubits, 7)
        self.assertEqual(layout.plaquettes, ((0, 1, 2, 3), (3, 4, 5, 6)))

    def test_hamiltonian_shape_and_hermitian(self) -> None:
        matrix = hamiltonian_dense(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.2)
        self.assertEqual(matrix.shape, (16, 16))
        self.assertTrue(np.allclose(matrix, matrix.T.conj()))

    def test_pauli_terms_are_explicit(self) -> None:
        terms = pauli_terms(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.2)
        labels = [label for label, _ in terms]
        self.assertIn("ZZZZ", labels)
        self.assertEqual(len(terms), 5)

    def test_pauli_label_uses_qiskit_qubit_ordering(self) -> None:
        self.assertEqual(pauli_label(3, {0: "X", 2: "Z"}), "ZIX")

    def test_pauli_dense_replica_matches_direct_dense_for_order_sensitive_case(self) -> None:
        direct = hamiltonian_dense(n_plaquettes=2, plaquette_coupling=0.7, transverse_field=0.3)
        replica = pauli_terms_to_dense(pauli_terms(n_plaquettes=2, plaquette_coupling=0.7, transverse_field=0.3))
        self.assertTrue(np.allclose(direct, replica, atol=1e-12))

    def test_state_observables_for_basis_state(self) -> None:
        layout = open_plaquette_chain_layout(1)
        state = np.zeros(1 << layout.n_qubits)
        state[0] = 1.0
        observables = state_observables(state, layout)
        self.assertEqual(observables["plaquette_z"], [1.0])
        self.assertEqual(observables["mean_plaquette_z"], 1.0)
        self.assertEqual(observables["mean_link_x"], 0.0)

    def test_ground_state_observables_are_finite(self) -> None:
        observables = ground_state_observables(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.2)
        self.assertTrue(np.isfinite(observables["mean_plaquette_z"]))
        self.assertTrue(np.isfinite(observables["mean_link_x"]))

    def test_metadata_claim_boundary(self) -> None:
        metadata = model_metadata()
        self.assertEqual(metadata["claim_boundary"], CLAIM_BOUNDARY)
        self.assertIn("no continuum Yang-Mills", metadata["claim_boundary"])

    def test_bad_inputs_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            open_plaquette_chain_layout(0)
        with self.assertRaises(ValueError):
            hamiltonian_dense(n_plaquettes=10)
        with self.assertRaises(ValueError):
            pauli_label(2, {2: "X"})
        with self.assertRaises(ValueError):
            pauli_terms(transverse_field=float("nan"))


if __name__ == "__main__":
    unittest.main()
