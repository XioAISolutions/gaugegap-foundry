from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COQ_ROOT = ROOT / "formal"
DAG_PATH = ROOT / "formal" / "lean" / "dag.json"

#: Named results in a Coq source. ``Definition`` is deliberately excluded: only
#: proved statements need a Lean counterpart.
NAMED_RESULT = re.compile(r"(?m)^(?:Lemma|Theorem|Corollary|Proposition)\s+(\w+)")


def _coq_sources() -> list[Path]:
    return sorted(
        path
        for path in COQ_ROOT.rglob("*.v")
        if ".lake" not in path.parts and "lake-packages" not in path.parts
    )


def _dag() -> dict:
    return json.loads(DAG_PATH.read_text(encoding="utf-8"))


class ProverCorrespondenceTests(unittest.TestCase):
    """Every curated Coq result must be named by a Lean DAG node.

    This is what makes "two independent kernels check the same thing" a
    maintained property rather than a claim: adding a Coq result without a Lean
    counterpart fails here.
    """

    def test_curated_coq_sources_are_found(self) -> None:
        sources = _coq_sources()
        self.assertTrue(sources, "no Coq sources under formal/")
        names = {path.name for path in sources}
        self.assertIn("no_hiding_finite.v", names)
        self.assertIn("gram_identity.v", names)

    def test_every_coq_result_has_a_named_lean_node(self) -> None:
        described = " ".join(node["description"] for node in _dag()["nodes"])
        missing: list[str] = []
        total = 0
        for path in _coq_sources():
            for name in NAMED_RESULT.findall(path.read_text(encoding="utf-8")):
                total += 1
                if name not in described:
                    missing.append(f"{path.relative_to(ROOT)}::{name}")
        self.assertTrue(total, "no named Coq results were parsed")
        self.assertEqual(missing, [], f"Coq results with no Lean node: {missing}")

    def test_the_regex_actually_matches_the_coq_keywords(self) -> None:
        """Guard against the previous test passing because nothing parsed."""
        sample = "Lemma a : True.\nTheorem b : True.\nCorollary c : True.\nDefinition d := 1.\n"
        self.assertEqual(NAMED_RESULT.findall(sample), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
