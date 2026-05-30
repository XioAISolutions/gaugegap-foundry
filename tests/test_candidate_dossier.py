from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gaugegap.search.candidate_dossier import candidate_to_markdown, write_candidate_dossiers
from gaugegap.search.gap_search import SearchConfig, search_gap_candidates


class CandidateDossierTests(unittest.TestCase):
    def test_markdown_contains_boundary_and_not_proof_warning(self) -> None:
        candidate = search_gap_candidates(
            SearchConfig(
                n_plaquettes=(1,),
                plaquette_couplings=(1.0,),
                transverse_fields=(0.2,),
                max_candidates=1,
                run_id="test-run",
            )
        )[0]
        markdown = candidate_to_markdown(candidate)
        self.assertIn("no continuum Yang-Mills mass-gap claim", markdown)
        self.assertIn("not a Yang-Mills proof", markdown)

    def test_write_candidate_dossiers_creates_json_and_markdown(self) -> None:
        candidate = search_gap_candidates(
            SearchConfig(
                n_plaquettes=(1,),
                plaquette_couplings=(1.0,),
                transverse_fields=(0.2,),
                max_candidates=1,
                run_id="test-run",
            )
        )[0]
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_candidate_dossiers(Path(tmp), [candidate], limit=1)
            self.assertEqual(len(paths), 2)
            for path in paths:
                self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
