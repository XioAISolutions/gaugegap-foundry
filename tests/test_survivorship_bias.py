"""Tests for the survivorship-bias (Wald bombers) decision-theory vignette."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.decision.survivorship_bias import (
    BOMBER_REGIONS,
    analyze_survivorship,
    naive_armor_choice,
    survivor_hit_rate,
    wald_armor_choice,
)


class TestSurvivorshipBias(unittest.TestCase):
    def test_survivor_hit_rate_formula(self):
        self.assertTrue(math.isclose(survivor_hit_rate(0.3, 0.8), 0.3 * 0.2, rel_tol=1e-12))

    def test_wald_picks_engine(self):
        self.assertEqual(wald_armor_choice(BOMBER_REGIONS), "engine")

    def test_naive_disagrees_with_wald(self):
        self.assertNotEqual(naive_armor_choice(BOMBER_REGIONS),
                            wald_armor_choice(BOMBER_REGIONS))

    def test_naive_picks_low_lethality(self):
        # naive armors the least lethal region (most surviving holes): tail.
        self.assertEqual(naive_armor_choice(BOMBER_REGIONS), "tail")

    def test_analyze_payload(self):
        res = analyze_survivorship()
        self.assertEqual(res.wald_choice, "engine")
        self.assertNotEqual(res.naive_choice, res.wald_choice)
        self.assertTrue(res.naive_is_wrong)
        d = res.to_dict()
        self.assertEqual(d["kind"], "survivorship_bias")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            survivor_hit_rate(1.5, 0.5)
        with self.assertRaises(ValueError):
            survivor_hit_rate(0.5, -0.1)


if __name__ == "__main__":
    unittest.main()
