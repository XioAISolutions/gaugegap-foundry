"""Tests for the quantum-speed-limit certification of entanglement formation."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.entanglement_dynamics import two_qubit_exchange_model
from gaugegap.quantum.entanglement_speed_limit import (
    certified_buildup_speed_limit,
    fubini_study_angle,
    quantum_speed_limit,
    energy_uncertainty,
)


class TestEntanglementSpeedLimit(unittest.TestCase):
    def test_buildup_time_respects_qsl_floor(self):
        # The measured build-up time must never beat the QSL floor (a theorem).
        for J in (0.5, 1.0, 2.0):
            H, psi0 = two_qubit_exchange_model(coupling=J)
            r = certified_buildup_speed_limit(H, psi0, n_samples=400)
            self.assertTrue(r.respects_qsl)
            self.assertGreaterEqual(r.buildup_time + 1e-9, r.tau_qsl)

    def test_exchange_evolution_saturates_mandelstam_tamm(self):
        # XX+YY exchange moves along a geodesic, so build-up time == QSL floor.
        H, psi0 = two_qubit_exchange_model(coupling=1.0)
        r = certified_buildup_speed_limit(H, psi0, n_samples=600)
        self.assertAlmostEqual(r.buildup_time, r.tau_qsl, places=3)

    def test_floor_scales_inversely_with_coupling(self):
        # Doubling the coupling halves the floor (dE scales linearly with J).
        H1, p1 = two_qubit_exchange_model(coupling=1.0)
        H2, p2 = two_qubit_exchange_model(coupling=2.0)
        r1 = certified_buildup_speed_limit(H1, p1, n_samples=600)
        r2 = certified_buildup_speed_limit(H2, p2, n_samples=600)
        self.assertAlmostEqual(r1.tau_qsl / r2.tau_qsl, 2.0, places=2)

    def test_certificate_is_hole_free(self):
        H, psi0 = two_qubit_exchange_model(coupling=1.0)
        r = certified_buildup_speed_limit(H, psi0, n_samples=200)
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("respects_qsl", r.lean4)
        self.assertIn("respects_qsl", r.coq)

    def test_fubini_study_angle_basic(self):
        z0 = np.array([1.0, 0.0], dtype=complex)
        z1 = np.array([0.0, 1.0], dtype=complex)
        self.assertAlmostEqual(fubini_study_angle(z0, z0), 0.0, places=9)
        self.assertAlmostEqual(fubini_study_angle(z0, z1), np.pi / 2, places=9)

    def test_qsl_consistent_with_components(self):
        H, psi0 = two_qubit_exchange_model(coupling=1.0)
        # evolve a quarter way and check tau_MT = angle / dE
        from gaugegap.quantum.entanglement_speed_limit import evolve_state  # noqa
        psi_t = evolve_state(H, psi0, 0.2)
        qsl = quantum_speed_limit(H, psi0, psi_t)
        dE = energy_uncertainty(H, psi0)
        self.assertAlmostEqual(qsl["tau_mandelstam_tamm"], qsl["angle"] / dE, places=9)


if __name__ == "__main__":
    unittest.main()
