from __future__ import annotations

import unittest

from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY
from gaugegap.search.gap_search import SearchConfig, search_gap_candidates


class GapSearchTests(unittest.TestCase):
    def test_search_is_deterministic_for_tiny_config(self) -> None:
        config = SearchConfig(
            n_plaquettes=(1,),
            plaquette_couplings=(1.0,),
            transverse_fields=(0.1, 0.3),
            max_candidates=1,
            run_id="test-run",
        )
        first = search_gap_candidates(config)
        second = search_gap_candidates(config)
        self.assertEqual(first[0]["candidate_id"], second[0]["candidate_id"])
        self.assertAlmostEqual(float(first[0]["score"]), float(second[0]["score"]))

    def test_candidate_contains_claim_boundary(self) -> None:
        config = SearchConfig(
            n_plaquettes=(1,),
            plaquette_couplings=(1.0,),
            transverse_fields=(0.2,),
            max_candidates=1,
            run_id="test-run",
        )
        candidate = search_gap_candidates(config)[0]
        self.assertEqual(candidate["claim_boundary"], CLAIM_BOUNDARY)
        self.assertIn("score_components", candidate)
        self.assertIn("gap_profile", candidate)
        self.assertGreaterEqual(float(candidate["score"]), -100.0)


if __name__ == "__main__":
    unittest.main()
