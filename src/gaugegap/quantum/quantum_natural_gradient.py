"""
Quantum Natural Gradient (QNG) for Variational Quantum Algorithms

Mathematical Framework
----------------------
The Quantum Natural Gradient uses the quantum geometric tensor (QGT) to
define a Riemannian metric on the parameter space of quantum states.

For a parameterized state |ψ(θ)⟩, the QGT is:
g_ij(θ) = Re[⟨∂_i ψ|∂_j ψ⟩ - ⟨∂_i ψ|ψ⟩⟨ψ|∂_j ψ⟩]

where ∂_i = ∂/∂θ_i.

The quantum natural gradient is:
∇̃_θ E = g⁻¹(θ) ∇_θ E

This accounts for the geometry of quantum state space, leading to faster
convergence than standard gradient descent.

Fubini-Study Metric
-------------------
The QGT is related to the Fubini-Study metric on the projective Hilbert space:
ds² = Σ_ij g_ij dθ_i dθ_j

This is the natural distance measure between quantum states.

Parameter Shift Rule
--------------------
For quantum circuits, gradients can be computed via parameter shift:
∂_i E(θ) = [E(θ + π/2 e_i) - E(θ - π/2 e_i)] / 2

This requires 2n circuit evaluations for n parameters.

Block-Diagonal Approximation
----------------------------
Full QGT is O(n²) to compute and invert. For hardware-efficient ansätze,
use block-diagonal approximation:
g ≈ diag(g_11, g_22, ..., g_nn)

Reduces to O(n) complexity.

Physics Basis
-------------
QNG follows the natural geometry of quantum state manifolds, avoiding
plateaus in the optimization landscape. Particularly effective for:
- Barren plateau mitigation
- Faster VQE convergence
- Better local minima avoidance

Claim Boundary Compliance
-------------------------
QNG is an optimization technique for variational quantum algorithms.
It does not change the physics being simulated, only improves the
efficiency of finding optimal parameters. All computational overhead
is reported.

References
----------
- Stokes et al. (2020). Quantum Natural Gradient
- Yamamoto (2019). On the natural gradient for variational quantum eigensolver
- Wierichs et al. (2020). Avoiding local minima in VQE with QNG
- Koczor & Benjamin (2022). Quantum analytic descent
"""

from typing import List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class QNGConfig:
    """Configuration for Quantum Natural Gradient."""
    
    regularization: float = 1e-6
    """Regularization parameter for QGT inversion"""
    
    block_diagonal: bool = True
    """Use block-diagonal approximation"""
    
    parameter_shift: float = np.pi / 2
    """Shift for parameter shift rule"""
    
    max_qgt_condition: float = 1e8
    """Maximum condition number for QGT"""


@dataclass
class QNGResult:
    """Result of QNG optimization step."""
    
    natural_gradient: np.ndarray
    """Quantum natural gradient"""
    
    standard_gradient: np.ndarray
    """Standard gradient for comparison"""
    
    qgt: np.ndarray
    """Quantum geometric tensor"""
    
    qgt_condition: float
    """Condition number of QGT"""
    
    step_size: float
    """Effective step size"""
    
    n_circuit_evals: int
    """Number of circuit evaluations"""
    
    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "natural_gradient_norm": float(np.linalg.norm(self.natural_gradient)),
            "standard_gradient_norm": float(np.linalg.norm(self.standard_gradient)),
            "qgt_condition": float(self.qgt_condition),
            "step_size": float(self.step_size),
            "n_circuit_evals": self.n_circuit_evals,
        }


def compute_parameter_shift_gradient(
    cost_function: Callable[[np.ndarray], float],
    parameters: np.ndarray,
    shift: float = np.pi / 2,
) -> np.ndarray:
    """
    Compute gradient using parameter shift rule.
    
    Parameters
    ----------
    cost_function : callable
        Function to minimize (e.g., energy expectation)
    parameters : array
        Current parameter values
    shift : float
        Parameter shift amount
    
    Returns
    -------
    array
        Gradient vector
    
    Notes
    -----
    Requires 2n function evaluations for n parameters.
    Exact for quantum circuits with specific gate types.
    """
    n_params = len(parameters)
    gradient = np.zeros(n_params)
    
    for i in range(n_params):
        # Shift parameter forward
        params_plus = parameters.copy()
        params_plus[i] += shift
        
        # Shift parameter backward
        params_minus = parameters.copy()
        params_minus[i] -= shift
        
        # Parameter shift rule
        gradient[i] = (cost_function(params_plus) - cost_function(params_minus)) / 2
    
    return gradient


def compute_qgt_diagonal(
    state_function: Callable[[np.ndarray], np.ndarray],
    parameters: np.ndarray,
    shift: float = np.pi / 2,
) -> np.ndarray:
    """
    Compute diagonal approximation of quantum geometric tensor.
    
    Parameters
    ----------
    state_function : callable
        Function returning quantum state |ψ(θ)⟩
    parameters : array
        Current parameter values
    shift : float
        Parameter shift amount
    
    Returns
    -------
    array
        Diagonal QGT elements
    
    Notes
    -----
    For diagonal approximation:
    g_ii = 1 - |⟨ψ(θ)|ψ(θ + shift e_i)⟩|²
    """
    n_params = len(parameters)
    qgt_diag = np.zeros(n_params)
    
    # Reference state
    psi_0 = state_function(parameters)
    
    for i in range(n_params):
        # Shifted state
        params_shifted = parameters.copy()
        params_shifted[i] += shift
        psi_shifted = state_function(params_shifted)
        
        # Overlap
        overlap = np.abs(np.vdot(psi_0, psi_shifted))**2
        
        # Diagonal QGT element
        qgt_diag[i] = 1 - overlap
    
    return qgt_diag


def compute_qgt_full(
    state_function: Callable[[np.ndarray], np.ndarray],
    parameters: np.ndarray,
    shift: float = np.pi / 4,
) -> np.ndarray:
    """
    Compute full quantum geometric tensor.
    
    Parameters
    ----------
    state_function : callable
        Function returning quantum state |ψ(θ)⟩
    parameters : array
        Current parameter values
    shift : float
        Parameter shift amount
    
    Returns
    -------
    array
        Full QGT matrix
    
    Notes
    -----
    Full QGT requires O(n²) state preparations.
    Use diagonal approximation for large parameter spaces.
    """
    n_params = len(parameters)
    qgt = np.zeros((n_params, n_params))
    
    # Reference state
    psi_0 = state_function(parameters)
    
    for i in range(n_params):
        for j in range(i, n_params):
            # Compute g_ij using finite differences
            # g_ij ≈ Re[⟨ψ(θ)|ψ(θ + δθ_i + δθ_j)⟩ - ⟨ψ(θ)|ψ(θ + δθ_i)⟩⟨ψ(θ + δθ_j)|ψ(θ)⟩]
            
            params_i = parameters.copy()
            params_i[i] += shift
            psi_i = state_function(params_i)
            
            params_j = parameters.copy()
            params_j[j] += shift
            psi_j = state_function(params_j)
            
            params_ij = parameters.copy()
            params_ij[i] += shift
            params_ij[j] += shift
            psi_ij = state_function(params_ij)
            
            # QGT element
            overlap_ij = complex(np.vdot(psi_0, psi_ij))
            overlap_i = complex(np.vdot(psi_0, psi_i))
            overlap_j = complex(np.vdot(psi_j, psi_0))
            
            qgt[i, j] = float(np.real(overlap_ij - overlap_i * overlap_j))
            qgt[j, i] = qgt[i, j]  # Symmetric
    
    return qgt


def quantum_natural_gradient_step(
    cost_function: Callable[[np.ndarray], float],
    state_function: Callable[[np.ndarray], np.ndarray],
    parameters: np.ndarray,
    learning_rate: float = 0.01,
    config: Optional[QNGConfig] = None,
) -> Tuple[np.ndarray, QNGResult]:
    """
    Perform one step of quantum natural gradient descent.
    
    Parameters
    ----------
    cost_function : callable
        Cost function to minimize
    state_function : callable
        Function returning quantum state
    parameters : array
        Current parameters
    learning_rate : float
        Learning rate
    config : QNGConfig, optional
        QNG configuration
    
    Returns
    -------
    new_parameters : array
        Updated parameters
    result : QNGResult
        Step information
    
    Notes
    -----
    Update rule: θ_new = θ - η g⁻¹ ∇E
    where g is the QGT and ∇E is the gradient.
    """
    if config is None:
        config = QNGConfig()
    
    # Compute standard gradient
    gradient = compute_parameter_shift_gradient(
        cost_function,
        parameters,
        shift=config.parameter_shift,
    )
    
    # Compute QGT
    if config.block_diagonal:
        qgt_diag = compute_qgt_diagonal(
            state_function,
            parameters,
            shift=config.parameter_shift,
        )
        # Add regularization
        qgt_diag_reg = qgt_diag + config.regularization
        # Invert (diagonal)
        qgt_inv = np.diag(1.0 / qgt_diag_reg)
        qgt = np.diag(qgt_diag)
        n_evals = 2 * len(parameters) + len(parameters)  # gradient + QGT diagonal
        # Calculate condition number
        cond = np.max(qgt_diag) / (np.min(qgt_diag) + config.regularization)
    else:
        qgt = compute_qgt_full(
            state_function,
            parameters,
            shift=config.parameter_shift / 2,
        )
        # Add regularization
        qgt_reg = qgt + config.regularization * np.eye(len(parameters))
        # Invert (full)
        qgt_inv = np.linalg.pinv(qgt_reg)
        n_evals = 2 * len(parameters) + len(parameters)**2  # gradient + QGT full
        # Calculate condition number
        cond = np.linalg.cond(qgt)
    
    # Compute natural gradient
    natural_gradient = qgt_inv @ gradient
    
    # Update parameters
    new_parameters = parameters - learning_rate * natural_gradient
    
    result = QNGResult(
        natural_gradient=natural_gradient,
        standard_gradient=gradient,
        qgt=qgt,
        qgt_condition=float(cond),
        step_size=learning_rate,
        n_circuit_evals=n_evals,
    )
    
    return new_parameters, result


def compare_qng_vs_standard(
    cost_function: Callable[[np.ndarray], float],
    state_function: Callable[[np.ndarray], np.ndarray],
    initial_parameters: np.ndarray,
    n_steps: int = 10,
    learning_rate: float = 0.01,
) -> dict:
    """
    Compare QNG vs standard gradient descent.
    
    Parameters
    ----------
    cost_function : callable
        Cost function to minimize
    state_function : callable
        Function returning quantum state
    initial_parameters : array
        Starting parameters
    n_steps : int
        Number of optimization steps
    learning_rate : float
        Learning rate
    
    Returns
    -------
    dict
        Comparison results
    """
    params_qng = initial_parameters.copy()
    params_std = initial_parameters.copy()
    
    costs_qng = [cost_function(params_qng)]
    costs_std = [cost_function(params_std)]
    
    for step in range(n_steps):
        # QNG step
        params_qng, qng_result = quantum_natural_gradient_step(
            cost_function,
            state_function,
            params_qng,
            learning_rate,
        )
        costs_qng.append(cost_function(params_qng))
        
        # Standard gradient step
        gradient_std = compute_parameter_shift_gradient(
            cost_function,
            params_std,
        )
        params_std = params_std - learning_rate * gradient_std
        costs_std.append(cost_function(params_std))
    
    return {
        "costs_qng": costs_qng,
        "costs_std": costs_std,
        "final_cost_qng": costs_qng[-1],
        "final_cost_std": costs_std[-1],
        "improvement": (costs_std[-1] - costs_qng[-1]) / abs(costs_std[-1]),
        "n_steps": n_steps,
    }


# Made with Bob