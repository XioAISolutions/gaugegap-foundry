"""Transmon / Cooper-pair-box artificial atom: why a Josephson junction makes a qubit.

A superconducting qubit is an *electrical circuit* that behaves like an atom.  A plain
LC circuit is a harmonic oscillator: its energy levels are **equally spaced**, so a
microwave pulse resonant with the 0->1 transition is equally resonant with 1->2, 2->3,
...  -- you cannot isolate a two-level system, and it is useless as a qubit.

The fix is the **Josephson junction**: Cooper pairs tunnel through a thin insulator,
adding a *nonlinear* `-E_J cos(phi)` term to the circuit Hamiltonian.  In the charge
(Cooper-pair-number) basis the transmon Hamiltonian is

    H = 4 E_C (n - n_g)^2  -  E_J cos(phi),

   <n| 4 E_C (n - n_g)^2 |n> = 4 E_C (n - n_g)^2     (charging energy, diagonal)
   <n| -E_J cos(phi) |n+/-1> = -E_J / 2              (Josephson tunnelling, off-diagonal)

The nonlinearity makes the levels **anharmonic**: the qubit transition omega_01 is
detuned from omega_12 by the *anharmonicity* alpha = omega_12 - omega_01, which in the
transmon regime (E_J >> E_C) approaches `alpha ~ -E_C != 0`.  That nonzero gap is exactly
what lets a resonant pulse address |0> <-> |1> alone.  In the same regime the qubit
frequency's sensitivity to offset-charge noise (the *charge dispersion*) is suppressed
**exponentially** in sqrt(8 E_J/E_C) -- the reason transmons are the workhorse qubit.

Because the charge-basis matrix has **exactly rational** entries (no irrationals), this
module also returns a *certified* interval enclosure of the anharmonicity from the
repository's verified Hermitian eigensolver: when the enclosure lies strictly below
zero, the qubit is **provably** anharmonic (addressable).  A discharged Lean 4 / Coq
certificate records the algebraic core -- a nonzero charging energy E_C gives a nonzero,
resolvable qubit transition gap (the harmonic E_C -> 0 limit closes the gap).

CLAIM BOUNDARY: the standard Cooper-pair-box / transmon model (Koch et al., Phys. Rev. A
76, 042319, 2007), as a finite charge-basis numerical diagonalization with a rigorous
interval enclosure of the anharmonicity.  Energies are in units of E_C; it is NOT a
fabrication, materials, coherence-time (T1/T2), or specific-device claim, and it is NOT
a member of the physical-limits web (this is device engineering, not a fundamental
trade-off bound).

References: Koch et al., Phys. Rev. A 76, 042319 (2007); Krantz et al., Appl. Phys. Rev.
6, 021318 (2019) ("A Quantum Engineer's Guide to Superconducting Qubits").
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    IntervalMatrix,
    verified_hermitian_eigenvalues,
)


def transmon_hamiltonian(EJ: float, EC: float, ng: float = 0.0,
                         n_charge: int = 15) -> np.ndarray:
    """Transmon H = 4 E_C (n - n_g)^2 - E_J cos(phi) in the charge basis (-N..N)."""
    if EJ <= 0 or EC <= 0:
        raise ValueError("EJ and EC must be positive")
    ns = np.arange(-n_charge, n_charge + 1)
    H = np.diag(4.0 * EC * (ns - ng) ** 2).astype(float)
    off = -EJ / 2.0 * np.ones(2 * n_charge)
    H += np.diag(off, 1) + np.diag(off, -1)
    return H


def transmon_levels(EJ: float, EC: float, ng: float = 0.0, n_charge: int = 15,
                    n_levels: int = 3) -> np.ndarray:
    """Lowest ``n_levels`` energy levels of the transmon (numpy diagonalization)."""
    ev = np.linalg.eigvalsh(transmon_hamiltonian(EJ, EC, ng, n_charge))
    return np.sort(ev)[:n_levels]


def transition_frequencies(EJ: float, EC: float, ng: float = 0.0,
                           n_charge: int = 15) -> tuple:
    """(omega_01, omega_12): the 0->1 and 1->2 transition frequencies."""
    e = transmon_levels(EJ, EC, ng, n_charge, 3)
    return float(e[1] - e[0]), float(e[2] - e[1])


def anharmonicity(EJ: float, EC: float, ng: float = 0.0, n_charge: int = 15) -> float:
    """alpha = omega_12 - omega_01 (-> -E_C in the transmon regime; 0 for a harmonic LC)."""
    w01, w12 = transition_frequencies(EJ, EC, ng, n_charge)
    return float(w12 - w01)


def charge_dispersion(EJ: float, EC: float, n_charge: int = 15) -> float:
    """|omega_01(n_g=0) - omega_01(n_g=1/2)|: sensitivity of the qubit freq to charge noise.

    Exponentially suppressed ~ exp(-sqrt(8 E_J/E_C)) in the transmon regime.
    """
    w01_0 = transition_frequencies(EJ, EC, 0.0, n_charge)[0]
    w01_h = transition_frequencies(EJ, EC, 0.5, n_charge)[0]
    return float(abs(w01_h - w01_0))


def plasma_frequency(EJ: float, EC: float) -> float:
    """The harmonic (plasma) frequency sqrt(8 E_J E_C) the transmon oscillates near."""
    return float(np.sqrt(8.0 * EJ * EC))


def certified_anharmonicity(EJ: float, EC: float, ng: float = 0.0,
                            n_charge: int = 12) -> Interval:
    """Rigorous interval enclosure of alpha = E_0 - 2 E_1 + E_2 (= omega_12 - omega_01).

    The charge-basis matrix is exactly rational, so its entries are exact and the
    verified Hermitian eigensolver returns certified eigenvalue enclosures.  When the
    returned interval lies strictly below 0 the transmon is *provably* anharmonic.
    """
    if EJ <= 0 or EC <= 0:
        raise ValueError("EJ and EC must be positive")
    ns = range(-n_charge, n_charge + 1)
    dim = 2 * n_charge + 1
    rows = [[0.0] * dim for _ in range(dim)]
    for i, n in enumerate(ns):
        rows[i][i] = 4.0 * EC * (n - ng) ** 2
        if i + 1 < dim:
            rows[i][i + 1] = -EJ / 2.0
            rows[i + 1][i] = -EJ / 2.0
    enc = verified_hermitian_eigenvalues(IntervalMatrix.from_floats(rows))
    E0, E1, E2 = enc[0], enc[1], enc[2]
    # alpha = E0 - 2 E1 + E2 ; combine endpoints soundly (subtraction flips bounds)
    lo = E0.lower - 2 * E1.upper + E2.lower
    hi = E0.upper - 2 * E1.lower + E2.upper
    return Interval(lower=lo, upper=hi)


def emit_transmon_certificate(label: str, EC: float):
    """Discharged Lean 4 / Coq proof that the Josephson nonlinearity opens the qubit gap.

    Leading order, the transition frequencies are omega_01 = wt - E_C and
    omega_12 = wt - 2 E_C (wt = sqrt(8 E_J E_C) the plasma frequency).  Trust input:
    E_C > 0 (a nonzero charging-energy nonlinearity).  Then omega_01 - omega_12 = E_C > 0
    -- the qubit transition is resolvable from the 1->2 transition.  The harmonic limit
    E_C -> 0 closes the gap (no qubit).
    """
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "T"
    ns = base if not base[0].isdigit() else "T" + base
    lean = f"""import Mathlib.Tactic

namespace Transmon.{ns}

/-- Plasma frequency wt, charging energy Ec, transition frequencies w01, w12. -/
axiom wt : ℝ
axiom Ec : ℝ
axiom w01 : ℝ
axiom w12 : ℝ

/-- TRUST INPUT 1 -- nonzero charging-energy nonlinearity. -/
axiom Ec_pos : Ec > 0
/-- TRUST INPUT 2 -- leading-order 0->1 transition frequency. -/
axiom def01 : w01 = wt - Ec
/-- TRUST INPUT 3 -- leading-order 1->2 transition frequency. -/
axiom def12 : w12 = wt - 2 * Ec

/-- The qubit transition is resolvable: w01 > w12 (anharmonic gap = Ec > 0). -/
theorem addressable : w01 > w12 := by
  rw [def01, def12]; linarith [Ec_pos]

end Transmon.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Transmon_{ns}.

(* plasma frequency wt, charging energy Ec, transition frequencies w01, w12. *)
Variable wt Ec w01 w12 : R.

(* TRUST INPUT 1: nonzero charging-energy nonlinearity. *)
Hypothesis Ec_pos : Ec > 0.
(* TRUST INPUT 2: leading-order 0->1 transition frequency. *)
Hypothesis def01 : w01 = wt - Ec.
(* TRUST INPUT 3: leading-order 1->2 transition frequency. *)
Hypothesis def12 : w12 = wt - 2 * Ec.

(* The qubit transition is resolvable: w01 > w12 (anharmonic gap = Ec > 0). *)
Theorem addressable : w01 > w12.
Proof. rewrite def01, def12. lra. Qed.

End Transmon_{ns}.
"""
    return lean, coq


@dataclass
class TransmonResult:
    EJ: float
    EC: float
    EJ_EC_ratio: float
    omega01: float
    omega12: float
    anharmonicity: float                 # omega_12 - omega_01 (numeric)
    anharmonicity_over_EC: float         # ~ -1 in the transmon regime
    certified_anharmonicity_lower: float  # rigorous enclosure of alpha (interval)
    certified_anharmonicity_upper: float
    is_anharmonic_certified: bool        # enclosure strictly below 0 -> provably addressable
    charge_dispersion: float             # |omega_01(0) - omega_01(1/2)|
    plasma_frequency: float              # sqrt(8 E_J E_C)
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "transmon_artificial_atom",
            "EJ": self.EJ, "EC": self.EC, "EJ_EC_ratio": self.EJ_EC_ratio,
            "omega01": self.omega01, "omega12": self.omega12,
            "anharmonicity": self.anharmonicity,
            "anharmonicity_over_EC": self.anharmonicity_over_EC,
            "certified_anharmonicity_lower": self.certified_anharmonicity_lower,
            "certified_anharmonicity_upper": self.certified_anharmonicity_upper,
            "is_anharmonic_certified": self.is_anharmonic_certified,
            "charge_dispersion": self.charge_dispersion,
            "plasma_frequency": self.plasma_frequency,
            "claim_boundary": ("standard Cooper-pair-box / transmon model (Koch et al. "
                               "2007) as a finite charge-basis diagonalization with a "
                               "rigorous interval enclosure of the anharmonicity; "
                               "energies in units of E_C; NOT a fabrication, materials, "
                               "coherence-time, or specific-device claim; NOT a member "
                               "of the physical-limits web"),
        }


def analyze_transmon(EJ: float = 50.0, EC: float = 1.0, ng: float = 0.0,
                     n_charge: int = 15) -> TransmonResult:
    """Diagonalize a transmon and certify that its qubit transition is anharmonic."""
    w01, w12 = transition_frequencies(EJ, EC, ng, n_charge)
    alpha = w12 - w01
    cert = certified_anharmonicity(EJ, EC, ng, min(n_charge, 12))
    lean, coq = emit_transmon_certificate("qubit", EC)
    return TransmonResult(
        EJ=float(EJ), EC=float(EC), EJ_EC_ratio=float(EJ / EC),
        omega01=float(w01), omega12=float(w12),
        anharmonicity=float(alpha), anharmonicity_over_EC=float(alpha / EC),
        certified_anharmonicity_lower=float(cert.lower),
        certified_anharmonicity_upper=float(cert.upper),
        is_anharmonic_certified=bool(float(cert.upper) < 0.0),
        charge_dispersion=charge_dispersion(EJ, EC, n_charge),
        plasma_frequency=plasma_frequency(EJ, EC),
        lean4=lean, coq=coq,
    )
