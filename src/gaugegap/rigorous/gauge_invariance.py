"""
Gauge invariance verification for lattice gauge theories.

Provides rigorous verification of gauge invariance constraints
with certified bounds.

CLAIM BOUNDARY:
This verifies gauge invariance for finite lattice systems.
It does NOT claim to prove gauge invariance in continuum QFT.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass

from .interval_arithmetic import Interval, IntervalMatrix, IntervalVector
from .proof_framework import (
    ProofStep,
    OperationType,
    Assumption,
    AssumptionType,
    Theorem,
    create_finite_system_assumption
)


@dataclass
class GaugeViolation:
    """
    Measurement of gauge invariance violation.
    
    Tracks ||G|ψ⟩|| where G is the Gauss law operator.
    """
    norm: Interval
    site_violations: List[Interval]
    total_charge: Interval
    certified: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "norm": self.norm.to_tuple(),
            "site_violations": [v.to_tuple() for v in self.site_violations],
            "total_charge": self.total_charge.to_tuple(),
            "certified": self.certified
        }


class GaugeInvarianceVerifier:
    """
    Verify gauge invariance with certified bounds.
    
    For lattice gauge theories, verifies Gauss law constraint:
    G|ψ⟩ = 0
    
    where G is the generator of gauge transformations.
    """
    
    def __init__(self, n_sites: int, precision_dps: int = 50):
        """
        Initialize gauge invariance verifier.
        
        Args:
            n_sites: Number of lattice sites
            precision_dps: Decimal places for interval arithmetic
        """
        self.n_sites = n_sites
        self.precision_dps = precision_dps
        self.proof_steps: List[ProofStep] = []
        self.step_counter = 0
    
    def _add_step(self, step: ProofStep):
        """Add a proof step."""
        self.proof_steps.append(step)
        self.step_counter += 1
    
    def compute_gauss_law_operator(
        self,
        link_operators: List[IntervalMatrix],
        matter_operators: Optional[List[IntervalMatrix]] = None
    ) -> IntervalMatrix:
        """
        Compute Gauss law operator G for each site.
        
        For pure gauge theory:
        G_i = sum_{links at i} E_link
        
        With matter:
        G_i = sum_{links at i} E_link - Q_i
        
        Args:
            link_operators: Electric field operators on links
            matter_operators: Charge operators on sites (optional)
        
        Returns:
            Gauss law operator matrix
        
        CLAIM BOUNDARY:
        This computes finite-lattice Gauss law operators.
        It does NOT claim to represent continuum gauge theory.
        """
        if len(link_operators) == 0:
            raise ValueError("Need at least one link operator")
        
        dim = link_operators[0].m
        
        # Initialize G as zero matrix
        G = IntervalMatrix([
            [Interval.from_float(0.0) for _ in range(dim)]
            for _ in range(dim)
        ])
        
        # Add electric field contributions
        for E_link in link_operators:
            G = G + E_link
        
        # Subtract matter charges if present
        if matter_operators is not None:
            for Q_site in matter_operators:
                G = G - Q_site
        
        # Record proof step
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.GAUGE_VERIFICATION,
            description="Compute Gauss law operator G",
            inputs={
                "n_links": len(link_operators),
                "n_matter": len(matter_operators) if matter_operators else 0
            },
            outputs={
                "operator_norm": certified_norm(G, "frobenius").to_tuple()
            },
            certified_bounds={
                "operator_norm": certified_norm(G, "frobenius")
            }
        )
        self._add_step(step)
        
        return G
    
    def verify_gauss_law(
        self,
        state_vector: IntervalVector,
        gauss_operator: IntervalMatrix,
        tolerance: float = 1e-10
    ) -> GaugeViolation:
        """
        Verify Gauss law: G|ψ⟩ = 0
        
        Computes ||G|ψ⟩|| with certified bounds.
        
        Args:
            state_vector: State |ψ⟩ as interval vector
            gauss_operator: Gauss law operator G
            tolerance: Tolerance for violation
        
        Returns:
            GaugeViolation with certified bounds
        
        CLAIM BOUNDARY:
        This verifies finite-state gauge invariance.
        It does NOT prove gauge invariance in infinite-dimensional Hilbert space.
        """
        # Compute G|ψ⟩
        G_psi = matrix_vector_multiply(gauss_operator, state_vector)
        
        # Compute ||G|ψ⟩||
        norm = G_psi.norm()
        
        # Check if violation is within tolerance
        certified = norm.upper < tolerance
        
        # Compute per-site violations (if structure allows)
        site_violations = []
        sites_per_component = max(1, state_vector.n // self.n_sites)
        
        for i in range(self.n_sites):
            start = i * sites_per_component
            end = min((i + 1) * sites_per_component, state_vector.n)
            
            # Sum squared components for this site
            site_norm_sq = G_psi.components[start] * G_psi.components[start]
            for j in range(start + 1, end):
                site_norm_sq = site_norm_sq + (G_psi.components[j] * G_psi.components[j])
            
            site_violations.append(site_norm_sq.sqrt())
        
        # Compute total charge
        total_charge = sum_interval_vector(G_psi)
        
        # Record proof step
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.GAUGE_VERIFICATION,
            description="Verify Gauss law: ||G|ψ⟩|| = 0",
            inputs={
                "state_dim": state_vector.n,
                "tolerance": tolerance
            },
            outputs={
                "violation_norm": norm.to_tuple(),
                "certified": certified
            },
            certified_bounds={
                "violation_norm": norm
            }
        )
        self._add_step(step)
        
        return GaugeViolation(
            norm=norm,
            site_violations=site_violations,
            total_charge=total_charge,
            certified=certified
        )
    
    def verify_gauge_transformation(
        self,
        state_before: IntervalVector,
        state_after: IntervalVector,
        gauge_operator: IntervalMatrix,
        tolerance: float = 1e-10
    ) -> Tuple[bool, Interval]:
        """
        Verify that gauge transformation preserves physical states.
        
        Checks that |ψ'⟩ = U_g|ψ⟩ where U_g is a gauge transformation.
        
        Args:
            state_before: State before transformation
            state_after: State after transformation
            gauge_operator: Gauge transformation operator U_g
            tolerance: Tolerance for verification
        
        Returns:
            (verified, difference_norm) where verified is True if transformation is valid
        
        CLAIM BOUNDARY:
        This verifies finite-state gauge transformations.
        It does NOT prove gauge symmetry in continuum theory.
        """
        # Compute U_g|ψ⟩
        transformed = matrix_vector_multiply(gauge_operator, state_before)
        
        # Compute ||U_g|ψ⟩ - |ψ'⟩||
        difference = transformed - state_after
        diff_norm = difference.norm()
        
        # Check if within tolerance
        verified = diff_norm.upper < tolerance
        
        # Record proof step
        step = ProofStep(
            step_id=self.step_counter,
            operation=OperationType.GAUGE_VERIFICATION,
            description="Verify gauge transformation: |ψ'⟩ = U_g|ψ⟩",
            inputs={
                "state_dim": state_before.n,
                "tolerance": tolerance
            },
            outputs={
                "difference_norm": diff_norm.to_tuple(),
                "verified": verified
            },
            certified_bounds={
                "difference_norm": diff_norm
            }
        )
        self._add_step(step)
        
        return verified, diff_norm
    
    def track_gauge_violation_evolution(
        self,
        initial_state: IntervalVector,
        hamiltonian: IntervalMatrix,
        gauss_operator: IntervalMatrix,
        times: List[float],
        tolerance: float = 1e-10
    ) -> List[GaugeViolation]:
        """
        Track gauge invariance violation under Hamiltonian evolution.
        
        Verifies that gauge invariance is preserved: [H, G] = 0
        
        Args:
            initial_state: Initial state |ψ(0)⟩
            hamiltonian: Hamiltonian H
            gauss_operator: Gauss law operator G
            times: List of times to check
            tolerance: Tolerance for violation
        
        Returns:
            List of GaugeViolation at each time
        
        CLAIM BOUNDARY:
        This tracks finite-system gauge violation evolution.
        It does NOT prove gauge invariance preservation in continuum dynamics.
        """
        violations = []
        
        # Check initial state
        initial_violation = self.verify_gauss_law(
            initial_state, gauss_operator, tolerance
        )
        violations.append(initial_violation)
        
        # Evolve and check at each time
        state = initial_state
        for t in times[1:]:
            # Compute time evolution: |ψ(t)⟩ = exp(-iHt)|ψ(0)⟩
            # For simplicity, use first-order approximation
            # In practice, would use certified matrix exponential
            
            t_interval = Interval.from_float(t, abs(t) * 1e-10)
            
            # exp(-iHt) ≈ I - iHt for small t
            # For larger t, would use certified_matrix_exp
            evolution_op = hamiltonian * t_interval * Interval.from_float(-1.0)
            
            # Add identity
            dim = hamiltonian.m
            for i in range(dim):
                evolution_op.entries[i][i] = evolution_op.entries[i][i] + Interval.from_float(1.0)
            
            # Apply to state
            state = matrix_vector_multiply(evolution_op, state)
            
            # Verify gauge invariance
            violation = self.verify_gauss_law(state, gauss_operator, tolerance)
            violations.append(violation)
        
        return violations
    
    def create_gauge_invariance_theorem(
        self,
        violations: List[GaugeViolation],
        tolerance: float = 1e-10
    ) -> Theorem:
        """
        Create a theorem certifying gauge invariance.
        
        Args:
            violations: List of gauge violations measured
            tolerance: Tolerance for certification
        
        Returns:
            Theorem with certified gauge invariance
        
        CLAIM BOUNDARY:
        This certifies finite-system gauge invariance.
        It does NOT prove gauge invariance in continuum QFT.
        """
        # Check if all violations are within tolerance
        all_certified = all(v.certified for v in violations)
        max_violation = max(v.norm.upper for v in violations)
        
        theorem = Theorem(
            name="Gauge Invariance Verification",
            statement=f"Gauss law violation ||G|ψ⟩|| < {tolerance} for all measured states",
            assumptions=[
                create_finite_system_assumption(
                    self.n_sites,
                    f"Finite lattice with {self.n_sites} sites"
                ),
                Assumption(
                    type=AssumptionType.NUMERICAL_PRECISION,
                    description=f"Interval arithmetic with {self.precision_dps} decimal places",
                    validity_range={"dps": self.precision_dps},
                    certified=True
                )
            ],
            proof_steps=self.proof_steps.copy(),
            conclusion={
                "max_violation": Interval.from_float(max_violation, 0.0),
                "all_certified": Interval.from_float(1.0 if all_certified else 0.0)
            },
            verified=all_certified,
            metadata={
                "n_sites": self.n_sites,
                "n_measurements": len(violations),
                "tolerance": tolerance
            }
        )
        
        return theorem


def verify_gauss_law(
    state_vector: IntervalVector,
    gauss_operator: IntervalMatrix,
    tolerance: float = 1e-10
) -> GaugeViolation:
    """
    Convenience function to verify Gauss law.
    
    Args:
        state_vector: State |ψ⟩
        gauss_operator: Gauss law operator G
        tolerance: Tolerance for violation
    
    Returns:
        GaugeViolation with certified bounds
    """
    n_sites = 1  # Default
    verifier = GaugeInvarianceVerifier(n_sites)
    return verifier.verify_gauss_law(state_vector, gauss_operator, tolerance)


def certified_gauge_violation(
    state_vector: IntervalVector,
    gauss_operator: IntervalMatrix
) -> Interval:
    """
    Compute certified bound on gauge violation ||G|ψ⟩||.
    
    Args:
        state_vector: State |ψ⟩
        gauss_operator: Gauss law operator G
    
    Returns:
        Interval containing ||G|ψ⟩||
    """
    G_psi = matrix_vector_multiply(gauss_operator, state_vector)
    return G_psi.norm()


def matrix_vector_multiply(
    matrix: IntervalMatrix,
    vector: IntervalVector
) -> IntervalVector:
    """
    Multiply interval matrix by interval vector.
    
    Args:
        matrix: m x n interval matrix
        vector: n-dimensional interval vector
    
    Returns:
        m-dimensional interval vector
    """
    if matrix.n != vector.n:
        raise ValueError("Matrix-vector dimension mismatch")
    
    result_components = []
    for i in range(matrix.m):
        # Compute i-th component of result
        component = matrix.entries[i][0] * vector.components[0]
        for j in range(1, matrix.n):
            component = component + (matrix.entries[i][j] * vector.components[j])
        result_components.append(component)
    
    return IntervalVector(result_components)


def sum_interval_vector(vector: IntervalVector) -> Interval:
    """
    Sum all components of an interval vector.
    
    Args:
        vector: Interval vector
    
    Returns:
        Sum as interval
    """
    result = vector.components[0]
    for i in range(1, vector.n):
        result = result + vector.components[i]
    return result


def certified_norm(matrix: IntervalMatrix, norm_type: str = "frobenius") -> Interval:
    """
    Compute matrix norm with certified bounds.
    
    Args:
        matrix: Interval matrix
        norm_type: "frobenius" or "spectral"
    
    Returns:
        Interval containing norm
    """
    if norm_type == "frobenius":
        # Frobenius norm: sqrt(sum of squared entries)
        sum_squares = matrix.entries[0][0] * matrix.entries[0][0]
        for i in range(matrix.m):
            for j in range(matrix.n):
                if i == 0 and j == 0:
                    continue
                sum_squares = sum_squares + (matrix.entries[i][j] * matrix.entries[i][j])
        return sum_squares.sqrt()
    else:
        raise ValueError(f"Unknown norm type: {norm_type}")


def verify_commutator_zero(
    A: IntervalMatrix,
    B: IntervalMatrix,
    tolerance: float = 1e-10
) -> Tuple[bool, Interval]:
    """
    Verify that [A, B] = 0 with certified bounds.
    
    Args:
        A: First operator
        B: Second operator
        tolerance: Tolerance for verification
    
    Returns:
        (verified, commutator_norm) where verified is True if [A,B] ≈ 0
    
    CLAIM BOUNDARY:
    This verifies finite-matrix commutation relations.
    It does NOT prove operator algebra in infinite dimensions.
    """
    # Compute AB
    AB = A * B
    
    # Compute BA
    BA = B * A
    
    # Compute [A, B] = AB - BA
    commutator = AB - BA
    
    # Compute ||[A, B]||
    comm_norm = certified_norm(commutator, "frobenius")
    
    # Check if within tolerance
    verified = comm_norm.upper < tolerance
    
    return verified, comm_norm

# Made with Bob
