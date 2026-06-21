"""Tests for entanglement-formation dynamics (finite-model build-up)."""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import unittest
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.entanglement_dynamics import (
    simulate_buildup, buildup_time, two_qubit_exchange_model, entanglement_curve,
)


class TestEntanglementDynamics(unittest.TestCase):
    def test_builds_from_zero_to_ln2(self):
        H, psi0 = two_qubit_exchange_model(1.0)
        r = simulate_buildup(H, psi0, t_max=1.6, n_samples=200)
        self.assertAlmostEqual(r.entropies[0], 0.0, places=6)   # product start
        self.assertGreater(r.s_asymptote, 0.6)                   # near ln2
        self.assertLessEqual(r.s_asymptote, np.log(2) + 1e-6)
        self.assertGreater(r.buildup_time, 0.0)                  # finite build-up time
        self.assertLess(r.buildup_time, 1.6)

    def test_buildup_time_interpolation(self):
        times = [0.0, 1.0, 2.0, 3.0]
        ent = [0.0, 0.5, 1.0, 1.0]      # max 1.0; 90% -> 0.9 between t=1 and t=2
        tb, smax = buildup_time(times, ent, fraction=0.9)
        self.assertEqual(smax, 1.0)
        self.assertTrue(1.0 <= tb <= 2.0)

    def test_attosecond_conversion_is_linear(self):
        H, psi0 = two_qubit_exchange_model(1.0)
        a = simulate_buildup(H, psi0, t_max=1.6, n_samples=150)
        b = simulate_buildup(H, psi0, t_max=1.6, n_samples=150, energy_scale_eV=10.0)
        self.assertEqual(a.time_unit, "model")
        self.assertEqual(b.time_unit, "attoseconds")
        # ratio == hbar/E applied to the model build-up time
        self.assertAlmostEqual(b.buildup_time / a.buildup_time, 658.2119569 / 10.0,
                               places=3)

    def test_zero_coupling_no_entanglement(self):
        H, psi0 = two_qubit_exchange_model(0.0)   # no interaction
        ent = entanglement_curve(H, psi0, [0.0, 0.5, 1.0])
        self.assertTrue(all(s < 1e-9 for s in ent))


if __name__ == "__main__":
    unittest.main()
