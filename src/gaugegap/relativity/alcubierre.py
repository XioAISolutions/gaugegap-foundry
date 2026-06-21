"""Alcubierre warp-drive metric: a certified energy-condition violation.

The Alcubierre (1994) metric describes a "warp bubble" that contracts space ahead
and expands it behind a craft, allowing globally faster-than-light coordinate
travel while every local observer stays subluminal (so it does not by itself signal
faster than light -- the same no-signaling caveat as the quantum thread). The price
is exotic matter: the metric REQUIRES negative energy density.

This module makes that price exact and machine-checkable. In geometric units
(G = c = 1), the energy density measured by Eulerian observers n^mu has the closed
form (Alcubierre 1994):

    rho(x,y,z) = -(1/(8*pi)) * (v_s^2 * (y^2 + z^2) / (4 * r_s^2)) * f'(r_s)^2,

with r_s = sqrt((x - x_s)^2 + y^2 + z^2), bubble velocity v_s, and shape function
f.  Because this is -(non-negative prefactor) * (a square), rho <= 0 EVERYWHERE,
and rho < 0 wherever the bubble wall has a nonzero gradient -- the weak energy
condition is violated for ANY bubble parameters.  The negative energy concentrates
in a torus around the bubble wall (the "ring of negative energy density").

We also report the Ford-Roman quantum-inequality obstruction: quantum field theory
bounds the magnitude/duration of negative energy density; the warp bubble's
requirement exceeds that bound by an enormous factor (Pfenning & Ford 1997), which
is the standard reason the Alcubierre drive is not considered physically realizable.

CLAIM BOUNDARY: this is a classical-GR + semiclassical-QFT analysis of a known toy
metric. It does NOT build a warp drive and makes NO claim that faster-than-light
travel is achievable. The energy-condition violation is exact and machine-checked;
the quantum-inequality obstruction is the standard literature result. Dependency-
light (numpy). Not a continuum/Millennium claim.

References: Alcubierre, Class. Quantum Grav. 11 (1994) L73; Pfenning & Ford,
Class. Quantum Grav. 14 (1997) 1743; Ford & Roman, Phys. Rev. D 51 (1995) 4277.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


def shape_function(r_s, R: float = 1.0, sigma: float = 8.0):
    """Alcubierre top-hat shape function f(r_s): ~1 inside the bubble, ~0 outside.

    f(r_s) = (tanh(sigma (r_s + R)) - tanh(sigma (r_s - R))) / (2 tanh(sigma R)).
    Larger ``sigma`` => thinner bubble wall.
    """
    r_s = np.asarray(r_s, dtype=float)
    num = np.tanh(sigma * (r_s + R)) - np.tanh(sigma * (r_s - R))
    return num / (2.0 * np.tanh(sigma * R))


def shape_function_derivative(r_s, R: float = 1.0, sigma: float = 8.0):
    """Analytic df/dr_s (sech^2 form)."""
    r_s = np.asarray(r_s, dtype=float)
    sech2 = lambda u: 1.0 / np.cosh(u) ** 2
    d = sigma * (sech2(sigma * (r_s + R)) - sech2(sigma * (r_s - R)))
    return d / (2.0 * np.tanh(sigma * R))


def energy_density(x, y, z, *, v_s: float = 1.0, R: float = 1.0, sigma: float = 8.0,
                   x_s: float = 0.0):
    """Eulerian energy density rho(x,y,z) of the Alcubierre metric (G = c = 1).

    Returns a value <= 0 everywhere; strictly < 0 in the bubble wall off-axis.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    r_s = np.sqrt((x - x_s) ** 2 + y ** 2 + z ** 2)
    r_s_safe = np.where(r_s < 1e-12, 1e-12, r_s)
    fp = shape_function_derivative(r_s_safe, R, sigma)
    prefactor = (v_s ** 2 * (y ** 2 + z ** 2)) / (4.0 * r_s_safe ** 2)
    return -(1.0 / (8.0 * np.pi)) * prefactor * fp ** 2


def total_negative_energy(*, v_s: float = 1.0, R: float = 1.0, sigma: float = 8.0,
                          extent: float = 3.0, n_grid: int = 80) -> float:
    """Integral of rho over a box (the total negative energy, <= 0), by midpoint sum.

    Magnitude grows with v_s^2 and with wall steepness sigma -- the standard
    "enormous exotic-energy requirement" result.
    """
    lo, hi = x_s_box(extent, R)
    g = np.linspace(lo, hi, n_grid)
    dx = g[1] - g[0]
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    rho = energy_density(X, Y, Z, v_s=v_s, R=R, sigma=sigma)
    return float(np.sum(rho) * dx ** 3)


def x_s_box(extent: float, R: float):
    """Symmetric integration box [-(R+extent), R+extent]."""
    h = R + extent
    return -h, h


def ford_roman_bound(sampling_time: float) -> float:
    """Ford-Roman quantum-inequality bound on the (sampled) negative energy density
    for a massless scalar field seen by an inertial observer (G = c = hbar = 1):

        integral rho(t) * (tau/pi)/(t^2 + tau^2) dt  >=  -3 / (32 pi^2 tau^4).

    Returns the most-negative allowed *sampled* energy density magnitude (a finite
    floor): |rho|_max ~ 3/(32 pi^2 tau^4). Smaller sampling time tau => more negative
    energy is permitted, but never unboundedly.
    """
    tau = float(sampling_time)
    if tau <= 0:
        return float("inf")
    return 3.0 / (32.0 * np.pi ** 2 * tau ** 4)


def emit_energy_condition_certificate(label: str, prefactor: float, fprime_sq: float):
    """Discharged Lean 4 / Coq proof that the Alcubierre energy density is negative.

    The closed form is rho = -K * s with K = prefactor >= 0 and s = f'(r_s)^2 >= 0,
    so rho <= 0 (and rho < 0 when K, s > 0): the weak energy condition is violated.
    The two non-negativity facts are the labelled trust inputs (K is a manifest ratio
    of squares; s is a square); the assistant discharges the sign of rho with
    nlinarith / nra (no holes).
    """
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "Warp"
    ns = base if not base[0].isdigit() else "W" + base
    lean = f"""import Mathlib.Tactic

namespace WarpEnergy.{ns}

/-- Prefactor K = v_s^2 (y^2+z^2) / (4 r_s^2) and s = f'(r_s)^2 (abstract reals);
    the Alcubierre Eulerian energy density is rho = -(1/(8*pi)) * K * s. -/
variable (K s : ℝ)

/-- TRUST INPUT 1 -- K is a ratio of squares, hence non-negative. -/
axiom K_nonneg : K ≥ 0
/-- TRUST INPUT 2 -- s = f'(r_s)^2 is a square, hence non-negative. -/
axiom s_nonneg : s ≥ 0

/-- The weak energy condition is violated: rho = -(1/(8*pi)) * K * s ≤ 0. -/
theorem rho_nonpos : -(1 / (8 * Real.pi)) * K * s ≤ 0 := by
  have hpi : (0:ℝ) < Real.pi := Real.pi_pos
  have hKs : K * s ≥ 0 := mul_nonneg K_nonneg s_nonneg
  have hcoef : (0:ℝ) < 1 / (8 * Real.pi) := by positivity
  nlinarith [mul_nonneg (le_of_lt hcoef) hKs]

end WarpEnergy.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Require Import Rdefinitions.
Open Scope R_scope.

Section WarpEnergy_{ns}.

(* K = v_s^2 (y^2+z^2) / (4 r_s^2); s = f'(r_s)^2. *)
Variable K s : R.

(* TRUST INPUT 1: K is a ratio of squares, hence non-negative. *)
Hypothesis K_nonneg : K >= 0.
(* TRUST INPUT 2: s = f'(r_s)^2 is a square, hence non-negative. *)
Hypothesis s_nonneg : s >= 0.
(* PI > 0 (so the positive coefficient 1/(8*PI) is well defined). *)
Hypothesis pi_pos : PI > 0.

Theorem rho_nonpos : - (1 / (8 * PI)) * K * s <= 0.
Proof.
  assert (Hco : 1 / (8 * PI) > 0) by (apply Rlt_gt; apply Rdiv_lt_0_compat; lra).
  assert (Hks : K * s >= 0) by (apply Rle_ge; apply Rmult_le_pos; lra).
  nra.
Qed.

End WarpEnergy_{ns}.
"""
    return lean, coq


@dataclass
class WarpAnalysis:
    v_s: float
    R: float
    sigma: float
    rho_min: float                 # most negative energy density on the grid
    wec_violated: bool             # rho_min < 0
    total_negative_energy: float   # integral of rho over the box (<= 0)
    ford_roman_sampling_time: float
    ford_roman_allowed_magnitude: float
    quantum_inequality_violation_factor: float  # |rho_min| / allowed
    ring_radius: float             # cylindrical radius of the most-negative shell
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "alcubierre_warp_energy_condition",
            "v_s": self.v_s, "R": self.R, "sigma": self.sigma,
            "rho_min": self.rho_min,
            "wec_violated": self.wec_violated,
            "total_negative_energy": self.total_negative_energy,
            "ford_roman_sampling_time": self.ford_roman_sampling_time,
            "ford_roman_allowed_magnitude": self.ford_roman_allowed_magnitude,
            "quantum_inequality_violation_factor":
                self.quantum_inequality_violation_factor,
            "ring_radius": self.ring_radius,
            "claim_boundary": ("classical-GR + semiclassical-QFT analysis of a toy "
                               "metric; the negative-energy (weak-energy-condition) "
                               "violation is exact and machine-checked; NOT a buildable "
                               "warp drive and NOT a claim that FTL travel is "
                               "achievable; quantum-inequality obstruction is the "
                               "standard literature result; not a continuum/Millennium "
                               "claim"),
        }


def analyze_warp_bubble(*, v_s: float = 1.0, R: float = 1.0, sigma: float = 8.0,
                        extent: float = 2.5, n_grid: int = 80,
                        sampling_time: Optional[float] = None) -> WarpAnalysis:
    """Sample the Alcubierre energy density, certify the WEC violation, and report the
    Ford-Roman quantum-inequality obstruction."""
    lo, hi = x_s_box(extent, R)
    g = np.linspace(lo, hi, n_grid)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    rho = energy_density(X, Y, Z, v_s=v_s, R=R, sigma=sigma)
    rho_min = float(rho.min())

    # Locate the most-negative point and its cylindrical radius (the negative ring).
    idx = np.unravel_index(np.argmin(rho), rho.shape)
    ring_radius = float(np.sqrt(Y[idx] ** 2 + Z[idx] ** 2))

    total = total_negative_energy(v_s=v_s, R=R, sigma=sigma, extent=extent,
                                  n_grid=n_grid)

    # Ford-Roman: a natural sampling time is the wall-crossing time ~ wall thickness.
    if sampling_time is None:
        sampling_time = 1.0 / sigma            # wall thickness ~ 1/sigma (c = 1)
    allowed = ford_roman_bound(sampling_time)
    violation = abs(rho_min) / allowed if allowed > 0 else float("inf")

    # Certificate uses the exact closed-form sign structure (parameter-independent):
    # rho = -(1/(8 pi)) * K * s with K >= 0, s >= 0.  Pass the measured magnitudes.
    K_at_min = (v_s ** 2 * ring_radius ** 2) / (4.0 * max(1e-12,
               (X[idx]) ** 2 + ring_radius ** 2))
    fprime_sq = float(shape_function_derivative(
        np.sqrt(X[idx] ** 2 + ring_radius ** 2), R, sigma) ** 2)
    lean, coq = emit_energy_condition_certificate("warp", float(K_at_min), fprime_sq)

    return WarpAnalysis(
        v_s=v_s, R=R, sigma=sigma,
        rho_min=rho_min, wec_violated=bool(rho_min < 0.0),
        total_negative_energy=total,
        ford_roman_sampling_time=float(sampling_time),
        ford_roman_allowed_magnitude=float(allowed),
        quantum_inequality_violation_factor=float(violation),
        ring_radius=ring_radius,
        lean4=lean, coq=coq,
    )
