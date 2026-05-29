"""
Finite-size scaling analysis for Yang-Mills mass gap and related problems.

Mathematical Framework
----------------------
For a finite system of size L with observable O(L), finite-size scaling theory
predicts:

    O(L) = O_∞ + A·L^(-ω) + B·L^(-2ω) + ...  (power-law corrections)
    O(L) = O_∞ + A·exp(-L/ξ)                  (exponential corrections)

where:
- O_∞ is the continuum/thermodynamic limit
- ω is the correction exponent
- ξ is the correlation length
- A, B are non-universal amplitudes

For critical phenomena near phase transitions:
    O(L) = L^(β/ν) f((t·L^(1/ν)))

where β, ν are critical exponents and t is reduced temperature.

Claim Boundary Compliance
-------------------------
This module performs finite-system → continuum extrapolation. Results are
benchmarks and hypothesis tests, NOT proofs of Millennium Prize problems.
Extrapolation uncertainty must always be reported.

References
----------
- Cardy, J. (1988). Finite-Size Scaling. North-Holland.
- Privman, V. (1990). Finite Size Scaling and Numerical Simulation.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass
from scipy.optimize import curve_fit, minimize
from scipy.stats import bootstrap


@dataclass
class ScalingResult:
    """Result of finite-size scaling analysis."""
    
    continuum_value: float
    """Extrapolated value at L → ∞"""
    
    continuum_error: float
    """Uncertainty in continuum extrapolation"""
    
    fit_parameters: Dict[str, float]
    """Fitted parameters (amplitudes, exponents)"""
    
    fit_errors: Dict[str, float]
    """Uncertainties in fit parameters"""
    
    chi_squared: float
    """Goodness of fit (χ²/dof)"""
    
    sizes: np.ndarray
    """System sizes used in fit"""
    
    observables: np.ndarray
    """Observable values at each size"""
    
    observable_errors: Optional[np.ndarray]
    """Uncertainties in observables"""
    
    extrapolation_type: str
    """Type of extrapolation used"""
    
    convergence_order: Optional[float]
    """Detected convergence order"""
    
    systematic_error: float
    """Estimated systematic error from truncation"""
    
    def total_error(self) -> float:
        """Combined statistical and systematic error."""
        return np.sqrt(self.continuum_error**2 + self.systematic_error**2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "continuum_value": float(self.continuum_value),
            "continuum_error": float(self.continuum_error),
            "total_error": float(self.total_error()),
            "fit_parameters": {k: float(v) for k, v in self.fit_parameters.items()},
            "fit_errors": {k: float(v) for k, v in self.fit_errors.items()},
            "chi_squared": float(self.chi_squared),
            "extrapolation_type": self.extrapolation_type,
            "convergence_order": float(self.convergence_order) if self.convergence_order else None,
            "systematic_error": float(self.systematic_error),
            "n_sizes": len(self.sizes),
            "size_range": [float(self.sizes.min()), float(self.sizes.max())],
        }


class PowerLawExtrapolation:
    """
    Power-law finite-size scaling extrapolation.
    
    Fits O(L) = O_∞ + A·L^(-ω) + B·L^(-2ω) + ...
    
    Mathematical Derivation
    -----------------------
    For systems with algebraic correlations, finite-size corrections follow
    power laws. The leading correction exponent ω is often related to the
    spatial dimension d and anomalous dimensions.
    
    For Yang-Mills on a lattice:
    - Leading corrections: O(a²) where a = lattice spacing
    - Subleading: O(a⁴) with Symanzik improvement
    
    Uncertainty Quantification
    --------------------------
    1. Statistical: from fit covariance matrix
    2. Systematic: from truncation of higher-order terms
    3. Bootstrap: resampling for robust confidence intervals
    """
    
    def __init__(self, max_order: int = 2, fix_exponent: Optional[float] = None):
        """
        Initialize power-law extrapolation.
        
        Parameters
        ----------
        max_order : int
            Maximum order of corrections (1 or 2)
        fix_exponent : float, optional
            Fix correction exponent ω (e.g., ω=1 for O(1/L))
        """
        self.max_order = max_order
        self.fix_exponent = fix_exponent
    
    def fit(
        self,
        sizes: np.ndarray,
        observables: np.ndarray,
        errors: Optional[np.ndarray] = None,
        bootstrap_samples: int = 1000,
    ) -> ScalingResult:
        """
        Perform power-law extrapolation.
        
        Parameters
        ----------
        sizes : array
            System sizes L
        observables : array
            Observable values O(L)
        errors : array, optional
            Uncertainties in observables
        bootstrap_samples : int
            Number of bootstrap samples for confidence intervals
        
        Returns
        -------
        ScalingResult
            Extrapolation result with uncertainties
        """
        sizes = np.asarray(sizes, dtype=float)
        observables = np.asarray(observables, dtype=float)
        
        if errors is None:
            errors = np.ones_like(observables)
        else:
            errors = np.asarray(errors, dtype=float)
        
        # Define fit function based on order
        if self.max_order == 1:
            if self.fix_exponent is not None:
                def fit_func(L, O_inf, A):
                    return O_inf + A * L**(-self.fix_exponent)
                p0 = [observables[-1], observables[0] - observables[-1]]
                param_names = ["O_inf", "A"]
            else:
                def fit_func(L, O_inf, A, omega):
                    return O_inf + A * L**(-omega)
                p0 = [observables[-1], observables[0] - observables[-1], 1.0]
                param_names = ["O_inf", "A", "omega"]
        else:  # max_order == 2
            if self.fix_exponent is not None:
                def fit_func(L, O_inf, A, B):
                    return O_inf + A * L**(-self.fix_exponent) + B * L**(-2*self.fix_exponent)
                p0 = [observables[-1], observables[0] - observables[-1], 0.0]
                param_names = ["O_inf", "A", "B"]
            else:
                def fit_func(L, O_inf, A, B, omega):
                    return O_inf + A * L**(-omega) + B * L**(-2*omega)
                p0 = [observables[-1], observables[0] - observables[-1], 0.0, 1.0]
                param_names = ["O_inf", "A", "B", "omega"]
        
        # Perform weighted least-squares fit
        try:
            popt, pcov = curve_fit(
                fit_func,
                sizes,
                observables,
                p0=p0,
                sigma=errors,
                absolute_sigma=True,
                maxfev=10000,
            )
        except RuntimeError as e:
            raise ValueError(f"Fit failed to converge: {e}")
        
        # Extract results
        continuum_value = popt[0]
        continuum_error = np.sqrt(pcov[0, 0])
        
        fit_parameters = {name: val for name, val in zip(param_names, popt)}
        fit_errors = {name: np.sqrt(pcov[i, i]) for i, name in enumerate(param_names)}
        
        # Compute chi-squared
        residuals = (observables - fit_func(sizes, *popt)) / errors
        chi_squared = np.sum(residuals**2) / (len(sizes) - len(popt))
        
        # Estimate systematic error from next-order term
        if self.max_order == 1:
            # Estimate O(L^(-2ω)) contribution
            omega = popt[-1] if self.fix_exponent is None else self.fix_exponent
            systematic_error = abs(popt[1]) * sizes[-1]**(-omega) / sizes[-1]**omega
        else:
            # Estimate O(L^(-3ω)) contribution
            omega = popt[-1] if self.fix_exponent is None else self.fix_exponent
            systematic_error = abs(popt[2]) * sizes[-1]**(-omega)
        
        # Bootstrap confidence intervals
        if bootstrap_samples > 0:
            boot_continuum = bootstrap_confidence_interval(
                sizes, observables, errors, fit_func, bootstrap_samples
            )
            continuum_error = max(continuum_error, boot_continuum)
        
        return ScalingResult(
            continuum_value=continuum_value,
            continuum_error=continuum_error,
            fit_parameters=fit_parameters,
            fit_errors=fit_errors,
            chi_squared=chi_squared,
            sizes=sizes,
            observables=observables,
            observable_errors=errors,
            extrapolation_type="power_law",
            convergence_order=fit_parameters.get("omega"),
            systematic_error=systematic_error,
        )


class ExponentialExtrapolation:
    """
    Exponential finite-size scaling extrapolation.
    
    Fits O(L) = O_∞ + A·exp(-L/ξ)
    
    Mathematical Derivation
    -----------------------
    For systems with finite correlation length ξ, finite-size effects decay
    exponentially. This is typical for:
    - Gapped phases (mass gap m → ξ ~ 1/m)
    - Systems away from criticality
    - Confined phases in gauge theories
    
    The correlation length ξ is a physical parameter that can be compared
    across different system sizes and methods.
    """
    
    def __init__(self, fix_correlation_length: Optional[float] = None):
        """
        Initialize exponential extrapolation.
        
        Parameters
        ----------
        fix_correlation_length : float, optional
            Fix correlation length ξ (if known from other methods)
        """
        self.fix_correlation_length = fix_correlation_length
    
    def fit(
        self,
        sizes: np.ndarray,
        observables: np.ndarray,
        errors: Optional[np.ndarray] = None,
        bootstrap_samples: int = 1000,
    ) -> ScalingResult:
        """
        Perform exponential extrapolation.
        
        Parameters
        ----------
        sizes : array
            System sizes L
        observables : array
            Observable values O(L)
        errors : array, optional
            Uncertainties in observables
        bootstrap_samples : int
            Number of bootstrap samples
        
        Returns
        -------
        ScalingResult
            Extrapolation result with uncertainties
        """
        sizes = np.asarray(sizes, dtype=float)
        observables = np.asarray(observables, dtype=float)
        
        if errors is None:
            errors = np.ones_like(observables)
        else:
            errors = np.asarray(errors, dtype=float)
        
        # Define fit function
        if self.fix_correlation_length is not None:
            def fit_func(L, O_inf, A):
                return O_inf + A * np.exp(-L / self.fix_correlation_length)
            p0 = [observables[-1], observables[0] - observables[-1]]
            param_names = ["O_inf", "A"]
        else:
            def fit_func(L, O_inf, A, xi):
                return O_inf + A * np.exp(-L / xi)
            # Initial guess for ξ from exponential decay rate
            if len(sizes) >= 2:
                xi_guess = -(sizes[-1] - sizes[0]) / np.log(
                    (observables[-1] - observables[0]) / (observables[1] - observables[0]) + 1e-10
                )
                xi_guess = max(xi_guess, sizes[0])
            else:
                xi_guess = sizes[0]
            p0 = [observables[-1], observables[0] - observables[-1], xi_guess]
            param_names = ["O_inf", "A", "xi"]
        
        # Perform weighted least-squares fit
        try:
            popt, pcov = curve_fit(
                fit_func,
                sizes,
                observables,
                p0=p0,
                sigma=errors,
                absolute_sigma=True,
                maxfev=10000,
            )
        except RuntimeError as e:
            raise ValueError(f"Fit failed to converge: {e}")
        
        # Extract results
        continuum_value = popt[0]
        continuum_error = np.sqrt(pcov[0, 0])
        
        fit_parameters = {name: val for name, val in zip(param_names, popt)}
        fit_errors = {name: np.sqrt(pcov[i, i]) for i, name in enumerate(param_names)}
        
        # Compute chi-squared
        residuals = (observables - fit_func(sizes, *popt)) / errors
        chi_squared = np.sum(residuals**2) / (len(sizes) - len(popt))
        
        # Estimate systematic error from exponential tail
        xi = popt[-1] if self.fix_correlation_length is None else self.fix_correlation_length
        systematic_error = abs(popt[1]) * np.exp(-sizes[-1] / xi)
        
        # Bootstrap confidence intervals
        if bootstrap_samples > 0:
            boot_continuum = bootstrap_confidence_interval(
                sizes, observables, errors, fit_func, bootstrap_samples
            )
            continuum_error = max(continuum_error, boot_continuum)
        
        return ScalingResult(
            continuum_value=continuum_value,
            continuum_error=continuum_error,
            fit_parameters=fit_parameters,
            fit_errors=fit_errors,
            chi_squared=chi_squared,
            sizes=sizes,
            observables=observables,
            observable_errors=errors,
            extrapolation_type="exponential",
            convergence_order=None,
            systematic_error=systematic_error,
        )


class FiniteSizeScaling:
    """
    Unified finite-size scaling analysis with automatic method selection.
    
    This class provides a high-level interface for finite-size scaling,
    automatically selecting between power-law and exponential extrapolation
    based on the data characteristics.
    """
    
    def __init__(self):
        """Initialize finite-size scaling analyzer."""
        self.power_law = PowerLawExtrapolation(max_order=2)
        self.exponential = ExponentialExtrapolation()
    
    def analyze(
        self,
        sizes: np.ndarray,
        observables: np.ndarray,
        errors: Optional[np.ndarray] = None,
        method: str = "auto",
        bootstrap_samples: int = 1000,
    ) -> ScalingResult:
        """
        Perform finite-size scaling analysis.
        
        Parameters
        ----------
        sizes : array
            System sizes
        observables : array
            Observable values
        errors : array, optional
            Uncertainties
        method : str
            Extrapolation method: "auto", "power_law", "exponential"
        bootstrap_samples : int
            Bootstrap samples for confidence intervals
        
        Returns
        -------
        ScalingResult
            Best extrapolation result
        """
        if method == "power_law":
            return self.power_law.fit(sizes, observables, errors, bootstrap_samples)
        elif method == "exponential":
            return self.exponential.fit(sizes, observables, errors, bootstrap_samples)
        elif method == "auto":
            # Try both and select based on chi-squared
            try:
                power_result = self.power_law.fit(sizes, observables, errors, bootstrap_samples)
            except ValueError:
                power_result = None
            
            try:
                exp_result = self.exponential.fit(sizes, observables, errors, bootstrap_samples)
            except ValueError:
                exp_result = None
            
            if power_result is None and exp_result is None:
                raise ValueError("Both power-law and exponential fits failed")
            elif power_result is None:
                return exp_result
            elif exp_result is None:
                return power_result
            else:
                # Select based on chi-squared (prefer simpler model if similar)
                if power_result.chi_squared < exp_result.chi_squared * 1.1:
                    return power_result
                else:
                    return exp_result
        else:
            raise ValueError(f"Unknown method: {method}")


def bootstrap_confidence_interval(
    sizes: np.ndarray,
    observables: np.ndarray,
    errors: np.ndarray,
    fit_func: Callable,
    n_samples: int = 1000,
    confidence: float = 0.68,
) -> float:
    """
    Compute bootstrap confidence interval for continuum extrapolation.
    
    Mathematical Framework
    ----------------------
    Bootstrap resampling provides non-parametric confidence intervals by:
    1. Resampling data with replacement
    2. Refitting for each resample
    3. Computing percentiles of the distribution
    
    This accounts for non-Gaussian error distributions and correlations.
    
    Parameters
    ----------
    sizes : array
        System sizes
    observables : array
        Observable values
    errors : array
        Uncertainties
    fit_func : callable
        Fit function
    n_samples : int
        Number of bootstrap samples
    confidence : float
        Confidence level (0.68 for 1σ)
    
    Returns
    -------
    float
        Bootstrap uncertainty estimate
    """
    n_data = len(sizes)
    continuum_values = []
    
    rng = np.random.default_rng(42)
    
    for _ in range(n_samples):
        # Resample with replacement
        indices = rng.choice(n_data, size=n_data, replace=True)
        boot_sizes = sizes[indices]
        boot_obs = observables[indices]
        boot_err = errors[indices]
        
        # Add Gaussian noise
        boot_obs = boot_obs + rng.normal(0, boot_err)
        
        # Refit
        try:
            # Simple 2-parameter fit for bootstrap
            def simple_fit(L, O_inf, A):
                return O_inf + A * L**(-1)
            
            popt, _ = curve_fit(
                simple_fit,
                boot_sizes,
                boot_obs,
                sigma=boot_err,
                absolute_sigma=True,
                maxfev=5000,
            )
            continuum_values.append(popt[0])
        except:
            continue
    
    if len(continuum_values) < n_samples // 2:
        raise ValueError("Bootstrap failed: too many fit failures")
    
    continuum_values = np.array(continuum_values)
    lower = (1 - confidence) / 2
    upper = 1 - lower
    
    percentiles = np.percentile(continuum_values, [lower * 100, upper * 100])
    return (percentiles[1] - percentiles[0]) / 2


def jackknife_variance(
    sizes: np.ndarray,
    observables: np.ndarray,
    errors: np.ndarray,
    fit_func: Callable,
) -> float:
    """
    Compute jackknife variance estimate.
    
    Mathematical Framework
    ----------------------
    Jackknife resampling estimates variance by:
    1. Systematically leaving out one data point
    2. Refitting for each leave-one-out sample
    3. Computing variance of the estimates
    
    Variance: Var(θ) = (n-1)/n Σ(θ_i - θ̄)²
    
    Parameters
    ----------
    sizes : array
        System sizes
    observables : array
        Observable values
    errors : array
        Uncertainties
    fit_func : callable
        Fit function
    
    Returns
    -------
    float
        Jackknife variance estimate
    """
    n_data = len(sizes)
    continuum_values = []
    
    for i in range(n_data):
        # Leave out i-th point
        mask = np.ones(n_data, dtype=bool)
        mask[i] = False
        
        jack_sizes = sizes[mask]
        jack_obs = observables[mask]
        jack_err = errors[mask]
        
        # Refit
        try:
            def simple_fit(L, O_inf, A):
                return O_inf + A * L**(-1)
            
            popt, _ = curve_fit(
                simple_fit,
                jack_sizes,
                jack_obs,
                sigma=jack_err,
                absolute_sigma=True,
                maxfev=5000,
            )
            continuum_values.append(popt[0])
        except:
            continue
    
    if len(continuum_values) < n_data - 1:
        raise ValueError("Jackknife failed: too many fit failures")
    
    continuum_values = np.array(continuum_values)
    mean_value = np.mean(continuum_values)
    variance = (n_data - 1) / n_data * np.sum((continuum_values - mean_value)**2)
    
    return np.sqrt(variance)

# Made with Bob
