"""Tests for the Spectra certified-screening DSL.

Covers parsing, the certify -> interval semantic, the defining rule that an
`assert separated` cannot pass unless the interval kernel certifies it, and
report emission. QPE (`measure`) is exercised elsewhere and needs qiskit, so it
is not used here.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.spectra_lang import SpectraError, run_program, run_file


class TestSpectra(unittest.TestCase):
    def test_certify_yields_interval_and_assert_passes(self):
        prog = run_program(
            "zeros Z = riemann(20)\n"
            "operator xp = berry_keating(n=20)\n"
            "certify Mx = mismatch(xp, Z)\n"
            "assert separated(Mx, threshold=1.0)\n"
        )
        c = prog.certificates["Mx"]
        self.assertEqual(c["family"], "xp")
        self.assertLessEqual(c["lower"], c["upper"])
        self.assertGreater(c["lower"], 1.0)
        self.assertEqual(len(prog.assertions), 1)
        self.assertTrue(prog.assertions[0]["separated"])
        # Discharged proof emitted (real tactic, not a hole).
        self.assertIn("linarith", prog.assertions[0]["lean4"])
        self.assertNotIn("sorry", prog.assertions[0]["lean4"])

    def test_assert_fails_when_kernel_cannot_certify(self):
        # The defining semantic: you cannot assert a separation the certified
        # interval does not support. An absurd threshold must fail the program.
        with self.assertRaises(SpectraError):
            run_program(
                "zeros Z = riemann(20)\n"
                "operator xp = berry_keating(n=20)\n"
                "certify Mx = mismatch(xp, Z)\n"
                "assert separated(Mx, threshold=1000000000.0)\n"
            )

    def test_all_three_families(self):
        prog = run_program(
            "zeros Z = riemann(20)\n"
            "operator a = berry_keating(n=15)\n"
            "operator b = dirac_rindler(n=15)\n"
            "operator c = quantum_graph(n=15)\n"
            "certify Ma = mismatch(a, Z)\n"
            "certify Mb = mismatch(b, Z)\n"
            "certify Mc = mismatch(c, Z)\n"
        )
        self.assertEqual(set(prog.certificates), {"Ma", "Mb", "Mc"})
        self.assertEqual(prog.certificates["Mb"]["family"], "dirac_rindler")

    def test_parse_errors(self):
        with self.assertRaises(SpectraError):
            run_program("operator xp = nonsense_family(n=10)\n")
        with self.assertRaises(SpectraError):
            run_program("certify Mx = mismatch(unknown_op, Z)\n")
        with self.assertRaises(SpectraError):
            run_program("this is not valid spectra\n")

    def test_report_emits_bundle_and_certificates(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = (
                "zeros Z = riemann(20)\n"
                "operator xp = berry_keating(n=20)\n"
                "certify Mx = mismatch(xp, Z)\n"
                "assert separated(Mx, threshold=1.0)\n"
                f'report "{tmp}"\n'
            )
            run_program(src)
            self.assertTrue((Path(tmp) / "spectra_report.json").exists())
            self.assertTrue((Path(tmp) / "Mx_separation.lean").exists())
            self.assertTrue((Path(tmp) / "Mx_separation.v").exists())

    def test_prove_monotone_passes_for_xp(self):
        prog = run_program(
            "zeros Z = riemann(20)\n"
            "prove monotone(berry_keating, panel=10,15,20, zeros=Z)\n"
        )
        self.assertEqual(len(prog.monotonicity), 1)
        m = prog.monotonicity[0]
        self.assertEqual(m["family"], "xp")
        self.assertTrue(all(a < b for a, b in zip(m["lowers"], m["lowers"][1:])))
        self.assertIn("norm_num", m["lean4"])
        self.assertNotIn("sorry", m["lean4"])

    def test_prove_monotone_fails_for_dirac_rindler(self):
        # dirac_rindler bounds fluctuate; the language must refuse the claim.
        with self.assertRaises(SpectraError):
            run_program(
                "zeros Z = riemann(20)\n"
                "prove monotone(dirac_rindler, panel=10,15,20, zeros=Z)\n"
            )

    def test_measure_backend_validation(self):
        # An unknown backend is a parse/semantic error (no silent default).
        with self.assertRaises(SpectraError):
            run_program(
                "zeros Z = riemann(20)\n"
                "operator xp = berry_keating(n=8)\n"
                "measure Q = qpe(xp, window=0.5, precision=4, backend=nonsense)\n"
            )

    def test_example_program_runs(self):
        prog = run_file(ROOT / "examples" / "curverank_screen.spectra")
        self.assertEqual(len(prog.assertions), 3)
        self.assertTrue(all(a["separated"] for a in prog.assertions))
        self.assertEqual(len(prog.monotonicity), 1)


if __name__ == "__main__":
    unittest.main()
