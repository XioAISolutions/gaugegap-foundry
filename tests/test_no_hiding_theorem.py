from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap import no_hiding_theorem as mirror  # noqa: E402
from gaugegap.lean_mirror import NODE_CHECKS, mirror_summary  # noqa: E402

COQ_SOURCE = ROOT / "formal" / "infogap" / "no_hiding_finite.v"
DAG_PATH = ROOT / "formal" / "lean" / "dag.json"


class NoHidingMirrorTests(unittest.TestCase):
    def test_every_node_holds_on_the_sampled_inputs(self) -> None:
        results = {node_id: check() for node_id, check in mirror.NODE_CHECKS.items()}
        self.assertTrue(all(results.values()), results)

    def test_sample_inputs_are_exactly_normalised(self) -> None:
        self.assertTrue(mirror.INPUTS)
        for item in mirror.INPUTS:
            self.assertEqual(mirror.input_norm(*item), 1, item)

    def test_system_statistics_are_blind_to_the_input(self) -> None:
        """The no-hiding content: every normalised input gives weight 1/2."""
        weights = {mirror.branch_weight(mirror.H_SQUARED, *item) for item in mirror.INPUTS}
        self.assertEqual(weights, {Fraction(1, 2)})

    def test_recovery_is_not_vacuous(self) -> None:
        """Recovery returns the input probabilities, which differ between inputs."""
        recovered = {
            mirror.recovered_pair(mirror.H_SQUARED, ar, ai) for ar, ai, _, _ in mirror.INPUTS
        }
        self.assertGreater(len(recovered), 1)
        for ar, ai, _, _ in mirror.INPUTS:
            self.assertEqual(
                mirror.recovered_pair(mirror.H_SQUARED, ar, ai),
                mirror.pair_probability(ar, ai),
            )

    def test_wrong_hadamard_weight_breaks_recovery(self) -> None:
        """h^2 = 1/2 carries the result; nothing here is true for free."""
        self.assertNotEqual(
            mirror.recovered_pair(Fraction(1, 3), Fraction(1), Fraction(0)),
            mirror.pair_probability(Fraction(1), Fraction(0)),
        )


class CoqCorrespondenceTests(unittest.TestCase):
    def test_every_coq_theorem_has_a_named_lean_counterpart(self) -> None:
        """A Coq theorem with no Lean node makes the cross-prover claim false."""
        coq_theorems = set(
            re.findall(r"(?m)^Theorem\s+(\w+)", COQ_SOURCE.read_text(encoding="utf-8"))
        )
        self.assertTrue(coq_theorems)
        described = " ".join(
            node["description"]
            for node in json.loads(DAG_PATH.read_text(encoding="utf-8"))["nodes"]
            if node["track"] == "infogap-no-hiding"
        )
        missing = sorted(name for name in coq_theorems if name not in described)
        self.assertEqual(missing, [], f"Coq theorems with no Lean node: {missing}")


class CombinedMirrorTests(unittest.TestCase):
    def test_registry_covers_both_tracks(self) -> None:
        self.assertTrue(any(node_id.startswith("A") for node_id in NODE_CHECKS))
        self.assertTrue(any(node_id.startswith("B") for node_id in NODE_CHECKS))
        summary = mirror_summary()
        self.assertTrue(summary["all_hold"], summary["nodes"])


if __name__ == "__main__":
    unittest.main()
