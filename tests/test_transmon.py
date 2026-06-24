"""Tests for the transmon / Cooper-pair-box artificial atom."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.transmon import (
    analyze_transmon,
    anharmonicity,
    certified_anharmonicity,
    charge_dispersion,
    emit_transmon_certificate,
    plasma_frequency,
    transmon_levels,
)


class TestTransmon(unittest.TestCase):
    def test_anharmonicity_is_negative(self):
        # the qubit transition is detuned from 1->2: the system is anharmonic
        self.assertLess(anharmonicity(50.0, 1.0), 0.0)

    def test_anharmonicity_approaches_minus_EC(self):
        # transmon regime E_J >> E_C: alpha -> -E_C
        for EC in (1.0, 2.0):
            a = anharmonicity(120.0 * EC, EC)
            self.assertTrue(math.isclose(a, -EC, rel_tol=0.15))

    def test_charge_dispersion_exponentially_suppressed(self):
        # increasing E_J/E_C suppresses charge-noise sensitivity by orders of magnitude
        d10 = charge_dispersion(10.0, 1.0)
        d50 = charge_dispersion(50.0, 1.0)
        d100 = charge_dispersion(100.0, 1.0)
        self.assertGreater(d10, d50)
        self.assertGreater(d50, d100)
        self.assertLess(d100, 1e-5)

    def test_plasma_frequency(self):
        self.assertTrue(math.isclose(plasma_frequency(50.0, 1.0), math.sqrt(8 * 50.0),
                                     rel_tol=1e-12))

    def test_certified_anharmonicity_excludes_zero(self):
        # the rigorous interval enclosure lies strictly below 0 -> provably addressable
        iv = certified_anharmonicity(50.0, 1.0)
        self.assertLess(float(iv.upper), 0.0)
        self.assertLessEqual(float(iv.lower), float(iv.upper))
        # the numeric anharmonicity lies within the certified enclosure
        a = anharmonicity(50.0, 1.0, n_charge=12)
        self.assertGreaterEqual(a, float(iv.lower) - 1e-9)
        self.assertLessEqual(a, float(iv.upper) + 1e-9)

    def test_levels_are_increasing(self):
        e = transmon_levels(50.0, 1.0, n_levels=4)
        self.assertTrue(all(e[i + 1] > e[i] for i in range(len(e) - 1)))

    def test_analyze_payload(self):
        r = analyze_transmon()
        self.assertTrue(r.is_anharmonic_certified)
        self.assertLess(r.anharmonicity, 0.0)
        self.assertTrue(math.isclose(r.anharmonicity_over_EC, -1.0, rel_tol=0.2))
        d = r.to_dict()
        self.assertEqual(d["kind"], "transmon_artificial_atom")
        self.assertIn("NOT a member of the physical-limits web", d["claim_boundary"])

    def test_certificate_hole_free(self):
        r = analyze_transmon()
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("addressable", r.lean4)
        self.assertIn("addressable", r.coq)
        self.assertIn("Qed.", r.coq)

    def test_certificate_namespace_safe(self):
        lean, _ = emit_transmon_certificate("3rd", 1.0)
        self.assertNotIn("namespace Transmon.3", lean)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            transmon_levels(-1.0, 1.0)


if __name__ == "__main__":
    unittest.main()
