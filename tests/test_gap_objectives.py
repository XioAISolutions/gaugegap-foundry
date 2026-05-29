from __future__ import annotations

import unittest

from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY
from gaugegap.search.gap_objectives import total_candidate_score


def record(gap: float, n_plaquettes: int = 1, status: str = "pass") -> dict[str, object]:
    return {
        "value": gap,
        "residual_norm": 1e-12,
        "params": {
            "n_plaquettes": n_plaquettes,
            "plaquette_coupling": 1.0,
            "transverse_field": 0.2,
        },
        "pauli_replica": {
            "status": status,
            "matrix_delta": 0.0,
            "gap_delta": 0.0,
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }


class GapObjectiveTests(unittest.TestCase):
    def test_better_gap_profile_scores_higher(self) -> None:
        strong = {"records": [record(0.8, 1), record(0.7, 2)], "claim_boundary": CLAIM_BOUNDARY}
        weak = {"records": [record(0.08, 1), record(0.03, 2)], "claim_boundary": CLAIM_BOUNDARY}
        self.assertGreater(total_candidate_score(strong), total_candidate_score(weak))

    def test_pauli_mismatch_penalizes_score(self) -> None:
        clean = {"records": [record(0.5, 1)], "claim_boundary": CLAIM_BOUNDARY}
        mismatched = {"records": [record(0.5, 1, status="fail")], "claim_boundary": CLAIM_BOUNDARY}
        self.assertLess(total_candidate_score(mismatched), total_candidate_score(clean))

    def test_missing_claim_boundary_is_severely_penalized(self) -> None:
        bounded = {"records": [record(0.5, 1)], "claim_boundary": CLAIM_BOUNDARY}
        unbounded = {"records": [record(0.5, 1)], "claim_boundary": ""}
        self.assertLess(total_candidate_score(unbounded), total_candidate_score(bounded) - 50.0)


if __name__ == "__main__":
    unittest.main()
