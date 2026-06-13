"""Tests for the CurveRank formal-proof bundle.

Verifies that the certified finite-truncation theorem is assembled, verified, and
exported to all three proof assistants as well-formed certificates. Honesty
guard: asserts the exports carry the unproven proof-term placeholder so the
bundle is never mistaken for an assistant-discharged proof.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_spectral import riemann_zero_targets
from gaugegap.rigorous.spectral_impossibility import SpectralMismatchProof
from gaugegap.rigorous.formal_export import export_all_formats, verify_certificate
from gaugegap.rigorous.curverank_formal_emit import (
    discharged_separation_proof,
    all_family_proofs,
)


class TestFormalProof(unittest.TestCase):
    def test_theorem_is_verified_and_separated(self):
        zeros = riemann_zero_targets(20).tolist()
        theorem = SpectralMismatchProof().prove_berry_keating_impossibility(10, zeros)
        self.assertTrue(theorem.verify())
        lo, hi = theorem.conclusion["mismatch"].to_tuple()
        self.assertLessEqual(lo, hi)
        # The certified separation reproduces the recorded headline bound.
        self.assertAlmostEqual(float(lo), 27.391322449240914, places=5)
        self.assertGreater(float(lo), 1.0)  # certifiably separated from zero

    def test_exports_are_wellformed_in_all_assistants(self):
        zeros = riemann_zero_targets(20).tolist()
        theorem = SpectralMismatchProof().prove_berry_keating_impossibility(10, zeros)
        with tempfile.TemporaryDirectory() as tmp:
            certs = export_all_formats(theorem, tmp)
            self.assertEqual(set(certs), {"lean4", "coq", "isabelle"})
            for c in certs.values():
                self.assertTrue(verify_certificate(c))
            # Honesty guard: the proof terms are placeholders, not discharged.
            self.assertIn("sorry", certs["lean4"].certificate_text)

    def test_script_runs_and_bundles(self):
        path = ROOT / "scripts" / "run_curverank_formal_proof.py"
        spec = importlib.util.spec_from_file_location("cr_formal_proof", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            summary = mod.build_and_export([10], k_zeros=20, output_dir=Path(tmp))
            self.assertTrue(summary["all_theorems_verified"])
            self.assertTrue(summary["all_certificates_wellformed"])
            self.assertIn("Riemann Hypothesis", summary["claim_boundary"])
            self.assertTrue((Path(tmp) / "formal_proof_summary.json").exists())
            self.assertTrue((Path(tmp) / "theorem_n10.json").exists())


class TestDischargedProofs(unittest.TestCase):
    def test_all_three_families_are_discharged(self):
        proofs = all_family_proofs(20, k_zeros=20)
        self.assertEqual({p.family for p in proofs},
                         {"xp", "dirac_rindler", "quantum_graph"})
        for p in proofs:
            self.assertTrue(p.separated)
            self.assertGreater(p.lower_bound, p.threshold)
            # Genuinely discharged: no proof holes, real tactics present.
            self.assertNotIn("sorry", p.lean4)
            self.assertNotIn("Admitted", p.coq)
            self.assertIn("linarith", p.lean4)
            self.assertIn("lra", p.coq)
            # The certified bound is imported as a single explicit axiom.
            self.assertIn("axiom certified_lower_bound", p.lean4)
            self.assertIn(repr(p.lower_bound), p.lean4)

    def test_refuses_to_emit_when_not_separated(self):
        # An impossibly high threshold leaves nothing to prove -> explicit error,
        # never a vacuous or fabricated proof.
        with self.assertRaises(ValueError):
            discharged_separation_proof("xp", 10, k_zeros=20, threshold=1e9)


if __name__ == "__main__":
    unittest.main()
