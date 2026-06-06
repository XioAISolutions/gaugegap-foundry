"""Certified Eightfold-Way / Gell-Mann-Okubo finite benchmark.

The Eightfold Way classifies hadrons into SU(3)-flavor multiplets (the baryon
octet and decuplet) and turns the symmetry *breaking* into the Gell-Mann-Okubo
(GMO) mass relations.  Its mathematical content is an effective mass operator on
a multiplet,

    M = a * 1  +  b * Y  +  c * ( I(I+1) - Y^2 / 4 ),

i.e. an SU(3)-flavor singlet term plus a term transforming like the hypercharge
(``T_8``) component of an octet.  This module realises that operator as a
*certified interval matrix* and runs it through the rigorous residual-enclosure
eigensolver (``gaugegap.rigorous``), so the resulting multiplet structure and
mass relations are machine-checked finite-system bounds rather than
floating-point estimates.

Three certified pieces:

  (A) ``certified_octet_spectrum`` / ``certified_levels`` -- certified eigenvalue
      enclosures of the octet mass operator; certified count of *distinct* mass
      levels (disjoint enclosures) shows the symmetry breaking lifting the
      degeneracy.
  (B) ``certified_gmo_residual_model`` -- the GMO combination
      ``2(M_N + M_Xi) - 3 M_Lambda - M_Sigma`` evaluated in interval arithmetic
      on the operator's own levels; it is certified to enclose 0 (the relation is
      exact for an octet-transforming breaking term).
  (C) ``gmo_residual_from_masses`` and ``certified_omega_prediction`` -- certified
      enclosures from measured masses-with-uncertainties: the (small, nonzero)
      empirical GMO residual and the famous decuplet equal-spacing prediction of
      the Omega^- mass.

CLAIM BOUNDARY:
This is a finite-dimensional *effective* SU(3)-flavor mass-operator model -- the
Gell-Mann-Okubo phenomenology -- made rigorous with interval arithmetic.  It is
NOT a dynamical lattice-QCD computation: it does not derive hadron masses from a
gauge+matter path integral, and it makes no continuum or first-principles claim.
The certified statements are about the finite model operator and about linear
relations among input masses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    IntervalMatrix,
    verified_hermitian_eigenvalues,
)


@dataclass(frozen=True)
class FlavorState:
    """A flavor basis state with its SU(3) quantum numbers."""

    name: str
    multiplet: str  # isospin-multiplet label, e.g. "N", "Sigma", "Lambda", "Xi"
    iso: float      # total isospin I
    iso3: float     # third component I3
    hyper: float    # hypercharge Y = B + S


# Baryon octet (J^P = 1/2+), ordered by (Y desc, I3 desc).
OCTET: Tuple[FlavorState, ...] = (
    FlavorState("p", "N", 0.5, 0.5, 1.0),
    FlavorState("n", "N", 0.5, -0.5, 1.0),
    FlavorState("Sigma+", "Sigma", 1.0, 1.0, 0.0),
    FlavorState("Sigma0", "Sigma", 1.0, 0.0, 0.0),
    FlavorState("Sigma-", "Sigma", 1.0, -1.0, 0.0),
    FlavorState("Lambda", "Lambda", 0.0, 0.0, 0.0),
    FlavorState("Xi0", "Xi", 0.5, 0.5, -1.0),
    FlavorState("Xi-", "Xi", 0.5, -0.5, -1.0),
)

# Index of the Sigma0 and Lambda states (the only I3 = 0, Y = 0 pair; they mix
# under isospin breaking, giving a genuine off-diagonal 2x2 block).
_SIGMA0_IDX = 3
_LAMBDA_IDX = 5


@dataclass
class OctetModel:
    """Coefficients of the octet mass operator (in arbitrary mass units).

    M = a*1 + b*Y + c*(I(I+1) - Y^2/4) + iso_break*I3 + lam_sigma_mix*(Lambda<->Sigma0)
    """

    a: float = 1150.0          # SU(3) singlet mass
    b: float = -190.0          # hypercharge (octet) term
    c: float = 40.0            # isospin-Casimir (octet) term
    iso_break: float = 0.0     # I3 (electromagnetic/up-down) breaking
    lam_sigma_mix: float = 0.0  # Lambda-Sigma0 mixing strength

    def _diag(self, s: FlavorState) -> float:
        return (
            self.a
            + self.b * s.hyper
            + self.c * (s.iso * (s.iso + 1.0) - s.hyper * s.hyper / 4.0)
            + self.iso_break * s.iso3
        )

    def interval_matrix(self) -> IntervalMatrix:
        """Build the mass operator as a real-symmetric interval matrix."""
        n = len(OCTET)
        entries = [
            [Interval.from_float(0.0) for _ in range(n)] for _ in range(n)
        ]
        for i, s in enumerate(OCTET):
            entries[i][i] = Interval.from_float(self._diag(s))
        if self.lam_sigma_mix != 0.0:
            mix = Interval.from_float(self.lam_sigma_mix)
            entries[_SIGMA0_IDX][_LAMBDA_IDX] = mix
            entries[_LAMBDA_IDX][_SIGMA0_IDX] = mix
        return IntervalMatrix(entries)

    def level_intervals(self) -> Dict[str, Interval]:
        """Certified mass interval for each isospin multiplet (no I3/mixing).

        These are exact (zero-width) intervals built from the operator
        coefficients; used for the GMO relation, which is defined on the
        isospin-averaged multiplet masses.
        """
        reps = {s.multiplet: s for s in OCTET}
        return {name: Interval.from_float(self._diag(s)) for name, s in reps.items()}


def certified_octet_spectrum(model: OctetModel) -> List[Interval]:
    """Certified eigenvalue enclosures of the octet mass operator."""
    return verified_hermitian_eigenvalues(model.interval_matrix())


def certified_distinct_levels(enclosures: List[Interval]) -> List[List[Interval]]:
    """Group enclosures into certified-distinct clusters.

    Two enclosures that are disjoint correspond to *certifiably distinct*
    eigenvalues.  Sweeping the midpoint-sorted enclosures, we start a new cluster
    whenever the next enclosure is disjoint from the running cluster's upper
    edge.  The number of clusters is a rigorous lower bound on the number of
    distinct mass levels; cluster sizes are the multiplicities consistent with
    the enclosures (overlap means "not certified distinct", not "proven equal").
    """
    ordered = sorted(enclosures, key=lambda iv: iv.midpoint())
    clusters: List[List[Interval]] = []
    for iv in ordered:
        if clusters and not (iv.lower > clusters[-1][-1].upper):
            clusters[-1].append(iv)
        else:
            clusters.append([iv])
    return clusters


def certified_gmo_residual(
    m_N: Interval, m_Sigma: Interval, m_Lambda: Interval, m_Xi: Interval
) -> Interval:
    """Certified enclosure of the GMO residual ``2(N+Xi) - 3*Lambda - Sigma``.

    For the octet mass operator this is exactly 0; for measured masses it is the
    (small) certified GMO discrepancy.
    """
    two = Interval.from_float(2.0)
    three = Interval.from_float(3.0)
    return two * (m_N + m_Xi) - three * m_Lambda - m_Sigma


def certified_gmo_residual_model(model: OctetModel) -> Interval:
    """GMO residual evaluated on the model operator's own multiplet levels."""
    lv = model.level_intervals()
    return certified_gmo_residual(lv["N"], lv["Sigma"], lv["Lambda"], lv["Xi"])


# ---------------------------------------------------------------------------
# Empirical (data-driven) certified checks.
# ---------------------------------------------------------------------------

def _iv(value: float, error: float) -> Interval:
    return Interval.from_float(value, error)


def gmo_residual_from_masses(
    m_N: Tuple[float, float],
    m_Sigma: Tuple[float, float],
    m_Lambda: Tuple[float, float],
    m_Xi: Tuple[float, float],
) -> Interval:
    """Certified GMO residual from isospin-averaged masses ``(value, error)``."""
    return certified_gmo_residual(_iv(*m_N), _iv(*m_Sigma), _iv(*m_Lambda), _iv(*m_Xi))


def certified_omega_prediction(
    m_Sigma_star: Tuple[float, float], m_Xi_star: Tuple[float, float]
) -> Interval:
    """Certified decuplet equal-spacing prediction of the Omega^- mass.

    Equal spacing in hypercharge gives ``M_Omega = 2*M_Xi* - M_Sigma*`` from the
    two heavier known decuplet members.
    """
    two = Interval.from_float(2.0)
    return two * _iv(*m_Xi_star) - _iv(*m_Sigma_star)


# Particle Data Group isospin-averaged masses (MeV), with representative
# uncertainties; used by the empirical certified checks and the runner script.
PDG_OCTET: Dict[str, Tuple[float, float]] = {
    "N": (938.919, 0.001),
    "Sigma": (1193.153, 0.05),
    "Lambda": (1115.683, 0.006),
    "Xi": (1318.285, 0.05),
}
PDG_DECUPLET: Dict[str, Tuple[float, float]] = {
    "Delta": (1232.0, 1.0),
    "Sigma_star": (1383.7, 1.0),
    "Xi_star": (1531.8, 0.4),
    "Omega": (1672.45, 0.29),
}
