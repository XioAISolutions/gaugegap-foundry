from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.gaugegap_u1 import (
    u1_electric_field_expectation,
    u1_link_operators,
    u1_mass_gap,
    u1_plaquette_hamiltonian,
    u1_spectrum,
    u1_wilson_loop_expectation,
)


class TestU1LinkOperators(unittest.TestCase):
    def test_dimensions(self):
        E, Up, Um = u1_link_operators(2)
        self.assertEqual(E.shape, (5, 5))
        self.assertEqual(Up.shape, (5, 5))
        self.assertEqual(Um.shape, (5, 5))

    def test_electric_diagonal(self):
        E, _, _ = u1_link_operators(3)
        expected = np.diag([-3, -2, -1, 0, 1, 2, 3], 0)
        np.testing.assert_allclose(E, expected, atol=1e-14)

    def test_raising_lowering_adjoint(self):
        _, Up, Um = u1_link_operators(2)
        np.testing.assert_allclose(Um, Up.T, atol=1e-14)

    def test_raising_periodic(self):
        _, Up, _ = u1_link_operators(1)
        self.assertAlmostEqual(Up[0, 2], 1.0)


class TestU1PlaquetteHamiltonian(unittest.TestCase):
    def test_hermiticity(self):
        H = u1_plaquette_hamiltonian(2, 1.0, 0.5, 1)
        np.testing.assert_allclose(H, H.T, atol=1e-12)

    def test_dimension(self):
        H = u1_plaquette_hamiltonian(2, 1.0, 1.0, 2)
        link_dim = 2 * 2 + 1
        self.assertEqual(H.shape, (link_dim ** 2, link_dim ** 2))

    def test_pure_electric_limit(self):
        H = u1_plaquette_hamiltonian(2, 1.0, 0.0, 2)
        eigs = np.linalg.eigvalsh(H)
        self.assertAlmostEqual(eigs[0], 0.0, places=10)

    def test_invalid_n_links(self):
        with self.assertRaises(ValueError):
            u1_plaquette_hamiltonian(1, 1.0, 1.0, 1)

    def test_invalid_truncation(self):
        with self.assertRaises(ValueError):
            u1_plaquette_hamiltonian(2, 1.0, 1.0, 0)


class TestU1Spectrum(unittest.TestCase):
    def test_real_eigenvalues(self):
        eigs = u1_spectrum(2, 1.0, 0.5, 1)
        np.testing.assert_allclose(eigs.imag, 0.0, atol=1e-10)

    def test_ground_state_below_first_excited(self):
        eigs = u1_spectrum(2, 1.0, 1.0, 2)
        self.assertLess(eigs[0], eigs[1])


class TestU1MassGap(unittest.TestCase):
    def test_positive_gap(self):
        gap, e0, e1 = u1_mass_gap(2, 1.0, 0.5, 2)
        self.assertGreater(gap, 0.0)
        self.assertAlmostEqual(gap, e1 - e0, places=12)

    def test_gap_decreases_with_magnetic_coupling(self):
        gap_low, _, _ = u1_mass_gap(2, 1.0, 0.1, 2)
        gap_high, _, _ = u1_mass_gap(2, 1.0, 2.0, 2)
        self.assertNotAlmostEqual(gap_low, gap_high, places=3)


class TestU1Observables(unittest.TestCase):
    def test_electric_field_nonnegative(self):
        H = u1_plaquette_hamiltonian(2, 1.0, 0.5, 1)
        eigs, vecs = np.linalg.eigh(H)
        ground = vecs[:, 0]
        e2 = u1_electric_field_expectation(ground, 0, 2, 1)
        self.assertGreaterEqual(e2, -1e-10)

    def test_wilson_loop_bounded(self):
        H = u1_plaquette_hamiltonian(2, 1.0, 0.5, 1)
        eigs, vecs = np.linalg.eigh(H)
        ground = vecs[:, 0]
        w = u1_wilson_loop_expectation(ground, [0], 2, 1)
        self.assertLessEqual(abs(w), 1.0 + 1e-10)


if __name__ == "__main__":
    unittest.main()
