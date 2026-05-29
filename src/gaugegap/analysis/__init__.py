"""
Advanced mathematical analysis infrastructure for theorem-relevant progress.

This package provides rigorous mathematical tools for:
- Finite-size scaling analysis and continuum extrapolation
- Hypothesis pruning with Bayesian model comparison
- Tensor network baselines for classical benchmarking
- Advanced error mitigation strategies

All modules maintain claim boundary compliance: finite-system results
are extrapolated to continuum limits but do not constitute proofs.
"""

from .finite_size_scaling import (
    FiniteSizeScaling,
    PowerLawExtrapolation,
    ExponentialExtrapolation,
    bootstrap_confidence_interval,
    jackknife_variance,
)

from .continuum_extrapolation import (
    ContinuumExtrapolation,
    richardson_extrapolation,
    symanzik_improvement,
    detect_convergence_order,
)

from .hypothesis_pruning import (
    HypothesisPruner,
    BayesianModelComparison,
    compute_evidence_ratio,
    information_criteria,
)

__all__ = [
    "FiniteSizeScaling",
    "PowerLawExtrapolation",
    "ExponentialExtrapolation",
    "bootstrap_confidence_interval",
    "jackknife_variance",
    "ContinuumExtrapolation",
    "richardson_extrapolation",
    "symanzik_improvement",
    "detect_convergence_order",
    "HypothesisPruner",
    "BayesianModelComparison",
    "compute_evidence_ratio",
    "information_criteria",
]

# Made with Bob
