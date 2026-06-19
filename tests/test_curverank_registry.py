"""Tests for the operator registry and the general certified-enclosure path."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap import curverank_registry as reg


class TestRegistry(unittest.TestCase):
    def test_list_and_get(self):
        names = reg.list_operators()
        for expected in ("berry_keating_xp", "dirac_rindler", "quantum_graph"):
            self.assertIn(expected, names)
        spec = reg.get_operator("xp")  # alias
        self.assertEqual(spec.name, "berry_keating_xp")
        H = spec.build(8)
        self.assertEqual(H.shape, (8, 8))
        self.assertTrue(np.allclose(H, H.conj().T))

    def test_unknown_operator_raises(self):
        with self.assertRaises(ValueError):
            reg.get_operator("not_an_operator")

    def test_general_enclosure_contains_classical(self):
        """build_certified_general brackets every eigenvalue of an arbitrary
        real-symmetric matrix (the core correctness claim for any operator)."""
        rng = np.random.default_rng(0)
        A = rng.standard_normal((6, 6))
        H = (A + A.T) / 2
        encl = reg.build_certified_general(H)
        ev = np.linalg.eigvalsh(H)
        self.assertEqual(len(encl), 6)
        for i, iv in enumerate(encl):
            lo, hi = iv.to_tuple()
            self.assertLessEqual(float(lo), ev[i])
            self.assertLessEqual(ev[i], float(hi))

    def test_general_enclosure_complex_hermitian(self):
        """The general path also handles a genuinely complex Hermitian matrix
        via the real embedding + doubled-spectrum collapse."""
        rng = np.random.default_rng(1)
        A = rng.standard_normal((4, 4)) + 1j * rng.standard_normal((4, 4))
        H = (A + A.conj().T) / 2
        encl = reg.build_certified_general(H)
        ev = np.linalg.eigvalsh(H)
        self.assertEqual(len(encl), 4)
        for i, iv in enumerate(encl):
            lo, hi = iv.to_tuple()
            self.assertLessEqual(float(lo) - 1e-9, ev[i])
            self.assertLessEqual(ev[i], float(hi) + 1e-9)

    def test_registered_and_general_both_bracket(self):
        spec = reg.get_operator("berry_keating_xp")
        H = spec.build(8)
        ev = np.linalg.eigvalsh((H + H.conj().T) / 2)
        for source in (spec.certified(8), reg.build_certified_general(H)):
            for i, iv in enumerate(source):
                lo, hi = iv.to_tuple()
                self.assertLessEqual(float(lo) - 1e-9, ev[i])
                self.assertLessEqual(ev[i], float(hi) + 1e-9)

    def test_non_hermitian_rejected(self):
        with self.assertRaises(ValueError):
            reg.build_certified_general(np.array([[0.0, 1.0], [0.0, 0.0]]))


if __name__ == "__main__":
    unittest.main()
