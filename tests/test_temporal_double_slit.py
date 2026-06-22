"""Tests for the temporal double-slit (time diffraction) module."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.temporal_double_slit import (
    analyze_time_diffraction,
    fringe_spacing_theory,
    spectral_std,
    spectrum,
    temporal_std,
    time_bandwidth_product,
    time_slits,
)


class TestTemporalDoubleSlit(unittest.TestCase):
    def test_fringe_law_recovers_separation(self):
        # Delta_omega = 2 pi / Delta_t: recovering separation from fringes matches dt.
        for dt in (6.0, 8.0, 12.0, 16.0):
            r = analyze_time_diffraction(dt=dt, tau=0.6)
            self.assertAlmostEqual(r.separation_recovered, dt, delta=0.05)
            self.assertLess(r.fringe_relative_error, 1e-2)

    def test_fringe_spacing_inversely_proportional(self):
        # doubling the separation halves the fringe spacing
        self.assertAlmostEqual(
            fringe_spacing_theory(6.0) / fringe_spacing_theory(12.0), 2.0, places=9)

    def test_time_bandwidth_respects_uncertainty(self):
        r = analyze_time_diffraction(dt=8.0, tau=0.6)
        self.assertGreaterEqual(r.time_bandwidth_product, 0.5 - 1e-9)
        self.assertTrue(r.uncertainty_respected)

    def test_gaussian_saturates_time_bandwidth(self):
        # a single Gaussian slit nearly saturates sigma_t sigma_omega = 1/2
        tau = 0.8
        t_max, n = 60.0, 16384
        times = np.linspace(-t_max, t_max, n)
        single = time_slits(times, 0.0, tau, n_slits=1)
        omega, env = spectrum(times, single)
        prod = time_bandwidth_product(temporal_std(times, single),
                                      spectral_std(omega, env))
        self.assertAlmostEqual(prod, 0.5, delta=0.02)

    def test_two_slits_show_fringes(self):
        # the two-slit spectrum is modulated (variance >> single-slit baseline ratio)
        t_max, n = 40.0, 8192
        times = np.linspace(-t_max, t_max, n)
        _, p2 = spectrum(times, time_slits(times, 8.0, 0.6))
        # cos^2 modulation drives the spectrum to ~0 between fringes
        self.assertLess(p2.min() / p2.max(), 1e-2)

    def test_certificate_hole_free(self):
        r = analyze_time_diffraction(dt=8.0, tau=0.6)
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("time_bandwidth", r.lean4)
        self.assertIn("time_bandwidth", r.coq)


if __name__ == "__main__":
    unittest.main()
