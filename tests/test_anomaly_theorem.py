from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.anomaly_audit import Hypercharges, audit  # noqa: E402
from gaugegap import anomaly_theorem as theorem  # noqa: E402


class AnomalyTheoremMirrorTests(unittest.TestCase):
    def test_every_mirrored_node_holds_on_the_grid(self) -> None:
        summary = theorem.mirror_summary()
        self.assertTrue(summary["all_hold"], summary["nodes"])
        self.assertEqual(len(summary["nodes"]), len(theorem.NODE_CHECKS))

    def test_mirror_coefficients_agree_with_the_audited_forge(self) -> None:
        """The Lean mirror and anomaly_audit must compute the same numbers."""
        h = Hypercharges()
        result = audit(h)
        generations = Fraction(h.generations)
        self.assertEqual(
            generations * theorem.su3_u1(h.y_q, h.y_u, h.y_d), result.su3_u1
        )
        self.assertEqual(
            generations * theorem.su2_u1(Fraction(h.colors), h.y_q, h.y_l), result.su2_u1
        )
        self.assertEqual(
            generations
            * theorem.grav_u1(
                Fraction(h.colors), h.y_q, h.y_u, h.y_d, h.y_l, h.y_e, Fraction(0)
            ),
            result.gravity_u1,
        )
        self.assertEqual(
            generations
            * theorem.u1_cubed(
                Fraction(h.colors), h.y_q, h.y_u, h.y_d, h.y_l, h.y_e, Fraction(0)
            ),
            result.u1_cubed,
        )

    def test_uniqueness_has_teeth_off_the_solution(self) -> None:
        """A04 is not vacuous: moving Y_Q off Y_H / n breaks gravity^2-U(1)."""
        n, y_h = Fraction(3), Fraction(1, 2)
        for y_q in (Fraction(1, 5), Fraction(0), Fraction(1, 7)):
            y_l = -(n * y_q)
            self.assertNotEqual(
                theorem.grav_u1(
                    n, y_q, y_q + y_h, y_q - y_h, y_l, y_l - y_h, Fraction(0)
                ),
                0,
            )
        self.assertEqual(
            theorem.grav_u1(
                Fraction(3),
                Fraction(1, 6),
                Fraction(2, 3),
                Fraction(-1, 3),
                Fraction(-1, 2),
                Fraction(-1),
                Fraction(0),
            ),
            0,
        )

    def test_right_neutrino_family_breaks_uniqueness(self) -> None:
        """The declared boundary on A04: with a Dirac neutrino, many
        assignments cancel, so uniqueness is a statement about the
        neutrino-free inventory only."""
        n, y_h = Fraction(3), Fraction(1, 2)
        solutions = 0
        for y_q in (Fraction(1, 6), Fraction(1, 5), Fraction(-2, 3)):
            y_l = -(n * y_q)
            self.assertTrue(
                theorem.is_anomaly_free(
                    n, y_q, y_q + y_h, y_q - y_h, y_l, y_l - y_h, y_l + y_h
                )
            )
            solutions += 1
        self.assertGreater(solutions, 1)

    def test_neutrino_hypercharge_vanishes_at_the_standard_model_point(self) -> None:
        n, y_q = Fraction(3), Fraction(1, 6)
        y_h = n * y_q
        self.assertEqual(-(n * y_q) + y_h, 0)
        self.assertEqual(y_h, Fraction(1, 2))


if __name__ == "__main__":
    unittest.main()
