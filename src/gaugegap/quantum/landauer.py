"""Landauer's principle: the energy cost of erasing information (info <-> energy).

The keystone that connects the information modules (decoherence/branching) to the
thermodynamics module (ergotropy) and the second law. Erasing information is not
free: resetting a system whose von Neumann entropy drops by Delta_S, in contact with
a bath at temperature T, dissipates at least

    W_min = k_B T * Delta_S        (Delta_S in nats; one bit = ln 2),

so erasing a single fully-mixed bit costs at least k_B T ln 2 (Landauer 1961). This
ties directly to the rest of the suite: decoherence raises a system's entropy (a web
of branches), and undoing that -- resetting to a pure state -- has a provable energy
cost; ergotropy is the work that *can* be extracted, Landauer the work that *must* be
paid to erase.

This module computes the Landauer bound and emits a discharged Lean 4 / Coq
certificate that W_min >= k_B T ln 2 whenever at least one bit is erased.

CLAIM BOUNDARY: an exact finite-system statement of a well-established bound
(Landauer's principle); k_B, T are explicit. It is a *lower bound on dissipated
energy*, not a device or an over-unity claim. Default units are natural (k_B = 1);
an SI value of k_B is available. Not a continuum/Millennium claim.

References: Landauer, IBM J. Res. Dev. 5 (1961) 183; Bennett, Int. J. Theor. Phys.
21 (1982) 905.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from gaugegap.quantum.quantum_information import von_neumann_entropy

# Boltzmann constant in eV/K (used only if SI-style output is requested).
_KB_EV_PER_K = 8.617333262e-5
_LN2 = float(np.log(2.0))


def landauer_bound(delta_S_nats: float, T: float, k_B: float = 1.0) -> float:
    """Minimal dissipated energy to reduce entropy by ``delta_S_nats`` at temp ``T``."""
    return float(k_B * T * delta_S_nats)


def landauer_bit(T: float, k_B: float = 1.0) -> float:
    """Minimal cost to erase one bit: k_B T ln 2."""
    return float(k_B * T * _LN2)


def erasure_cost(rho: np.ndarray, T: float, k_B: float = 1.0) -> float:
    """Cost to reset ``rho`` to a pure state: k_B T S(rho) (S = von Neumann entropy)."""
    return float(k_B * T * von_neumann_entropy(np.asarray(rho, dtype=complex)))


def emit_landauer_certificate(label: str, k_B: float, T: float, delta_S: float):
    """Discharged Lean 4 / Coq proof that W_min = k_B T Delta_S >= k_B T ln 2 when at
    least one bit is erased (Delta_S >= ln 2).

    Trust inputs: k_B > 0, T > 0, and Delta_S >= ln 2 (at least one bit erased); the
    assistant discharges W_min >= k_B T ln 2 with nlinarith / nra.
    """
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "W"
    ns = base if not base[0].isdigit() else "W" + base
    kb, t = float(k_B), float(T)
    floor = kb * t * _LN2
    lean = f"""import Mathlib.Tactic

namespace Landauer.{ns}

/-- Boltzmann constant kB, temperature T, entropy drop dS, and one-bit entropy
    b = ln 2 (nats) -- abstract reals; only the labelled trust facts are used. -/
axiom kB : ℝ
axiom T : ℝ
axiom dS : ℝ
axiom b : ℝ

/-- TRUST INPUT 1 -- positive Boltzmann constant. -/
axiom kB_pos : kB > 0
/-- TRUST INPUT 2 -- positive temperature. -/
axiom T_pos : T > 0
/-- TRUST INPUT 3 -- at least one bit erased: dS >= b (b = ln 2). -/
axiom dS_bit : dS ≥ b

/-- Erasing at least one bit costs at least kB*T*b = k_B T ln 2 (no holes). -/
theorem landauer_floor : kB * T * dS ≥ kB * T * b := by
  have hkt : (0:ℝ) ≤ kB * T := le_of_lt (mul_pos kB_pos T_pos)
  nlinarith [mul_le_mul_of_nonneg_left dS_bit hkt]

end Landauer.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Landauer_{ns}.

(* kB, T, entropy drop dS, one-bit entropy b = ln 2 (nats). *)
Variable kB T dS b : R.

(* TRUST INPUT 1: positive Boltzmann constant. *)
Hypothesis kB_pos : kB > 0.
(* TRUST INPUT 2: positive temperature. *)
Hypothesis T_pos : T > 0.
(* TRUST INPUT 3: at least one bit erased: dS >= b (b = ln 2). *)
Hypothesis dS_bit : dS >= b.

Theorem landauer_floor : kB * T * dS >= kB * T * b.
Proof.
  assert (Hkt : 0 <= kB * T) by (apply Rlt_le; apply Rmult_lt_0_compat; lra).
  nra.
Qed.

End Landauer_{ns}.
"""
    return lean, coq, floor


@dataclass
class LandauerResult:
    entropy_nats: float            # S(rho), the information content erased
    temperature: float
    k_B: float
    erasure_cost: float            # k_B T S
    bit_floor: float               # k_B T ln 2
    bits_erased: float             # S / ln 2
    erasure_cost_eV: Optional[float]
    above_bit_floor: bool          # erasure_cost >= bit_floor (>= 1 bit)
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "landauer_erasure_cost",
            "entropy_nats": self.entropy_nats,
            "temperature": self.temperature, "k_B": self.k_B,
            "erasure_cost": self.erasure_cost, "bit_floor": self.bit_floor,
            "bits_erased": self.bits_erased,
            "erasure_cost_eV": self.erasure_cost_eV,
            "above_bit_floor": self.above_bit_floor,
            "claim_boundary": ("exact finite-system Landauer bound: erasing entropy "
                               "Delta_S costs >= k_B T Delta_S; a lower bound on "
                               "dissipated energy, not a device or over-unity claim; "
                               "not a continuum/Millennium claim"),
        }


def analyze_landauer(rho: np.ndarray, T: float = 1.0, k_B: float = 1.0,
                     temperature_K: Optional[float] = None) -> LandauerResult:
    """Erasure cost of resetting ``rho`` to a pure state, with a certified k_B T ln 2
    floor when at least one bit is erased.

    If ``temperature_K`` is given, an SI cost in eV is also reported (k_B in eV/K)."""
    S = von_neumann_entropy(np.asarray(rho, dtype=complex))
    cost = k_B * T * S
    floor = landauer_bit(T, k_B)
    lean, coq, _ = emit_landauer_certificate("W_erase", k_B, T, S)
    cost_eV = None
    if temperature_K is not None:
        cost_eV = float(_KB_EV_PER_K * temperature_K * S)
    return LandauerResult(
        entropy_nats=float(S), temperature=float(T), k_B=float(k_B),
        erasure_cost=float(cost), bit_floor=float(floor),
        bits_erased=float(S / _LN2), erasure_cost_eV=cost_eV,
        above_bit_floor=bool(S >= _LN2 - 1e-12), lean4=lean, coq=coq,
    )
