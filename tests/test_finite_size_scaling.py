"""
Tests for finite-size scaling analysis module.

Tests cover:
- Power-law extrapolation with known convergence
- Exponential extrapolation for gapped systems
- Bootstrap and jackknife uncertainty quantification
- Systematic error estimation
- Automatic method selection
"""

import pytest
import numpy as np
from src.gaugegap.analysis.finite_size_scaling import (
    FiniteSizeScaling,
    PowerLawExtrapolation,
    ExponentialExtrapolation,
    bootstrap_confidence_interval,
    jackknife_variance,
)


class TestPowerLawExtrapolation:
    """Test power-law finite-size scaling."""
    
    def test_simple_power_law(self):
        """Test extrapolation with known O(1/L) corrections."""
        # Generate synthetic data: O(L) = 1.0 + 2.0/L
        sizes = np.array([4, 8, 16, 32, 64])
        true_continuum = 1.0
        observables = true_continuum + 2.0 / sizes
        
        extrapolator = PowerLawExtrapolation(max_order=1, fix_exponent=1.0)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=100)
        
        # Check continuum value
        assert abs(result.continuum_value - true_continuum) < 0.01
        assert result.extrapolation_type == "power_law"
        assert result.chi_squared < 2.0  # Good fit
    
    def test_second_order_corrections(self):
        """Test with O(1/L²) corrections."""
        sizes = np.array([8, 16, 32, 64])
        true_continuum = 2.5
        observables = true_continuum + 1.0 / sizes + 0.5 / sizes**2
        
        extrapolator = PowerLawExtrapolation(max_order=2, fix_exponent=1.0)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=100)
        
        assert abs(result.continuum_value - true_continuum) < 0.05
        assert "A" in result.fit_parameters
        assert "B" in result.fit_parameters
    
    def test_with_errors(self):
        """Test extrapolation with measurement uncertainties."""
        sizes = np.array([4, 8, 16, 32])
        true_continuum = 1.5
        observables = true_continuum + 1.0 / sizes
        errors = np.array([0.1, 0.05, 0.03, 0.02])
        
        extrapolator = PowerLawExtrapolation(max_order=1, fix_exponent=1.0)
        result = extrapolator.fit(sizes, observables, errors, bootstrap_samples=100)
        
        assert result.continuum_error > 0
        assert result.systematic_error > 0
        assert result.total_error() > result.continuum_error
    
    def test_free_exponent(self):
        """Test with free correction exponent."""
        sizes = np.array([4, 8, 16, 32, 64])
        true_continuum = 1.0
        true_exponent = 1.5
        observables = true_continuum + 2.0 / sizes**true_exponent
        
        extrapolator = PowerLawExtrapolation(max_order=1, fix_exponent=None)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=50)
        
        assert abs(result.continuum_value - true_continuum) < 0.1
        assert "omega" in result.fit_parameters
        assert abs(result.fit_parameters["omega"] - true_exponent) < 0.3


class TestExponentialExtrapolation:
    """Test exponential finite-size scaling."""
    
    def test_simple_exponential(self):
        """Test extrapolation with exponential corrections."""
        sizes = np.array([4, 8, 12, 16, 20])
        true_continuum = 3.0
        xi = 5.0  # Correlation length
        observables = true_continuum + 1.0 * np.exp(-sizes / xi)
        
        extrapolator = ExponentialExtrapolation(fix_correlation_length=None)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=100)
        
        assert abs(result.continuum_value - true_continuum) < 0.1
        assert result.extrapolation_type == "exponential"
        assert "xi" in result.fit_parameters
    
    def test_fixed_correlation_length(self):
        """Test with known correlation length."""
        sizes = np.array([5, 10, 15, 20])
        true_continuum = 2.0
        xi = 8.0
        observables = true_continuum + 0.5 * np.exp(-sizes / xi)
        
        extrapolator = ExponentialExtrapolation(fix_correlation_length=xi)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=50)
        
        assert abs(result.continuum_value - true_continuum) < 0.05
        assert "xi" not in result.fit_parameters  # Fixed, not fitted


class TestFiniteSizeScaling:
    """Test unified finite-size scaling interface."""
    
    def test_auto_method_selection_power_law(self):
        """Test automatic selection of power-law method."""
        sizes = np.array([4, 8, 16, 32])
        observables = 1.0 + 2.0 / sizes  # Clear power-law behavior
        
        analyzer = FiniteSizeScaling()
        result = analyzer.analyze(sizes, observables, method="auto")
        
        assert result.extrapolation_type in ["power_law", "exponential"]
        assert result.continuum_value > 0
    
    def test_auto_method_selection_exponential(self):
        """Test automatic selection of exponential method."""
        sizes = np.array([5, 10, 15, 20, 25])
        observables = 2.0 + 1.0 * np.exp(-sizes / 10.0)
        
        analyzer = FiniteSizeScaling()
        result = analyzer.analyze(sizes, observables, method="auto")
        
        assert result.continuum_value > 0
        assert result.chi_squared < 5.0
    
    def test_forced_method(self):
        """Test forcing specific method."""
        sizes = np.array([4, 8, 16, 32])
        observables = 1.0 + 1.0 / sizes
        
        analyzer = FiniteSizeScaling()
        
        result_power = analyzer.analyze(sizes, observables, method="power_law")
        assert result_power.extrapolation_type == "power_law"
        
        result_exp = analyzer.analyze(sizes, observables, method="exponential")
        assert result_exp.extrapolation_type == "exponential"


class TestUncertaintyQuantification:
    """Test bootstrap and jackknife methods."""
    
    def test_bootstrap_confidence_interval(self):
        """Test bootstrap uncertainty estimation."""
        sizes = np.array([4, 8, 16, 32])
        observables = 1.0 + 1.0 / sizes
        errors = np.ones_like(observables) * 0.05
        
        def fit_func(L, O_inf, A):
            return O_inf + A * L**(-1)
        
        boot_error = bootstrap_confidence_interval(
            sizes, observables, errors, fit_func, n_samples=100
        )
        
        assert boot_error > 0
        assert boot_error < 1.0  # Reasonable magnitude
    
    def test_jackknife_variance(self):
        """Test jackknife variance estimation."""
        sizes = np.array([4, 8, 16, 32, 64])
        observables = 1.0 + 1.0 / sizes
        errors = np.ones_like(observables) * 0.05
        
        def fit_func(L, O_inf, A):
            return O_inf + A * L**(-1)
        
        jack_error = jackknife_variance(sizes, observables, errors, fit_func)
        
        assert jack_error > 0
        assert jack_error < 1.0


class TestScalingResult:
    """Test ScalingResult dataclass."""
    
    def test_result_export(self):
        """Test exporting result to dictionary."""
        sizes = np.array([4, 8, 16])
        observables = np.array([1.5, 1.25, 1.125])
        
        extrapolator = PowerLawExtrapolation(max_order=1, fix_exponent=1.0)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=50)
        
        result_dict = result.to_dict()
        
        assert "continuum_value" in result_dict
        assert "continuum_error" in result_dict
        assert "total_error" in result_dict
        assert "fit_parameters" in result_dict
        assert "chi_squared" in result_dict
        assert result_dict["extrapolation_type"] == "power_law"
    
    def test_total_error_combination(self):
        """Test that total error combines statistical and systematic."""
        sizes = np.array([4, 8, 16, 32])
        observables = 1.0 + 1.0 / sizes
        
        extrapolator = PowerLawExtrapolation(max_order=1, fix_exponent=1.0)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=50)
        
        total = result.total_error()
        expected = np.sqrt(result.continuum_error**2 + result.systematic_error**2)
        
        assert abs(total - expected) < 1e-10


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_insufficient_data(self):
        """Test with too few data points."""
        sizes = np.array([4])
        observables = np.array([1.5])
        
        extrapolator = PowerLawExtrapolation(max_order=1)
        
        with pytest.raises(ValueError):
            extrapolator.fit(sizes, observables)
    
    def test_noisy_data(self):
        """Test robustness to noisy data."""
        np.random.seed(42)
        sizes = np.array([4, 8, 16, 32, 64])
        true_continuum = 1.0
        observables = true_continuum + 1.0 / sizes + np.random.normal(0, 0.1, len(sizes))
        
        extrapolator = PowerLawExtrapolation(max_order=1, fix_exponent=1.0)
        result = extrapolator.fit(sizes, observables, bootstrap_samples=50)
        
        # Should still get reasonable result
        assert abs(result.continuum_value - true_continuum) < 0.3
    
    def test_convergence_failure(self):
        """Test handling of fit convergence failure."""
        sizes = np.array([4, 8, 16])
        observables = np.array([1.0, 1.0, 1.0])  # No variation
        
        extrapolator = PowerLawExtrapolation(max_order=2, fix_exponent=None)
        
        # Should handle gracefully or raise informative error
        try:
            result = extrapolator.fit(sizes, observables, bootstrap_samples=10)
            # If it succeeds, check it's reasonable
            assert result.continuum_value > 0
        except ValueError as e:
            # Expected for degenerate data
            assert "converge" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
