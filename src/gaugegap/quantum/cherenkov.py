"""Cherenkov radiation: a certified "local speed limit" and its cone geometry.

The honest core of the Cherenkov reel (the blue glow in reactor pools). In a medium of
refractive index n, light travels at c/n, so a charged particle with speed beta*c can
exceed the *local* light speed when beta > 1/n. It then outruns the spherical
wavefronts it emits, which pile up into a coherent cone (the optical sonic boom). The
Cherenkov angle obeys

    cos(theta_c) = 1 / (n * beta),

which is real only at/above the threshold beta = 1/n (n*beta >= 1). This is the
velocity<->geometry edge of the physical-limits web: a local speed limit (c/n) whose
breach has an exact geometric signature, sibling to the quantum speed limit
(time<->energy) and the Alcubierre energy condition (energy<->geometry).

This module simulates the wavefront pile-up, recovers the cone angle numerically from
the emitted-wavefront point cloud, verifies cos(theta_c) = 1/(n beta), and emits a
discharged Lean 4 / Coq certificate that the cone cosine is valid (0 < cos theta_c <= 1)
at/above threshold.

CLAIM BOUNDARY: a finite, exact classical-electromagnetism / geometry demonstration of
the Cherenkov principle; NOT a reproduction of any detector or its numbers (RICH,
Super-Kamiokande, etc.), and the "why it's blue" spectral weighting is not modelled.
The cone relation and threshold are exact theorems. Dependency-light (numpy). Not a
continuum/Millennium claim.

References: Cherenkov (1934); Frank & Tamm (1937); Jackson, Classical Electrodynamics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


def cherenkov_threshold(n: float) -> float:
    """Minimum speed (as a fraction of c) for emission: beta_min = 1/n."""
    return 1.0 / float(n)


def emits(n: float, beta: float) -> bool:
    """True iff the particle outruns light-in-medium: n*beta > 1 (above threshold)."""
    return bool(float(n) * float(beta) > 1.0)


def cone_angle(n: float, beta: float) -> Optional[float]:
    """Cherenkov angle theta_c = arccos(1/(n beta)) (radians), or None below threshold."""
    x = 1.0 / (float(n) * float(beta))
    if x > 1.0:
        return None
    return float(np.arccos(x))


def wavefront_cone(n: float, beta: float, *, t_obs: float = 1.0,
                   n_sources: int = 400, n_phi: int = 720) -> dict:
    """Simulate the spherical wavefronts emitted along the track and RECOVER the cone
    angle from the resulting point cloud (no use of the closed form in the recovery).

    Sets c = 1. The particle moves along +x at speed ``beta``; at emission time t_k it
    sits at x_k = beta*t_k and emits a sphere expanding at c/n; by ``t_obs`` that sphere
    has radius (t_obs - t_k)/n. The leading point (apex) is at x_apex = beta*t_obs; the
    cone surface is the outermost tangent from the apex, at half-angle alpha from the
    axis with sin(alpha) = 1/(n beta) = cos(theta_c).
    """
    t_obs = float(t_obs)
    x_apex = beta * t_obs
    ts = np.linspace(0.0, t_obs, n_sources)
    phis = np.linspace(0.0, 2 * np.pi, n_phi, endpoint=False)
    cos_p, sin_p = np.cos(phis), np.sin(phis)
    best = 0.0
    for tk in ts:
        r = (t_obs - tk) / n
        if r <= 0:
            continue
        xc = beta * tk
        xs = xc + r * cos_p
        rho = np.abs(r * sin_p)
        dx = x_apex - xs
        mask = dx > 1e-9
        if not np.any(mask):
            continue
        ang = np.max(np.arctan(rho[mask] / dx[mask]))   # angle from axis at the apex
        best = max(best, float(ang))
    cos_theta_c_recovered = float(np.sin(best))          # cos theta_c = sin(alpha)
    return {"apex_half_angle": best,
            "cos_theta_c_recovered": cos_theta_c_recovered,
            "x_apex": float(x_apex)}


def emit_cherenkov_certificate(label: str, n: float, beta: float):
    """Discharged Lean 4 / Coq proof that the Cherenkov cone cosine is valid at/above
    threshold: with c = cos(theta_c), nb = n*beta, the facts nb >= 1, c > 0, c*nb = 1
    give 0 < c <= 1 (so theta_c is a real angle)."""
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "Ch"
    ns = base if not base[0].isdigit() else "C" + base
    lean = f"""import Mathlib.Tactic

namespace Cherenkov.{ns}

/-- c = cos(theta_c) and nb = n*beta (abstract reals). -/
axiom c : ℝ
axiom nb : ℝ

/-- TRUST INPUT 1 -- at/above threshold: n*beta >= 1. -/
axiom above_threshold : nb ≥ 1
/-- TRUST INPUT 2 -- the cone cosine is positive. -/
axiom cos_pos : c > 0
/-- TRUST INPUT 3 -- the Cherenkov relation cos(theta_c) * (n beta) = 1. -/
axiom cherenkov_relation : c * nb = 1

/-- The cone cosine is a valid cosine: 0 < c <= 1 (theta_c is a real angle). -/
theorem cone_valid : 0 < c ∧ c ≤ 1 := by
  refine ⟨cos_pos, ?_⟩
  nlinarith [cherenkov_relation, above_threshold, cos_pos]

end Cherenkov.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Cherenkov_{ns}.

(* c = cos(theta_c), nb = n*beta. *)
Variable c nb : R.

(* TRUST INPUT 1: at/above threshold n*beta >= 1. *)
Hypothesis above_threshold : nb >= 1.
(* TRUST INPUT 2: the cone cosine is positive. *)
Hypothesis cos_pos : c > 0.
(* TRUST INPUT 3: the Cherenkov relation cos(theta_c) * (n beta) = 1. *)
Hypothesis cherenkov_relation : c * nb = 1.

Theorem cone_valid : 0 < c /\\ c <= 1.
Proof. split; nra. Qed.

End Cherenkov_{ns}.
"""
    return lean, coq


@dataclass
class CherenkovResult:
    n: float
    beta: float
    threshold_beta: float
    emits: bool
    cos_theta_c: float            # 1/(n beta) (closed form)
    theta_c_deg: float            # Cherenkov angle in degrees
    cos_theta_c_recovered: float  # from the wavefront simulation
    recovery_error: float         # |recovered - closed form|
    cone_valid: bool              # 0 < cos_theta_c <= 1
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "cherenkov_cone",
            "n": self.n, "beta": self.beta, "threshold_beta": self.threshold_beta,
            "emits": self.emits, "cos_theta_c": self.cos_theta_c,
            "theta_c_deg": self.theta_c_deg,
            "cos_theta_c_recovered": self.cos_theta_c_recovered,
            "recovery_error": self.recovery_error, "cone_valid": self.cone_valid,
            "claim_boundary": ("finite exact EM/geometry demo of the Cherenkov cone "
                               "(local speed limit c/n; cos theta_c = 1/(n beta)); NOT "
                               "a detector reproduction and spectral 'blue' weighting "
                               "not modelled; the cone relation and threshold are exact "
                               "theorems; not a continuum/Millennium claim"),
        }


def analyze_cherenkov(n: float = 1.33, beta: float = 0.9, *, t_obs: float = 1.0,
                      n_sources: int = 400, n_phi: int = 720) -> CherenkovResult:
    """Cherenkov cone for a particle of speed ``beta`` in a medium of index ``n``:
    closed-form angle, numerically recovered angle from the wavefront pile-up, and a
    discharged Lean/Coq certificate that the cone cosine is valid (above threshold)."""
    thr = cherenkov_threshold(n)
    does_emit = emits(n, beta)
    cos_tc = 1.0 / (n * beta)
    theta = cone_angle(n, beta)
    sim = wavefront_cone(n, beta, t_obs=t_obs, n_sources=n_sources, n_phi=n_phi)
    rec = sim["cos_theta_c_recovered"]
    err = abs(rec - cos_tc) if does_emit else float("nan")
    lean, coq = emit_cherenkov_certificate("cone", n, beta)
    return CherenkovResult(
        n=float(n), beta=float(beta), threshold_beta=float(thr), emits=does_emit,
        cos_theta_c=float(cos_tc),
        theta_c_deg=float(np.degrees(theta)) if theta is not None else float("nan"),
        cos_theta_c_recovered=float(rec), recovery_error=float(err),
        cone_valid=bool(does_emit and 0.0 < cos_tc <= 1.0),
        lean4=lean, coq=coq,
    )
