"""
Classical Shadow Tomography for Efficient State Characterization

Mathematical Framework
----------------------
Classical shadows provide an efficient method for predicting many properties
of a quantum state with exponentially fewer measurements than full tomography.

1. Shadow Protocol:
   - Apply random Clifford unitary U
   - Measure in computational basis: outcome b
   - Store classical snapshot: (U, b)
   - Invert: |ψ̂⟩ = U† (3|b⟩⟨b| - I) U

2. Shadow Estimator:
   For observable O, estimate ⟨O⟩ using N snapshots:
   ⟨O⟩ ≈ (1/N) Σᵢ Tr(O |ψ̂ᵢ⟩⟨ψ̂ᵢ|)

3. Sample Complexity:
   For k observables with bounded norm:
   N = O(log(k) max_i ||Oᵢ||²_shadow / ε²)
   
   Exponentially better than standard tomography: O(2ⁿ) → O(log k)

4. Shadow Norm:
   ||O||²_shadow = Tr(O†O) for Pauli measurements
   Determines sample complexity

Physics Applications
--------------------
For gauge theories:
- Measure plaquette operators efficiently
- Characterize entanglement structure
- Verify gauge invariance
- Compute Wilson loops

Advantages over full tomography:
- Exponentially fewer measurements
- Works for large systems
- Predicts many observables simultaneously

Claim Boundary Compliance
-------------------------
Shadow tomography is a measurement technique for quantum state characterization.
It provides efficient estimation of observables but does not change the physics
or constitute proofs of Millennium Prize problems. All estimates have
well-defined statistical errors.

References
----------
- Huang et al. (2020). Predicting many properties of a quantum system from very few measurements
- Hadfield et al. (2022). Measurements of quantum Hamiltonians with locally-biased classical shadows
- Aaronson (2018). Shadow tomography of quantum states
- Elben et al. (2020). Mixed-state entanglement from local randomized measurements
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass
import warnings


@dataclass
class ShadowResult:
    """Result of shadow tomography."""
    
    observable_estimates: Dict[str, float]
    """Estimated expectation values"""
    
    observable_errors: Dict[str, float]
    """Statistical errors on estimates"""
    
    n_snapshots: int
    """Number of classical snapshots used"""
    
    n_qubits: int
    """Number of qubits"""
    
    method: str
    """Shadow method used"""
    
    metadata: Dict[str, Any]
    """Additional information"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "observable_estimates": {k: float(v) for k, v in self.observable_estimates.items()},
            "observable_errors": {k: float(v) for k, v in self.observable_errors.items()},
            "n_snapshots": self.n_snapshots,
            "n_qubits": self.n_qubits,
            "method": self.method,
            "metadata": self.metadata,
        }


def classical_shadow_pauli(
    state: np.ndarray,
    observables: Dict[str, np.ndarray],
    n_snapshots: int,
    seed: Optional[int] = None,
) -> ShadowResult:
    """
    Classical shadow tomography using random Pauli measurements.
    
    Mathematical Framework
    ----------------------
    For each snapshot:
    1. Choose random Pauli basis for each qubit: X, Y, or Z
    2. Measure in that basis
    3. Reconstruct local density matrix
    4. Estimate observables
    
    Sample complexity: N = O(3ⁿ ||O||²_shadow / ε²)
    where ||O||²_shadow = Tr(O†O) for Pauli observables
    
    Parameters
    ----------
    state : array
        Quantum state vector
    observables : dict
        Dictionary of {name: operator_matrix}
    n_snapshots : int
        Number of classical snapshots
    seed : int, optional
        Random seed
    
    Returns
    -------
    ShadowResult
        Shadow tomography estimates
    """
    rng = np.random.default_rng(seed)
    n_qubits = int(np.log2(len(state)))
    
    # Store snapshots
    snapshots = []
    
    for _ in range(n_snapshots):
        # Random Pauli basis for each qubit
        bases = rng.choice(['X', 'Y', 'Z'], size=n_qubits)
        
        # Rotate state to measurement basis
        rotated_state = state.copy()
        for qubit, basis in enumerate(bases):
            if basis == 'X':
                # Rotate Z → X (Hadamard)
                rotated_state = _apply_hadamard(rotated_state, qubit, n_qubits)
            elif basis == 'Y':
                # Rotate Z → Y (S†H)
                rotated_state = _apply_s_dagger(rotated_state, qubit, n_qubits)
                rotated_state = _apply_hadamard(rotated_state, qubit, n_qubits)
        
        # Measure in computational basis
        probabilities = np.abs(rotated_state)**2
        outcome = rng.choice(len(probabilities), p=probabilities)
        
        # Store snapshot
        snapshots.append((bases, outcome))
    
    # Estimate observables
    estimates = {}
    errors = {}
    
    for obs_name, obs_matrix in observables.items():
        # Compute estimate from snapshots
        values = []
        for bases, outcome in snapshots:
            # Reconstruct local state
            reconstructed = _reconstruct_from_snapshot(bases, outcome, n_qubits)
            
            # Compute expectation value
            value = np.real(np.trace(obs_matrix @ reconstructed))
            values.append(value)
        
        # Mean and standard error
        estimates[obs_name] = float(np.mean(values))
        errors[obs_name] = float(np.std(values) / np.sqrt(n_snapshots))
    
    return ShadowResult(
        observable_estimates=estimates,
        observable_errors=errors,
        n_snapshots=n_snapshots,
        n_qubits=n_qubits,
        method="pauli_shadow",
        metadata={
            "bases_used": ["X", "Y", "Z"],
            "n_observables": len(observables),
        },
    )


def classical_shadow_clifford(
    state: np.ndarray,
    observables: Dict[str, np.ndarray],
    n_snapshots: int,
    seed: Optional[int] = None,
) -> ShadowResult:
    """
    Classical shadow tomography using random Clifford unitaries.
    
    Mathematical Framework
    ----------------------
    For each snapshot:
    1. Apply random Clifford unitary U
    2. Measure in computational basis: outcome b
    3. Invert: ρ̂ = U† (2ⁿ|b⟩⟨b| - I) U / (2ⁿ - 1)
    4. Estimate: ⟨O⟩ ≈ Tr(O ρ̂)
    
    Better sample complexity than Pauli for some observables.
    
    Parameters
    ----------
    state : array
        Quantum state vector
    observables : dict
        Dictionary of {name: operator_matrix}
    n_snapshots : int
        Number of classical snapshots
    seed : int, optional
        Random seed
    
    Returns
    -------
    ShadowResult
        Shadow tomography estimates
    """
    rng = np.random.default_rng(seed)
    n_qubits = int(np.log2(len(state)))
    dim = 2**n_qubits
    
    # For simplicity, use random Pauli measurements as proxy for Clifford
    # Full implementation would sample from Clifford group
    snapshots = []
    
    for _ in range(n_snapshots):
        # Apply random Clifford (simplified: random Pauli rotations)
        rotated_state = state.copy()
        
        # Random single-qubit Cliffords
        for qubit in range(n_qubits):
            gate = rng.choice(['I', 'H', 'S', 'HS'])
            if gate == 'H':
                rotated_state = _apply_hadamard(rotated_state, qubit, n_qubits)
            elif gate == 'S':
                rotated_state = _apply_s(rotated_state, qubit, n_qubits)
            elif gate == 'HS':
                rotated_state = _apply_hadamard(rotated_state, qubit, n_qubits)
                rotated_state = _apply_s(rotated_state, qubit, n_qubits)
        
        # Measure
        probabilities = np.abs(rotated_state)**2
        outcome = rng.choice(len(probabilities), p=probabilities)
        
        snapshots.append(outcome)
    
    # Estimate observables
    estimates = {}
    errors = {}
    
    for obs_name, obs_matrix in observables.items():
        values = []
        for outcome in snapshots:
            # Reconstruct density matrix (simplified)
            # Full: ρ̂ = U† (2ⁿ|b⟩⟨b| - I) U / (2ⁿ - 1)
            rho_reconstructed = np.zeros((dim, dim), dtype=complex)
            rho_reconstructed[outcome, outcome] = dim
            rho_reconstructed -= np.eye(dim)
            rho_reconstructed /= (dim - 1)
            
            # Compute expectation
            value = np.real(np.trace(obs_matrix @ rho_reconstructed))
            values.append(value)
        
        estimates[obs_name] = float(np.mean(values))
        errors[obs_name] = float(np.std(values) / np.sqrt(n_snapshots))
    
    return ShadowResult(
        observable_estimates=estimates,
        observable_errors=errors,
        n_snapshots=n_snapshots,
        n_qubits=n_qubits,
        method="clifford_shadow",
        metadata={
            "clifford_group": "single_qubit_cliffords",
            "n_observables": len(observables),
        },
    )


def adaptive_shadow_tomography(
    state: np.ndarray,
    observables: Dict[str, np.ndarray],
    target_error: float,
    max_snapshots: int = 10000,
    seed: Optional[int] = None,
) -> ShadowResult:
    """
    Adaptive shadow tomography with automatic sample size selection.
    
    Automatically determines number of snapshots to achieve target error.
    
    Parameters
    ----------
    state : array
        Quantum state vector
    observables : dict
        Dictionary of observables
    target_error : float
        Target statistical error
    max_snapshots : int
        Maximum allowed snapshots
    seed : int, optional
        Random seed
    
    Returns
    -------
    ShadowResult
        Shadow estimates meeting error target
    """
    # Start with initial estimate
    n_initial = 100
    result = classical_shadow_pauli(state, observables, n_initial, seed=seed)
    
    # Check if errors meet target
    max_error = max(result.observable_errors.values())
    
    if max_error <= target_error:
        # Already met target with initial snapshots
        result.metadata["adaptive"] = True
        result.metadata["target_error"] = target_error
        result.metadata["n_initial"] = n_initial
        return result
    
    # Estimate required snapshots: error ~ 1/√N
    n_required = int(np.ceil(n_initial * (max_error / target_error)**2))
    
    if n_required > max_snapshots:
        warnings.warn(
            f"Required snapshots {n_required} exceeds max {max_snapshots}. "
            f"Using max; errors may exceed target."
        )
        n_required = max_snapshots
    
    # Run with required snapshots
    result = classical_shadow_pauli(state, observables, n_required, seed=seed)
    result.metadata["adaptive"] = True
    result.metadata["target_error"] = target_error
    result.metadata["n_initial"] = n_initial
    result.metadata["n_required"] = n_required
    
    return result


def shadow_norm(observable: np.ndarray) -> float:
    """
    Compute shadow norm of an observable.
    
    Mathematical Framework
    ----------------------
    For Pauli measurements:
    ||O||²_shadow = Tr(O†O)
    
    This determines sample complexity for shadow tomography.
    
    Parameters
    ----------
    observable : array
        Observable matrix
    
    Returns
    -------
    float
        Shadow norm
    """
    return float(np.real(np.trace(observable.conj().T @ observable)))


def estimate_sample_complexity(
    observables: Dict[str, np.ndarray],
    target_error: float,
    confidence: float = 0.95,
) -> Dict[str, Any]:
    """
    Estimate sample complexity for shadow tomography.
    
    Parameters
    ----------
    observables : dict
        Dictionary of observables
    target_error : float
        Target error per observable
    confidence : float
        Confidence level
    
    Returns
    -------
    dict
        Sample complexity estimates
    """
    # Compute shadow norms
    norms = {name: shadow_norm(obs) for name, obs in observables.items()}
    
    # Sample complexity: N ~ ||O||²_shadow / ε²
    # Include log(k) factor for k observables
    k = len(observables)
    log_factor = np.log(k / (1 - confidence))
    
    complexities = {
        name: int(np.ceil(log_factor * norm / target_error**2))
        for name, norm in norms.items()
    }
    
    max_complexity = max(complexities.values())
    
    return {
        "per_observable": complexities,
        "max_complexity": max_complexity,
        "shadow_norms": norms,
        "n_observables": k,
        "target_error": target_error,
        "confidence": confidence,
    }


# Helper functions for gate applications

def _apply_hadamard(state: np.ndarray, qubit: int, n_qubits: int) -> np.ndarray:
    """Apply Hadamard gate."""
    result = state.copy()
    bit = 1 << qubit
    factor = 1.0 / np.sqrt(2.0)
    for idx in range(len(state)):
        if idx & bit:
            continue
        j = idx | bit
        a0 = state[idx]
        a1 = state[j]
        result[idx] = factor * (a0 + a1)
        result[j] = factor * (a0 - a1)
    return result


def _apply_s(state: np.ndarray, qubit: int, n_qubits: int) -> np.ndarray:
    """Apply S gate (phase gate)."""
    result = state.copy()
    bit = 1 << qubit
    for idx in range(len(state)):
        if idx & bit:
            result[idx] *= 1j
    return result


def _apply_s_dagger(state: np.ndarray, qubit: int, n_qubits: int) -> np.ndarray:
    """Apply S† gate."""
    result = state.copy()
    bit = 1 << qubit
    for idx in range(len(state)):
        if idx & bit:
            result[idx] *= -1j
    return result


def _reconstruct_from_snapshot(
    bases: np.ndarray,
    outcome: int,
    n_qubits: int,
) -> np.ndarray:
    """
    Reconstruct density matrix from single snapshot.
    
    For Pauli measurements:
    ρ̂ = ⊗ᵢ (3|bᵢ⟩⟨bᵢ| - I) / 2
    
    where |bᵢ⟩ is the measurement outcome in basis i.
    """
    dim = 2**n_qubits
    
    # Start with first qubit
    bit_value = outcome & 1
    local_rho = np.zeros((2, 2), dtype=complex)
    local_rho[bit_value, bit_value] = 3.0
    local_rho -= np.eye(2)
    local_rho /= 2.0
    
    # Rotate back from measurement basis
    if bases[0] == 'X':
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        local_rho = H @ local_rho @ H.conj().T
    elif bases[0] == 'Y':
        HS = np.array([[1, -1j], [1, 1j]]) / np.sqrt(2)
        local_rho = HS @ local_rho @ HS.conj().T
    
    rho = local_rho
    
    # Tensor product with remaining qubits
    for qubit in range(1, n_qubits):
        bit_value = (outcome >> qubit) & 1
        
        local_rho = np.zeros((2, 2), dtype=complex)
        local_rho[bit_value, bit_value] = 3.0
        local_rho -= np.eye(2)
        local_rho /= 2.0
        
        # Rotate back from measurement basis
        if bases[qubit] == 'X':
            H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
            local_rho = H @ local_rho @ H.conj().T
        elif bases[qubit] == 'Y':
            HS = np.array([[1, -1j], [1, 1j]]) / np.sqrt(2)
            local_rho = HS @ local_rho @ HS.conj().T
        
        rho = np.kron(rho, local_rho)
    
    return rho


def compare_shadow_methods(
    state: np.ndarray,
    observables: Dict[str, np.ndarray],
    n_snapshots: int,
    exact_values: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compare different shadow tomography methods.
    
    Parameters
    ----------
    state : array
        Quantum state
    observables : dict
        Observables to estimate
    n_snapshots : int
        Number of snapshots
    exact_values : dict, optional
        Exact expectation values for comparison
    
    Returns
    -------
    dict
        Comparison results
    """
    results = {}
    
    # Pauli shadow
    result_pauli = classical_shadow_pauli(state, observables, n_snapshots)
    results["pauli"] = result_pauli.to_dict()
    
    # Clifford shadow
    result_clifford = classical_shadow_clifford(state, observables, n_snapshots)
    results["clifford"] = result_clifford.to_dict()
    
    # Compare to exact if provided
    if exact_values is not None:
        for method, result_obj in [("pauli", result_pauli), ("clifford", result_clifford)]:
            errors = {}
            for obs_name in observables:
                if obs_name in exact_values:
                    estimate = result_obj.observable_estimates[obs_name]
                    exact = exact_values[obs_name]
                    errors[obs_name] = abs(estimate - exact)
            results[method]["exact_errors"] = errors
    
    # Sample complexity estimates
    complexity = estimate_sample_complexity(observables, target_error=0.01)
    results["sample_complexity"] = complexity
    
    return results


# Made with Bob