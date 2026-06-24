"""Compton-Schwarzschild bound: the mass-radius map of physical objects.

The "cosmic mass-radius diagram" (everything from an electron to the Hubble volume)
is bounded by two lines that close off the lower-left of the plane:

  * **Forbidden by gravity** -- the Schwarzschild radius.  An object of mass M packed
    inside ``R_s(M) = 2 G M / c^2`` is inside its own horizon (a black hole); a
    classical object must have ``R >= R_s``.   [energy/mass <-> geometry]

  * **Forbidden by quantum uncertainty** -- the (reduced) Compton wavelength.  You
    cannot localize a mass M to better than ``lambda_C(M) = hbar / (M c)`` without
    pair-creation; a localizable object has ``R >= lambda_C``.   [mass <-> quantum]

These two limits are the same currencies the rest of the physical-limits web trades in
(geometry, energy, the quantum scale), and they meet at the **Planck point**.  The key
exact identity is *mass-independent*:

    R_s(M) * lambda_C(M) = (2 G M / c^2)(hbar / M c) = 2 G hbar / c^3 = 2 * l_P^2 ,

so the geometric mean of an object's gravitational and quantum length scales is the
Planck length (times sqrt 2), for **every** mass.  Hence any object that is neither a
black hole (``R >= R_s``) nor sub-Compton (``R >= lambda_C``) satisfies

    R^2 >= R_s * lambda_C = 2 l_P^2      i.e.   R >= sqrt(2) * l_P ,

with equality at ``M = m_P / sqrt 2``.  This is the apex of the diagram: **no physical
object can be smaller than (order) the Planck length**, and that floor is reached
exactly where the gravitational and quantum boundaries cross.

This module computes the two boundary curves for a given mass, reports the Planck-point
identity, and emits a discharged Lean 4 / Coq certificate of the polynomial core
``R^2 >= R_s * lambda_C`` from the two trust inputs ``R >= R_s`` and ``R >= lambda_C``.

CLAIM BOUNDARY: this is the standard order-of-magnitude Compton-Schwarzschild bound /
"Planck length as a minimal length scale" heuristic, expressed as an exact inequality
among an object's radius and its two limit lengths.  It is NOT a derivation of quantum
gravity, NOT a claim that spacetime is discrete, and NOT a statement that the Planck
length is operationally reachable.  SI units by default; the certified inequality is
unit-agnostic.

References: Schwarzschild (1916); Compton (1923); Carr, Mureika & Nicolini,
JHEP 07 (2015) 052 (the unified Compton-Schwarzschild line).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# CODATA-ish SI constants (values are illustrative; the certified inequality does not
# depend on them).
G_SI = 6.674_30e-11        # m^3 kg^-1 s^-2
C_SI = 2.997_924_58e8      # m s^-1
HBAR_SI = 1.054_571_817e-34  # J s


def schwarzschild_radius(mass: float, *, G: float = G_SI, c: float = C_SI) -> float:
    """Schwarzschild radius R_s = 2 G M / c^2 (the 'forbidden by gravity' boundary)."""
    return float(2.0 * G * mass / (c * c))


def compton_wavelength(mass: float, *, hbar: float = HBAR_SI, c: float = C_SI) -> float:
    """Reduced Compton wavelength lambda_C = hbar / (M c) (the quantum-uncertainty boundary)."""
    if mass <= 0:
        return float("inf")
    return float(hbar / (mass * c))


def planck_length(*, hbar: float = HBAR_SI, G: float = G_SI, c: float = C_SI) -> float:
    """Planck length l_P = sqrt(hbar G / c^3)."""
    return float(np.sqrt(hbar * G / c**3))


def planck_mass(*, hbar: float = HBAR_SI, G: float = G_SI, c: float = C_SI) -> float:
    """Planck mass m_P = sqrt(hbar c / G)."""
    return float(np.sqrt(hbar * c / G))


def min_allowed_radius(mass: float, *, G: float = G_SI, c: float = C_SI,
                       hbar: float = HBAR_SI) -> float:
    """Smallest radius a real object of mass M may have: max(R_s, lambda_C)."""
    return float(max(schwarzschild_radius(mass, G=G, c=c),
                     compton_wavelength(mass, hbar=hbar, c=c)))


def emit_compton_schwarzschild_certificate(label: str, R_s: float, lambda_C: float):
    """Discharged Lean 4 / Coq proof of R^2 >= R_s * lambda_C from R >= both limits.

    Trust inputs: R_s > 0, lambda_C > 0, R >= R_s and R >= lambda_C (the object is
    neither inside its horizon nor below its Compton wavelength).  The assistant
    discharges R*R >= R_s * lambda_C with nlinarith/nra.  Physically R_s * lambda_C =
    2 l_P^2, so this is exactly R >= sqrt(2) l_P (the Planck-length floor).
    """
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "CS"
    ns = base if not base[0].isdigit() else "CS" + base
    lean = f"""import Mathlib.Tactic

namespace ComptonSchwarzschild.{ns}

/-- Object radius R, Schwarzschild radius Rs, Compton wavelength Lc (abstract reals). -/
axiom R : ℝ
axiom Rs : ℝ
axiom Lc : ℝ

/-- TRUST INPUT 1 -- the Schwarzschild radius is positive. -/
axiom Rs_pos : Rs > 0
/-- TRUST INPUT 2 -- the Compton wavelength is positive. -/
axiom Lc_pos : Lc > 0
/-- TRUST INPUT 3 -- the object is not inside its own horizon. -/
axiom not_bh : R ≥ Rs
/-- TRUST INPUT 4 -- the object is not localized below its Compton wavelength. -/
axiom localizable : R ≥ Lc

/-- The radius-squared dominates the product of the two limit lengths:
    R^2 ≥ Rs * Lc  (= 2 l_P^2, the Planck-length floor). -/
theorem planck_floor : R * R ≥ Rs * Lc := by
  nlinarith [Rs_pos, Lc_pos, not_bh, localizable]

end ComptonSchwarzschild.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section ComptonSchwarzschild_{ns}.

(* object radius Rad, Schwarzschild radius Rs, Compton wavelength Lc
   (Rad avoids shadowing the type R). *)
Variable Rad Rs Lc : R.

(* TRUST INPUT 1: positive Schwarzschild radius. *)
Hypothesis Rs_pos : Rs > 0.
(* TRUST INPUT 2: positive Compton wavelength. *)
Hypothesis Lc_pos : Lc > 0.
(* TRUST INPUT 3: not inside its own horizon. *)
Hypothesis not_bh : Rad >= Rs.
(* TRUST INPUT 4: not localized below its Compton wavelength. *)
Hypothesis localizable : Rad >= Lc.

(* R^2 >= Rs * Lc  (= 2 l_P^2): the Planck-length floor on object size. *)
Theorem planck_floor : Rad * Rad >= Rs * Lc.
Proof. nra. Qed.

End ComptonSchwarzschild_{ns}.
"""
    return lean, coq


@dataclass
class ComptonSchwarzschildResult:
    mass: float
    schwarzschild_radius: float        # R_s = 2GM/c^2
    compton_wavelength: float          # lambda_C = hbar/(Mc)
    min_allowed_radius: float          # max(R_s, lambda_C)
    planck_length: float               # l_P
    planck_mass: float                 # m_P
    rs_times_compton: float            # R_s * lambda_C
    two_planck_length_sq: float        # 2 l_P^2  (should equal rs_times_compton)
    identity_holds: bool               # R_s * lambda_C == 2 l_P^2
    is_gravity_dominated: bool         # R_s >= lambda_C (mass above ~Planck mass)
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "compton_schwarzschild_bound",
            "mass": self.mass,
            "schwarzschild_radius": self.schwarzschild_radius,
            "compton_wavelength": self.compton_wavelength,
            "min_allowed_radius": self.min_allowed_radius,
            "planck_length": self.planck_length,
            "planck_mass": self.planck_mass,
            "rs_times_compton": self.rs_times_compton,
            "two_planck_length_sq": self.two_planck_length_sq,
            "identity_holds": self.identity_holds,
            "is_gravity_dominated": self.is_gravity_dominated,
            "claim_boundary": ("standard order-of-magnitude Compton-Schwarzschild / "
                               "minimal-length bound expressed as an exact inequality "
                               "R^2 >= R_s*lambda_C = 2 l_P^2; NOT a derivation of "
                               "quantum gravity, NOT a claim that spacetime is discrete "
                               "or that the Planck length is operationally reachable"),
        }


def analyze_compton_schwarzschild(mass: float, *, G: float = G_SI, c: float = C_SI,
                                  hbar: float = HBAR_SI) -> ComptonSchwarzschildResult:
    """Compton-Schwarzschild boundaries and the Planck-point identity for ``mass``."""
    R_s = schwarzschild_radius(mass, G=G, c=c)
    lam = compton_wavelength(mass, hbar=hbar, c=c)
    l_P = planck_length(hbar=hbar, G=G, c=c)
    m_P = planck_mass(hbar=hbar, G=G, c=c)
    product = float(R_s * lam)
    two_lp2 = float(2.0 * l_P * l_P)
    # mass-independent identity R_s * lambda_C = 2 l_P^2 (relative tolerance)
    identity = bool(abs(product - two_lp2) <= 1e-9 * max(two_lp2, 1e-300))
    lean, coq = emit_compton_schwarzschild_certificate("planck", R_s, lam)
    return ComptonSchwarzschildResult(
        mass=float(mass),
        schwarzschild_radius=float(R_s),
        compton_wavelength=float(lam),
        min_allowed_radius=float(max(R_s, lam)),
        planck_length=float(l_P),
        planck_mass=float(m_P),
        rs_times_compton=product,
        two_planck_length_sq=two_lp2,
        identity_holds=identity,
        is_gravity_dominated=bool(R_s >= lam),
        lean4=lean, coq=coq,
    )


# A small catalogue of named objects for the mass-radius diagram (mass in kg, radius in
# m).  Illustrative order-of-magnitude values; used only to plot the allowed region.
NAMED_OBJECTS = (
    ("electron", 9.109e-31, 3.862e-13),   # radius ~ its Compton wavelength
    ("proton", 1.673e-27, 8.4e-16),
    ("virus", 1e-19, 5e-8),
    ("human", 7e1, 5e-1),
    ("asteroid", 1e15, 5e5),
    ("Earth", 5.972e24, 6.371e6),
    ("Jupiter", 1.898e27, 6.991e7),
    ("Sun", 1.989e30, 6.957e8),
    ("white dwarf", 2.4e30, 7e6),
    ("neutron star", 2.8e30, 1.2e4),
    ("Sgr A* (SMBH)", 8.26e36, 1.2e10),
)
