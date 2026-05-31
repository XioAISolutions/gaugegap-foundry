"""
Continuum limit extrapolation for lattice gauge theories.

Mathematical Framework
----------------------
For lattice gauge theories with spacing a, physical observables approach
continuum values as a → 0:

    O(a) = O_cont + c₂·a² + c₄·a⁴ + ...  (Symanzik improvement)

Richardson extrapolation accelerates convergence by combining results at
different lattice spacings:

    O_ext = (2^p·O(a/2) - O(a)) / (2^p - 1)

where p is the convergence order.

For Yang-Mills mass gap:
- Tree-level: O(a²) corrections
- One-loop: O(a⁴) with improved actions
- Tadpole improvement: O(αₛ·a²) resummation

Claim Boundary Compliance
-------------------------
Continuum extrapolation is a mathematical procedure with quantified
uncertainties. Results are finite-system benchmarks, NOT proofs of
the Yang-Mills mass gap or other Millennium Prize problems.

References
----------
- Symanzik, K. (1983). Continuum limit and improved action.
- Lüscher, M. (2010). Properties and uses of the Wilson flow.
- Della Morte, M. & Sommer, R. (2005). Non-perturbative improvement.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline


@dataclass
class ContinuumResult:
    """Result of continuum limit extrapolation."""
    
    continuum_value: float
    """Extrapolated continuum value"""
    
    continuum_error: float
    """Statistical uncertainty"""
    
    systematic_error: float
    """Systematic error from truncation"""
    
    convergence_order: int
    """Detected convergence order"""
    
    lattice_spacings: np.ndarray
    """Lattice spacings used"""
    
    lattice_values: np.ndarray
    """Observable values at each spacing"""
    
    lattice_errors: Optional[np.ndarray]
    """Uncertainties at each spacing"""
    
    improvement_type: str
    """Type of improvement used"""
    
    chi_squared: float
    """Goodness of fit"""
    
    coefficients: Dict[str, float]
    """Fitted correction coefficients"""
    
    def total_error(self) -> float:
        """Combined statistical and systematic error."""
        return np.sqrt(self.continuum_error**2 + self.systematic_error**2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "continuum_value": float(self.continuum_value),
            "continuum_error": float(self.continuum_error),
            "systematic_error": float(self.systematic_error),
            "total_error": float(self.total_error()),
            "convergence_order": int(self.convergence_order),
            "improvement_type": self.improvement_type,
            "chi_squared": float(self.chi_squared),
            "coefficients": {k: float(v) for k, v in self.coefficients.items()},
            "n_spacings": len(self.lattice_spacings),
            "spacing_range": [float(self.lattice_spacings.min()), float(self.lattice_spacings.max())],
        }


def richardson_extrapolation(
    values: np.ndarray,
    spacings: np.ndarray,
    order: Optional[int] = None,
) -> Tuple[float, int]:
    """
    Richardson extrapolation to continuum limit.
    
    Mathematical Derivation
    -----------------------
    Given O(a) = O_cont + c·a^p + O(a^(p+1)), Richardson extrapolation
    eliminates the leading error term:
    
    O_ext = (r^p·O(a/r) - O(a)) / (r^p - 1)
    
    where r = a₁/a₂ is the refinement ratio.
    
    For multiple spacings, we can recursively apply Richardson extrapolation
    to build a Romberg table, achieving higher-order accuracy.
    
    Parameters
    ----------
    values : array
        Observable values at different spacings (ordered from fine to coarse)
    spacings : array
        Lattice spacings (ordered from fine to coarse)
    order : int, optional
        Convergence order p. If None, automatically detected.
    
    Returns
    -------
    continuum_value : float
        Extrapolated continuum value
    detected_order : int
        Detected or used convergence order
    
    Examples
    --------
    >>> spacings = np.array([0.05, 0.1, 0.2])
    >>> values = np.array([1.05, 1.20, 1.80])
    >>> cont_val, order = richardson_extrapolation(values, spacings)
    """
    values = np.asarray(values, dtype=float)
    spacings = np.asarray(spacings, dtype=float)
    
    if len(values) < 2:
        raise ValueError("Need at least 2 values for Richardson extrapolation")
    
    # Sort by spacing (finest first)
    sort_idx = np.argsort(spacings)
    spacings = spacings[sort_idx]
    values = values[sort_idx]
    
    # Detect convergence order if not provided
    if order is None:
        order = detect_convergence_order(spacings, values)
    
    # Build Romberg table
    n = len(values)
    table = np.zeros((n, n))
    table[:, 0] = values
    
    for j in range(1, n):
        for i in range(n - j):
            r = spacings[i + j] / spacings[i]
            table[i, j] = (r**order * table[i, j - 1] - table[i + 1, j - 1]) / (r**order - 1)
    
    # Best estimate is top-right corner
    continuum_value = table[0, n - 1]
    
    return continuum_value, order


def symanzik_improvement(
    spacings: np.ndarray,
    values: np.ndarray,
    errors: Optional[np.ndarray] = None,
    max_order: int = 2,
) -> ContinuumResult:
    """
    Symanzik improved continuum extrapolation.
    
    Mathematical Framework
    ----------------------
    Symanzik improvement systematically removes O(a²) errors by adding
    higher-dimensional operators to the action:
    
    S_imp = S_Wilson + c₁·a²·O₁ + c₂·a²·O₂ + ...
    
    For observables:
    O(a) = O_cont + c₂·a² + c₄·a⁴ + ...
    
    We fit this expansion and extrapolate to a = 0.
    
    Parameters
    ----------
    spacings : array
        Lattice spacings
    values : array
        Observable values
    errors : array, optional
        Uncertainties
    max_order : int
        Maximum order of a² corrections (1 or 2)
    
    Returns
    -------
    ContinuumResult
        Extrapolation result with uncertainties
    
    Examples
    --------
    >>> spacings = np.array([0.1, 0.08, 0.06, 0.04])
    >>> values = np.array([1.2, 1.15, 1.10, 1.06])
    >>> result = symanzik_improvement(spacings, values)
    >>> print(f"Continuum: {result.continuum_value:.4f} ± {result.total_error():.4f}")
    """
    spacings = np.asarray(spacings, dtype=float)
    values = np.asarray(values, dtype=float)
    
    if errors is None:
        errors = np.ones_like(values) * 0.01 * np.abs(values)
    else:
        errors = np.asarray(errors, dtype=float)
    
    # Define fit function based on order
    if max_order == 1:
        def fit_func(a, O_cont, c2):
            return O_cont + c2 * a**2
        param_names = ["O_cont", "c2"]
        p0 = [values[np.argmin(spacings)], (values[-1] - values[0]) / (spacings[-1]**2 - spacings[0]**2)]
    else:  # max_order == 2
        def fit_func(a, O_cont, c2, c4):
            return O_cont + c2 * a**2 + c4 * a**4
        param_names = ["O_cont", "c2", "c4"]
        p0 = [values[np.argmin(spacings)], 0.0, 0.0]
    
    # Perform weighted fit
    try:
        popt, pcov = curve_fit(
            fit_func,
            spacings,
            values,
            p0=p0,
            sigma=errors,
            absolute_sigma=True,
            maxfev=10000,
        )
    except RuntimeError as e:
        raise ValueError(f"Symanzik fit failed: {e}")
    
    # Extract results
    continuum_value = popt[0]
    continuum_error = np.sqrt(pcov[0, 0])
    
    coefficients = {name: val for name, val in zip(param_names, popt)}
    
    # Compute chi-squared
    residuals = (values - fit_func(spacings, *popt)) / errors
    chi_squared = np.sum(residuals**2) / (len(values) - len(popt))
    
    # Estimate systematic error from next order
    if max_order == 1:
        # Estimate O(a⁴) contribution
        systematic_error = abs(popt[1]) * spacings.min()**2
    else:
        # Estimate O(a⁶) contribution
        systematic_error = abs(popt[2]) * spacings.min()**2
    
    return ContinuumResult(
        continuum_value=continuum_value,
        continuum_error=continuum_error,
        systematic_error=systematic_error,
        convergence_order=2 * max_order,
        lattice_spacings=spacings,
        lattice_values=values,
        lattice_errors=errors,
        improvement_type="symanzik",
        chi_squared=chi_squared,
        coefficients=coefficients,
    )


def detect_convergence_order(
    spacings: np.ndarray,
    values: np.ndarray,
    min_order: int = 1,
    max_order: int = 4,
) -> int:
    """
    Automatically detect convergence order from data.
    
    Mathematical Framework
    ----------------------
    For O(a) = O_cont + c·a^p, the convergence order p can be estimated from:
    
    p ≈ log((O(a₃) - O(a₂)) / (O(a₂) - O(a₁))) / log(a₃/a₂)
    
    We test multiple orders and select the one that best describes the data.
    
    Parameters
    ----------
    spacings : array
        Lattice spacings (at least 3 values)
    values : array
        Observable values
    min_order : int
        Minimum order to test
    max_order : int
        Maximum order to test
    
    Returns
    -------
    int
        Detected convergence order
    
    Examples
    --------
    >>> spacings = np.array([0.1, 0.05, 0.025])
    >>> values = np.array([1.1, 1.025, 1.00625])  # O(a²) convergence
    >>> order = detect_convergence_order(spacings, values)
    >>> print(f"Detected order: {order}")
    """
    spacings = np.asarray(spacings, dtype=float)
    values = np.asarray(values, dtype=float)
    
    if len(values) < 3:
        # Default to O(a²) for lattice gauge theory
        return 2
    
    # Sort by spacing
    sort_idx = np.argsort(spacings)
    spacings = spacings[sort_idx]
    values = values[sort_idx]
    
    # Estimate order from consecutive differences
    if len(values) >= 3:
        # Use finest three points
        a1, a2, a3 = spacings[:3]
        v1, v2, v3 = values[:3]
        
        # Avoid division by zero
        if abs(v2 - v1) < 1e-10 or abs(v3 - v2) < 1e-10:
            return 2
        
        # Estimate order
        ratio = (v3 - v2) / (v2 - v1)
        spacing_ratio = a3 / a2
        
        if ratio > 0 and spacing_ratio > 1:
            estimated_order = np.log(ratio) / np.log(spacing_ratio)
            
            # Round to nearest integer in allowed range
            estimated_order = int(np.round(estimated_order))
            estimated_order = max(min_order, min(estimated_order, max_order))
            
            return estimated_order
    
    # Default to O(a²) for lattice theories
    return 2


class ContinuumExtrapolation:
    """
    Unified continuum limit extrapolation with multiple methods.
    
    This class provides a high-level interface for continuum extrapolation,
    supporting Richardson extrapolation, Symanzik improvement, and automatic
    method selection based on data characteristics.
    """
    
    def __init__(self):
        """Initialize continuum extrapolation analyzer."""
        pass
    
    def extrapolate(
        self,
        spacings: np.ndarray,
        values: np.ndarray,
        errors: Optional[np.ndarray] = None,
        method: str = "auto",
        convergence_order: Optional[int] = None,
    ) -> ContinuumResult:
        """
        Perform continuum limit extrapolation.
        
        Parameters
        ----------
        spacings : array
            Lattice spacings
        values : array
            Observable values
        errors : array, optional
            Uncertainties
        method : str
            Extrapolation method: "auto", "richardson", "symanzik"
        convergence_order : int, optional
            Known convergence order (if available)
        
        Returns
        -------
        ContinuumResult
            Extrapolation result with uncertainties
        
        Examples
        --------
        >>> extrapolator = ContinuumExtrapolation()
        >>> spacings = np.array([0.1, 0.08, 0.06, 0.04])
        >>> values = np.array([1.2, 1.15, 1.10, 1.06])
        >>> result = extrapolator.extrapolate(spacings, values)
        """
        spacings = np.asarray(spacings, dtype=float)
        values = np.asarray(values, dtype=float)
        
        if len(spacings) < 2:
            raise ValueError("Need at least 2 lattice spacings for extrapolation")
        
        if method == "richardson":
            return self._richardson_method(spacings, values, errors, convergence_order)
        elif method == "symanzik":
            return self._symanzik_method(spacings, values, errors)
        elif method == "auto":
            # Try both methods and select best
            try:
                symanzik_result = self._symanzik_method(spacings, values, errors)
            except ValueError:
                symanzik_result = None
            
            try:
                richardson_result = self._richardson_method(spacings, values, errors, convergence_order)
            except ValueError:
                richardson_result = None
            
            if symanzik_result is None and richardson_result is None:
                raise ValueError("Both extrapolation methods failed")
            elif symanzik_result is None:
                return richardson_result
            elif richardson_result is None:
                return symanzik_result
            else:
                # Prefer Symanzik if chi-squared is reasonable
                if symanzik_result.chi_squared < 2.0:
                    return symanzik_result
                else:
                    return richardson_result
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _richardson_method(
        self,
        spacings: np.ndarray,
        values: np.ndarray,
        errors: Optional[np.ndarray],
        convergence_order: Optional[int],
    ) -> ContinuumResult:
        """Apply Richardson extrapolation."""
        continuum_value, order = richardson_extrapolation(values, spacings, convergence_order)
        
        # Estimate uncertainty from spread of intermediate values
        if errors is not None:
            # Propagate errors through Richardson extrapolation
            continuum_error = np.sqrt(np.sum(errors**2)) / len(errors)
        else:
            # Use spread of values as uncertainty estimate
            continuum_error = np.std(values) / np.sqrt(len(values))
        
        # Estimate systematic error from finest spacing
        finest_idx = np.argmin(spacings)
        systematic_error = abs(values[finest_idx] - continuum_value) * 0.5
        
        return ContinuumResult(
            continuum_value=continuum_value,
            continuum_error=continuum_error,
            systematic_error=systematic_error,
            convergence_order=order,
            lattice_spacings=spacings,
            lattice_values=values,
            lattice_errors=errors,
            improvement_type="richardson",
            chi_squared=1.0,  # Not applicable for Richardson
            coefficients={"order": float(order)},
        )
    
    def _symanzik_method(
        self,
        spacings: np.ndarray,
        values: np.ndarray,
        errors: Optional[np.ndarray],
    ) -> ContinuumResult:
        """Apply Symanzik improvement."""
        # Try second-order first, fall back to first-order if needed
        try:
            return symanzik_improvement(spacings, values, errors, max_order=2)
        except ValueError:
            return symanzik_improvement(spacings, values, errors, max_order=1)
    
    def compare_methods(
        self,
        spacings: np.ndarray,
        values: np.ndarray,
        errors: Optional[np.ndarray] = None,
    ) -> Dict[str, ContinuumResult]:
        """
        Compare different extrapolation methods.
        
        Parameters
        ----------
        spacings : array
            Lattice spacings
        values : array
            Observable values
        errors : array, optional
            Uncertainties
        
        Returns
        -------
        dict
            Results from each method
        """
        results = {}
        
        try:
            results["richardson"] = self._richardson_method(spacings, values, errors, None)
        except ValueError as e:
            results["richardson"] = f"Failed: {e}"
        
        try:
            results["symanzik"] = self._symanzik_method(spacings, values, errors)
        except ValueError as e:
            results["symanzik"] = f"Failed: {e}"
        
        return results
    
    def uncertainty_propagation(
        self,
        spacings: np.ndarray,
        values: np.ndarray,
        errors: np.ndarray,
        n_bootstrap: int = 1000,
    ) -> Tuple[float, float]:
        """
        Propagate uncertainties through extrapolation using bootstrap.
        
        Parameters
        ----------
        spacings : array
            Lattice spacings
        values : array
            Observable values
        errors : array
            Uncertainties
        n_bootstrap : int
            Number of bootstrap samples
        
        Returns
        -------
        mean : float
            Mean continuum value
        std : float
            Standard deviation
        """
        rng = np.random.default_rng(42)
        continuum_values = []
        
        for _ in range(n_bootstrap):
            # Add Gaussian noise
            boot_values = values + rng.normal(0, errors)
            
            try:
                result = self.extrapolate(spacings, boot_values, errors, method="symanzik")
                continuum_values.append(result.continuum_value)
            except:
                continue
        
        if len(continuum_values) < n_bootstrap // 2:
            raise ValueError("Bootstrap failed: too many extrapolation failures")
        
        continuum_values = np.array(continuum_values)
        return np.mean(continuum_values), np.std(continuum_values)

# Made with Bob
