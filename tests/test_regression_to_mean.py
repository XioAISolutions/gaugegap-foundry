"""Tests for the regression-to-the-mean decision-theory vignette."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.decision.regression_to_mean import (
    analyze_regression_to_mean,
    conditional_expectation,
    expected_followup,
    regresses_toward_mean,
    regression_fraction,
)


class TestRegressionToMean(unittest.TestCase):
    def test_conditional_expectation_closed_form(self):
        # E[Y | X = x] = rho * x
        self.assertTrue(math.isclose(conditional_expectation(2.5, 0.4), 1.0,
                                     rel_tol=1e-12))
        self.assertTrue(math.isclose(conditional_expectation(3.0, 0.5), 1.5,
                                     rel_tol=1e-12))
        self.assertTrue(math.isclose(conditional_expectation(-2.0, 0.25), -0.5,
                                     rel_tol=1e-12))

    def test_expected_followup_alias(self):
        self.assertTrue(math.isclose(expected_followup(2.5, 0.4),
                                     conditional_expectation(2.5, 0.4), rel_tol=1e-12))

    def test_regression_fraction_closed_form(self):
        # fraction 1 - rho regresses toward the mean
        self.assertTrue(math.isclose(regression_fraction(0.4), 0.6, rel_tol=1e-12))
        self.assertTrue(math.isclose(regression_fraction(1.0), 0.0, rel_tol=1e-12))
        self.assertTrue(math.isclose(regression_fraction(0.0), 1.0, rel_tol=1e-12))

    def test_regresses_toward_mean_contracts_extremes(self):
        # selected extreme regresses for 0 < rho < 1
        self.assertTrue(regresses_toward_mean(3.0, 0.5))
        self.assertTrue(regresses_toward_mean(-4.0, 0.9))
        # perfect correlation: no regression
        self.assertFalse(regresses_toward_mean(3.0, 1.0))
        # at the mean there is nothing to contract
        self.assertFalse(regresses_toward_mean(0.0, 0.5))

    def test_contraction_inequality(self):
        # |E[Y|X=x]| <= |x| for |rho| <= 1
        for x in (-5.0, -1.0, 2.0, 7.0):
            for rho in (-1.0, -0.3, 0.0, 0.6, 1.0):
                self.assertLessEqual(abs(conditional_expectation(x, rho)) - 1e-12,
                                     abs(x))

    def test_analyze_payload(self):
        res = analyze_regression_to_mean(3.0, 0.5)
        self.assertTrue(math.isclose(res.conditional_expectation, 1.5, rel_tol=1e-12))
        self.assertTrue(math.isclose(res.regression_fraction, 0.5, rel_tol=1e-12))
        self.assertTrue(res.regresses_toward_mean)
        d = res.to_dict()
        self.assertEqual(d["kind"], "regression_to_mean")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            conditional_expectation(2.0, 1.5)
        with self.assertRaises(ValueError):
            regression_fraction(-1.2)
        with self.assertRaises(ValueError):
            analyze_regression_to_mean(2.0, 2.0)


if __name__ == "__main__":
    unittest.main()
