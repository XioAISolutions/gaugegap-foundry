from __future__ import annotations

from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap import gram_theorem as mirror  # noqa: E402


class GramMirrorTests(unittest.TestCase):
    def test_every_node_holds_exhaustively(self) -> None:
        results = {node_id: check() for node_id, check in mirror.NODE_CHECKS.items()}
        self.assertTrue(all(results.values()), results)

    def test_enumeration_is_exhaustive_for_each_length(self) -> None:
        for length in range(mirror.MAX_LENGTH + 1):
            self.assertEqual(len(list(mirror.signs(length))), 2**length)

    def test_orthogonality_hypothesis_is_not_vacuous(self) -> None:
        """C07 and C08 would be trivially true if no pair were orthogonal."""
        self.assertGreater(mirror.orthogonal_pair_count(), 0)

    def test_odd_length_vectors_are_never_orthogonal(self) -> None:
        """The content of C08, checked from the other direction."""
        for u, v in mirror.equal_length_pairs():
            if len(u) % 2 == 1:
                self.assertNotEqual(mirror.inner(u, v), 0, (u, v))

    def test_popcount_form_differs_from_a_naive_sum(self) -> None:
        """C04 says something: the two sides are not the same expression."""
        u, v = (1, 1, -1), (1, -1, -1)
        self.assertEqual(mirror.mismatches(u, v), 1)
        self.assertEqual(mirror.inner(u, v), 1)
        self.assertNotEqual(mirror.inner(u, v), mirror.mismatches(u, v) * len(u))


if __name__ == "__main__":
    unittest.main()
