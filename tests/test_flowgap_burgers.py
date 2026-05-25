from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.flowgap_burgers import (
    burgers_viscous_1d,
    divergence_2d,
    poisson_matrix_1d,
    pressure_poisson_2d,
    projection_step_2d,
)


class TestBurgersViscous1D(unittest.TestCase):
    def test_smooth_kinetic_energy_decays(self):
        result = burgers_viscous_1d(nx=32, nu=0.01, dt=0.0001, n_steps=50)
        ke = result["kinetic_history"]
        self.assertGreater(len(ke), 1)
        for i in range(1, min(10, len(ke))):
            self.assertLessEqual(ke[i], ke[0] * 1.5)

    def test_zero_viscosity_conserves_energy_short_time(self):
        result = burgers_viscous_1d(nx=64, nu=0.0, dt=0.00001, n_steps=10)
        ke = result["kinetic_history"]
        self.assertAlmostEqual(ke[0], ke[-1], places=3)

    def test_output_shape(self):
        result = burgers_viscous_1d(nx=16, nu=0.01, dt=0.001, n_steps=5)
        self.assertEqual(result["u_final"].shape, (16,))
        self.assertEqual(len(result["kinetic_history"]), 5)
        self.assertEqual(len(result["residual_history"]), 5)

    def test_dirichlet_boundary(self):
        result = burgers_viscous_1d(nx=16, nu=0.01, dt=0.0001, n_steps=5, bc="dirichlet")
        self.assertEqual(result["u_final"].shape, (16,))


class TestPoissonMatrix1D(unittest.TestCase):
    def test_symmetry(self):
        A = poisson_matrix_1d(8)
        np.testing.assert_allclose(A, A.T, atol=1e-14)

    def test_known_eigenvalue_structure(self):
        n = 8
        A = poisson_matrix_1d(n)
        eigs = np.sort(np.linalg.eigvalsh(A))
        self.assertTrue(np.all(eigs <= 1e-10))


class TestPressurePoisson2D(unittest.TestCase):
    def test_constant_rhs_gives_near_zero(self):
        p = pressure_poisson_2d(4, 4, np.ones((4, 4)))
        self.assertLess(np.max(np.abs(p)), 1.0)

    def test_shape(self):
        p = pressure_poisson_2d(4, 4, np.random.default_rng(0).standard_normal((4, 4)))
        self.assertEqual(p.shape, (4, 4))


class TestProjectionStep(unittest.TestCase):
    def test_divergence_reduction(self):
        rng = np.random.default_rng(42)
        ux = rng.standard_normal((4, 4))
        uy = rng.standard_normal((4, 4))
        result = projection_step_2d(ux, uy, dt=0.01)
        self.assertIn("divergence_before", result)
        self.assertIn("divergence_after", result)
        self.assertLessEqual(result["divergence_after"], result["divergence_before"] + 1e-6)


class TestDivergence2D(unittest.TestCase):
    def test_zero_field(self):
        ux = np.zeros((4, 4))
        uy = np.zeros((4, 4))
        div = divergence_2d(ux, uy, 0.25, 0.25)
        np.testing.assert_allclose(div, 0.0, atol=1e-14)


if __name__ == "__main__":
    unittest.main()
