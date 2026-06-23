"""Regression to the mean, reduced to its exact linear-Gaussian closed form.

Take a standard bivariate normal ``(X, Y)`` with zero means, unit variances, and
correlation ``rho`` (so both coordinates are measured in standard-deviation units).  The
conditional expectation of the follow-up given an observed first value is the exact linear
formula

    E[Y | X = x] = rho * x        (x in SD units).

"Regression to the mean" is the statement that, whenever ``|rho| < 1``, the expected
follow-up is *closer to the mean* than the original observation: selecting an extreme
``x`` and then re-measuring yields, on average, a less extreme value.  This is purely a
consequence of imperfect correlation, and each piece is an exact closed form:

  1. **Conditional expectation (exact).**  ``E[Y | X = x] = rho * x``.
  2. **Regression fraction (exact).**  A fraction ``1 - rho`` of the deviation is expected
     to regress toward the mean (for ``0 < rho < 1``).
  3. **Contraction of extremes (exact inequality).**  ``|E[Y | X = x]| = |rho| * |x| <=
     |x|`` whenever ``|rho| <= 1``, with strict contraction when ``|rho| < 1`` and
     ``x != 0``.

So regression to the mean is precisely the gap between an observed extreme and its
expected follow-up under imperfect correlation -- an exact property of the linear-Gaussian
model, not a tendency that "pulls" data over time.

CLAIM BOUNDARY: this is exact for the linear-Gaussian / standard bivariate-normal model,
verified here by exact closed forms (not Monte-Carlo, not Coq-discharged).  "Regression to
the mean" is a consequence of imperfect correlation between two measurements -- it is NOT
a causal force, NOT a real-world trend, and NOT a claim about any particular dataset.
This is NOT a physical bound and is deliberately NOT a member of the physical-limits web.
Dependency-light (numpy only).

References: Galton (1886), "Regression towards mediocrity in hereditary stature";
Stigler (1997) on the statistical meaning of regression.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def conditional_expectation(x_sd: float, rho: float) -> float:
    """E[Y | X = x] = rho * x in standard-deviation units (exact linear-Gaussian form)."""
    if abs(rho) > 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    return float(rho * x_sd)


def regression_fraction(rho: float) -> float:
    """Fraction 1 - rho of the deviation expected to regress toward the mean.

    For ``0 < rho < 1`` this lies strictly in ``(0, 1)``; ``rho = 1`` gives 0 (no
    regression) and ``rho = 0`` gives 1 (full regression to the mean).
    """
    if abs(rho) > 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    return float(1.0 - rho)


def expected_followup(x_sd: float, rho: float) -> float:
    """Expected follow-up measurement given first value ``x_sd`` (alias of E[Y|X=x])."""
    return conditional_expectation(x_sd, rho)


def regresses_toward_mean(x_sd: float, rho: float) -> bool:
    """Whether the expected follow-up is strictly closer to the mean than ``x_sd``.

    True when ``|E[Y | X = x]| < |x|``, i.e. ``|rho| < 1`` and ``x != 0``.  This encodes
    the exact contraction-of-extremes inequality ``|rho * x| <= |x|`` for ``|rho| <= 1``.
    """
    if abs(rho) > 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    return bool(abs(conditional_expectation(x_sd, rho)) < abs(x_sd))


@dataclass
class RegressionToMeanResult:
    x_sd: float
    rho: float
    conditional_expectation: float    # rho * x_sd
    regression_fraction: float        # 1 - rho
    regresses_toward_mean: bool       # |cond_exp| < |x_sd| (0 < rho < 1, x != 0)

    def to_dict(self) -> dict:
        return {
            "kind": "regression_to_mean",
            "x_sd": self.x_sd,
            "rho": self.rho,
            "conditional_expectation": self.conditional_expectation,
            "regression_fraction": self.regression_fraction,
            "regresses_toward_mean": self.regresses_toward_mean,
            "claim_boundary": ("exact linear-Gaussian / bivariate-normal result: "
                               "E[Y|X=x] = rho * x, a fraction 1 - rho of the deviation "
                               "regresses toward the mean; this is a consequence of "
                               "imperfect correlation, NOT a causal force or real-world "
                               "trend, NOT a physical bound, NOT a member of the "
                               "physical-limits web"),
        }


def analyze_regression_to_mean(x_sd: float, rho: float) -> RegressionToMeanResult:
    """Run the exactly-computable views of regression to the mean at ``(x_sd, rho)``."""
    if abs(rho) > 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    cond = conditional_expectation(x_sd, rho)
    # exact contraction inequality, confirmed with the closed form
    contracts = bool(abs(cond) < abs(x_sd)) and bool(np.isclose(cond, rho * x_sd))
    return RegressionToMeanResult(
        x_sd=float(x_sd),
        rho=float(rho),
        conditional_expectation=float(cond),
        regression_fraction=regression_fraction(rho),
        regresses_toward_mean=contracts,
    )
