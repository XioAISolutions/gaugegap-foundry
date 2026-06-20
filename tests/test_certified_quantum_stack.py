"""Tests for Phase 3: certified-quantum stack (registry gauge ops, quantum error
budget, Spectra certify_quantum verb)."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.curverank_registry import get_operator, list_operators
from gaugegap.quantum_validation import quantum_error_budget
from gaugegap.spectra_lang.interpreter import run_program, SpectraError


class TestGaugeOperatorsInRegistry(unittest.TestCase):
    def test_registered(self):
        ops = list_operators()
        self.assertIn("z2", ops)
        self.assertIn("u1", ops)

    def test_z2_certified_brackets_classical(self):
        spec = get_operator("z2")
        H = spec.build(3)
        Hh = (H + H.conj().T) / 2
        ev = np.linalg.eigvalsh(Hh)
        encl = spec.certified(3)
        for i in range(len(ev)):
            self.assertLessEqual(float(encl[i].lower) - 1e-9, ev[i])
            self.assertLessEqual(ev[i], float(encl[i].upper) + 1e-9)

    def test_z2_certified_bracket_runs(self):
        from gaugegap.certified_bracket import (
            certified_ground_bracket, bracket_contains_exact,
        )
        H = get_operator("z2").build(3)
        b = certified_ground_bracket(H)
        self.assertTrue(b.valid)
        self.assertTrue(bracket_contains_exact(H, b))


class TestQuantumErrorBudget(unittest.TestCase):
    def test_qcels_budget(self):
        r = quantum_error_budget("berry_keating_xp", 8, method="qcels",
                                 n_runs=8, shots=600)
        self.assertEqual(r["method"], "qcels")
        self.assertIn("error_budget", r)
        self.assertGreater(r["total"], 0.0)
        self.assertEqual(r["dominant_source"], "qcels_shot_noise")

    def test_unknown_method_rejected(self):
        with self.assertRaises(ValueError):
            quantum_error_budget("berry_keating_xp", 8, method="nope", n_runs=4)


class TestSpectraCertifyQuantum(unittest.TestCase):
    def test_esprit_certifies_and_asserts(self):
        prog = run_program(
            "operator xp = berry_keating(n=8)\n"
            "certify_quantum Cx = validate(xp, method=esprit)\n"
            "assert quantum_certified(Cx)\n"
        )
        qv = prog.quantum_validations["Cx"]
        self.assertTrue(qv["all_certified"])
        self.assertTrue(qv.get("asserted"))

    def test_unbacked_quantum_claim_fails(self):
        with self.assertRaises(SpectraError):
            run_program(
                "operator xp = berry_keating(n=8)\n"
                "certify_quantum Cq = validate(xp, method=qcels)\n"
                "assert quantum_certified(Cq)\n"
            )

    def test_unknown_method_in_dsl(self):
        with self.assertRaises(SpectraError):
            run_program(
                "operator xp = berry_keating(n=8)\n"
                "certify_quantum Cx = validate(xp, method=bogus)\n"
            )

    def test_assert_requires_prior_certify(self):
        with self.assertRaises(SpectraError):
            run_program("assert quantum_certified(Nope)\n")


if __name__ == "__main__":
    unittest.main()
