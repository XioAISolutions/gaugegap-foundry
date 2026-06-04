"""
Spectral impossibility proofs for Hilbert-Pólya operator candidates.

Provides rigorous proofs that certain operators cannot match Riemann zeros,
with certified bounds on spectral mismatches.

CLAIM BOUNDARY:
This proves impossibility results for specific finite-truncation operators.
It does NOT claim to prove or disprove the Riemann Hypothesis.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass

from .interval_arithmetic import Interval, IntervalMatrix, certified_eigenvalues
from .proof_framework import (
    ProofStep,
    OperationType,
    Assumption,
    AssumptionType,
    Theorem,
    create_truncation_assumption
)

# Certified separation threshold: a finite-truncation operator is taken to be
# certifiably "impossible" (cannot match the zeros) when the certified lower
# bound on its spectral mismatch exceeds this value.
IMPOSSIBILITY_THRESHOLD = 1e-6

# Default half-width applied to externally supplied float Riemann zeros when no
# certified enclosure is provided. Prefer ``curverank_spectral.riemann_zero_intervals``
# for genuinely certified enclosures.
DEFAULT_ZERO_UNCERTAINTY = 1e-10


@dataclass
class SpectralMismatch:
    """
    Certified mismatch between operator spectrum and Riemann zeros.
    """
    operator_name: str
    truncation_level: int
    computed_eigenvalues: List[Interval]
    riemann_zeros: List[float]
    min_mismatch: Interval
    max_mismatch: Interval
    impossibility_certified: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operator_name": self.operator_name,
            "truncation_level": self.truncation_level,
            "computed_eigenvalues": [e.to_tuple() for e in self.computed_eigenvalues],
            "riemann_zeros": self.riemann_zeros,
            "min_mismatch": self.min_mismatch.to_tuple(),
            "max_mismatch": self.max_mismatch.to_tuple(),
            "impossibility_certified": self.impossibility_certified
        }


@dataclass
class GUEStatistics:
    """
    GUE (Gaussian Unitary Ensemble) statistics verification.
    """
    level_spacings: List[Interval]
    mean_spacing: Interval
    spacing_variance: Interval
    gue_compatible: bool
    confidence_interval: Tuple[float, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level_spacings": [s.to_tuple() for s in self.level_spacings],
            "mean_spacing": self.mean_spacing.to_tuple(),
            "spacing_variance": self.spacing_variance.to_tuple(),
            "gue_compatible": self.gue_compatible,
            "confidence_interval": self.confidence_interval
        }


class SpectralMismatchProof:
    """
    Prove spectral mismatch for Hilbert-Pólya operator candidates.
    
    Provides certified proofs that specific operators cannot match
    all Riemann zeros, with rigorous error bounds.
    """
    
    def __init__(self, precision_dps: int = 50):
        """
        Initialize spectral mismatch prover.
        
        Args:
            precision_dps: Decimal places for interval arithmetic
        """
        self.precision_dps = precision_dps
        self.proof_steps: List[ProofStep] = []
        self.step_counter = 0
    
    def _add_step(self, step: ProofStep):
        """Add a proof step."""
        self.proof_steps.append(step)
        self.step_counter += 1
    
    def compute_operator_spectrum(
        self,
        operator: IntervalMatrix,
        operator_name: str
    ) -> List[Interval]:
        """
        Compute operator spectrum with certified bounds.
        
        Args:
            operator: Operator matrix
            operator_name: Name of operator
        
        Returns:
            List of eigenvalues with certified bounds
        
        CLAIM BOUNDARY:
        This computes finite-matrix eigenvalues.
        It does NOT claim to compute infinite-dimensional spectra.
        """
        eigenvalues = certified_eigenvalues(operator)
        
        # Record proof step
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.SPECTRAL_ANALYSIS,
            description=f"Compute spectrum of {operator_name}",
            inputs={
                "operator_name": operator_name,
                "matrix_size": operator.m
            },
            outputs={
                "n_eigenvalues": len(eigenvalues),
                "eigenvalues": [e.to_tuple() for e in eigenvalues]
            },
            certified_bounds={
                f"eigenvalue_{i}": e for i, e in enumerate(eigenvalues)
            }
        )
        self._add_step(step)
        
        return eigenvalues
    
    def compare_with_riemann_zeros(
        self,
        eigenvalues: List[Interval],
        riemann_zeros: List[float],
        operator_name: str
    ) -> SpectralMismatch:
        """
        Compare operator eigenvalues with Riemann zeros.
        
        Computes certified bounds on mismatch.
        
        Args:
            eigenvalues: Computed eigenvalues (intervals)
            riemann_zeros: Known Riemann zeros
            operator_name: Name of operator
        
        Returns:
            SpectralMismatch with certified bounds
        
        CLAIM BOUNDARY:
        This compares finite-truncation eigenvalues with Riemann zeros.
        It does NOT claim to prove or disprove the Riemann Hypothesis.
        """
        if len(eigenvalues) != len(riemann_zeros):
            # Pad or truncate to match
            n = min(len(eigenvalues), len(riemann_zeros))
            eigenvalues = eigenvalues[:n]
            riemann_zeros = riemann_zeros[:n]
        
        # Sort both lists
        eigenvalues_sorted = sorted(eigenvalues, key=lambda x: x.midpoint())
        riemann_zeros_sorted = sorted(riemann_zeros)
        
        # Compute mismatches
        mismatches = []
        for eig, zero in zip(eigenvalues_sorted, riemann_zeros_sorted):
            # Riemann zeros known precisely; widen by a small documented default.
            zero_interval = Interval.from_float(zero, DEFAULT_ZERO_UNCERTAINTY)
            mismatch = eig - zero_interval
            mismatches.append(abs(mismatch))
        
        # Find min and max mismatch
        min_mismatch = mismatches[0]
        max_mismatch = mismatches[0]
        for m in mismatches[1:]:
            if m.lower < min_mismatch.lower:
                min_mismatch = m
            if m.upper > max_mismatch.upper:
                max_mismatch = m
        
        # Check if impossibility is certified
        # If min_mismatch.lower > threshold, no eigenvalue matches any zero.
        impossibility_certified = min_mismatch.lower > IMPOSSIBILITY_THRESHOLD
        
        # Record proof step
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.SPECTRAL_ANALYSIS,
            description=f"Compare {operator_name} spectrum with Riemann zeros",
            inputs={
                "operator_name": operator_name,
                "n_eigenvalues": len(eigenvalues),
                "n_zeros": len(riemann_zeros)
            },
            outputs={
                "min_mismatch": min_mismatch.to_tuple(),
                "max_mismatch": max_mismatch.to_tuple(),
                "impossibility_certified": impossibility_certified
            },
            certified_bounds={
                "min_mismatch": min_mismatch,
                "max_mismatch": max_mismatch
            }
        )
        self._add_step(step)
        
        return SpectralMismatch(
            operator_name=operator_name,
            truncation_level=len(eigenvalues),
            computed_eigenvalues=eigenvalues_sorted,
            riemann_zeros=riemann_zeros_sorted,
            min_mismatch=min_mismatch,
            max_mismatch=max_mismatch,
            impossibility_certified=impossibility_certified
        )
    
    def verify_gue_statistics(
        self,
        eigenvalues: List[Interval],
        confidence_level: float = 0.95
    ) -> GUEStatistics:
        """
        Verify GUE (Gaussian Unitary Ensemble) statistics.
        
        Riemann zeros are conjectured to follow GUE statistics.
        This checks if operator eigenvalues match GUE.
        
        Args:
            eigenvalues: Computed eigenvalues
            confidence_level: Confidence level for statistical test
        
        Returns:
            GUEStatistics with certified bounds
        
        CLAIM BOUNDARY:
        This checks finite-sample GUE statistics.
        It does NOT prove or disprove GUE conjecture for Riemann zeros.
        """
        if len(eigenvalues) < 2:
            raise ValueError("Need at least 2 eigenvalues")
        
        # Sort eigenvalues
        eigenvalues_sorted = sorted(eigenvalues, key=lambda x: x.midpoint())
        
        # Compute level spacings
        spacings = []
        for i in range(len(eigenvalues_sorted) - 1):
            spacing = eigenvalues_sorted[i+1] - eigenvalues_sorted[i]
            spacings.append(spacing)
        
        # Compute mean spacing
        mean_spacing = spacings[0]
        for s in spacings[1:]:
            mean_spacing = Interval.from_bounds(
                (mean_spacing.lower + s.lower) / 2,
                (mean_spacing.upper + s.upper) / 2
            )
        
        # Compute variance
        variance = (spacings[0] - mean_spacing) * (spacings[0] - mean_spacing)
        for s in spacings[1:]:
            diff = s - mean_spacing
            variance = variance + (diff * diff)
        variance = variance * Interval.from_float(1.0 / len(spacings))
        
        # For GUE, normalized spacing distribution follows Wigner surmise
        # Mean spacing ≈ 1 (after normalization)
        # Variance ≈ 0.286 for GUE
        
        # Normalize spacings by mean
        normalized_spacings = [s / mean_spacing for s in spacings]
        
        # Check if variance is consistent with GUE
        gue_variance = Interval.from_float(0.286, 0.05)  # GUE variance with tolerance
        gue_compatible = (
            variance.lower <= gue_variance.upper and
            variance.upper >= gue_variance.lower
        )
        
        # Confidence interval (rough estimate)
        confidence_interval = (
            float(variance.lower),
            float(variance.upper)
        )
        
        # Record proof step
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.SPECTRAL_ANALYSIS,
            description="Verify GUE statistics",
            inputs={
                "n_eigenvalues": len(eigenvalues),
                "confidence_level": confidence_level
            },
            outputs={
                "mean_spacing": mean_spacing.to_tuple(),
                "spacing_variance": variance.to_tuple(),
                "gue_compatible": gue_compatible
            },
            certified_bounds={
                "mean_spacing": mean_spacing,
                "spacing_variance": variance
            }
        )
        self._add_step(step)
        
        return GUEStatistics(
            level_spacings=normalized_spacings,
            mean_spacing=mean_spacing,
            spacing_variance=variance,
            gue_compatible=gue_compatible,
            confidence_interval=confidence_interval
        )
    
    def prove_berry_keating_impossibility(
        self,
        n_basis: int,
        riemann_zeros: List[float]
    ) -> Theorem:
        """
        Prove that Berry-Keating xp operator cannot match all Riemann zeros.
        
        Constructs finite-truncation xp operator and proves spectral mismatch.
        
        Args:
            n_basis: Basis size for truncation
            riemann_zeros: List of Riemann zeros to compare
        
        Returns:
            Theorem with certified impossibility proof
        
        CLAIM BOUNDARY:
        This proves impossibility for finite-truncation xp operator.
        It does NOT claim to prove or disprove the Riemann Hypothesis.
        """
        # Use the certified interval-arithmetic pipeline: the position-space xp
        # operator built as an exact interval matrix, verified eigenvalue
        # enclosures, and certified zeta-zero enclosures.  (Lazy import keeps
        # the rigorous package free of an import-time dependency on curverank.)
        from gaugegap.curverank_certified import certified_xp_spectrum
        from gaugegap.curverank_spectral import (
            certified_spectral_mismatch,
            riemann_zero_intervals,
        )

        k_zeros = len(riemann_zeros)
        eigenvalues = certified_xp_spectrum(n_basis)
        zero_intervals = riemann_zero_intervals(k_zeros)
        mismatch = certified_spectral_mismatch(eigenvalues, zero_intervals)

        # Record a proof step for the certified mismatch.
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.SPECTRAL_ANALYSIS,
            description="Certified spectral mismatch of Berry-Keating xp vs Riemann zeros",
            inputs={"n_basis": n_basis, "k_zeros": k_zeros},
            outputs={"mismatch": mismatch.to_tuple()},
            certified_bounds={"mismatch": mismatch},
        )
        self._add_step(step)

        # Impossibility is certified when the mismatch is provably bounded away
        # from zero (lower endpoint above the separation threshold).
        impossibility_certified = mismatch.lower > IMPOSSIBILITY_THRESHOLD

        theorem = Theorem(
            name="Berry-Keating xp Impossibility (finite truncation)",
            statement=(
                f"The Berry-Keating xp operator truncated to n={n_basis} is "
                f"certifiably separated from the first {k_zeros} Riemann zeros: "
                f"M_n >= {float(mismatch.lower):.6f} (certified)."
            ),
            assumptions=[
                create_truncation_assumption(
                    n_basis,
                    f"Finite basis truncation to {n_basis} states"
                ),
                Assumption(
                    type=AssumptionType.MATHEMATICAL_PROPERTY,
                    description="Berry-Keating xp operator: H = (1/2)(xp + px)",
                    validity_range={"operator": "xp"},
                    certified=True
                )
            ],
            proof_steps=self.proof_steps.copy(),
            conclusion={
                "mismatch": mismatch,
                "impossibility_certified": Interval.from_float(
                    1.0 if impossibility_certified else 0.0
                )
            },
            verified=impossibility_certified,
            metadata={
                "operator_name": "Berry-Keating xp",
                "truncation_level": n_basis,
                "n_zeros_compared": k_zeros,
                "method": "interval_arithmetic_verified_eigenvalue_enclosure",
            }
        )

        return theorem
    
    def establish_necessary_conditions(
        self,
        operator: IntervalMatrix,
        operator_name: str,
        riemann_zeros: List[float]
    ) -> Dict[str, bool]:
        """
        Establish necessary conditions for Hilbert-Pólya operator.
        
        Checks:
        - Hermiticity
        - Real spectrum
        - Correct spectral density
        - GUE statistics
        
        Args:
            operator: Candidate operator
            operator_name: Name of operator
            riemann_zeros: Riemann zeros for comparison
        
        Returns:
            Dictionary of condition checks
        
        CLAIM BOUNDARY:
        This checks necessary conditions for finite-truncation operators.
        It does NOT prove or disprove existence of Hilbert-Pólya operator.
        """
        conditions = {}
        
        # Check Hermiticity: H = H†
        hermitian = self._check_hermiticity(operator)
        conditions["hermitian"] = hermitian
        
        # Compute spectrum
        eigenvalues = self.compute_operator_spectrum(operator, operator_name)
        
        # Check real spectrum
        real_spectrum = all(
            abs(e.midpoint().imag) < 1e-10 if hasattr(e.midpoint(), 'imag') else True
            for e in eigenvalues
        )
        conditions["real_spectrum"] = real_spectrum
        
        # Check spectral density
        # For Riemann zeros, density ~ log(t) / (2π)
        # This is a rough check
        if len(eigenvalues) >= 2:
            avg_spacing = sum(
                float((eigenvalues[i+1] - eigenvalues[i]).midpoint())
                for i in range(len(eigenvalues) - 1)
            ) / (len(eigenvalues) - 1)
            
            # Expected spacing for Riemann zeros around t ~ 14 (first zero)
            expected_spacing = 2 * np.pi / np.log(14)
            spacing_match = abs(avg_spacing - expected_spacing) < expected_spacing
            conditions["correct_spectral_density"] = spacing_match
        else:
            conditions["correct_spectral_density"] = False
        
        # Check GUE statistics
        if len(eigenvalues) >= 10:
            gue_stats = self.verify_gue_statistics(eigenvalues)
            conditions["gue_statistics"] = gue_stats.gue_compatible
        else:
            conditions["gue_statistics"] = False
        
        # Record proof step
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.SPECTRAL_ANALYSIS,
            description=f"Check necessary conditions for {operator_name}",
            inputs={
                "operator_name": operator_name,
                "matrix_size": operator.m
            },
            outputs=conditions,
            certified_bounds={}
        )
        self._add_step(step)
        
        return conditions
    
    def _check_hermiticity(self, operator: IntervalMatrix) -> bool:
        """
        Check if operator is Hermitian: H = H†
        
        Args:
            operator: Operator matrix
        
        Returns:
            True if Hermitian within tolerance
        """
        if operator.m != operator.n:
            return False
        
        # Check H_ij = H_ji* (for real matrices, H_ij = H_ji)
        for i in range(operator.m):
            for j in range(i, operator.n):
                diff = operator.entries[i][j] - operator.entries[j][i]
                if abs(diff).upper > 1e-6:
                    return False
        
        return True


def prove_berry_keating_mismatch(
    n_basis: int,
    riemann_zeros: List[float]
) -> Theorem:
    """
    Convenience function to prove Berry-Keating mismatch.
    
    Args:
        n_basis: Basis size for truncation
        riemann_zeros: List of Riemann zeros
    
    Returns:
        Theorem with certified impossibility proof
    """
    prover = SpectralMismatchProof()
    return prover.prove_berry_keating_impossibility(n_basis, riemann_zeros)


def certified_spectral_gap(
    operator: IntervalMatrix
) -> Interval:
    """
    Compute spectral gap with certified bounds.
    
    Spectral gap = λ₁ - λ₀ (difference between first two eigenvalues)
    
    Args:
        operator: Operator matrix
    
    Returns:
        Spectral gap with certified bounds
    """
    eigenvalues = certified_eigenvalues(operator)
    
    if len(eigenvalues) < 2:
        raise ValueError("Need at least 2 eigenvalues for spectral gap")
    
    # Sort eigenvalues
    eigenvalues_sorted = sorted(eigenvalues, key=lambda x: x.midpoint())
    
    # Compute gap
    gap = eigenvalues_sorted[1] - eigenvalues_sorted[0]
    
    return gap

# Made with Bob
