"""Tests for the generic spectral-enclosure certificate emitter."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.rigorous.enclosure_certificate import emit_enclosure_certificate
from gaugegap.certify import certify_spectrum


class TestEnclosureCertificate(unittest.TestCase):
    def test_global_bounds_and_structure(self):
        cert = emit_enclosure_certificate([(-1.0, -0.9), (0.5, 0.6), (2.0, 2.1)],
                                          name="Demo")
        self.assertEqual(cert.n, 3)
        self.assertEqual(cert.global_lower, -1.0)
        self.assertEqual(cert.global_upper, 2.1)

    def test_no_proof_holes(self):
        cert = emit_enclosure_certificate([(0.0, 1.0), (1.0, 2.0)], name="X")
        self.assertNotIn("sorry", cert.lean4)
        self.assertNotIn("admit", cert.coq.lower())
        self.assertIn("linarith", cert.lean4)
        self.assertIn("lra", cert.coq)
        # one discharged theorem per eigenvalue
        self.assertEqual(cert.lean4.count("theorem eig_"), 2)
        self.assertEqual(cert.coq.count("Theorem eig_"), 2)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            emit_enclosure_certificate([])

    def test_certify_spectrum_emit_formal(self):
        rng = np.random.default_rng(0)
        A = rng.standard_normal((4, 4))
        H = (A + A.T) / 2
        cert = certify_spectrum(H, emit_formal=True, name="RandSym")
        self.assertIsNotNone(cert.formal)
        self.assertEqual(cert.formal["kind"], "spectral_enclosure_certificate")
        lo, hi = cert.formal["global_enclosure"]
        ev = np.linalg.eigvalsh(H)
        self.assertLessEqual(lo, min(ev))
        self.assertLessEqual(max(ev), hi)


if __name__ == "__main__":
    unittest.main()
