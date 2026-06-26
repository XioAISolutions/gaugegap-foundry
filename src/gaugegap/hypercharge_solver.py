"""Solve anomaly-compatible hypercharges under explicit assumptions."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from gaugegap.anomaly_audit import Hypercharges, audit


@dataclass(frozen=True)
class HyperchargeSolution:
    status: str
    degrees_of_freedom: int
    assumptions: tuple[str, ...]
    assignment: Hypercharges
    family_parameter: str | None = None

    def summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "degrees_of_freedom": self.degrees_of_freedom,
            "family_parameter": self.family_parameter,
            "assumptions": list(self.assumptions),
            "assignment": self.assignment.summary(),
            "audit": audit(self.assignment).summary(),
        }


def solve(
    *,
    colors: int = 3,
    generations: int = 3,
    y_h: Fraction = Fraction(1, 2),
    include_right_neutrino: bool = False,
    family_y_q: Fraction | None = None,
) -> HyperchargeSolution:
    if colors < 1 or generations < 1:
        raise ValueError("colors and generations must be positive")
    y_h = Fraction(y_h)
    assumptions = (
        "Q = T3 + Y",
        "one Higgs doublet",
        "gauge-invariant up, down, and charged-lepton Yukawa terms",
        "generation-universal hypercharges",
    )
    if include_right_neutrino:
        y_q = y_h / colors if family_y_q is None else Fraction(family_y_q)
        y_l = -colors * y_q
        h = Hypercharges(
            colors=colors,
            generations=generations,
            y_q=y_q,
            y_u=y_q + y_h,
            y_d=y_q - y_h,
            y_l=y_l,
            y_e=y_l - y_h,
            y_nu=y_l + y_h,
            y_h=y_h,
        )
        return HyperchargeSolution(
            "underdetermined_family",
            1,
            assumptions + ("Dirac right-neutrino Yukawa term",),
            h,
            "Y_Q (equivalently a hypercharge/B-L admixture)",
        )

    y_l = -y_h
    y_q = y_h / colors
    h = Hypercharges(
        colors=colors,
        generations=generations,
        y_q=y_q,
        y_u=y_q + y_h,
        y_d=y_q - y_h,
        y_l=y_l,
        y_e=y_l - y_h,
        y_h=y_h,
    )
    return HyperchargeSolution(
        "unique_under_assumptions",
        0,
        assumptions + ("no right-handed neutrino",),
        h,
    )
