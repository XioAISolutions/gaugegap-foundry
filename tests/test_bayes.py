"""Tests for the Bayesian updating / base-rate fallacy decision-theory vignette."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.decision.bayes import (
    analyze_bayes,
    base_rate_fallacy_gap,
    bayes_posterior,
    bayes_posterior_negative,
    sequential_update,
)


class TestBayes(unittest.TestCase):
    def test_famous_base_rate_fallacy(self):
        # prior 0.1%, 99% sensitivity, 95% specificity -> posterior ~= 1.94%
        post = bayes_posterior(0.001, 0.99, 0.95)
        tp = 0.001 * 0.99
        fp = 0.999 * 0.05
        exact = tp / (tp + fp)
        self.assertTrue(math.isclose(post, exact, rel_tol=1e-12))
        self.assertTrue(math.isclose(post, 0.0194, rel_tol=1e-2))  # ~1.94%
        # the fallacy: the posterior is far below the 99% sensitivity intuition
        self.assertLess(post, 0.99)
        self.assertLess(post, 0.05)

    def test_textbook_one_twelfth(self):
        # tp = .009, fp = .99*.1 = .099, .009/.108 = 1/12 exactly
        post = bayes_posterior(0.01, 0.9, 0.9)
        self.assertTrue(math.isclose(post, 1.0 / 12.0, rel_tol=1e-12))

    def test_sequential_update_monotone_and_bounded(self):
        prior = 0.001
        update = (0.99, 0.95)
        prev = prior
        for n in range(1, 6):
            post = sequential_update(prior, [update] * n)
            self.assertGreater(post, prev)        # repeated positives increase belief
            self.assertGreater(post, 0.0)
            self.assertLess(post, 1.0)            # stays in (0, 1)
            prev = post

    def test_posterior_negative_below_prior(self):
        # a good test: a negative result should lower belief below the prior
        prior = 0.001
        post_neg = bayes_posterior_negative(prior, 0.99, 0.95)
        self.assertLess(post_neg, prior)
        self.assertGreater(post_neg, 0.0)

    def test_base_rate_fallacy_gap(self):
        naive, correct = base_rate_fallacy_gap(0.001, 0.99, 0.95)
        self.assertEqual(naive, 0.99)
        self.assertLess(correct, naive)

    def test_analyze_payload(self):
        res = analyze_bayes()
        self.assertTrue(math.isclose(res.posterior_positive, 0.0194, rel_tol=1e-2))
        self.assertEqual(res.naive_intuition, res.sensitivity)
        self.assertTrue(math.isclose(res.base_rate_fallacy_gap,
                                     res.sensitivity - res.posterior_positive,
                                     rel_tol=1e-12))
        d = res.to_dict()
        self.assertEqual(d["kind"], "bayes_base_rate_fallacy")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            bayes_posterior(-0.1, 0.99, 0.95)
        with self.assertRaises(ValueError):
            bayes_posterior(0.001, 1.5, 0.95)
        with self.assertRaises(ValueError):
            bayes_posterior_negative(0.001, 0.99, 2.0)


if __name__ == "__main__":
    unittest.main()
