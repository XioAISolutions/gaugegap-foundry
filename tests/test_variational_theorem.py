from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap import variational_theorem as mirror  # noqa: E402


class VariationalMirrorTests(unittest.TestCase):
    def test_every_node_holds(self) -> None:
        results = {node_id: check() for node_id, check in mirror.NODE_CHECKS.items()}
        self.assertTrue(all(results.values()), results)

    def test_sample_states_are_exactly_normalised(self) -> None:
        for c in mirror.NORMALISED:
            self.assertEqual(mirror.norm_sq(c), 1, c)

    def test_the_bound_is_not_an_equality_in_disguise(self) -> None:
        """If every trial state sat exactly at the ground energy, D04 would be
        true for an uninteresting reason."""
        self.assertGreater(mirror.strictly_above_ground_energy(), 0)

    def test_a_state_concentrated_on_the_ground_mode_attains_the_bound(self) -> None:
        lam = (Fraction(-5), Fraction(2))
        self.assertEqual(mirror.rayleigh(lam, (Fraction(1), Fraction(0))), Fraction(-5))
        self.assertEqual(mirror.rayleigh(lam, (Fraction(0), Fraction(1))), Fraction(2))

    def test_unnormalised_states_need_the_scaled_form(self) -> None:
        """D01 carries the squared norm because the bound is not scale-free."""
        lam = (Fraction(3), Fraction(3))
        c = (Fraction(2), Fraction(0))
        self.assertEqual(mirror.rayleigh(lam, c), 12)
        self.assertEqual(mirror.norm_sq(c), 4)
        self.assertLess(min(lam), mirror.rayleigh(lam, c))
        self.assertEqual(min(lam) * mirror.norm_sq(c), mirror.rayleigh(lam, c))


if __name__ == "__main__":
    unittest.main()
