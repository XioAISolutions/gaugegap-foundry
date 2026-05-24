from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import object_hash
from gaugegap.z2_chain import hamiltonian_dense, mass_gap


class Z2ChainTests(unittest.TestCase):
    def test_hamiltonian_is_symmetric(self) -> None:
        matrix = hamiltonian_dense(n_sites=3, exchange_coupling=1.0, transverse_field=0.4)
        self.assertTrue(np.allclose(matrix, matrix.T))

    def test_zero_field_open_chain_has_degenerate_ground_state(self) -> None:
        gap, ground, first = mass_gap(n_sites=3, exchange_coupling=1.0, transverse_field=0.0)
        self.assertAlmostEqual(gap, 0.0)
        self.assertAlmostEqual(ground, first)

    def test_decoupled_field_gap_matches_two_level_spacing(self) -> None:
        gap, _, _ = mass_gap(n_sites=2, exchange_coupling=0.0, transverse_field=1.0)
        self.assertAlmostEqual(gap, 2.0)

    def test_object_hash_is_stable_under_key_order(self) -> None:
        self.assertEqual(object_hash({"a": 1, "b": 2}), object_hash({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
