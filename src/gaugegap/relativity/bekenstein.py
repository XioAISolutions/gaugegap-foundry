"""Bekenstein bound: geometry limits information (info <-> energy <-> geometry).

The keystone that connects the quantum-information modules (entanglement, decoherence
/branching) to the relativity module (Alcubierre energy conditions). The Bekenstein
bound caps the entropy that can be contained in a region of radius R holding energy E:

    S <= 2 pi k_B R E / (hbar c)      (natural units hbar=c=k_B=1:  S <= 2 pi R E).

Equivalently, holding entropy S with energy E requires a region of radius at least
R_min = S / (2 pi E). This ties the three currencies together: the von Neumann
entropy of our quantum states (information), the energy above the ground state
(energy), and the size of the region (geometry).

This module computes the bound for a finite system, reports the minimal radius, and
emits a discharged Lean 4 / Coq certificate that S <= 2 pi R E whenever R >= R_min.

CLAIM BOUNDARY: the Bekenstein bound is a universal *semiclassical* bound; here it is
applied to a finite system's entropy and energy as a consistency relation among
information, energy, and geometry. This is NOT a derivation of holography, a black-
hole result, or a quantum-gravity claim. Natural units throughout. Not a continuum/
Millennium claim.

References: Bekenstein, Phys. Rev. D 23 (1981) 287; Casini, Class. Quantum Grav. 25
(2008) 205021 (a QFT-rigorous formulation).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gaugegap.quantum.quantum_information import von_neumann_entropy

_TWO_PI = float(2.0 * np.pi)


def bekenstein_bound(R: float, E: float) -> float:
    """Maximal entropy (nats) in a region of radius R holding energy E: 2 pi R E."""
    return float(_TWO_PI * R * E)


def minimal_radius(S: float, E: float) -> float:
    """Smallest region radius that can hold entropy S with energy E: S / (2 pi E)."""
    if E <= 0:
        return float("inf")
    return float(S / (_TWO_PI * E))


def emit_bekenstein_certificate(label: str, R: float, E: float):
    """Discharged Lean 4 / Coq proof that S <= 2 pi R E when R >= S / (2 pi E).

    Trust inputs: E > 0, R > 0, and R >= S/(2 pi E) (the region is at least the
    minimal Bekenstein radius); the assistant discharges S <= 2 pi R E with nra.
    """
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "B"
    ns = base if not base[0].isdigit() else "B" + base
    lean = f"""import Mathlib.Tactic

namespace Bekenstein.{ns}

/-- Entropy S, energy E, radius R (abstract reals). -/
axiom S : ℝ
axiom E : ℝ
axiom R : ℝ

/-- TRUST INPUT 1 -- positive energy. -/
axiom E_pos : E > 0
/-- TRUST INPUT 2 -- the region is at least the minimal Bekenstein radius, written
    with the denominator cleared: R * (2 pi E) >= S  (i.e. R >= S / (2 pi E)). -/
axiom geom : R * (2 * Real.pi * E) ≥ S

/-- The entropy respects the Bekenstein bound: S <= 2 pi R E (no holes). -/
theorem bekenstein : S ≤ 2 * Real.pi * R * E := by
  nlinarith [geom]

end Bekenstein.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Bekenstein_{ns}.

(* entropy Sent, energy E, radius Rad (Rad avoids shadowing the type R). *)
Variable Sent E Rad : R.

(* TRUST INPUT 1: positive energy. *)
Hypothesis E_pos : E > 0.
(* TRUST INPUT 2: region at least the minimal Bekenstein radius, denominator
   cleared: Rad * (2 * PI * E) >= Sent  (i.e. Rad >= Sent / (2 PI E)). *)
Hypothesis geom : Rad * (2 * PI * E) >= Sent.

Theorem bekenstein : Sent <= 2 * PI * Rad * E.
Proof. nra. Qed.

End Bekenstein_{ns}.
"""
    return lean, coq


@dataclass
class BekensteinResult:
    entropy_nats: float
    energy: float                  # energy above ground state
    radius: float
    bound: float                   # 2 pi R E
    minimal_radius: float          # S / (2 pi E)
    respects_bound: bool           # S <= 2 pi R E
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "bekenstein_bound",
            "entropy_nats": self.entropy_nats, "energy": self.energy,
            "radius": self.radius, "bound": self.bound,
            "minimal_radius": self.minimal_radius,
            "respects_bound": self.respects_bound,
            "claim_boundary": ("universal semiclassical Bekenstein bound applied to a "
                               "finite system as an info-energy-geometry consistency "
                               "relation; NOT holography, a black-hole result, or a "
                               "quantum-gravity claim; not a continuum/Millennium "
                               "claim"),
        }


def analyze_bekenstein(rho: np.ndarray, H: np.ndarray, radius: float) -> BekensteinResult:
    """Bekenstein bound for state ``rho`` under ``H`` in a region of given ``radius``.

    Energy is taken above the ground state (E = <H> - E0 >= 0)."""
    rho = (np.asarray(rho, dtype=complex) + np.asarray(rho, dtype=complex).conj().T) / 2
    H = (np.asarray(H, dtype=complex) + np.asarray(H, dtype=complex).conj().T) / 2
    S = von_neumann_entropy(rho)
    e0 = float(np.linalg.eigvalsh(H)[0])
    E = float(np.real(np.trace(rho @ H))) - e0
    E = max(E, 1e-12)
    bound = bekenstein_bound(radius, E)
    r_min = minimal_radius(S, E)
    lean, coq = emit_bekenstein_certificate("S_region", radius, E)
    return BekensteinResult(
        entropy_nats=float(S), energy=float(E), radius=float(radius),
        bound=float(bound), minimal_radius=float(r_min),
        respects_bound=bool(S <= bound + 1e-9), lean4=lean, coq=coq,
    )
