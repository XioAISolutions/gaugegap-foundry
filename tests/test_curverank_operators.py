from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import (
    berry_keating_xp,
    dirac_rindler_truncated,
    generate_candidate_family,
    quantum_graph_laplacian,
)


class TestBerryKeatingXP(unittest.TestCase):
    def test_hermiticity(self):
        H = berry_keating_xp(10)
        np.testing.assert_allclose(H, H.conj().T, atol=1e-12)

    def test_dimension(self):
        H = berry_keating_xp(8)
        self.assertEqual(H.shape, (8, 8))

    def test_real_eigenvalues(self):
        H = berry_keating_xp(12)
        eigs = np.linalg.eigvalsh(H)
        np.testing.assert_allclose(eigs.imag, 0.0, atol=1e-10)

    def test_min_basis_error(self):
        with self.assertRaises(ValueError):
            berry_keating_xp(1)


class TestQuantumGraphLaplacian(unittest.TestCase):
    def test_symmetry(self):
        edges = [(0, 1), (0, 2), (0, 3)]
        lengths = [1.0, np.sqrt(2), np.sqrt(3)]
        H = quantum_graph_laplacian(edges, lengths, 5)
        np.testing.assert_allclose(H, H.T, atol=1e-14)

    def test_positive_semidefinite(self):
        edges = [(0, 1), (1, 2)]
        lengths = [1.0, 1.0]
        H = quantum_graph_laplacian(edges, lengths, 4)
        eigs = np.linalg.eigvalsh(H)
        self.assertTrue(np.all(eigs >= -1e-10))

    def test_dimension(self):
        edges = [(0, 1), (0, 2)]
        lengths = [1.0, 2.0]
        H = quantum_graph_laplacian(edges, lengths, 3)
        self.assertEqual(H.shape, (6, 6))

    def test_mismatched_edges_lengths(self):
        with self.assertRaises(ValueError):
            quantum_graph_laplacian([(0, 1)], [1.0, 2.0], 3)


class TestDiracRindlerTruncated(unittest.TestCase):
    def test_hermiticity(self):
        H = dirac_rindler_truncated(8)
        np.testing.assert_allclose(H, H.conj().T, atol=1e-12)

    def test_dimension_doubling(self):
        H = dirac_rindler_truncated(6)
        self.assertEqual(H.shape, (12, 12))

    def test_real_eigenvalues(self):
        H = dirac_rindler_truncated(10, acceleration=0.5, mass=0.1)
        eigs = np.linalg.eigvalsh(H)
        np.testing.assert_allclose(eigs.imag, 0.0, atol=1e-10)

    def test_min_basis_error(self):
        with self.assertRaises(ValueError):
            dirac_rindler_truncated(1)


class TestGenerateCandidateFamily(unittest.TestCase):
    def test_xp_family(self):
        results = generate_candidate_family("xp", [5, 10, 15])
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertEqual(r["family"], "xp")
            self.assertIn("operator", r)

    def test_quantum_graph_family(self):
        results = generate_candidate_family("quantum_graph", [3, 5])
        self.assertEqual(len(results), 2)

    def test_dirac_rindler_family(self):
        results = generate_candidate_family("dirac_rindler", [4, 8])
        self.assertEqual(len(results), 2)

    def test_unknown_family(self):
        with self.assertRaises(ValueError):
            generate_candidate_family("nonexistent", [5])


if __name__ == "__main__":
    unittest.main()
