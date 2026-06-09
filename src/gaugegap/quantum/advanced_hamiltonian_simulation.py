"""
Advanced Hamiltonian Simulation Techniques

Mathematical Framework
----------------------
For time evolution under Hamiltonian H = Σᵢ Hᵢ:

1. Higher-Order Trotter Decomposition:
   Standard Trotter: e^(-iHt) ≈ ∏ᵢ e^(-iHᵢt)
   Error: O(t²/n) where n = number of steps
   
   Second-order (Suzuki): e^(-iHt) ≈ ∏ᵢ e^(-iHᵢt/2) ∏ᵢ₍ᵣₑᵥ₎ e^(-iHᵢt/2)
   Error: O(t³/n²)
   
   Fourth-order: Recursive composition with specific coefficients
   Error: O(t⁵/n⁴)

2. Randomized Trotter (qDRIFT):
   Sample Hamiltonian terms randomly with probability ∝ ||Hᵢ||
   Expected error: O(λ²t²/N) where λ = Σᵢ||Hᵢ|| and N = samples
   
   Advantages:
   - Gate count independent of number of terms
   - Better scaling for sparse Hamiltonians
   - Unbiased estimator

3. Linear Combination of Unitaries (LCU):
   Represent H = Σᵢ αᵢ Uᵢ where Uᵢ are unitaries
   Use quantum signal processing for optimal scaling

Physics Applications
--------------------
For gauge theories:
- Plaquette terms (field strength)
- Link terms (kinetic energy)
- Matter coupling terms

Higher-order methods reduce circuit depth for fixed accuracy,
critical for NISQ devices with limited coherence.

Claim Boundary Compliance
-------------------------
These are simulation techniques for finite quantum systems.
They provide benchmarks for quantum hardware performance but
do not constitute proofs of Millennium Prize problems.
All methods preserve unitary evolution and are mathematically exact
in the limit of infinite Trotter steps.

References
----------
- Suzuki, M. (1991). General theory of fractal path integrals
- Campbell, E. (2019). Random compiler for fast Hamiltonian simulation
- Childs et al. (2012). Hamiltonian simulation using linear combinations of unitaries
- Berry et al. (2015). Simulating Hamiltonian dynamics with a truncated Taylor series
- Poulin et al. (2011). The Trotter step size required for accurate quantum simulation
"""

import numpy as np
from typing import List, Tuple, Optional, Callable, Dict, Any
from dataclasses import dataclass
import warnings


@dataclass
class SimulationResult:
    """Result of Hamiltonian simulation."""
    
    final_state: np.ndarray
    """Final evolved state"""
    
    method: str
    """Simulation method used"""
    
    total_time: float
    """Total evolution time"""
    
    n_steps: int
    """Number of Trotter steps"""
    
    gate_count: int
    """Total gate count"""
    
    error_estimate: float
    """Estimated simulation error"""
    
    metadata: Dict[str, Any]
    """Additional method-specific data"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "method": self.method,
            "total_time": float(self.total_time),
            "n_steps": self.n_steps,
            "gate_count": self.gate_count,
            "error_estimate": float(self.error_estimate),
            "final_state_norm": float(np.linalg.norm(self.final_state)),
            "metadata": self.metadata,
        }


def first_order_trotter(
    hamiltonian_terms: List[np.ndarray],
    initial_state: np.ndarray,
    time: float,
    n_steps: int,
) -> SimulationResult:
    """
    First-order Trotter decomposition.
    
    Mathematical Framework
    ----------------------
    e^(-iHt) ≈ [∏ᵢ e^(-iHᵢδt)]^n where δt = t/n
    
    Error: O(t²/n) per step, O(t²) total
    
    Parameters
    ----------
    hamiltonian_terms : list
        List of Hamiltonian term matrices
    initial_state : array
        Initial state vector
    time : float
        Total evolution time
    n_steps : int
        Number of Trotter steps
    
    Returns
    -------
    SimulationResult
        Simulation result with error estimate
    """
    state = initial_state.copy()
    dt = time / n_steps
    
    # Count gates (one exponentiation per term per step)
    gate_count = len(hamiltonian_terms) * n_steps
    
    for step in range(n_steps):
        for H_term in hamiltonian_terms:
            # Apply e^(-iH_term * dt)
            U = _matrix_exponential(-1j * H_term * dt)
            state = U @ state
    
    # Error estimate: O(t²/n) for first-order
    # Assuming ||[Hᵢ, Hⱼ]|| ~ ||Hᵢ|| ||Hⱼ||
    norm_sum = sum(np.linalg.norm(H, ord=2) for H in hamiltonian_terms)
    error_estimate = float((norm_sum * time)**2 / n_steps)
    
    return SimulationResult(
        final_state=state,
        method="first_order_trotter",
        total_time=time,
        n_steps=n_steps,
        gate_count=gate_count,
        error_estimate=error_estimate,
        metadata={"order": 1, "n_terms": len(hamiltonian_terms)},
    )


def second_order_trotter(
    hamiltonian_terms: List[np.ndarray],
    initial_state: np.ndarray,
    time: float,
    n_steps: int,
) -> SimulationResult:
    """
    Second-order Trotter (Suzuki) decomposition.
    
    Mathematical Framework
    ----------------------
    e^(-iHt) ≈ [∏ᵢ e^(-iHᵢδt/2) ∏ᵢ₍ᵣₑᵥ₎ e^(-iHᵢδt/2)]^n
    
    Error: O(t³/n²) per step, O(t³/n) total
    
    Better accuracy than first-order for same step count.
    
    Parameters
    ----------
    hamiltonian_terms : list
        List of Hamiltonian term matrices
    initial_state : array
        Initial state vector
    time : float
        Total evolution time
    n_steps : int
        Number of Trotter steps
    
    Returns
    -------
    SimulationResult
        Simulation result with improved error estimate
    """
    state = initial_state.copy()
    dt = time / n_steps
    
    # Count gates (2 * n_terms per step)
    gate_count = 2 * len(hamiltonian_terms) * n_steps
    
    for step in range(n_steps):
        # Forward sweep with dt/2
        for H_term in hamiltonian_terms:
            U = _matrix_exponential(-1j * H_term * dt / 2)
            state = U @ state
        
        # Backward sweep with dt/2
        for H_term in reversed(hamiltonian_terms):
            U = _matrix_exponential(-1j * H_term * dt / 2)
            state = U @ state
    
    # Error estimate: O(t³/n²) for second-order
    norm_sum = sum(np.linalg.norm(H, ord=2) for H in hamiltonian_terms)
    error_estimate = float((norm_sum * time)**3 / n_steps**2)
    
    return SimulationResult(
        final_state=state,
        method="second_order_trotter",
        total_time=time,
        n_steps=n_steps,
        gate_count=gate_count,
        error_estimate=error_estimate,
        metadata={"order": 2, "n_terms": len(hamiltonian_terms)},
    )


def fourth_order_trotter(
    hamiltonian_terms: List[np.ndarray],
    initial_state: np.ndarray,
    time: float,
    n_steps: int,
) -> SimulationResult:
    """
    Fourth-order Trotter decomposition using Suzuki formula.
    
    Mathematical Framework
    ----------------------
    Uses recursive composition with coefficients:
    p₁ = p₂ = 1/(4 - 4^(1/3))
    p₃ = 1 - 4p₁
    
    S₄(t) = S₂(p₁t) S₂(p₂t) S₂(p₃t) S₂(p₂t) S₂(p₁t)
    
    Error: O(t⁵/n⁴) per step, O(t⁵/n³) total
    
    Parameters
    ----------
    hamiltonian_terms : list
        List of Hamiltonian term matrices
    initial_state : array
        Initial state vector
    time : float
        Total evolution time
    n_steps : int
        Number of Trotter steps
    
    Returns
    -------
    SimulationResult
        Simulation result with fourth-order accuracy
    """
    state = initial_state.copy()
    dt = time / n_steps
    
    # Suzuki coefficients for fourth-order
    p1 = 1.0 / (4.0 - 4.0**(1.0/3.0))
    p2 = p1
    p3 = 1.0 - 4.0 * p1
    coeffs = [p1, p2, p3, p2, p1]
    
    # Count gates (5 second-order steps per Trotter step)
    gate_count = 5 * 2 * len(hamiltonian_terms) * n_steps
    
    for step in range(n_steps):
        for coeff in coeffs:
            # Apply second-order step with scaled time
            dt_scaled = coeff * dt
            
            # Forward sweep
            for H_term in hamiltonian_terms:
                U = _matrix_exponential(-1j * H_term * dt_scaled / 2)
                state = U @ state
            
            # Backward sweep
            for H_term in reversed(hamiltonian_terms):
                U = _matrix_exponential(-1j * H_term * dt_scaled / 2)
                state = U @ state
    
    # Error estimate: O(t⁵/n⁴) for fourth-order
    norm_sum = sum(np.linalg.norm(H, ord=2) for H in hamiltonian_terms)
    error_estimate = float((norm_sum * time)**5 / n_steps**4)
    
    return SimulationResult(
        final_state=state,
        method="fourth_order_trotter",
        total_time=time,
        n_steps=n_steps,
        gate_count=gate_count,
        error_estimate=error_estimate,
        metadata={"order": 4, "n_terms": len(hamiltonian_terms)},
    )


def qdrift_simulation(
    hamiltonian_terms: List[np.ndarray],
    initial_state: np.ndarray,
    time: float,
    n_samples: int,
    seed: Optional[int] = None,
) -> SimulationResult:
    """
    Randomized Trotter (qDRIFT) simulation.
    
    Mathematical Framework
    ----------------------
    Sample Hamiltonian terms randomly with probability:
    p(Hᵢ) = ||Hᵢ|| / λ where λ = Σⱼ ||Hⱼ||
    
    Apply e^(-iHᵢ·t·λ/N) for sampled term
    
    Expected error: O(λ²t²/N)
    
    Advantages:
    - Gate count independent of number of terms
    - Better for sparse Hamiltonians
    - Unbiased estimator
    
    Parameters
    ----------
    hamiltonian_terms : list
        List of Hamiltonian term matrices
    initial_state : array
        Initial state vector
    time : float
        Total evolution time
    n_samples : int
        Number of random samples (N)
    seed : int, optional
        Random seed for reproducibility
    
    Returns
    -------
    SimulationResult
        Simulation result with qDRIFT statistics
    """
    rng = np.random.default_rng(seed)
    state = initial_state.copy()
    
    # Compute norms and total norm
    norms = np.array([np.linalg.norm(H, ord=2) for H in hamiltonian_terms])
    lambda_total = np.sum(norms)
    
    # Sampling probabilities
    probabilities = norms / lambda_total
    
    # Sample and apply terms
    sampled_indices = []
    for _ in range(n_samples):
        # Sample term index
        idx = rng.choice(len(hamiltonian_terms), p=probabilities)
        sampled_indices.append(idx)
        
        # Apply evolution with scaled time
        H_term = hamiltonian_terms[idx]
        dt_scaled = time * lambda_total / n_samples
        U = _matrix_exponential(-1j * H_term * dt_scaled)
        state = U @ state
    
    # Error estimate: O(λ²t²/N)
    error_estimate = float((lambda_total * time)**2 / n_samples)
    
    # Statistics on sampling
    unique_terms = len(set(sampled_indices))
    
    return SimulationResult(
        final_state=state,
        method="qdrift",
        total_time=time,
        n_steps=n_samples,
        gate_count=n_samples,
        error_estimate=error_estimate,
        metadata={
            "lambda_total": float(lambda_total),
            "n_terms": len(hamiltonian_terms),
            "unique_terms_sampled": unique_terms,
            "sampling_efficiency": unique_terms / len(hamiltonian_terms),
        },
    )


def adaptive_trotter(
    hamiltonian_terms: List[np.ndarray],
    initial_state: np.ndarray,
    time: float,
    target_error: float,
    max_steps: int = 10000,
) -> SimulationResult:
    """
    Adaptive Trotter with automatic step size selection.
    
    Automatically determines number of steps to achieve target error.
    Uses second-order Trotter with error estimation.
    
    Parameters
    ----------
    hamiltonian_terms : list
        List of Hamiltonian term matrices
    initial_state : array
        Initial state vector
    time : float
        Total evolution time
    target_error : float
        Target simulation error
    max_steps : int
        Maximum allowed steps
    
    Returns
    -------
    SimulationResult
        Simulation result meeting error target
    """
    # Estimate required steps for target error
    # For second-order: error ~ (λt)³/n²
    norm_sum = sum(np.linalg.norm(H, ord=2) for H in hamiltonian_terms)
    
    # Solve for n: (λt)³/n² = target_error
    n_required = int(np.ceil(((norm_sum * time)**3 / target_error)**0.5))
    
    if n_required > max_steps:
        warnings.warn(
            f"Required steps {n_required} exceeds max_steps {max_steps}. "
            f"Using max_steps; error may exceed target."
        )
        n_required = max_steps
    
    # Use second-order Trotter
    result = second_order_trotter(
        hamiltonian_terms,
        initial_state,
        time,
        n_required,
    )
    
    result.metadata["adaptive"] = True
    result.metadata["target_error"] = target_error
    result.metadata["achieved_error"] = result.error_estimate
    
    return result


def compare_simulation_methods(
    hamiltonian_terms: List[np.ndarray],
    initial_state: np.ndarray,
    time: float,
    n_steps: int,
    exact_state: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Compare different Hamiltonian simulation methods.
    
    Parameters
    ----------
    hamiltonian_terms : list
        List of Hamiltonian term matrices
    initial_state : array
        Initial state vector
    time : float
        Total evolution time
    n_steps : int
        Number of steps for Trotter methods
    exact_state : array, optional
        Exact evolved state for comparison
    
    Returns
    -------
    dict
        Comparison results for all methods
    """
    results = {}
    
    # First-order Trotter
    result_1st = first_order_trotter(hamiltonian_terms, initial_state, time, n_steps)
    results["first_order"] = result_1st.to_dict()
    
    # Second-order Trotter
    result_2nd = second_order_trotter(hamiltonian_terms, initial_state, time, n_steps)
    results["second_order"] = result_2nd.to_dict()
    
    # Fourth-order Trotter
    result_4th = fourth_order_trotter(hamiltonian_terms, initial_state, time, n_steps)
    results["fourth_order"] = result_4th.to_dict()
    
    # qDRIFT with same total gate count as first-order
    result_qdrift = qdrift_simulation(
        hamiltonian_terms, initial_state, time, n_samples=len(hamiltonian_terms) * n_steps
    )
    results["qdrift"] = result_qdrift.to_dict()
    
    # Compare to exact if provided
    if exact_state is not None:
        for method, result_obj in [
            ("first_order", result_1st),
            ("second_order", result_2nd),
            ("fourth_order", result_4th),
            ("qdrift", result_qdrift),
        ]:
            # Fidelity: |⟨ψ_exact|ψ_sim⟩|²
            overlap = np.abs(np.vdot(exact_state, result_obj.final_state))**2
            results[method]["fidelity"] = float(overlap)
            results[method]["infidelity"] = float(1 - overlap)
    
    return results


def _matrix_exponential(A: np.ndarray) -> np.ndarray:
    """
    Compute matrix exponential e^A.
    
    Uses scipy for efficiency and numerical stability.
    """
    from scipy.linalg import expm
    return expm(A)


def gauge_theory_trotter_terms(
    plaquette_coupling: float,
    transverse_field: float,
    n_plaquettes: int,
) -> List[np.ndarray]:
    """
    Construct Hamiltonian terms for Z2 gauge theory Trotter decomposition.
    
    Separates plaquette terms and link terms for efficient simulation.
    
    Parameters
    ----------
    plaquette_coupling : float
        Plaquette coupling strength
    transverse_field : float
        Transverse field strength
    n_plaquettes : int
        Number of plaquettes
    
    Returns
    -------
    list
        List of Hamiltonian term matrices
    """
    from ..models.z2_plaquette import (
        open_plaquette_chain_layout,
        pauli_label,
    )
    
    layout = open_plaquette_chain_layout(n_plaquettes)
    n_qubits = layout.n_qubits
    dim = 1 << n_qubits
    
    terms = []
    
    # Plaquette terms (each is a separate term for Trotter)
    for plaquette in layout.plaquettes:
        H_plaq = np.zeros((dim, dim), dtype=complex)
        for state in range(dim):
            parity = 1
            for link in plaquette:
                if state & (1 << link):
                    parity *= -1
            H_plaq[state, state] = -plaquette_coupling * parity
        terms.append(H_plaq)
    
    # Link terms (each is a separate term)
    for link in range(n_qubits):
        H_link = np.zeros((dim, dim), dtype=complex)
        for state in range(dim):
            flipped = state ^ (1 << link)
            H_link[flipped, state] = -transverse_field
        terms.append(H_link)
    
    return terms


# Made with Bob