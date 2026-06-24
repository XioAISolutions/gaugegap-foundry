"""Tests for the Compton-Schwarzschild bound (the mass-radius map / Planck floor)."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.relativity.compton_schwarzschild import (
    analyze_compton_schwarzschild,
    compton_wavelength,
    emit_compton_schwarzschild_certificate,
    min_allowed_radius,
    planck_length,
    planck_mass,
    schwarzschild_radius,
)


class TestComptonSchwarzschild(unittest.TestCase):
    def test_schwarzschild_formula(self):
        # R_s = 2GM/c^2; Sun (~2e30 kg) is ~2.95 km
        rs = schwarzschild_radius(1.989e30)
        self.assertAlmostEqual(rs, 2.95e3, delta=0.1e3)

    def test_compton_formula(self):
        # electron reduced Compton wavelength ~ 3.86e-13 m
        lam = compton_wavelength(9.109e-31)
        self.assertAlmostEqual(lam, 3.86e-13, delta=0.05e-13)

    def test_planck_point_identity_mass_independent(self):
        # R_s * lambda_C = 2 l_P^2 for ANY mass
        two_lp2 = 2.0 * planck_length() ** 2
        for m in (9.109e-31, 1.0, 1.989e30, planck_mass()):
            prod = schwarzschild_radius(m) * compton_wavelength(m)
            self.assertTrue(math.isclose(prod, two_lp2, rel_tol=1e-9))

    def test_apex_at_planck_mass(self):
        # the two boundaries cross at M = m_P / sqrt(2), where R = sqrt(2) l_P
        m_star = planck_mass() / math.sqrt(2.0)
        res = analyze_compton_schwarzschild(m_star)
        self.assertTrue(math.isclose(res.schwarzschild_radius,
                                     res.compton_wavelength, rel_tol=1e-6))
        self.assertTrue(math.isclose(res.min_allowed_radius,
                                     math.sqrt(2.0) * planck_length(), rel_tol=1e-6))

    def test_planck_floor_is_minimum_over_mass(self):
        # min over mass of max(R_s, lambda_C) is achieved near the Planck mass and no
        # object beats sqrt(2) l_P
        floor = math.sqrt(2.0) * planck_length()
        m_star = planck_mass() / math.sqrt(2.0)
        for factor in (1e-12, 1e-6, 1.0, 1e6, 1e12):
            self.assertGreaterEqual(min_allowed_radius(m_star * factor),
                                    floor * (1.0 - 1e-9))

    def test_light_objects_quantum_dominated_heavy_gravity_dominated(self):
        self.assertFalse(analyze_compton_schwarzschild(9.109e-31).is_gravity_dominated)
        self.assertTrue(analyze_compton_schwarzschild(1.989e30).is_gravity_dominated)

    def test_radius_squared_dominates_product(self):
        # the certified inequality holds for an allowed object: R^2 >= R_s * lambda_C
        res = analyze_compton_schwarzschild(5.972e24)  # Earth
        R = res.min_allowed_radius
        self.assertGreaterEqual(R * R, res.rs_times_compton * (1.0 - 1e-9))

    def test_identity_flag(self):
        self.assertTrue(analyze_compton_schwarzschild(1.0).identity_holds)

    def test_certificate_hole_free(self):
        res = analyze_compton_schwarzschild(1.0)
        self.assertNotIn("sorry", res.lean4)
        self.assertNotIn("admit", res.lean4.lower())
        self.assertNotIn("Admitted", res.coq)
        self.assertIn("planck_floor", res.lean4)
        self.assertIn("planck_floor", res.coq)
        self.assertIn("Qed.", res.coq)

    def test_certificate_namespace_safe(self):
        # label starting with a digit must not produce an invalid identifier
        lean, coq = emit_compton_schwarzschild_certificate("1st", 1.0, 2.0)
        self.assertNotIn("namespace ComptonSchwarzschild.1", lean)
        self.assertIn("planck_floor", coq)


if __name__ == "__main__":
    unittest.main()
