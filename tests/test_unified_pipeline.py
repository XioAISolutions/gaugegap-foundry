"""Tests for the unified CurveRank pipeline orchestrator.

Exercises the integration path (classical -> certified -> signal -> advanced ->
cross-validation -> formal -> DSL) in-process without the Aer QPE stage, so the
test is fast and does not require a simulator. The QPE stage itself is covered by
test_curverank_qpe.py.
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_pipeline_module():
    path = ROOT / "scripts" / "run_unified_pipeline.py"
    spec = importlib.util.spec_from_file_location("unified_pipeline", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestUnifiedPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _load_pipeline_module()
        cls.n = 8
        cls.k = 20

    def test_classical_and_certified_agree(self):
        c0 = self.m.stage0_classical(self.n)
        c1 = self.m.stage1_certified(self.n, self.k)
        self.assertEqual(len(c0["eigenvalues"]), self.n)
        # Every classical eigenvalue lies inside its certified enclosure.
        for ev, (lo, hi) in zip(c0["eigenvalues"], c1["enclosures"]):
            self.assertLessEqual(lo - 1e-9, ev)
            self.assertLessEqual(ev, hi + 1e-9)

    def test_signal_modes_in_enclosure(self):
        c0 = self.m.stage0_classical(self.n)
        c1 = self.m.stage1_certified(self.n, self.k)
        c3 = self.m.stage3_signal(c0["_H"], c1["_enclosures"], seed=0)
        self.assertTrue(c3["esprit_all_certified"])

    def test_cross_validation_methods_agree(self):
        c0 = self.m.stage0_classical(self.n)
        c1 = self.m.stage1_certified(self.n, self.k)
        c3 = self.m.stage3_signal(c0["_H"], c1["_enclosures"], seed=0)
        # Feed the classical target as the QPE estimate (the --skip-quantum path).
        idx = self.m._smallest_positive_index(c0["_evals"])
        qpe = {"estimated_eigenvalue": float(c0["_evals"][idx])}
        c5 = self.m.stage5_cross_validation(c0, c1, qpe, c3)
        self.assertTrue(c5["classical_in_enclosure"])
        self.assertTrue(c5["all_methods_agree_to_1e-2"])
        self.assertLess(c5["max_cross_method_error"], 1e-2)

    def test_advanced_entanglement_bounded(self):
        c0 = self.m.stage0_classical(self.n)
        c4 = self.m.stage4_advanced(c0["_evecs"], self.n)
        self.assertEqual(c4["n_qubits"], int(math.log2(self.n)))
        for val in c4["ground_state_entanglement_entropy"].values():
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, math.log(2) + 1e-9)

    def test_formal_proof_discharged_and_separated(self):
        c6 = self.m.stage6_formal(self.n, self.k, threshold=1.0)
        self.assertTrue(c6["separated"])
        self.assertGreater(c6["lower_bound"], c6["threshold"])
        self.assertGreater(c6["lean4_chars"], 0)
        self.assertGreater(c6["coq_chars"], 0)

    def test_dsl_assertion_certified(self):
        c7 = self.m.stage7_dsl(self.n, threshold=1.0)
        self.assertTrue(c7["assertion_satisfied"])
        self.assertGreater(c7["certified_lower"], 1.0)

    def test_deep_quantum_krylov_in_enclosure(self):
        c0 = self.m.stage0_classical(self.n)
        c1 = self.m.stage1_certified(self.n, self.k)
        deep = self.m.stage4b_deep_quantum(
            c0["_H"], c0["_evecs"], c0["_evals"], c1["_enclosures"], self.n
        )
        # The quantum Krylov eigensolver lands every recovered low eigenvalue in a
        # certified enclosure.
        self.assertTrue(deep["quantum_krylov"]["all_certified"])
        # Heisenberg-limited metrology bound is reported with a Fisher information.
        self.assertTrue(deep["metrology_heisenberg"]["heisenberg_limited"])
        self.assertGreater(deep["metrology_heisenberg"]["fisher_information"], 0.0)
        # Entanglement structure is physical (non-negative).
        es = deep["entanglement_structure"]
        self.assertGreaterEqual(es["ground_negativity_q0"], 0.0)


if __name__ == "__main__":
    unittest.main()
