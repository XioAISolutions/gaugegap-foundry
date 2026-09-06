from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.run_lean_forge import (
    HOLE_PATTERN,
    _lean_sources,
    build_report,
    check_structure,
    run_lake,
    _strip_comments,
)

ROOT = Path(__file__).resolve().parents[1]
DAG_PATH = ROOT / "formal" / "lean" / "dag.json"


def _dag() -> dict:
    return json.loads(DAG_PATH.read_text(encoding="utf-8"))


class LeanForgeStructureTests(unittest.TestCase):
    def test_checked_in_dag_matches_the_lean_sources(self) -> None:
        self.assertEqual(check_structure(_dag()), [])

    def test_dag_declares_no_verification_status(self) -> None:
        """Verification status is produced by lake build, never checked in."""
        text = DAG_PATH.read_text(encoding="utf-8").lower()
        for word in ("proved", "verified", "status"):
            for node in _dag()["nodes"]:
                self.assertNotIn(word, {key.lower() for key in node})
        self.assertNotIn('"status"', text)

    def test_dag_covers_every_declared_track(self) -> None:
        dag = _dag()
        tracks = {node["track"] for node in dag["nodes"]}
        self.assertEqual(tracks, set(dag["targets"]))
        for node in dag["nodes"]:
            self.assertTrue((ROOT / "formal" / "lean" / node["statement_module"]).exists())
            self.assertTrue((ROOT / "formal" / "lean" / node["proof_module"]).exists())

    def test_dependency_declaration_is_enforced(self) -> None:
        dag = _dag()
        for node in dag["nodes"]:
            if node["id"] in {"A13", "B06"}:
                node["depends_on"] = []
        issues = check_structure(dag)
        for node_id in ("A13", "B06"):
            self.assertTrue(
                any(
                    item.node_id == node_id and "dependencies" in item.problem
                    for item in issues
                ),
                issues,
            )

    def test_missing_proof_is_reported(self) -> None:
        dag = _dag()
        dag["nodes"][0]["proof"] = "a01_does_not_exist"
        issues = check_structure(dag)
        self.assertTrue(any("missing proof" in item.problem for item in issues), issues)

    def test_dependency_checkouts_are_not_scanned(self) -> None:
        """Mathlib's own test files carry `sorry`; they are not our sources."""
        vendored = (
            ROOT / "formal" / "lean" / ".lake" / "packages" / "probe" / "Probe.lean"
        )
        vendored.parent.mkdir(parents=True, exist_ok=True)
        vendored.write_text("theorem probe : True := by\n  sorry\n", encoding="utf-8")
        try:
            self.assertNotIn(
                vendored, _lean_sources(), "dependency checkout was scanned"
            )
            self.assertEqual(check_structure(_dag()), [])
        finally:
            vendored.unlink()
            for parent in (vendored.parent, vendored.parent.parent):
                if not any(parent.iterdir()):
                    parent.rmdir()

    def test_hole_pattern_detects_sorry_but_not_prose(self) -> None:
        self.assertTrue(HOLE_PATTERN.search("theorem t : P := by\n  sorry\n"))
        self.assertTrue(HOLE_PATTERN.search("theorem t : P := by\n  native_decide\n"))
        self.assertFalse(HOLE_PATTERN.search(_strip_comments("/-- no sorry here -/\n")))


class LeanForgeGateTests(unittest.TestCase):
    def test_no_simulated_verification_path(self) -> None:
        """With no toolchain the gate reports toolchain_missing, never verified."""
        result = run_lake("/nonexistent/lake-binary-for-tests", timeout=5)
        self.assertNotEqual(result["status"], "verified")

    def test_skipping_lake_never_marks_a_node_verified(self) -> None:
        report = build_report(lake=None, timeout=5, skip_lake=True)
        self.assertTrue(report["structure"]["ok"], report["structure"]["issues"])
        self.assertTrue(report["mirror"]["all_hold"])
        self.assertEqual(report["kernel_check"]["status"], "skipped")
        for node in report["nodes"]:
            self.assertNotEqual(node["lean_status"], "verified")

    def test_report_hashes_every_lean_source(self) -> None:
        report = build_report(lake=None, timeout=5, skip_lake=True)
        tracked = set(report["sources"])
        self.assertIn("formal/lean/dag.json", tracked)
        self.assertIn("formal/lean/GaugeGapLean/AnomalyForge/Proofs.lean", tracked)
        self.assertIn("formal/lean/lean-toolchain", tracked)
        self.assertIn("formal/lean/lake-manifest.json", tracked)
        self.assertEqual(len(report["content_hash"]), 64)

    def test_every_node_has_a_python_mirror(self) -> None:
        report = build_report(lake=None, timeout=5, skip_lake=True)
        self.assertEqual(len(report["nodes"]), report["node_count"])
        for node in report["nodes"]:
            self.assertTrue(node["mirror_holds"], node["id"])


if __name__ == "__main__":
    unittest.main()
