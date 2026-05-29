"""
Tests for rigorous computational mathematics modules.

Tests interval arithmetic, proof framework, certified extrapolation,
gauge invariance, energy bounds, spectral impossibility, and formal export.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile

# Import rigorous modules
from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    IntervalVector,
    IntervalMatrix,
    certified_eigenvalues,
    certified_matrix_exp,
)
from gaugegap.rigorous.proof_framework import (
    Theorem,
    ProofStep,
    Assumption,
    AssumptionType,
    OperationType,
    create_finite_system_assumption,
    verify_inequality,
)
from gaugegap.rigorous.certified_extrapolation import (
    CertifiedExtrapolation,
    certified_continuum_limit,
    verify_convergence,
)
from gaugegap.rigorous.gauge_invariance import (
    GaugeInvarianceVerifier,
    verify_gauss_law,
    certified_gauge_violation,
)
from gaugegap.rigorous.energy_bounds import (
    EnergyBoundsVerifier,
    certified_dissipation_rate,
)
from gaugegap.rigorous.spectral_impossibility import (
    SpectralMismatchProof,
    prove_berry_keating_mismatch,
    certified_spectral_gap,
)
from gaugegap.rigorous.formal_export import (
    export_to_lean4,
    export_to_coq,
    export_to_isabelle,
    verify_certificate,
)


class TestIntervalArithmetic:
    """Test interval arithmetic operations."""
    
    def test_interval_creation(self):
        """Test interval creation."""
        # From float
        i1 = Interval.from_float(1.0, 0.1)
        assert i1.lower <= 1.0 <= i1.upper
        assert i1.width() <= 0.2
        
        # From bounds
        i2 = Interval.from_bounds(0.9, 1.1)
        assert i2.lower == 0.9
        assert i2.upper == 1.1
    
    def test_interval_arithmetic(self):
        """Test interval arithmetic operations."""
        i1 = Interval.from_float(2.0, 0.1)
        i2 = Interval.from_float(3.0, 0.1)
        
        # Addition
        i_sum = i1 + i2
        assert i_sum.contains(5.0)
        
        # Subtraction
        i_diff = i2 - i1
        assert i_diff.contains(1.0)
        
        # Multiplication
        i_prod = i1 * i2
        assert i_prod.contains(6.0)
        
        # Division
        i_quot = i2 / i1
        assert i_quot.contains(1.5)
    
    def test_interval_functions(self):
        """Test interval mathematical functions."""
        i = Interval.from_float(1.0, 0.01)
        
        # Square root
        i_sqrt = i.sqrt()
        assert i_sqrt.contains(1.0)
        
        # Exponential
        i_exp = i.exp()
        assert i_exp.contains(np.e)
        
        # Logarithm
        i_log = i.log()
        assert i_log.contains(0.0)
    
    def test_interval_vector(self):
        """Test interval vector operations."""
        v1 = IntervalVector.from_floats([1.0, 2.0, 3.0])
        v2 = IntervalVector.from_floats([4.0, 5.0, 6.0])
        
        # Addition
        v_sum = v1 + v2
        assert v_sum[0].contains(5.0)
        
        # Dot product
        dot = v1.dot(v2)
        assert dot.contains(32.0)  # 1*4 + 2*5 + 3*6 = 32
        
        # Norm
        norm = v1.norm()
        assert norm.contains(np.sqrt(14))  # sqrt(1 + 4 + 9)
    
    def test_interval_matrix(self):
        """Test interval matrix operations."""
        # Create 2x2 matrix
        m1 = IntervalMatrix.from_floats([[1.0, 2.0], [3.0, 4.0]])
        m2 = IntervalMatrix.from_floats([[5.0, 6.0], [7.0, 8.0]])
        
        # Addition
        m_sum = m1 + m2
        assert m_sum[0, 0].contains(6.0)
        
        # Multiplication
        m_prod = m1 * m2
        assert m_prod[0, 0].contains(19.0)  # 1*5 + 2*7 = 19
        
        # Transpose
        m_t = m1.transpose()
        assert m_t[0, 1].contains(3.0)
    
    def test_certified_eigenvalues(self):
        """Test certified eigenvalue computation."""
        # Create symmetric matrix with known eigenvalues
        # [[2, 1], [1, 2]] has eigenvalues 1 and 3
        m = IntervalMatrix.from_floats([[2.0, 1.0], [1.0, 2.0]])
        
        eigenvalues = certified_eigenvalues(m)
        assert len(eigenvalues) == 2
        
        # Check eigenvalues are in correct range
        eig_values = sorted([e.midpoint() for e in eigenvalues])
        assert abs(float(eig_values[0]) - 1.0) < 0.1
        assert abs(float(eig_values[1]) - 3.0) < 0.1


class TestProofFramework:
    """Test proof framework."""
    
    def test_assumption_creation(self):
        """Test assumption creation."""
        assumption = create_finite_system_assumption(10, "Test system")
        assert assumption.type == AssumptionType.FINITE_SYSTEM
        assert assumption.certified
    
    def test_proof_step(self):
        """Test proof step creation."""
        step = ProofStep(
            step_id=1,
            operation=OperationType.EIGENVALUE_COMPUTATION,
            description="Test step",
            inputs={"x": 1.0},
            outputs={"y": 2.0},
            certified_bounds={"result": Interval.from_float(2.0, 0.1)}
        )
        
        assert step.verify_bounds()
        assert step.step_id == 1
    
    def test_theorem_creation(self):
        """Test theorem creation and verification."""
        theorem = Theorem(
            name="Test Theorem",
            statement="Test statement",
            assumptions=[
                create_finite_system_assumption(5, "Test")
            ]
        )
        
        # Add a proof step
        step = ProofStep(
            step_id=1,
            operation=OperationType.INEQUALITY_VERIFICATION,
            description="Test inequality",
            inputs={},
            outputs={},
            certified_bounds={"x": Interval.from_float(1.0, 0.1)}
        )
        theorem.add_step(step)
        
        # Set conclusion
        theorem.set_conclusion({"result": Interval.from_float(1.0, 0.1)})
        
        # Verify
        assert theorem.verify()
    
    def test_verify_inequality(self):
        """Test inequality verification."""
        left = Interval.from_float(1.0, 0.1)
        right = Interval.from_float(2.0, 0.1)
        
        # Should verify: 1 <= 2
        assert verify_inequality(left, right, "<=")
        
        # Should not verify: 2 <= 1
        assert not verify_inequality(right, left, "<=")


class TestCertifiedExtrapolation:
    """Test certified extrapolation."""
    
    def test_power_law_fit(self):
        """Test power law fitting."""
        # Create data with known power law: value(L) = 1 + 0.5 * L^(-1)
        system_sizes = [4, 8, 16, 32]
        values = [
            Interval.from_float(1.0 + 0.5 / L, 0.01)
            for L in system_sizes
        ]
        
        extrapolator = CertifiedExtrapolation()
        a, b, exponent = extrapolator.power_law_fit(system_sizes, values)
        
        # Check that a is close to 1 (continuum limit)
        assert abs(float(a.midpoint()) - 1.0) < 0.2
    
    def test_richardson_extrapolation(self):
        """Test Richardson extrapolation."""
        # Create data with geometric progression
        system_sizes = [4, 8, 16]
        values = [
            Interval.from_float(1.0 + 1.0 / L, 0.01)
            for L in system_sizes
        ]
        
        extrapolator = CertifiedExtrapolation()
        result = extrapolator.richardson_extrapolation(system_sizes, values, order=1)
        
        # Should extrapolate close to 1.0
        assert abs(float(result.midpoint()) - 1.0) < 0.5
    
    def test_continuum_limit(self):
        """Test continuum limit extrapolation."""
        system_sizes = [4, 8, 16, 32]
        values = [
            Interval.from_float(1.0 + 1.0 / L, 0.01)
            for L in system_sizes
        ]
        
        result = certified_continuum_limit(system_sizes, values, method="power_law")
        
        assert result.extrapolated_value.contains(1.0)
        assert len(result.proof_steps) > 0
    
    def test_verify_convergence(self):
        """Test convergence rate verification."""
        system_sizes = [4, 8, 16]
        values = [
            Interval.from_float(1.0 + 1.0 / L, 0.01)
            for L in system_sizes
        ]
        
        verified, rate = verify_convergence(system_sizes, values, expected_rate=-1.0)
        
        # Should verify convergence rate close to -1
        assert rate.contains(-1.0) or abs(float(rate.midpoint()) + 1.0) < 1.0


class TestGaugeInvariance:
    """Test gauge invariance verification."""
    
    def test_gauss_law_verification(self):
        """Test Gauss law verification."""
        # Create a gauge-invariant state (all zeros for G|ψ⟩)
        state = IntervalVector.from_floats([1.0, 0.0, 0.0, 0.0])
        
        # Create trivial Gauss operator (zero matrix)
        gauss_op = IntervalMatrix.from_floats([
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0]
        ])
        
        violation = verify_gauss_law(state, gauss_op, tolerance=1e-10)
        
        assert violation.certified
        assert violation.norm.upper < 1e-10
    
    def test_gauge_violation_computation(self):
        """Test gauge violation computation."""
        state = IntervalVector.from_floats([1.0, 0.0])
        gauss_op = IntervalMatrix.from_floats([[0.1, 0.0], [0.0, 0.1]])
        
        violation_norm = certified_gauge_violation(state, gauss_op)
        
        # Should be small but non-zero
        assert violation_norm.upper > 0


class TestEnergyBounds:
    """Test energy dissipation bounds."""
    
    def test_energy_computation(self):
        """Test kinetic energy computation."""
        velocity = IntervalVector.from_floats([1.0, 2.0, 3.0])
        
        verifier = EnergyBoundsVerifier(viscosity=0.1)
        energy = verifier.compute_energy(velocity)
        
        # E = (1/2) * (1 + 4 + 9) = 7
        assert energy.contains(7.0)
    
    def test_enstrophy_computation(self):
        """Test enstrophy computation."""
        vorticity = IntervalVector.from_floats([1.0, 1.0])
        
        verifier = EnergyBoundsVerifier(viscosity=0.1)
        enstrophy = verifier.compute_enstrophy(vorticity)
        
        # Z = (1/2) * (1 + 1) = 1
        assert enstrophy.contains(1.0)
    
    def test_dissipation_rate(self):
        """Test dissipation rate computation."""
        velocity = IntervalVector.from_floats([1.0, 2.0, 3.0])
        
        dissipation = certified_dissipation_rate(velocity, viscosity=0.1)
        
        # Should be positive
        assert dissipation.lower >= 0


class TestSpectralImpossibility:
    """Test spectral impossibility proofs."""
    
    def test_spectrum_computation(self):
        """Test operator spectrum computation."""
        # Create simple 2x2 matrix
        operator = IntervalMatrix.from_floats([[1.0, 0.0], [0.0, 2.0]])
        
        prover = SpectralMismatchProof()
        eigenvalues = prover.compute_operator_spectrum(operator, "Test")
        
        assert len(eigenvalues) == 2
    
    def test_riemann_zero_comparison(self):
        """Test comparison with Riemann zeros."""
        # Create operator with known spectrum
        operator = IntervalMatrix.from_floats([[14.0, 0.0], [0.0, 21.0]])
        
        prover = SpectralMismatchProof()
        eigenvalues = prover.compute_operator_spectrum(operator, "Test")
        
        # First two Riemann zeros (imaginary parts)
        riemann_zeros = [14.134725, 21.022040]
        
        mismatch = prover.compare_with_riemann_zeros(
            eigenvalues, riemann_zeros, "Test"
        )
        
        assert mismatch.min_mismatch.lower >= 0
    
    def test_certified_spectral_gap(self):
        """Test certified spectral gap computation."""
        operator = IntervalMatrix.from_floats([[1.0, 0.0], [0.0, 3.0]])
        
        gap = certified_spectral_gap(operator)
        
        # Gap should be close to 2.0
        assert gap.contains(2.0) or abs(float(gap.midpoint()) - 2.0) < 0.5


class TestFormalExport:
    """Test formal proof export."""
    
    def test_lean4_export(self):
        """Test export to Lean 4."""
        theorem = Theorem(
            name="Test Theorem",
            statement="Test statement",
            assumptions=[create_finite_system_assumption(5, "Test")],
            conclusion={"x": Interval.from_float(1.0, 0.1)}
        )
        theorem.verified = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test.lean"
            certificate = export_to_lean4(theorem, filepath)
            
            assert certificate.format == "lean4"
            assert "theorem" in certificate.certificate_text.lower()
            assert Path(filepath).exists()
    
    def test_coq_export(self):
        """Test export to Coq."""
        theorem = Theorem(
            name="Test Theorem",
            statement="Test statement",
            assumptions=[create_finite_system_assumption(5, "Test")],
            conclusion={"x": Interval.from_float(1.0, 0.1)}
        )
        theorem.verified = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test.v"
            certificate = export_to_coq(theorem, filepath)
            
            assert certificate.format == "coq"
            assert "Theorem" in certificate.certificate_text
            assert Path(filepath).exists()
    
    def test_isabelle_export(self):
        """Test export to Isabelle/HOL."""
        theorem = Theorem(
            name="Test Theorem",
            statement="Test statement",
            assumptions=[create_finite_system_assumption(5, "Test")],
            conclusion={"x": Interval.from_float(1.0, 0.1)}
        )
        theorem.verified = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test.thy"
            certificate = export_to_isabelle(theorem, filepath)
            
            assert certificate.format == "isabelle"
            assert "theorem" in certificate.certificate_text.lower()
            assert Path(filepath).exists()
    
    def test_certificate_verification(self):
        """Test certificate verification."""
        theorem = Theorem(
            name="Test",
            statement="Test",
            assumptions=[],
            conclusion={"x": Interval.from_float(1.0)}
        )
        
        certificate = export_to_lean4(theorem)
        assert verify_certificate(certificate)


class TestIntegration:
    """Integration tests combining multiple modules."""
    
    def test_complete_proof_workflow(self):
        """Test complete proof workflow from computation to export."""
        # 1. Create finite-size data
        system_sizes = [4, 8, 16]
        values = [
            Interval.from_float(1.0 + 1.0 / L, 0.01)
            for L in system_sizes
        ]
        
        # 2. Perform extrapolation
        result = certified_continuum_limit(system_sizes, values)
        
        # 3. Create theorem
        theorem = Theorem(
            name="Continuum Limit Test",
            statement=f"Continuum limit is {result.extrapolated_value}",
            assumptions=result.assumptions,
            proof_steps=result.proof_steps,
            conclusion={"continuum_limit": result.extrapolated_value}
        )
        theorem.verified = True
        
        # 4. Export to formal proof assistant
        with tempfile.TemporaryDirectory() as tmpdir:
            certificate = export_to_lean4(theorem, f"{tmpdir}/test.lean")
            assert verify_certificate(certificate)
    
    def test_gauge_invariance_proof(self):
        """Test gauge invariance proof workflow."""
        # Create gauge-invariant state
        state = IntervalVector.from_floats([1.0, 0.0, 0.0, 0.0])
        gauss_op = IntervalMatrix.from_floats([
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0]
        ])
        
        # Verify gauge invariance
        verifier = GaugeInvarianceVerifier(n_sites=2)
        violation = verifier.verify_gauss_law(state, gauss_op)
        
        # Create theorem
        theorem = verifier.create_gauge_invariance_theorem([violation])
        
        assert theorem.verified
        assert len(theorem.proof_steps) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
