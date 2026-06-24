"""Tests for the Berkson's paradox decision-theory vignette."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.decision.berksons_paradox import (
    analyze_berksons,
    population_correlation,
    selected_correlation,
)


class TestBerksonsParadox(unittest.TestCase):
    def test_symmetric_case_is_minus_one_half(self):
        # Exact Pearson corr of the OR-selected sample at p = q = 1/2 is -1/2.
        self.assertTrue(math.isclose(selected_correlation(0.5, 0.5), -0.5, rel_tol=1e-12))

    def test_selected_correlation_negative_generally(self):
        for p, q in [(0.3, 0.7), (0.2, 0.2), (0.9, 0.1), (0.5, 0.8), (0.4, 0.6)]:
            self.assertLess(selected_correlation(p, q), 0.0)

    def test_population_correlation_zero(self):
        self.assertEqual(population_correlation(), 0.0)

    def test_analyze_payload(self):
        res = analyze_berksons()
        self.assertEqual(res.population_correlation, 0.0)
        self.assertTrue(math.isclose(res.selected_correlation, -0.5, rel_tol=1e-12))
        self.assertTrue(res.induced_negative)
        d = res.to_dict()
        self.assertEqual(d["kind"], "berksons_paradox")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_input_validation(self):
        for bad in [(0.0, 0.5), (1.0, 0.5), (0.5, 0.0), (0.5, 1.0)]:
            with self.assertRaises(ValueError):
                selected_correlation(*bad)


if __name__ == "__main__":
    unittest.main()
