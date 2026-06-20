"""Tests for the Temple-Kato certified ground-energy bracket (Phase 5A)."""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import unittest
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.temple_kato import certified_temple_bracket, temple_lower_bound
from gaugegap.curverank_registry import get_operator


def _rand_herm(n, seed):
    rng = np.random.default_rng(seed); A = rng.standard_normal((n, n))
    return (A + A.T) / 2


class TestTempleKato(unittest.TestCase):
    def test_bracket_contains_exact(self):
        for op, n in [("berry_keating_xp", 8), ("z2", 3)]:
            H = get_operator(op).build(n)
            b = certified_temple_bracket(H)
            ev = float(np.linalg.eigvalsh((H + H.conj().T) / 2)[0])
            self.assertTrue(b.valid)
            self.assertLessEqual(b.lower, ev + 1e-9)   # rigorous lower
            self.assertGreaterEqual(b.upper, ev - 1e-9)  # variational upper
            self.assertTrue(b.contains_exact)

    def test_lower_bound_is_rigorous_on_random(self):
        H = _rand_herm(6, 1)
        b = certified_temple_bracket(H)
        ev = float(np.linalg.eigvalsh(H)[0])
        self.assertLessEqual(b.lower, ev + 1e-9)

    def test_temple_validity_condition(self):
        # if mu <= <H>, temple_lower_bound returns None
        H = np.diag([0.0, 1.0]).astype(complex)
        psi = np.array([1, 1], dtype=complex) / np.sqrt(2)  # <H> = 0.5
        self.assertIsNone(temple_lower_bound(H, psi, mu=0.4))  # mu < <H>
        self.assertIsNotNone(temple_lower_bound(H, psi, mu=0.9))

    def test_certificate_hole_free(self):
        b = certified_temple_bracket(get_operator("z2").build(3))
        self.assertIn("linarith", b.lean4)
        self.assertNotIn("sorry", b.lean4)
        self.assertNotIn("Admitted", b.coq)


if __name__ == "__main__":
    unittest.main()
