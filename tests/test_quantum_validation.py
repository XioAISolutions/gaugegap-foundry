"""Tests for the quantum-validation harness."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap import quantum_validation as qv
from gaugegap.curverank_registry import get_operator


class TestValidateEstimates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = get_operator("berry_keating_xp")
        cls.n = 8
        H = cls.spec.build(cls.n)
        cls.H = (H + H.conj().T) / 2
        cls.enclosures = cls.spec.certified(cls.n)
        cls.classical = np.linalg.eigvalsh(cls.H)

    def test_perfect_estimates_all_certified(self):
        report = qv.validate_estimates(
            list(self.classical), method="exact",
            enclosures=self.enclosures, classical_evals=self.classical,
            operator=self.spec.name, n_basis=self.n,
        )
        self.assertTrue(report.all_certified)
        self.assertEqual(report.n_in_enclosure, len(self.classical))
        self.assertLess(report.max_abs_residual, 1e-9)
        d = report.to_dict()
        for key in ("operator", "method", "n_in_enclosure", "all_certified",
                    "results"):
            self.assertIn(key, d)

    def test_outlier_not_certified(self):
        estimates = list(self.classical[:-1]) + [9999.0]
        report = qv.validate_estimates(
            estimates, method="noisy", enclosures=self.enclosures,
            classical_evals=self.classical, operator=self.spec.name, n_basis=self.n,
        )
        self.assertFalse(report.all_certified)
        self.assertFalse(report.results[-1].in_certified_enclosure)


class TestValidateOperator(unittest.TestCase):
    def test_esprit_qcels_numpy_methods(self):
        # ESPRIT/QCELS are pure-numpy (no Aer); ESPRIT should fully certify.
        reports = qv.validate_operator(
            "berry_keating_xp", 8, methods=("esprit", "qcels"), seed=0,
        )
        self.assertIn("esprit", reports)
        self.assertTrue(reports["esprit"].all_certified)
        # QCELS is the coarser method; it still reports a small residual.
        self.assertLess(reports["qcels"].max_abs_residual, 1e-1)


if __name__ == "__main__":
    unittest.main()
