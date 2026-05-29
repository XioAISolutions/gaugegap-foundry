"""
Rigorous computational mathematics infrastructure for computer-assisted proofs.

This module provides certified numerical computations with guaranteed bounds,
suitable for computer-assisted mathematical proofs.

All numerical operations use interval arithmetic to provide rigorous bounds.
Results can be exported to formal proof assistants (Lean 4, Coq, Isabelle/HOL).

Modules:
- interval_arithmetic: Wrapper around mpmath interval arithmetic
- proof_framework: Computer-assisted proof framework with theorem/proof step tracking
- certified_extrapolation: Finite-size scaling with certified bounds
- gauge_invariance: Gauge invariance verification for lattice gauge theories
- energy_bounds: Energy dissipation bounds for Navier-Stokes
- spectral_impossibility: Spectral mismatch proofs for Hilbert-Pólya candidates
- formal_export: Export proofs to Lean 4, Coq, Isabelle/HOL

CLAIM BOUNDARY:
This module provides computer-assisted proofs and certified numerical bounds.
It does NOT claim to solve or prove any Millennium Prize problems.
Results are finite-system benchmarks with rigorous error bounds.
"""

from .interval_arithmetic import (
    Interval,
    IntervalMatrix,
    IntervalVector,
    certified_eigenvalues,
    certified_matrix_exp,
)
from .proof_framework import (
    Theorem,
    ProofStep,
    ProofTree,
    Assumption,
)
from .certified_extrapolation import (
    CertifiedExtrapolation,
    certified_continuum_limit,
    certified_richardson_extrapolation,
)
from .gauge_invariance import (
    GaugeInvarianceVerifier,
    verify_gauss_law,
    certified_gauge_violation,
)
from .energy_bounds import (
    EnergyBoundsVerifier,
    certified_dissipation_rate,
    beale_kato_majda_bound,
)
from .spectral_impossibility import (
    SpectralMismatchProof,
    prove_berry_keating_mismatch,
    certified_spectral_gap,
)
from .formal_export import (
    export_to_lean4,
    export_to_coq,
    export_to_isabelle,
    ProofCertificate,
)

__all__ = [
    # Interval arithmetic
    "Interval",
    "IntervalMatrix",
    "IntervalVector",
    "certified_eigenvalues",
    "certified_matrix_exp",
    # Proof framework
    "Theorem",
    "ProofStep",
    "ProofTree",
    "Assumption",
    # Certified extrapolation
    "CertifiedExtrapolation",
    "certified_continuum_limit",
    "certified_richardson_extrapolation",
    # Gauge invariance
    "GaugeInvarianceVerifier",
    "verify_gauss_law",
    "certified_gauge_violation",
    # Energy bounds
    "EnergyBoundsVerifier",
    "certified_dissipation_rate",
    "beale_kato_majda_bound",
    # Spectral impossibility
    "SpectralMismatchProof",
    "prove_berry_keating_mismatch",
    "certified_spectral_gap",
    # Formal export
    "export_to_lean4",
    "export_to_coq",
    "export_to_isabelle",
    "ProofCertificate",
]

# Made with Bob
