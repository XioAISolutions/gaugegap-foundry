"""Repeated-seed runs and confidence intervals for stochastic estimates.

Work-order A6 asks for repeated-seed runs with confidence intervals, built on the
existing reproducible-seeding (`seeding.child_seeds`) and error-budget
(`error_budget.ErrorBudget`) infrastructure.

CLAIM BOUNDARY: a confidence interval here quantifies the *statistical* spread of
a stochastic estimator at a FIXED finite system (lattice size, truncation,
precision). It says nothing about the continuum / thermodynamic limit and implies
no continuum mass gap. Systematic errors (finite-size, truncation, discretization)
are separate budget components, not part of this CI.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Sequence

from gaugegap.seeding import child_seeds

# Two-sided normal-approximation z for common confidence levels.
_Z = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}


@dataclass(frozen=True)
class RepeatedRunStats:
    n_runs: int
    mean: float
    std: float            # sample standard deviation (ddof=1)
    sem: float            # standard error of the mean
    ci_level: float
    ci_low: float
    ci_high: float
    samples: List[float]

    @property
    def ci_halfwidth(self) -> float:
        return (self.ci_high - self.ci_low) / 2.0

    def to_dict(self) -> dict:
        return {
            "n_runs": self.n_runs,
            "mean": self.mean,
            "std": self.std,
            "sem": self.sem,
            "ci_level": self.ci_level,
            "ci": [self.ci_low, self.ci_high],
            "ci_halfwidth": self.ci_halfwidth,
            "samples": self.samples,
            "interpretation": (
                "statistical spread of the estimator at a fixed finite system; "
                "no continuum/thermodynamic-limit implication"
            ),
        }


def confidence_interval(samples: Sequence[float], level: float = 0.95) -> RepeatedRunStats:
    """Normal-approximation confidence interval for the mean of ``samples``."""
    xs = [float(x) for x in samples]
    n = len(xs)
    if n < 2:
        raise ValueError("need at least two samples for a confidence interval")
    if level not in _Z:
        raise ValueError(f"level must be one of {sorted(_Z)}")
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    std = math.sqrt(var)
    sem = std / math.sqrt(n)
    half = _Z[level] * sem
    return RepeatedRunStats(
        n_runs=n, mean=mean, std=std, sem=sem, ci_level=level,
        ci_low=mean - half, ci_high=mean + half, samples=xs,
    )


def repeated_run(
    fn: Callable[[int], float],
    *,
    parent_seed: int = 1234,
    n_runs: int = 20,
    level: float = 0.95,
) -> RepeatedRunStats:
    """Run ``fn(seed)`` over ``n_runs`` independent child seeds and summarise.

    ``fn`` takes a seed and returns a scalar estimate. Child seeds are derived
    reproducibly from ``parent_seed`` via ``seeding.child_seeds`` (statistically
    independent SeedSequence streams).
    """
    seeds = child_seeds(parent_seed, n_runs)
    samples = [float(fn(s)) for s in seeds]
    return confidence_interval(samples, level=level)
