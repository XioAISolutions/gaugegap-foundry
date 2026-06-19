"""Tests for the public certify_spectrum API."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.certify import certify_spectrum, SpectrumCertificate
from gaugegap.curverank_registry import get_operator


class TestCertifySpectrum(unittest.TestCase):
    def test_arbitrary_hermitian_brackets_eigenvalues(self):
        rng = np.random.default_rng(0)
        A = rng.standard_normal((6, 6))
        H = (A + A.T) / 2
        cert = certify_spectrum(H)
        self.assertIsInstance(cert, SpectrumCertificate)
        self.assertEqual(cert.n, 6)
        ev = np.linalg.eigvalsh(H)
        for (lo, hi), e in zip(cert.enclosures, ev):
            self.assertLessEqual(lo, e)
            self.assertLessEqual(e, hi)
        self.assertGreaterEqual(cert.max_width, 0.0)
        self.assertIsNone(cert.formal)

    def test_complex_hermitian(self):
        rng = np.random.default_rng(1)
        A = rng.standard_normal((4, 4)) + 1j * rng.standard_normal((4, 4))
        H = (A + A.conj().T) / 2
        cert = certify_spectrum(H)
        ev = np.linalg.eigvalsh(H)
        self.assertEqual(cert.n, 4)
        for (lo, hi), e in zip(cert.enclosures, ev):
            self.assertLessEqual(lo - 1e-9, e)
            self.assertLessEqual(e, hi + 1e-9)

    def test_formal_family_attaches_discharged_proof(self):
        H = get_operator("xp").build(8)
        cert = certify_spectrum(H, formal_family="xp")
        self.assertIsNotNone(cert.formal)
        self.assertTrue(cert.formal["separated"])
        self.assertGreater(len(cert.formal["lean4"]), 0)
        self.assertGreater(len(cert.formal["coq"]), 0)

    def test_to_dict_has_claim_boundary(self):
        cert = certify_spectrum(np.diag([1.0, 2.0, 3.0]))
        d = cert.to_dict()
        self.assertIn("claim_boundary", d)
        self.assertEqual(len(d["enclosures"]), 3)


if __name__ == "__main__":
    unittest.main()
