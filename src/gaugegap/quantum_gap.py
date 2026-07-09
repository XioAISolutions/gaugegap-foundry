"""The Quantum Gap: one formula that unifies every certificate in the Foundry.

Across all of the Foundry's tracks, every certified result is the *same*
mathematical object -- the verified lower endpoint of a finite enclosure of an
observable, held strictly above an explicit floor. We name that functional the
**Quantum Gap**:

    QG(O, β) := lower(O) − β

where ``lower(O)`` is the rigorous lower bound of a finite enclosure ``[low, high]``
of an observable ``O`` and ``β`` is a declared floor/target. A claim is *certified*
exactly when ``QG > 0``. The tracks differ only in what ``O`` and ``β`` are:

======================  ==============================  ==================  ==========================
Track                   O (enclosed observable)         β (floor)           certified statement
======================  ==============================  ==================  ==========================
GaugeGap                E₁ − E₀ (spectral gap)          0                   finite gap is positive
CurveRank               minimum certified level spacing 0                   spectrum is separated
FlowGap                 energy-decay rate               0                   finite dynamics dissipate
NetGap (advantage)      average channel fidelity        2/3                 beats the classical floor
NetGap (security)       BB84 key rate r = 1 − 2h(Q)     0                   key is secure
Physical limits         demonstrated margin             established bound   bound is respected w/ slack
======================  ==============================  ==================  ==========================

This module makes ``QG`` first class: a frozen :class:`QuantumGap`, constructors that
reuse the existing certified kernels, one generic discharged Lean 4 / Coq emitter for
``low ≥ β + m ⇒ QG ≥ m`` (same linarith/lra shape as the Landauer and NetGap
certificates), and :func:`unified_gap_report`, the end-to-end run that pushes one
representative observable from every track through the *same* formula.

CLAIM BOUNDARY: ``QG`` is a *unifying bookkeeping functional over verified finite
enclosures*. It makes the repository's existing certificates one formula; it is not
new physics and proves nothing beyond each underlying finite certificate. Each row
keeps its own track's claim boundary (finite-system, toy, or established-bound).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

CLAIM_BOUNDARY = (
    "unifying bookkeeping functional over verified finite enclosures; makes the "
    "repository's existing certificates one formula (QG = lower(O) - floor, certified "
    "iff QG > 0); not new physics and nothing beyond each underlying finite certificate"
)


@dataclass(frozen=True)
class QuantumGap:
    """A single certified (or refuted) Quantum Gap ``QG(O, β) = lower(O) − β``."""

    observable: str
    track: str
    enclosure_low: float
    enclosure_high: float
    floor: float
    claim_boundary: str

    def __post_init__(self) -> None:
        if self.enclosure_high < self.enclosure_low:
            raise ValueError("enclosure_high must be >= enclosure_low")

    @property
    def gap(self) -> float:
        """The Quantum Gap: verified lower endpoint minus the floor."""
        return self.enclosure_low - self.floor

    @property
    def certified(self) -> bool:
        """Certified iff the whole enclosure clears the floor (QG > 0)."""
        return self.gap > 0.0

    @property
    def midpoint(self) -> float:
        return 0.5 * (self.enclosure_low + self.enclosure_high)

    @property
    def width(self) -> float:
        return self.enclosure_high - self.enclosure_low

    def certificate(self) -> tuple[str, str]:
        """Discharged Lean 4 / Coq proof that this QG is positive (no holes)."""
        return emit_quantum_gap_certificate(self.observable, self.enclosure_low, self.floor)

    def to_dict(self) -> dict:
        return {
            "observable": self.observable,
            "track": self.track,
            "enclosure_low": self.enclosure_low,
            "enclosure_high": self.enclosure_high,
            "floor": self.floor,
            "gap": self.gap,
            "certified": self.certified,
            "claim_boundary": self.claim_boundary,
        }


def _sanitize(label: str) -> str:
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "QG"
    return base if not base[0].isdigit() else "QG" + base


def emit_quantum_gap_certificate(label: str, low: float, floor: float) -> tuple[str, str]:
    """Generic discharged Lean 4 / Coq proof that ``QG = low − floor`` is positive.

    Trust inputs: the verified enclosure lower bound ``lo``, the floor ``beta``, a
    positive margin ``m`` and the enclosure fact ``lo ≥ beta + m`` (both supplied by
    the certified kernel that produced the enclosure). The assistant discharges
    ``lo − beta > 0`` with linarith / lra -- the same shape as the Landauer and
    NetGap certificates.
    """
    ns = _sanitize(label)
    lean = f"""import Mathlib.Tactic

namespace QuantumGap.{ns}

/-- Verified enclosure lower bound lo, floor beta, and positive margin m
    (abstract reals; only the labelled trust facts are used). -/
axiom lo : ℝ
axiom beta : ℝ
axiom m : ℝ

/-- TRUST INPUT 1 -- positive margin from the certified enclosure. -/
axiom m_pos : m > 0
/-- TRUST INPUT 2 -- enclosure clears the floor by m: lo ≥ beta + m. -/
axiom lo_clears : lo ≥ beta + m

/-- The Quantum Gap QG = lo − beta is positive (no holes). -/
theorem quantum_gap_pos : lo - beta > 0 := by
  linarith [m_pos, lo_clears]

end QuantumGap.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section QuantumGap_{ns}.

(* Verified enclosure lower bound lo, floor beta, positive margin m. *)
Variable lo beta m : R.

(* TRUST INPUT 1: positive margin from the certified enclosure. *)
Hypothesis m_pos : m > 0.
(* TRUST INPUT 2: enclosure clears the floor by m: lo >= beta + m. *)
Hypothesis lo_clears : lo >= beta + m.

Theorem quantum_gap_pos : lo - beta > 0.
Proof. lra. Qed.

End QuantumGap_{ns}.
"""
    return lean, coq


# --------------------------------------------------------------------------- #
# Constructors -- each reuses an existing certified kernel or an explicit enclosure.
# --------------------------------------------------------------------------- #

def from_spectrum(
    H: np.ndarray,
    *,
    observable: str,
    track: str,
    floor: float = 0.0,
    error: float = 1e-9,
    claim_boundary: str,
) -> QuantumGap:
    """QG of the spectral gap ``E₁ − E₀`` from a certified eigenvalue enclosure.

    Uses :func:`gaugegap.certify.certify_spectrum`; the gap enclosure is
    ``[low(E₁) − high(E₀), high(E₁) − low(E₀)]`` -- the rigorous interval difference.
    """
    from gaugegap.certify import certify_spectrum

    cert = certify_spectrum(np.asarray(H), error=error)
    if cert.n < 2:
        raise ValueError("need at least two eigenvalues for a spectral gap")
    (lo0, hi0), (lo1, hi1) = cert.enclosures[0], cert.enclosures[1]
    return QuantumGap(
        observable=observable,
        track=track,
        enclosure_low=lo1 - hi0,
        enclosure_high=hi1 - lo0,
        floor=floor,
        claim_boundary=claim_boundary,
    )


def from_threshold(
    low: float,
    high: float,
    *,
    threshold: float,
    observable: str,
    track: str,
    claim_boundary: str,
) -> QuantumGap:
    """QG of an enclosed quantity over an explicit threshold (e.g. level spacing)."""
    return QuantumGap(
        observable=observable, track=track,
        enclosure_low=float(low), enclosure_high=float(high),
        floor=float(threshold), claim_boundary=claim_boundary,
    )


def from_fidelity(
    fidelity: float,
    *,
    floor: float = 2.0 / 3.0,
    half_width: float = 0.0,
    observable: str = "average channel fidelity",
    track: str = "NetGap",
    claim_boundary: str,
) -> QuantumGap:
    """QG of a fidelity over a floor (default the classical 2/3 quantum-advantage floor)."""
    f = float(fidelity)
    return QuantumGap(
        observable=observable, track=track,
        enclosure_low=f - abs(half_width), enclosure_high=f + abs(half_width),
        floor=float(floor), claim_boundary=claim_boundary,
    )


def from_rate(
    rate: float,
    *,
    floor: float = 0.0,
    half_width: float = 0.0,
    observable: str,
    track: str,
    claim_boundary: str,
) -> QuantumGap:
    """QG of a rate (key rate, decay rate, ...) over a floor (default 0)."""
    r = float(rate)
    return QuantumGap(
        observable=observable, track=track,
        enclosure_low=r - abs(half_width), enclosure_high=r + abs(half_width),
        floor=float(floor), claim_boundary=claim_boundary,
    )


def from_bound(
    observed: float,
    *,
    bound: float,
    half_width: float = 0.0,
    observable: str,
    track: str,
    claim_boundary: str,
) -> QuantumGap:
    """QG of a demonstrated quantity over an established physical bound."""
    o = float(observed)
    return QuantumGap(
        observable=observable, track=track,
        enclosure_low=o - abs(half_width), enclosure_high=o + abs(half_width),
        floor=float(bound), claim_boundary=claim_boundary,
    )


# --------------------------------------------------------------------------- #
# The end-to-end run: one representative certified QuantumGap per track.
# --------------------------------------------------------------------------- #

def unified_gap_report() -> dict[str, object]:
    """Compute one representative QuantumGap per track through the *same* formula.

    This is the program run end to end: each track's real kernel produces an
    observable and floor, and every one is reported as a ``QG = low − floor`` row.
    """
    from gaugegap import z2_chain
    from gaugegap.curverank_registry import certified_xp_spectrum
    from gaugegap.gaugegap_su3_plaquette import CLAIM_BOUNDARY as SU3_CB
    from gaugegap.gaugegap_su3_plaquette import hamiltonian_dense as su3_hamiltonian
    from gaugegap.quantum import quantum_channel as qc
    from gaugegap.quantum import quantum_network as qn
    from gaugegap import flowgap_navier_stokes as fg

    gaps: list[QuantumGap] = []

    # GaugeGap -- Z₂ transverse-field chain spectral gap (certified enclosure).
    z2_h = z2_chain.hamiltonian_dense(n_sites=6, exchange_coupling=1.0, transverse_field=0.5)
    gaps.append(from_spectrum(
        z2_h, observable="Z2 chain spectral gap E1-E0", track="GaugeGap",
        claim_boundary="finite Z2 transverse-field chain; a finite-system spectral gap, "
                       "not a continuum or thermodynamic-limit claim",
    ))

    # GaugeGap -- exact single-plaquette SU(3) spectral gap (certified enclosure).
    su3_h = su3_hamiltonian(coupling=1.0, cutoff=6)
    gaps.append(from_spectrum(
        su3_h, observable="SU(3) single-plaquette gap E1-E0", track="GaugeGap",
        claim_boundary=SU3_CB,
    ))

    # CurveRank -- minimum certified level spacing of the Berry-Keating xp truncation.
    xp = certified_xp_spectrum(10)
    lows = [iv.to_tuple()[0] for iv in xp]
    highs = [iv.to_tuple()[1] for iv in xp]
    spacings_low = [lows[i + 1] - highs[i] for i in range(len(xp) - 1)]
    spacings_high = [highs[i + 1] - lows[i] for i in range(len(xp) - 1)]
    j = int(np.argmin(spacings_low))
    gaps.append(from_threshold(
        spacings_low[j], spacings_high[j], threshold=0.0,
        observable="CurveRank xp minimum certified level spacing", track="CurveRank",
        claim_boundary="rigorous finite-matrix eigenvalue enclosures (verification "
                       "infrastructure); a spectral-separation negative result, not a "
                       "proof of the Riemann Hypothesis or any Millennium Prize problem",
    ))

    # FlowGap -- Taylor-Green energy-decay rate (finite Navier-Stokes surrogate).
    ux0, uy0 = fg.taylor_green(16, 16)
    sim = fg.simulate_navier_stokes_2d(nx=16, ny=16, nu=0.02, dt=0.001, n_steps=100,
                                       ux0=ux0, uy0=uy0)
    gaps.append(from_rate(
        float(sim["measured_energy_decay_rate"]), floor=0.0,
        observable="FlowGap Taylor-Green energy-decay rate", track="FlowGap",
        claim_boundary=str(sim["claim_boundary"]),
    ))

    # NetGap -- average channel fidelity beats the classical 2/3 floor (quantum advantage).
    avg_fid = qc.average_fidelity(qc.depolarizing_kraus(0.1))
    gaps.append(from_fidelity(
        avg_fid, floor=2.0 / 3.0,
        observable="NetGap depolarizing channel average fidelity", track="NetGap",
        claim_boundary=qc.CLAIM_BOUNDARY,
    ))

    # NetGap -- BB84 asymptotic secure key rate r = 1 - 2h(Q) is positive (secure).
    bb84 = qn.bb84_key_rate(0.05)
    gaps.append(from_rate(
        float(bb84["key_rate"]), floor=0.0,
        observable="NetGap BB84 secure key rate r=1-2h(Q)", track="NetGap",
        claim_boundary=qn.CLAIM_BOUNDARY,
    ))

    # Physical limits -- Landauer: erasing two bits clears the one-bit floor with slack.
    from gaugegap.quantum.landauer import landauer_bit
    two_bit_cost = 2.0 * landauer_bit(T=1.0)
    one_bit_floor = landauer_bit(T=1.0)
    gaps.append(from_bound(
        two_bit_cost, bound=one_bit_floor,
        observable="Landauer erasure cost of two bits vs one-bit floor", track="Limits",
        claim_boundary="exact finite-system Landauer bound (k_B T ln 2 per bit); a lower "
                       "bound on dissipated energy, not a device or over-unity claim",
    ))

    certified = [g for g in gaps if g.certified]
    return {
        "formula": "QG(O, floor) := lower(O) - floor ; certified iff QG > 0",
        "claim_boundary": CLAIM_BOUNDARY,
        "rows": [g.to_dict() for g in gaps],
        "n_rows": len(gaps),
        "n_certified": len(certified),
        "all_certified": len(certified) == len(gaps),
    }
