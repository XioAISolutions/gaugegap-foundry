"""
Tests for continuum limit extrapolation module.

Tests cover:
- Richardson extrapolation with multiple orders
- Symanzik improvement for lattice theories
- Automatic convergence order detection
- Uncertainty propagation through extrapolation
"""

import pytest
import numpy as np
from src.gaugegap.analysis.continuum_extrapolation import (
    ContinuumExtrapolation,
    richardson_extrapolation,
    symanzik_improvement,
    detect_convergence_order,
)


class TestRichardsonExtrapolation:
    """Test Richardson extrapolation method."""
    
    def test_second_order_convergence(self):
        """Test Richardson extrapolation with O(a²) convergence."""
        # Generate data with O(a²) errors: O(a) = 1.0 + 0.5*a²
        spacings = np.array([0.1, 0.05, 0.025])
        true_continuum = 1.0
        values = true_continuum + 0.5 * spacings**2
        
        continuum, order = richardson_extrapolation(values, spacings, order=2)
        
        assert abs(continuum - true_continuum) < 0.01
        assert order == 2
    
    def test_first_order_convergence(self):
        """Test with O(a) convergence."""
        spacings = np.array([0.2, 0.1, 0.05])
        true_continuum = 2.0
        values = true_continuum + 1.0 * spacings
        
        continuum, order = richardson_extrapolation(values, spacings, order=1)
        
        assert abs(continuum - true_continuum) < 0.05
    
    def test_auto_order_detection(self):
        """Test automatic order detection."""
        spacings = np.array([0.1, 0.05, 0.025, 0.0125])
        true_continuum = 1.5
        values = true_continuum + 0.3 * spacings**2
        
        continuum, order = richardson_extrapolation(values, spacings, order=None)
        
        assert abs(continuum - true_continuum) < 0.1
        assert order in [1, 2, 3, 4]  # Should detect reasonable order
    
    def test_unsorted_spacings(self):
        """Test that unsorted spacings are handled correctly."""
        spacings = np.array([0.1, 0.025, 0.05])  # Unsorted
        true_continuum = 1.0
        values = true_continuum + 0.5 * spacings**2
        
        continuum, order = richardson_extrapolation(values, spacings, order=2)
        
        # Should sort internally and still work
        assert abs(continuum - true_continuum) < 0.1


class TestSymanzikImprovement:
    """Test Symanzik improved extrapolation."""
    
    def test_first_order_symanzik(self):
        """Test O(a²) Symanzik improvement."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        true_continuum = 3.0
        c2 = 2.0
        values = true_continuum + c2 * spacings**2
        
        result = symanzik_improvement(spacings, values, max_order=1)
        
        assert abs(result.continuum_value - true_continuum) < 0.05
        assert result.convergence_order == 2
        assert "c2" in result.coefficients
        assert abs(result.coefficients["c2"] - c2) < 0.5
    
    def test_second_order_symanzik(self):
        """Test O(a⁴) Symanzik improvement."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04, 0.02])
        true_continuum = 2.5
        c2, c4 = 1.5, 0.3
        values = true_continuum + c2 * spacings**2 + c4 * spacings**4
        
        result = symanzik_improvement(spacings, values, max_order=2)
        
        assert abs(result.continuum_value - true_continuum) < 0.1
        assert result.convergence_order == 4
        assert "c2" in result.coefficients
        assert "c4" in result.coefficients
    
    def test_with_errors(self):
        """Test Symanzik improvement with measurement errors."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        true_continuum = 1.5
        values = true_continuum + 1.0 * spacings**2
        errors = np.array([0.05, 0.04, 0.03, 0.02])
        
        result = symanzik_improvement(spacings, values, errors, max_order=1)
        
        assert result.continuum_error > 0
        assert result.systematic_error > 0
        assert result.chi_squared >= 0
    
    def test_result_export(self):
        """Test exporting result to dictionary."""
        spacings = np.array([0.1, 0.05, 0.025])
        values = np.array([1.2, 1.05, 1.0125])
        
        result = symanzik_improvement(spacings, values, max_order=1)
        result_dict = result.to_dict()
        
        assert "continuum_value" in result_dict
        assert "continuum_error" in result_dict
        assert "systematic_error" in result_dict
        assert "total_error" in result_dict
        assert "convergence_order" in result_dict
        assert result_dict["improvement_type"] == "symanzik"


class TestConvergenceOrderDetection:
    """Test automatic convergence order detection."""
    
    def test_detect_second_order(self):
        """Test detection of O(a²) convergence."""
        spacings = np.array([0.1, 0.05, 0.025])
        values = 1.0 + 0.5 * spacings**2
        
        order = detect_convergence_order(spacings, values)
        
        assert order == 2
    
    def test_detect_first_order(self):
        """Test detection of O(a) convergence."""
        spacings = np.array([0.2, 0.1, 0.05])
        values = 2.0 + 1.0 * spacings
        
        order = detect_convergence_order(spacings, values)
        
        # Should detect order 1 or close to it
        assert order in [1, 2]
    
    def test_insufficient_data(self):
        """Test with insufficient data points."""
        spacings = np.array([0.1, 0.05])
        values = np.array([1.1, 1.025])
        
        order = detect_convergence_order(spacings, values)
        
        # Should return default (2 for lattice theories)
        assert order == 2
    
    def test_noisy_data(self):
        """Test robustness to noisy data."""
        np.random.seed(42)
        spacings = np.array([0.1, 0.05, 0.025, 0.0125])
        values = 1.0 + 0.5 * spacings**2 + np.random.normal(0, 0.01, len(spacings))
        
        order = detect_convergence_order(spacings, values)
        
        # Should still detect reasonable order
        assert 1 <= order <= 4


class TestContinuumExtrapolation:
    """Test unified continuum extrapolation interface."""
    
    def test_richardson_method(self):
        """Test Richardson method selection."""
        spacings = np.array([0.1, 0.05, 0.025])
        values = 1.0 + 0.5 * spacings**2
        
        extrapolator = ContinuumExtrapolation()
        result = extrapolator.extrapolate(spacings, values, method="richardson")
        
        assert result.improvement_type == "richardson"
        assert abs(result.continuum_value - 1.0) < 0.1
    
    def test_symanzik_method(self):
        """Test Symanzik method selection."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        values = 2.0 + 1.0 * spacings**2
        
        extrapolator = ContinuumExtrapolation()
        result = extrapolator.extrapolate(spacings, values, method="symanzik")
        
        assert result.improvement_type == "symanzik"
        assert abs(result.continuum_value - 2.0) < 0.1
    
    def test_auto_method_selection(self):
        """Test automatic method selection."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        values = 1.5 + 0.8 * spacings**2
        
        extrapolator = ContinuumExtrapolation()
        result = extrapolator.extrapolate(spacings, values, method="auto")
        
        assert result.improvement_type in ["richardson", "symanzik"]
        assert result.continuum_value > 0
    
    def test_compare_methods(self):
        """Test comparison of different methods."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        values = 2.0 + 1.0 * spacings**2
        
        extrapolator = ContinuumExtrapolation()
        results = extrapolator.compare_methods(spacings, values)
        
        assert "richardson" in results
        assert "symanzik" in results
        
        # Both should give similar results for this data
        if isinstance(results["richardson"], str):
            # Method failed
            pass
        else:
            assert abs(results["richardson"].continuum_value - 2.0) < 0.2
    
    def test_uncertainty_propagation(self):
        """Test bootstrap uncertainty propagation."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        values = 1.5 + 0.5 * spacings**2
        errors = np.array([0.02, 0.015, 0.01, 0.008])
        
        extrapolator = ContinuumExtrapolation()
        mean, std = extrapolator.uncertainty_propagation(
            spacings, values, errors, n_bootstrap=100
        )
        
        assert abs(mean - 1.5) < 0.2
        assert std > 0
        assert std < 0.5  # Reasonable uncertainty


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_single_spacing(self):
        """Test with single lattice spacing."""
        spacings = np.array([0.1])
        values = np.array([1.5])
        
        extrapolator = ContinuumExtrapolation()
        
        with pytest.raises(ValueError):
            extrapolator.extrapolate(spacings, values)
    
    def test_identical_values(self):
        """Test with identical values (no convergence)."""
        spacings = np.array([0.1, 0.05, 0.025])
        values = np.array([1.0, 1.0, 1.0])
        
        extrapolator = ContinuumExtrapolation()
        
        # Should handle gracefully
        try:
            result = extrapolator.extrapolate(spacings, values, method="symanzik")
            # If successful, continuum should be ~1.0
            assert abs(result.continuum_value - 1.0) < 0.1
        except ValueError:
            # Also acceptable to fail on degenerate data
            pass
    
    def test_large_errors(self):
        """Test with large measurement errors."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        values = 1.5 + 0.5 * spacings**2
        errors = np.ones_like(values) * 0.5  # 50% errors
        
        extrapolator = ContinuumExtrapolation()
        result = extrapolator.extrapolate(spacings, values, errors, method="symanzik")
        
        # Should still work but with large uncertainty
        assert result.continuum_error > 0.1
    
    def test_non_monotonic_convergence(self):
        """Test with non-monotonic convergence."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        values = np.array([1.5, 1.3, 1.4, 1.2])  # Non-monotonic
        
        extrapolator = ContinuumExtrapolation()
        
        # Should handle but may have poor fit
        result = extrapolator.extrapolate(spacings, values, method="auto")
        assert result.continuum_value > 0


class TestPhysicalScenarios:
    """Test realistic physics scenarios."""
    
    def test_lattice_gauge_theory(self):
        """Test typical lattice gauge theory convergence."""
        # Simulate Yang-Mills mass gap with O(a²) corrections
        spacings = np.array([0.1, 0.08, 0.06, 0.04, 0.02])
        true_gap = 0.5  # Physical mass gap
        c2 = 0.3  # O(a²) coefficient
        values = true_gap + c2 * spacings**2
        
        extrapolator = ContinuumExtrapolation()
        result = extrapolator.extrapolate(spacings, values, method="symanzik")
        
        assert abs(result.continuum_value - true_gap) < 0.05
        assert result.convergence_order == 2 or result.convergence_order == 4
    
    def test_improved_action(self):
        """Test Symanzik-improved action with O(a⁴) leading."""
        spacings = np.array([0.1, 0.08, 0.06, 0.04])
        true_value = 1.0
        c4 = 0.1  # O(a⁴) coefficient (O(a²) removed by improvement)
        values = true_value + c4 * spacings**4
        
        extrapolator = ContinuumExtrapolation()
        result = extrapolator.extrapolate(spacings, values, method="symanzik")
        
        # Should extrapolate well even with higher-order corrections
        assert abs(result.continuum_value - true_value) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
