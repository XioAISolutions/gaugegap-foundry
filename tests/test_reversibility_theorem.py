"""The landauer-reversibility mirror, and the arithmetic it is there to keep honest."""
from __future__ import annotations

from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap import reversibility_theorem as mirror  # noqa: E402


class ReversibilityMirrorTests(unittest.TestCase):
    def test_every_node_holds(self) -> None:
        results = {node_id: check() for node_id, check in mirror.NODE_CHECKS.items()}
        self.assertTrue(all(results.values()), results)

    def test_the_checks_are_exhaustive_not_sampled(self) -> None:
        self.assertEqual(len(mirror.INPUTS_2), 4)
        self.assertEqual(len(mirror.INPUTS_3), 8)
        self.assertEqual(len(set(mirror.INPUTS_2)), 4)
        self.assertEqual(len(set(mirror.INPUTS_3)), 8)


class EntropyAccountingTests(unittest.TestCase):
    def test_the_destroyed_information_is_exactly_three_quarters_log_three(self) -> None:
        self.assertEqual(
            mirror.and_conditional_entropy_bits(), {3: Fraction(3, 4)}
        )

    def test_the_commonly_quoted_rounding_is_not_the_value(self) -> None:
        """1.1887 is a four-decimal rounding of an irrational number, not the
        number. Anything that asserts equality with it is asserting something
        false by about 2.2e-5 bits."""
        exact = mirror.combo_to_float(mirror.and_conditional_entropy_bits())
        self.assertNotEqual(exact, 1.1887)
        self.assertAlmostEqual(exact, 0.75 * math.log2(3), places=15)
        self.assertGreater(abs(exact - 1.1887), 2e-5)

    def test_output_entropy_and_conditional_entropy_add_to_the_input_entropy(self) -> None:
        """AND is a function, so H(X, Y) = H(X) = 2 bits and the chain rule
        gives H(Y) + H(X | Y) = 2 exactly."""
        total: dict[int, Fraction] = {}
        for combo in (mirror.and_output_entropy_bits(), mirror.and_conditional_entropy_bits()):
            for prime, coeff in combo.items():
                total[prime] = total.get(prime, Fraction(0)) + coeff
        self.assertEqual({k: v for k, v in total.items() if v}, {2: Fraction(2)})

    def test_entropies_are_canonical_over_primes(self) -> None:
        """log2 4 must reduce to 2 log2 2, or equality between entropies would
        depend on how they were written down."""
        self.assertEqual(mirror.shannon_entropy_bits((1, 1, 1, 1)), {2: Fraction(2)})
        self.assertEqual(mirror.shannon_entropy_bits((1, 1)), {2: Fraction(1)})

    def test_a_deterministic_outcome_carries_no_entropy(self) -> None:
        self.assertEqual(mirror.shannon_entropy_bits((7,)), {})
        self.assertEqual(mirror.combo_to_float({}), 0.0)

    def test_a_uniform_ternary_outcome_is_irrational(self) -> None:
        self.assertEqual(mirror.shannon_entropy_bits((1, 1, 1)), {3: Fraction(1)})

    def test_the_landauer_floor_is_delegated_not_reimplemented(self) -> None:
        from gaugegap.quantum.landauer import landauer_bound

        bits = mirror.combo_to_float(mirror.and_conditional_entropy_bits())
        self.assertEqual(
            mirror.and_erasure_floor(300.0, 8.617333262e-5),
            landauer_bound(bits * math.log(2.0), 300.0, 8.617333262e-5),
        )

    def test_the_floor_scales_with_temperature(self) -> None:
        self.assertAlmostEqual(
            mirror.and_erasure_floor(2.0), 2.0 * mirror.and_erasure_floor(1.0), places=12
        )

    def test_erasing_one_bit_costs_kT_ln2(self) -> None:
        """The textbook case, as a cross-check on the units: a fair coin."""
        from gaugegap.quantum.landauer import landauer_bit, landauer_bound

        one_bit = mirror.shannon_entropy_bits((1, 1))
        nats = mirror.combo_to_float(one_bit) * math.log(2.0)
        self.assertAlmostEqual(landauer_bound(nats, 1.0), landauer_bit(1.0), places=15)

    def test_negative_and_empty_count_vectors_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mirror.shannon_entropy_bits(())
        with self.assertRaises(ValueError):
            mirror.shannon_entropy_bits((3, -1))


class PermutationMatrixTests(unittest.TestCase):
    def test_toffoli_and_fredkin_matrices_are_orthogonal(self) -> None:
        for gate in (mirror.toffoli, mirror.fredkin):
            with self.subTest(gate=gate.__name__):
                self.assertTrue(mirror.gate_is_orthogonal(gate))

    def test_the_matrices_are_exact_integers(self) -> None:
        """Not a float tolerance: every entry is 0 or 1 and the product is the
        integer identity."""
        matrix = mirror.permutation_matrix(mirror.toffoli)
        self.assertEqual({type(x) for row in matrix for x in row}, {int})
        self.assertEqual(set(x for row in matrix for x in row), {0, 1})
        self.assertEqual(
            mirror.matmul(mirror.transpose(matrix), matrix), mirror.identity(8)
        )

    def test_the_matrix_is_the_gate_and_not_a_stand_in(self) -> None:
        """The matrix has to reproduce the gate, or orthogonality would be a
        statement about some other permutation."""
        matrix = mirror.permutation_matrix(mirror.toffoli)
        for j, x in enumerate(mirror.INPUTS_3):
            column = [matrix[i][j] for i in range(8)]
            self.assertEqual(sum(column), 1)
            self.assertEqual(mirror.INPUTS_3[column.index(1)], mirror.toffoli(x))

    def test_toffoli_is_not_the_identity(self) -> None:
        """Otherwise every claim in the track would be true and empty."""
        self.assertNotEqual(mirror.permutation_matrix(mirror.toffoli), mirror.identity(8))

    def test_the_orthogonality_check_can_fail(self) -> None:
        """A test that only ever passes is not a test. A matrix with a repeated
        column is not orthogonal, and this says so."""
        broken = tuple(
            tuple(1 if i == 0 else 0 for _ in range(8)) for i in range(8)
        )
        self.assertFalse(mirror.is_orthogonal(broken))

    def test_a_non_injective_gate_has_no_permutation_matrix(self) -> None:
        with self.assertRaises(ValueError):
            mirror.permutation_matrix(lambda x: (False, False, False))


class SummaryTests(unittest.TestCase):
    def test_summary_reports_the_exact_entropy_alongside_the_float(self) -> None:
        summary = mirror.mirror_summary()
        self.assertTrue(all(summary["nodes"].values()))
        self.assertEqual(summary["and_conditional_entropy_bits_exact"], {"3": "3/4"})
        self.assertTrue(summary["toffoli_orthogonal"])
        self.assertTrue(summary["fredkin_orthogonal"])
        self.assertIn("Landauer", summary["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
