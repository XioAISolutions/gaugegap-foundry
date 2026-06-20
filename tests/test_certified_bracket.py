"""Tests for the certified energy/gap bracket (Phase 1 flagship)."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.certified_bracket import (
    certified_ground_bracket, certified_gap_bracket, bracket_contains_exact,
)
from gaugegap.rigorous.bracket_certificate import emit_bracket_certificate
from gaugegap.curverank_registry import get_operator


def _random_hermitian(n, seed):
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n))
    return (A + A.T) / 2


class TestCertifiedBracket(unittest.TestCase):
    def test_ground_bracket_contains_exact_xp(self):
        H = get_operator("berry_keating_xp").build(8)
        b = certified_ground_bracket(H)
        self.assertTrue(b.valid)
        ev = np.linalg.eigvalsh((H + H.conj().T) / 2)
        self.assertLessEqual(b.lower, ev[0] + 1e-9)        # lower bound
        self.assertGreaterEqual(b.upper, ev[0] - 1e-9)     # upper bound
        self.assertTrue(b.contains(float(ev[0])))
        self.assertTrue(bracket_contains_exact(H, b))

    def test_ground_bracket_arbitrary_hermitian(self):
        H = _random_hermitian(6, seed=1)
        b = certified_ground_bracket(H)
        ev = np.linalg.eigvalsh(H)
        self.assertTrue(b.valid)
        self.assertLessEqual(b.lower, ev[0] + 1e-9)
        self.assertGreaterEqual(b.upper, ev[0] - 1e-9)

    def test_gap_bracket_contains_true_gap(self):
        H = get_operator("berry_keating_xp").build(8)
        g = certified_gap_bracket(H)
        ev = np.linalg.eigvalsh((H + H.conj().T) / 2)
        true_gap = float(ev[1] - ev[0])
        gb = g["gap_bracket"]
        self.assertLessEqual(gb["lower"], true_gap + 1e-9)
        self.assertGreaterEqual(gb["upper"], true_gap - 1e-9)

    def test_bracket_is_rigorous_two_sided(self):
        # upper must never be below lower (a non-empty bracket)
        for seed in (2, 3, 4):
            b = certified_ground_bracket(_random_hermitian(5, seed))
            self.assertLessEqual(b.lower, b.upper + 1e-9)


class TestBracketCertificate(unittest.TestCase):
    def test_discharged_and_hole_free(self):
        cert = emit_bracket_certificate("E0", -12.79, -12.78)
        self.assertIn("linarith", cert.lean4)
        self.assertIn("lra", cert.coq)
        self.assertNotIn("sorry", cert.lean4)
        self.assertNotIn("Admitted", cert.coq)
        d = cert.to_dict()
        self.assertEqual(d["kind"], "eigenvalue_bracket_certificate")

    def test_empty_bracket_rejected(self):
        with self.assertRaises(ValueError):
            emit_bracket_certificate("bad", 1.0, 0.0)

    def test_certificate_matches_bracket(self):
        H = get_operator("berry_keating_xp").build(8)
        b = certified_ground_bracket(H)
        cert = emit_bracket_certificate("E0", b.lower, b.upper)
        self.assertEqual(cert.lower, b.lower)
        self.assertEqual(cert.upper, b.upper)


if __name__ == "__main__":
    unittest.main()
