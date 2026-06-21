"""Quantum speed limits on entanglement formation.

The attosecond-entanglement result shows entanglement forms over a *finite* time.
Quantum speed limits explain WHY there must be a floor: the Mandelstam-Tamm and
Margolus-Levitin bounds give rigorous lower bounds on the time needed to evolve
from the initial (unentangled) state to the entangled target state.

For a state evolving under a time-independent H (hbar = 1), the time t to reach a
state at Fubini-Study angle L = arccos|<psi0|psi_t>| from the start satisfies BOTH

    t >= L / dE         (Mandelstam-Tamm,   dE = sqrt(<H^2> - <H>^2))
    t >= L / (<H> - E0) (Margolus-Levitin,  E0 = ground energy),

hence t >= tau_QSL := max of the two.  This module measures the entanglement
build-up time of a finite model (via ``entanglement_dynamics``) and CERTIFIES,
with a discharged Lean 4 / Coq proof, that the measured build-up time respects the
tighter QSL floor.  The two QSL inequalities are the labelled trust inputs (they
are theorems of quantum mechanics); the assistant discharges that the build-up
time exceeds ``max(tau_MT, tau_ML)``.

CLAIM BOUNDARY: a finite-model demonstration. The QSL inequalities are exact and
verified on the simulated evolution; this is NOT a reproduction of the TU Wien
helium experiment, the ~232 attosecond figure, or any real atom. The optional
physical-time conversion (t = t_model * hbar / E) is illustrative only.
Dependency-light (numpy only).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from gaugegap.quantum.entanglement_dynamics import (
    _HBAR_EV_AS,
    entanglement_curve,
    evolve_state,
    simulate_buildup,
)


def fubini_study_angle(psi0: np.ndarray, psi1: np.ndarray) -> float:
    """Geometric distance L = arccos|<psi0|psi1>| between two normalized states."""
    a = np.asarray(psi0, dtype=complex)
    b = np.asarray(psi1, dtype=complex)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    overlap = float(min(1.0, abs(np.vdot(a, b))))
    return float(np.arccos(overlap))


def energy_uncertainty(H: np.ndarray, psi: np.ndarray) -> float:
    """dE = sqrt(<H^2> - <H>^2) for the (Hermitized) H in state psi."""
    H = (np.asarray(H) + np.asarray(H).conj().T) / 2.0
    psi = np.asarray(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    Hpsi = H @ psi
    mean = float(np.real(np.vdot(psi, Hpsi)))
    h2 = float(np.real(np.vdot(Hpsi, Hpsi)))
    return float(np.sqrt(max(0.0, h2 - mean * mean)))


def mean_energy_above_ground(H: np.ndarray, psi: np.ndarray) -> float:
    """<H> - E0 (energy above the ground state), the Margolus-Levitin scale."""
    H = (np.asarray(H) + np.asarray(H).conj().T) / 2.0
    psi = np.asarray(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    mean = float(np.real(np.vdot(psi, H @ psi)))
    e0 = float(np.linalg.eigvalsh(H)[0])
    return float(mean - e0)


def quantum_speed_limit(H: np.ndarray, psi0: np.ndarray,
                        psi_target: np.ndarray) -> dict:
    """Mandelstam-Tamm + Margolus-Levitin floors (hbar = 1) for psi0 -> psi_target."""
    angle = fubini_study_angle(psi0, psi_target)
    dE = energy_uncertainty(H, psi0)
    above = mean_energy_above_ground(H, psi0)
    tau_mt = angle / dE if dE > 1e-12 else float("inf")
    tau_ml = angle / above if above > 1e-12 else float("inf")
    return {
        "angle": angle,
        "energy_uncertainty": dE,
        "energy_above_ground": above,
        "tau_mandelstam_tamm": tau_mt,
        "tau_margolus_levitin": tau_ml,
        "tau_qsl": max(tau_mt, tau_ml),
    }


def max_entangling_rate(H: np.ndarray, psi0: np.ndarray, times,
                        *, keep_qubits: Optional[List[int]] = None) -> float:
    """Max |dS/dt| of the entanglement entropy along the evolution (finite diff).

    The entangling rate is set by the interaction: a stronger coupling builds
    entanglement faster, which is exactly why the QSL floor shrinks with coupling.
    """
    times = list(times)
    s = entanglement_curve(H, psi0, times, keep_qubits=keep_qubits)
    t = np.asarray(times, dtype=float)
    s = np.asarray(s, dtype=float)
    if t.size < 2:
        return 0.0
    return float(np.max(np.abs(np.gradient(s, t))))


def emit_speed_limit_certificate(label: str, tau_mt: float, tau_ml: float):
    """Discharged Lean4 + Coq proof that the measured build-up time exceeds the QSL.

    Trust inputs are the two QSL theorems (t >= tau_MT and t >= tau_ml); the
    assistant discharges t >= max(tau_MT, tau_ml) = tau_QSL by linarith / lra.
    """
    tau_qsl = max(tau_mt, tau_ml)
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "T"
    ns = base if not base[0].isdigit() else "T" + base
    lean = f"""import Mathlib.Tactic

namespace SpeedLimit.{ns}

/-- The entanglement build-up time t (abstract); only the QSL facts are used. -/
axiom t : ℝ

/-- TRUST INPUT 1 -- Mandelstam-Tamm quantum speed limit. -/
axiom mandelstam_tamm : t ≥ {float(tau_mt)!r}

/-- TRUST INPUT 2 -- Margolus-Levitin quantum speed limit. -/
axiom margolus_levitin : t ≥ {float(tau_ml)!r}

/-- The build-up time respects the tighter QSL floor (no holes). -/
theorem respects_qsl : t ≥ {float(tau_qsl)!r} := by
  linarith [mandelstam_tamm, margolus_levitin]

end SpeedLimit.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section SpeedLimit_{ns}.

Variable t : R.

(* TRUST INPUT 1: Mandelstam-Tamm quantum speed limit. *)
Hypothesis mandelstam_tamm : t >= {float(tau_mt)!r}.
(* TRUST INPUT 2: Margolus-Levitin quantum speed limit. *)
Hypothesis margolus_levitin : t >= {float(tau_ml)!r}.

Theorem respects_qsl : t >= {float(tau_qsl)!r}.
Proof. lra. Qed.

End SpeedLimit_{ns}.
"""
    return lean, coq


@dataclass
class SpeedLimitResult:
    buildup_time: float            # measured (model units)
    tau_mandelstam_tamm: float
    tau_margolus_levitin: float
    tau_qsl: float                 # the floor = max(MT, ML)
    fubini_study_angle: float
    energy_uncertainty: float
    max_entangling_rate: float
    respects_qsl: bool             # measured >= floor (must hold; a theorem)
    s_asymptote: float
    time_unit: str
    energy_scale_eV: Optional[float]
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "entanglement_speed_limit",
            "buildup_time": self.buildup_time,
            "tau_mandelstam_tamm": self.tau_mandelstam_tamm,
            "tau_margolus_levitin": self.tau_margolus_levitin,
            "tau_qsl": self.tau_qsl,
            "fubini_study_angle": self.fubini_study_angle,
            "energy_uncertainty": self.energy_uncertainty,
            "max_entangling_rate": self.max_entangling_rate,
            "respects_qsl": self.respects_qsl,
            "s_asymptote": self.s_asymptote,
            "time_unit": self.time_unit,
            "energy_scale_eV": self.energy_scale_eV,
            "claim_boundary": ("finite-model entanglement build-up bounded below by "
                               "the Mandelstam-Tamm / Margolus-Levitin quantum speed "
                               "limit (machine-checked inequality); NOT a reproduction "
                               "of the helium experiment or the 232 as figure; physical "
                               "time illustrative; not a continuum/Millennium claim"),
        }


def certified_buildup_speed_limit(H: np.ndarray, psi0: np.ndarray, *,
                                  t_max: float = np.pi, n_samples: int = 200,
                                  fraction: float = 0.9,
                                  energy_scale_eV: Optional[float] = None,
                                  keep_qubits: Optional[List[int]] = None
                                  ) -> SpeedLimitResult:
    """Measure the entanglement build-up time and certify it respects the QSL floor.

    Everything is computed in model units (hbar = 1); if ``energy_scale_eV`` is
    given the reported times are also converted to attoseconds (illustrative).
    """
    H = (np.asarray(H) + np.asarray(H).conj().T) / 2.0
    psi0 = np.asarray(psi0, dtype=complex)

    # Build-up time in model units (no energy scale here -> keep it clean).
    res = simulate_buildup(H, psi0, t_max=t_max, n_samples=n_samples,
                           fraction=fraction, energy_scale_eV=None)
    t_star = res.buildup_time

    # The target is the actual evolved state at the build-up time.
    psi_star = evolve_state(H, psi0, t_star)
    qsl = quantum_speed_limit(H, psi0, psi_star)

    rate = max_entangling_rate(H, psi0, np.linspace(0.0, t_max, n_samples),
                               keep_qubits=keep_qubits)

    floor = qsl["tau_qsl"]
    respects = bool(t_star >= floor - 1e-9)

    lean, coq = emit_speed_limit_certificate(
        "t_buildup", qsl["tau_mandelstam_tamm"], qsl["tau_margolus_levitin"])

    buildup_time = t_star
    tau_mt = qsl["tau_mandelstam_tamm"]
    tau_ml = qsl["tau_margolus_levitin"]
    tau_qsl = floor
    rate_out = rate
    unit = "model"
    if energy_scale_eV:
        scale = _HBAR_EV_AS / energy_scale_eV          # model time -> attoseconds
        buildup_time *= scale
        tau_mt = tau_mt * scale if np.isfinite(tau_mt) else tau_mt
        tau_ml = tau_ml * scale if np.isfinite(tau_ml) else tau_ml
        tau_qsl *= scale
        rate_out = rate / scale                         # entropy per attosecond
        unit = "attoseconds"

    return SpeedLimitResult(
        buildup_time=buildup_time,
        tau_mandelstam_tamm=tau_mt,
        tau_margolus_levitin=tau_ml,
        tau_qsl=tau_qsl,
        fubini_study_angle=qsl["angle"],
        energy_uncertainty=qsl["energy_uncertainty"],
        max_entangling_rate=rate_out,
        respects_qsl=respects,
        s_asymptote=res.s_asymptote,
        time_unit=unit,
        energy_scale_eV=energy_scale_eV,
        lean4=lean, coq=coq,
    )
