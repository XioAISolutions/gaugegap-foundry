"""Quantum Zeno effect: observation freezes evolution (measurement <-> time).

"Being observed changes the system" is folk wisdom (the **Hawthorne effect** in human
studies: people behave differently when watched).  As sociology it has no exact,
certifiable core -- and naively equating it with quantum measurement would be a category
error.  But it *does* have a rigorous PHYSICAL cousin: in quantum mechanics, observation
genuinely and quantifiably changes the system, and the change can be machine-checked.

The cleanest form is the **quantum Zeno effect**.  Let a system start in state |psi>
and evolve under H for total time T, but interrupt it with N equally spaced projective
measurements onto |psi>.  Each interval lasts tau = T/N, and the single-interval
survival probability is

    P(tau) = |<psi| e^{-iH tau} |psi>|^2 = 1 - (dE * tau)^2 + O(tau^4),

with dE = sqrt(<H^2> - <H>^2) the energy uncertainty.  After N measurements the survival
probability is P(T/N)^N, which obeys the rigorous lower bound (Bernoulli's inequality)

    p_N  >=  1 - (dE * T)^2 / N   -->  1   as N -> infinity.

So **the more often you look, the less the system can evolve** -- in the limit of
continuous observation it is frozen ("a watched quantum pot never boils").  That is the
exact, certifiable version of "observation changes behaviour."

This module computes the real survival probability (via matrix exponentials), checks it
respects the Zeno bound and rises monotonically toward 1 with measurement frequency, and
emits a discharged Lean 4 / Coq certificate that the survival lower bound
B(N) = 1 - (dE T)^2 / N is non-decreasing in N (denominators cleared): more observation
=> a higher survival floor.

CLAIM BOUNDARY: the quantum Zeno effect for a finite-dimensional system under ideal
projective measurements.  It is offered as the rigorous physical *namesake/analogue* of
the sociological Hawthorne effect, NOT an identification with it -- the Hawthorne effect
is a study-design phenomenon about human behaviour with no exact core; this is the
physics of measurement back-action, a different domain.  Not a model of continuous weak
measurement, a specific experiment, or a real measuring apparatus' noise.

References: Misra & Sudarshan, J. Math. Phys. 18 (1977) 756; Itano et al.,
Phys. Rev. A 41 (1990) 2295 (experimental).  Hawthorne effect: Roethlisberger &
Dickson (1939) -- cited only for the analogy, with the boundary above.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.linalg import expm

from gaugegap.quantum.entanglement_speed_limit import energy_uncertainty


def survival_probability(H: np.ndarray, psi: np.ndarray, tau: float) -> float:
    """Single-interval survival |<psi| e^{-iH tau} |psi>|^2 (exact, via matrix exp)."""
    psi = np.asarray(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    H = (np.asarray(H, dtype=complex) + np.asarray(H, dtype=complex).conj().T) / 2.0
    amp = np.vdot(psi, expm(-1j * H * tau) @ psi)
    return float(abs(amp) ** 2)


def zeno_survival(H: np.ndarray, psi: np.ndarray, T: float, n_measurements: int) -> float:
    """Survival after ``n_measurements`` projections onto |psi> over total time T."""
    N = int(n_measurements)
    if N < 1:
        raise ValueError("n_measurements must be >= 1")
    return float(survival_probability(H, psi, T / N) ** N)


def zeno_lower_bound(dE: float, T: float, n_measurements: int) -> float:
    """Rigorous Zeno floor 1 - (dE T)^2 / N (-> 1 as N -> infinity)."""
    N = int(n_measurements)
    if N < 1:
        raise ValueError("n_measurements must be >= 1")
    return float(1.0 - (dE * T) ** 2 / N)


def emit_zeno_certificate(label: str, S: float, N1: float, N2: float):
    """Discharged Lean 4 / Coq proof that the Zeno survival floor is non-decreasing in N.

    The floor is B(N) = 1 - S/N with S = (dE T)^2 >= 0.  For measurement counts
    N2 >= N1 > 0 we have B(N2) >= B(N1); written with denominators cleared
    (multiply by N1*N2 > 0) this is ``N1*(N2 - S) >= N2*(N1 - S)``, which reduces to
    S*(N2 - N1) >= 0.  Trust inputs: S >= 0 and N2 >= N1.  Interpretation: observing
    more often raises the survival floor -- continuous observation freezes the system.
    """
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "Z"
    ns = base if not base[0].isdigit() else "Z" + base
    lean = f"""import Mathlib.Tactic

namespace QuantumZeno.{ns}

/-- Disturbance scale S = (dE T)^2 and two measurement counts N1, N2 (abstract reals). -/
axiom S : ℝ
axiom N1 : ℝ
axiom N2 : ℝ

/-- TRUST INPUT 1 -- the disturbance scale is non-negative. -/
axiom S_nonneg : S ≥ 0
/-- TRUST INPUT 2 -- N2 measures at least as often as N1. -/
axiom more_often : N2 ≥ N1

/-- The Zeno survival floor is non-decreasing in N (denominators cleared):
    N1*(N2 - S) ≥ N2*(N1 - S), i.e. B(N2) ≥ B(N1). -/
theorem zeno_floor_monotone : N1 * (N2 - S) ≥ N2 * (N1 - S) := by
  nlinarith [S_nonneg, more_often]

end QuantumZeno.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section QuantumZeno_{ns}.

(* disturbance scale Sdist = (dE T)^2, measurement counts Na, Nb. *)
Variable Sdist Na Nb : R.

(* TRUST INPUT 1: non-negative disturbance scale. *)
Hypothesis Sdist_nonneg : Sdist >= 0.
(* TRUST INPUT 2: Nb measures at least as often as Na. *)
Hypothesis more_often : Nb >= Na.

(* The Zeno survival floor is non-decreasing in N (denominators cleared):
   Na*(Nb - Sdist) >= Nb*(Na - Sdist), i.e. B(Nb) >= B(Na). *)
Theorem zeno_floor_monotone : Na * (Nb - Sdist) >= Nb * (Na - Sdist).
Proof. nra. Qed.

End QuantumZeno_{ns}.
"""
    return lean, coq


@dataclass
class ZenoResult:
    energy_uncertainty: float
    total_time: float
    n_measurements: list          # the N values sampled (increasing, frequent regime)
    survival: list                # actual P(T/N)^N for each N
    lower_bound: list             # Zeno floor 1 - (dE T)^2 / N for each N
    bound_respected: bool         # survival >= floor for every N
    bound_increases: bool         # the Zeno floor rises with N (always true; the cert)
    survival_increases: bool      # survival rises with N over the sampled frequent regime
    approaches_unity: bool        # survival at the largest N is within tol of 1
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "quantum_zeno_effect",
            "energy_uncertainty": self.energy_uncertainty,
            "total_time": self.total_time,
            "n_measurements": self.n_measurements,
            "survival": self.survival,
            "lower_bound": self.lower_bound,
            "bound_respected": self.bound_respected,
            "bound_increases": self.bound_increases,
            "survival_increases": self.survival_increases,
            "approaches_unity": self.approaches_unity,
            "claim_boundary": ("quantum Zeno effect for a finite-dimensional system "
                               "under ideal projective measurement; the rigorous "
                               "PHYSICAL namesake of the sociological Hawthorne effect, "
                               "NOT an identification with it; not continuous weak "
                               "measurement, a specific experiment, or apparatus noise"),
        }


def analyze_quantum_zeno(H: np.ndarray, psi: np.ndarray, T: float = 2.0,
                         n_list: Sequence[int] = (4, 8, 20, 100, 500)
                         ) -> ZenoResult:
    """Quantum Zeno effect: survival vs. measurement frequency, with the certified floor.

    The default ``n_list`` samples the *frequent-measurement* regime (interval
    ``tau = T/N`` small), where the actual survival rises monotonically toward 1.  The
    always-true, certified object is the lower bound ``1 - (dE T)^2 / N``, which is
    monotone in N for every system; the raw survival only freezes once measurements are
    frequent enough (for very sparse measurement it can oscillate first).
    """
    Ns = [int(n) for n in n_list]
    dE = energy_uncertainty(H, psi)
    surv = [zeno_survival(H, psi, T, n) for n in Ns]
    bound = [zeno_lower_bound(dE, T, n) for n in Ns]
    respected = all(s >= b - 1e-9 for s, b in zip(surv, bound))
    bound_inc = all(bound[i + 1] >= bound[i] - 1e-12 for i in range(len(bound) - 1))
    surv_inc = all(surv[i + 1] >= surv[i] - 1e-9 for i in range(len(surv) - 1))
    approaches = bool(surv[-1] >= 1.0 - max(2.0 * (dE * T) ** 2 / Ns[-1], 1e-6))
    S = float((dE * T) ** 2)
    lean, coq = emit_zeno_certificate("watched", S, float(Ns[0]), float(Ns[-1]))
    return ZenoResult(
        energy_uncertainty=float(dE),
        total_time=float(T),
        n_measurements=Ns,
        survival=[float(s) for s in surv],
        lower_bound=[float(b) for b in bound],
        bound_respected=bool(respected),
        bound_increases=bool(bound_inc),
        survival_increases=bool(surv_inc),
        approaches_unity=approaches,
        lean4=lean, coq=coq,
    )
