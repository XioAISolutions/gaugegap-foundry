"""
Advanced error mitigation strategies for quantum computations.

This package provides state-of-the-art error mitigation techniques:
- Probabilistic Error Cancellation (PEC)
- Clifford Data Regression (CDR)
- Symmetry verification and post-selection
- Virtual distillation
- Adaptive mitigation strategy selection

These methods reduce noise in quantum results without requiring
full quantum error correction.
"""

from .advanced_mitigation import (
    ProbabilisticErrorCancellation,
    CliffordDataRegression,
    SymmetryVerification,
    VirtualDistillation,
    AdaptiveMitigation,
    MitigationResult,
)

__all__ = [
    "ProbabilisticErrorCancellation",
    "CliffordDataRegression",
    "SymmetryVerification",
    "VirtualDistillation",
    "AdaptiveMitigation",
    "MitigationResult",
]

# Made with Bob
