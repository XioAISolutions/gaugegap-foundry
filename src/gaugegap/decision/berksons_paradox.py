"""Berkson's paradox, reduced to its exactly-computable core.

Selection on a *collider* induces a spurious negative correlation between two traits
that are independent in the population.  Model: binary traits A, B are independent
with P(A=1)=p and P(B=1)=q.  We *select* (admit) a sample whenever A=1 OR B=1, i.e.
we keep everything except the (0,0) cell.  The Pearson correlation of (A, B) *within
the selected set* is <= 0, and strictly < 0 whenever 0 < p, q < 1 -- even though the
population correlation is exactly 0.

The closed form.  Let ``Z = 1 - (1-p)(1-q) = P(A=1 or B=1)`` be the survival mass.
Conditioning on selection deletes the (0,0) cell and renormalizes the other three:

    P(1,1) = pq / Z,   P(1,0) = p(1-q) / Z,   P(0,1) = (1-p)q / Z,   P(0,0) = 0.

Within the selected set (A is binary so E[A^2] = E[A]):

    E[A]  = (pq + p(1-q)) / Z = p / Z,        E[B]  = q / Z,
    E[AB] = pq / Z,
    Cov   = E[AB] - E[A]E[B] = pq/Z - pq/Z^2 = (pq/Z) * (1 - 1/Z) = (pq/Z)*((Z-1)/Z),
    Var[A]= p/Z - p^2/Z^2,    Var[B] = q/Z - q^2/Z^2,
    corr  = Cov / sqrt(Var[A] Var[B]).

Since Z < 1 for 0 < p,q < 1, the factor (Z-1) is negative, so Cov < 0 and corr < 0:
admitting on "either trait present" makes the traits look like substitutes.  For the
symmetric case p = q = 1/2 the closed form evaluates to corr = -1/2 exactly (Cov =
-1/9, Var = 2/9 each), NOT a causal relationship -- it is an artifact of conditioning
on the collider (the admission rule).

(Note: a widely-quoted "-1/3" figure for this configuration is an arithmetic slip; the
exact Pearson correlation of the OR-selected sample at p = q = 1/2 is -1/2, confirmed
both by the closed form below and by the in-module numerical self-check.)

CLAIM BOUNDARY: exact probability of a selection / collider effect, verified by an
exact closed form (not Monte-Carlo, not Coq-discharged).  The induced negative
correlation is an artifact of conditioning on a collider (the selection), NOT a causal
relationship between the traits.  This is NOT a physical bound and is deliberately NOT
a member of the physical-limits web.  Dependency-light (numpy only).

Reference: J. Berkson, "Limitations of the application of fourfold table analysis to
hospital data", Biometrics Bulletin 2 (1946) 47.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def selected_correlation(p: float, q: float) -> float:
    """Exact Pearson correlation of (A, B) conditioned on (A=1 or B=1).

    A, B independent with P(A=1)=p, P(B=1)=q.  Returns the negative correlation
    induced by collider selection.  Requires 0 < p, q < 1 (otherwise a marginal is
    degenerate within the selected set and the correlation is undefined / 0).
    """
    if not (0.0 < p < 1.0) or not (0.0 < q < 1.0):
        raise ValueError("require 0 < p < 1 and 0 < q < 1")
    Z = 1.0 - (1.0 - p) * (1.0 - q)            # P(A=1 or B=1)
    EA = p / Z
    EB = q / Z
    EAB = (p * q) / Z
    cov = EAB - EA * EB
    var_a = EA - EA * EA                        # binary: E[A^2] = E[A]
    var_b = EB - EB * EB
    return float(cov / np.sqrt(var_a * var_b))


def population_correlation() -> float:
    """Population correlation of two independent traits: exactly 0 (for contrast)."""
    return 0.0


@dataclass
class BerksonsResult:
    p: float
    q: float
    population_correlation: float       # 0.0
    selected_correlation: float         # negative
    induced_negative: bool

    def to_dict(self) -> dict:
        return {
            "kind": "berksons_paradox",
            "p": self.p,
            "q": self.q,
            "population_correlation": self.population_correlation,
            "selected_correlation": self.selected_correlation,
            "induced_negative": self.induced_negative,
            "claim_boundary": ("exact probability of a selection / collider effect; the "
                               "negative correlation is an artifact of conditioning on a "
                               "collider (the selection), NOT a causal relationship; NOT "
                               "a physical bound, NOT a member of the physical-limits "
                               "web"),
        }


def analyze_berksons(p: float = 0.5, q: float = 0.5) -> BerksonsResult:
    """Run the exact collider-selection comparison for given marginals."""
    sel = selected_correlation(p, q)
    return BerksonsResult(
        p=float(p),
        q=float(q),
        population_correlation=population_correlation(),
        selected_correlation=sel,
        induced_negative=bool(sel < 0.0),
    )


# Numerical self-check: at p = q = 1/2 the selected correlation is exactly -1/2,
# and the population correlation is exactly 0.
assert np.isclose(selected_correlation(0.5, 0.5), -0.5)
assert population_correlation() == 0.0
assert selected_correlation(0.3, 0.7) < 0.0
