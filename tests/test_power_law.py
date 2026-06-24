"""Tests for the power-law (Pareto) decision-theory vignette."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.decision.power_law import (
    analyze_power_law,
    density_ratio,
    mean,
    moment_diverges,
    scale_invariance_ratio,
    tail_probability,
    variance,
)


class TestPowerLaw(unittest.TestCase):
    def test_tail_probability_closed_form(self):
        # P(X > x) = (x/xmin)^(-alpha)
        self.assertTrue(math.isclose(tail_probability(2.0, 1.0, 1.0), 0.5, rel_tol=1e-12))
        self.assertTrue(math.isclose(tail_probability(4.0, 2.0, 1.0), 1.0 / 16.0,
                                     rel_tol=1e-12))
        # below xmin the tail is 1 by convention
        self.assertEqual(tail_probability(0.5, 2.0, 1.0), 1.0)

    def test_scale_invariance_ratio(self):
        # tail self-similarity: c^(-alpha), independent of x
        self.assertTrue(math.isclose(scale_invariance_ratio(2.0, 1.0), 0.5, rel_tol=1e-12))
        self.assertTrue(math.isclose(scale_invariance_ratio(10.0, 2.0), 0.01,
                                     rel_tol=1e-12))

    def test_density_ratio_carries_extra_exponent(self):
        # density ratio is c^(-(alpha+1)), distinct from the tail ratio
        self.assertTrue(math.isclose(density_ratio(2.0, 1.0), 0.25, rel_tol=1e-12))

    def test_moment_diverges_threshold(self):
        # m-th moment diverges iff m >= alpha
        self.assertFalse(moment_diverges(1.5, 1))   # mean finite for alpha 1.5
        self.assertTrue(moment_diverges(1.5, 2))    # variance diverges for alpha 1.5
        self.assertTrue(moment_diverges(2.0, 2))    # boundary m == alpha diverges
        self.assertFalse(moment_diverges(2.5, 2))   # variance finite for alpha 2.5

    def test_mean_closed_form(self):
        self.assertTrue(math.isclose(mean(2.0, 1.0), 2.0, rel_tol=1e-12))
        self.assertTrue(math.isclose(mean(3.0, 1.0), 1.5, rel_tol=1e-12))
        # mean diverges for alpha <= 1
        self.assertEqual(mean(1.0, 1.0), float("inf"))
        self.assertEqual(mean(0.5, 1.0), float("inf"))

    def test_variance_closed_form(self):
        # alpha = 3, xmin = 1: 1 * 3 / (4 * 1) = 0.75
        self.assertTrue(math.isclose(variance(3.0, 1.0), 0.75, rel_tol=1e-12))
        # variance diverges for alpha <= 2
        self.assertEqual(variance(2.0, 1.0), float("inf"))
        self.assertEqual(variance(2.5, 1.0) > 0, True)
        self.assertTrue(math.isfinite(variance(2.5, 1.0)))

    def test_analyze_payload(self):
        res = analyze_power_law(2.5, 1.0)
        self.assertTrue(math.isclose(res.mean, 2.5 / 1.5, rel_tol=1e-12))
        self.assertTrue(math.isfinite(res.variance))
        self.assertFalse(res.mean_diverges)
        self.assertFalse(res.variance_diverges)
        for c, info in res.scale_invariance_check.items():
            self.assertTrue(info["match"])
            self.assertTrue(math.isclose(info["tail_ratio"], info["c_pow_minus_alpha"],
                                         rel_tol=1e-12))
        d = res.to_dict()
        self.assertEqual(d["kind"], "power_law_pareto")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_divergence_flags_small_alpha(self):
        res = analyze_power_law(0.8, 1.0)
        self.assertTrue(res.mean_diverges)
        self.assertTrue(res.variance_diverges)
        self.assertEqual(res.mean, float("inf"))
        self.assertEqual(res.variance, float("inf"))

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            tail_probability(2.0, 0.0, 1.0)
        with self.assertRaises(ValueError):
            mean(2.0, 0.0)
        with self.assertRaises(ValueError):
            scale_invariance_ratio(0.0, 1.0)


if __name__ == "__main__":
    unittest.main()
