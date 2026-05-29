"""
Classical baseline methods for benchmarking quantum approaches.

This package provides high-performance classical algorithms for:
- Tensor network methods (DMRG, PEPS, TEBD)
- Exact diagonalization with optimizations
- Classical simulation of quantum circuits
- Entanglement analysis

These baselines establish performance targets that quantum methods
must exceed to demonstrate quantum advantage.
"""

from .tensor_networks import (
    DMRGSolver,
    PEPSSolver,
    TEBDSolver,
    TensorNetworkResult,
    compute_entanglement_entropy,
    truncation_error_bound,
)

__all__ = [
    "DMRGSolver",
    "PEPSSolver",
    "TEBDSolver",
    "TensorNetworkResult",
    "compute_entanglement_entropy",
    "truncation_error_bound",
]

# Made with Bob
