"""Certifiable cores of power-law (Pareto) distributions, reduced to exact closed forms.

A continuous power-law (Pareto) tail with shape ``alpha > 0`` and lower cutoff
``xmin > 0`` is defined by the tail (complementary CDF)

    P(X > x) = (x / xmin) ** (-alpha)      for x >= xmin,

equivalently the density ``f(x) proportional to x ** (-(alpha + 1))``.  Power laws are
the canonical "scale-free" distributions, and several of their headline properties are
*exactly computable* closed forms rather than empirical fits:

  1. **Scale invariance / self-similarity (exact).**  The tail ratio
     ``P(X > c x) / P(X > x) = c ** (-alpha)`` is independent of ``x``.  Rescaling the
     observation window by a factor ``c`` multiplies the tail by a constant that depends
     only on ``c`` and ``alpha`` -- the signature of scale-freeness.
  2. **Moment divergence (exact threshold).**  The ``m``-th moment ``E[X^m]`` of the tail
     diverges iff ``m >= alpha``.  So the mean diverges iff ``alpha <= 1`` and the
     variance diverges iff ``alpha <= 2`` -- exact statements, not heuristics.
  3. **Finite moments are exact Pareto formulas.**  For ``alpha > 1`` the mean is
     ``alpha * xmin / (alpha - 1)``; for ``alpha > 2`` the variance is
     ``xmin^2 * alpha / ((alpha - 1)^2 (alpha - 2))``.

So the power law is precisely the gap between a scale-free, exactly self-similar tail and
the regime (small ``alpha``) where ordinary summary statistics simply do not exist.  The
boundary lines of the cosmic mass-radius diagram are themselves power laws (slope +/-1 in
log-log), which connects this vignette to the physical-limits picture by analogy only.

CLAIM BOUNDARY: this is the exact mathematics of the idealized power-law (Pareto)
distribution, verified here by exact closed forms (not Monte-Carlo, not Coq-discharged).
It is NOT a claim that any particular empirical dataset is power-law distributed -- that
requires goodness-of-fit testing (e.g. Clauset-Shalizi-Newman) which is deliberately out
of scope here.  This is NOT a physical bound and is deliberately NOT a member of the
physical-limits web.  Dependency-light (numpy only).

References: Newman (2005), "Power laws, Pareto distributions and Zipf's law"; Clauset,
Shalizi & Newman (2009), "Power-law distributions in empirical data".
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def tail_probability(x: float, alpha: float, xmin: float = 1.0) -> float:
    """Complementary CDF P(X > x) = (x / xmin) ** (-alpha) for x >= xmin > 0.

    For ``x < xmin`` the tail is 1 by convention (the variable is supported on
    ``[xmin, inf)``).  This is the exact certifiable core of the power-law tail.
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    if xmin <= 0:
        raise ValueError("xmin must be positive")
    if x < xmin:
        return 1.0
    return float((x / xmin) ** (-alpha))


def scale_invariance_ratio(c: float, alpha: float) -> float:
    """Self-similarity ratio of the tail: P(X > c x) / P(X > x) = c ** (-alpha).

    This is the *tail* (complementary-CDF) ratio, which is independent of ``x`` -- the
    exact statement of scale-freeness.  Note it differs from the *density* ratio
    ``f(c x) / f(x) = c ** (-(alpha + 1))``; this function returns the clean tail
    identity ``c ** (-alpha)``.
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    if c <= 0:
        raise ValueError("c must be positive")
    return float(c ** (-alpha))


def density_ratio(c: float, alpha: float) -> float:
    """Density self-similarity ratio f(c x) / f(x) = c ** (-(alpha + 1)).

    Provided alongside :func:`scale_invariance_ratio` to make explicit which ratio is
    which: the density carries the extra ``-1`` in the exponent relative to the tail.
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    if c <= 0:
        raise ValueError("c must be positive")
    return float(c ** (-(alpha + 1.0)))


def moment_diverges(alpha: float, m: float) -> bool:
    """Whether the m-th moment E[X^m] of the tail diverges: True iff m >= alpha.

    Exact threshold: the mean (m=1) diverges iff alpha <= 1, the variance involves the
    second moment (m=2) which diverges iff alpha <= 2.
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    return bool(m >= alpha)


def mean(alpha: float, xmin: float = 1.0) -> float:
    """Exact mean of the Pareto tail: alpha * xmin / (alpha - 1) for alpha > 1.

    For ``alpha <= 1`` the mean diverges and ``float('inf')`` is returned.
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    if xmin <= 0:
        raise ValueError("xmin must be positive")
    if alpha <= 1.0:
        return float("inf")
    return float(alpha * xmin / (alpha - 1.0))


def variance(alpha: float, xmin: float = 1.0) -> float:
    """Exact variance of the Pareto tail: xmin^2 * alpha / ((alpha-1)^2 (alpha-2)).

    Valid for ``alpha > 2``; for ``alpha <= 2`` the variance diverges and
    ``float('inf')`` is returned.
    """
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    if xmin <= 0:
        raise ValueError("xmin must be positive")
    if alpha <= 2.0:
        return float("inf")
    return float(xmin ** 2 * alpha / ((alpha - 1.0) ** 2 * (alpha - 2.0)))


@dataclass
class PowerLawResult:
    alpha: float
    xmin: float
    mean: float                 # may be inf (alpha <= 1)
    variance: float             # may be inf (alpha <= 2)
    mean_diverges: bool         # alpha <= 1
    variance_diverges: bool     # alpha <= 2
    scale_invariance_check: dict  # c -> {ratio, c_pow_minus_alpha} demonstrating equality

    def to_dict(self) -> dict:
        return {
            "kind": "power_law_pareto",
            "alpha": self.alpha,
            "xmin": self.xmin,
            "mean": self.mean,
            "variance": self.variance,
            "mean_diverges": self.mean_diverges,
            "variance_diverges": self.variance_diverges,
            "scale_invariance_check": self.scale_invariance_check,
            "claim_boundary": ("exact mathematics of the idealized power-law (Pareto) "
                               "distribution: scale-free tail ratio c^-alpha, moments "
                               "diverging iff m >= alpha; NOT a claim that any empirical "
                               "dataset is power-law (that needs goodness-of-fit "
                               "testing), NOT a physical bound, NOT a member of the "
                               "physical-limits web"),
        }


def analyze_power_law(alpha: float, xmin: float = 1.0,
                      scale_factors=(2.0, 10.0)) -> PowerLawResult:
    """Run the exactly-computable views of a power-law tail with shape ``alpha``."""
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    if xmin <= 0:
        raise ValueError("xmin must be positive")
    check = {}
    for c in scale_factors:
        # P(X > c x) / P(X > x) at a reference x = xmin (the ratio is x-independent),
        # confirmed equal to the closed form c ** (-alpha).
        x = xmin
        empirical = tail_probability(c * x, alpha, xmin) / tail_probability(x, alpha, xmin)
        closed = scale_invariance_ratio(c, alpha)
        check[float(c)] = {
            "tail_ratio": float(empirical),
            "c_pow_minus_alpha": float(closed),
            "match": bool(np.isclose(empirical, closed)),
        }
    return PowerLawResult(
        alpha=float(alpha),
        xmin=float(xmin),
        mean=mean(alpha, xmin),
        variance=variance(alpha, xmin),
        mean_diverges=bool(alpha <= 1.0),
        variance_diverges=bool(alpha <= 2.0),
        scale_invariance_check=check,
    )
