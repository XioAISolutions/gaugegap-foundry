"""Tests for the St. Petersburg paradox decision-theory vignette."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.decision.st_petersburg import (
    analyze_st_petersburg,
    bounded_bankroll_ev,
    log_utility_certainty_equivalent,
    log_utility_expected_utility,
    naive_truncated_ev,
)


class TestStPetersburg(unittest.TestCase):
    def test_truncated_ev_equals_n(self):
        # the certifiable core: each round contributes exactly $1, so EV_n == n
        for n in (1, 2, 5, 10, 50, 200):
            self.assertTrue(math.isclose(naive_truncated_ev(n), float(n), rel_tol=1e-12))

    def test_naive_ev_diverges(self):
        # strictly increasing and unbounded
        self.assertLess(naive_truncated_ev(10), naive_truncated_ev(100))
        self.assertGreaterEqual(naive_truncated_ev(1000), 1000.0 - 1e-6)

    def test_log_utility_certainty_equivalent_is_four(self):
        # geometric mean of payoffs = 2^(sum k/2^k) = 2^2 = $4 exactly
        self.assertTrue(math.isclose(log_utility_certainty_equivalent(), 4.0,
                                     rel_tol=1e-9))

    def test_log_utility_expected_utility_is_two_ln2(self):
        self.assertTrue(math.isclose(log_utility_expected_utility(),
                                     2.0 * math.log(2.0), rel_tol=1e-9))

    def test_bounded_bankroll_ev_equals_N_plus_1(self):
        for N in (0, 1, 5, 10, 20, 30):
            self.assertTrue(math.isclose(bounded_bankroll_ev(N), float(N + 1),
                                         rel_tol=1e-12))

    def test_finite_vs_infinite_gap(self):
        # the paradox in one assertion: truncated EV blows past the bounded-utility CE
        self.assertGreater(naive_truncated_ev(100), log_utility_certainty_equivalent())

    def test_analyze_payload(self):
        res = analyze_st_petersburg()
        self.assertTrue(res.naive_ev_diverges)
        self.assertTrue(math.isclose(res.log_utility_certainty_equivalent, 4.0,
                                     rel_tol=1e-9))
        for N, ev in res.bounded_bankroll_ev.items():
            self.assertTrue(math.isclose(ev, N + 1, rel_tol=1e-12))
        d = res.to_dict()
        self.assertEqual(d["kind"], "st_petersburg_paradox")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            naive_truncated_ev(-1)
        with self.assertRaises(ValueError):
            bounded_bankroll_ev(-1)


if __name__ == "__main__":
    unittest.main()
