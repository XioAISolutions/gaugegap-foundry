"""Tests for the quantum Zeno effect (measurement <-> time; Hawthorne's physical cousin)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.quantum_zeno import (
    analyze_quantum_zeno,
    emit_zeno_certificate,
    survival_probability,
    zeno_lower_bound,
    zeno_survival,
)


class TestQuantumZeno(unittest.TestCase):
    def setUp(self):
        self.H = np.array([[0, 1], [1, 0]], dtype=complex)  # Rabi drive 0<->1
        self.psi = np.array([1, 0], dtype=complex)

    def test_single_interval_survival_in_unit_interval(self):
        for tau in (0.0, 0.1, 1.0, 3.0):
            p = survival_probability(self.H, self.psi, tau)
            self.assertGreaterEqual(p, -1e-12)
            self.assertLessEqual(p, 1.0 + 1e-12)
        # at tau=0 nothing has happened: survival is exactly 1
        self.assertAlmostEqual(survival_probability(self.H, self.psi, 0.0), 1.0, places=9)

    def test_more_measurements_freeze_evolution(self):
        # in the frequent-measurement regime (tau = T/N small) survival rises toward 1
        T = 2.0
        prev = -1.0
        for N in (4, 8, 20, 100, 1000):  # all have tau = T/N <= 0.5 (Zeno regime)
            p = zeno_survival(self.H, self.psi, T, N)
            self.assertGreaterEqual(p, prev - 1e-9)
            prev = p
        # dense observation drives survival toward 1
        self.assertGreater(zeno_survival(self.H, self.psi, T, 2000), 0.99)

    def test_lower_bound_is_monotone_in_N(self):
        # the certified object: the Zeno floor rises with N for ALL N (no regime needed)
        dE, T = 1.0, 2.0
        prev = -1e9
        for N in (1, 2, 5, 20, 100, 1000):
            b = zeno_lower_bound(dE, T, N)
            self.assertGreaterEqual(b, prev - 1e-12)
            prev = b

    def test_zeno_lower_bound_is_respected(self):
        T = 2.0
        dE = 1.0  # for this H and |0>, dE = 1 exactly
        for N in (1, 2, 5, 20, 100, 1000):
            self.assertGreaterEqual(zeno_survival(self.H, self.psi, T, N),
                                    zeno_lower_bound(dE, T, N) - 1e-9)

    def test_bound_tends_to_one(self):
        self.assertAlmostEqual(zeno_lower_bound(1.0, 2.0, 10**6), 1.0, places=4)

    def test_analyze_payload(self):
        res = analyze_quantum_zeno(self.H, self.psi)
        self.assertTrue(res.bound_respected)
        self.assertTrue(res.bound_increases)
        self.assertTrue(res.survival_increases)
        self.assertTrue(res.approaches_unity)
        self.assertAlmostEqual(res.energy_uncertainty, 1.0, places=6)
        d = res.to_dict()
        self.assertEqual(d["kind"], "quantum_zeno_effect")
        self.assertIn("NOT an identification", d["claim_boundary"])

    def test_certificate_hole_free(self):
        res = analyze_quantum_zeno(self.H, self.psi)
        self.assertNotIn("sorry", res.lean4)
        self.assertNotIn("Admitted", res.coq)
        self.assertIn("zeno_floor_monotone", res.lean4)
        self.assertIn("zeno_floor_monotone", res.coq)
        self.assertIn("Qed.", res.coq)

    def test_certificate_namespace_safe(self):
        lean, coq = emit_zeno_certificate("2nd", 1.0, 1.0, 5.0)
        self.assertNotIn("namespace QuantumZeno.2", lean)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            zeno_survival(self.H, self.psi, 1.0, 0)


if __name__ == "__main__":
    unittest.main()
