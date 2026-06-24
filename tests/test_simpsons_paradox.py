"""Tests for the Simpson's paradox decision-theory vignette."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.decision.simpsons_paradox import (
    KIDNEY_STONE_A,
    KIDNEY_STONE_B,
    aggregate_rate,
    analyze_simpsons,
    is_simpsons_reversal,
    rate,
    subgroup_rates,
)


class TestSimpsonsParadox(unittest.TestCase):
    def test_rate_exact(self):
        self.assertTrue(math.isclose(rate(81, 87), 81.0 / 87.0, rel_tol=1e-12))

    def test_aggregate_rates(self):
        self.assertTrue(math.isclose(aggregate_rate(KIDNEY_STONE_A), 273.0 / 350.0,
                                     rel_tol=1e-12))
        self.assertTrue(math.isclose(aggregate_rate(KIDNEY_STONE_B), 289.0 / 350.0,
                                     rel_tol=1e-12))

    def test_a_wins_both_subgroups(self):
        a_sub = subgroup_rates(KIDNEY_STONE_A)
        b_sub = subgroup_rates(KIDNEY_STONE_B)
        self.assertGreater(a_sub[0], b_sub[0])   # small stones: .931 > .867
        self.assertGreater(a_sub[1], b_sub[1])   # large stones: .730 > .688

    def test_b_wins_aggregate(self):
        self.assertGreater(aggregate_rate(KIDNEY_STONE_B), aggregate_rate(KIDNEY_STONE_A))

    def test_reversal_true(self):
        self.assertTrue(is_simpsons_reversal(KIDNEY_STONE_A, KIDNEY_STONE_B))

    def test_no_reversal_when_consistent(self):
        # B dominates both subgroups and the aggregate -> no reversal.
        a = [(1, 10), (1, 10)]
        b = [(9, 10), (9, 10)]
        self.assertFalse(is_simpsons_reversal(a, b))

    def test_analyze_payload(self):
        res = analyze_simpsons()
        self.assertTrue(res.reversal)
        self.assertEqual(res.subgroup_winner, "A")
        self.assertEqual(res.aggregate_winner, "B")
        d = res.to_dict()
        self.assertEqual(d["kind"], "simpsons_paradox")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            rate(5, 0)
        with self.assertRaises(ValueError):
            rate(10, 5)


if __name__ == "__main__":
    unittest.main()
