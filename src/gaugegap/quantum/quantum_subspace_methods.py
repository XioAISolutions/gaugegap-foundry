"""
Quantum Subspace Methods for Variational Algorithms

Mathematical Framework
----------------------
Quantum subspace methods reduce the effective problem size by:

1. Quantum Subspace Expansion (QSE):
   - Prepare reference state |ψ₀⟩
   - Generate subspace: {|ψ₀⟩, Ô₁|ψ₀⟩, Ô₂|ψ₀⟩, ...}
   - Diagonalize H in this subspace
   - Ground state: |ψ_gs⟩ = Σᵢ cᵢ Ôᵢ|ψ₀⟩

2. Quantum Krylov Methods:
   - Build Krylov subspace: K_n = span{|ψ₀⟩, H|ψ₀⟩, H²|ψ₀⟩, ...}
   - Use Lanczos algorithm for efficient construction
   - Exponential convergence for gapped systems

3. Subspace-Search VQE (SSVQE):
   - Optimize multiple states simultaneously
   - Orthogonalize to find excited states
   - Better than sequential optimization

4. Contracted Quantum Eigensolver (CQE):
   - Use 2-RDM (reduced density matrix) constraints
   - Variational 2-RDM method on quantum computer
   - Polynomial scaling for certain systems

Advantages
----------
- Reduced circuit depth compared to full VQE
- Better convergence properties
- Access to excited states
- Mitigation of barren plateaus

Physics Applications
--------------------
For gauge theories:
- Low-energy spectrum of lattice Hamiltonians
- Excited states (particle excitations)
- Thermal states via imaginary time evolution
- String breaking dynamics

Claim Boundary Compliance
-------------------------
These are variational quantum algorithms for finite systems.
They provide efficient methods for quantum simulation but do not
constitute proofs of Millennium Prize problems. All results are
for finite lattices with specified parameters.

References
----------
- McClean et al. (2017). Hybrid quantum-classical hierarchy for mitigation of decoherence
- Takeshita et al. (2020). Increasing the representation accuracy of quantum simulations
- Parrish et al. (2019). Quantum computation of electronic transitions using a variational quantum eigensolver
- Motta et al. (2020). Determining eigenstates and thermal states on a quantum computer
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass
from scipy.linalg import eigh, svd


@dataclass
class SubspaceResult:
    """Result of quantum subspace method."""
    
    energies: np.ndarray
    """Eigenvalues in subspace"""
    
    coefficients: np.ndarray
    """Expansion coefficients"""
    
    subspace_dimension: int
    """Dimension of subspace"""
    
    method: str
    """Subspace method used"""
    
    convergence_error: float
    """Estimated convergence error"""
    
    metadata: Dict[str, Any]
    """Additional information"""
    
    def ground_state_energy(self) -> float:
        """Return ground state energy."""
        return float(self.energies[0])
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "energies": self.energies.tolist(),
            "ground_state_energy": self.ground_state_energy(),
            "subspace_dimension": self.subspace_dimension,
            "method": self.method,
            "convergence_error": float(self.convergence_error),
            "metadata": self.metadata,
        }


def quantum_subspace_expansion(
    reference_state: np.ndarray,
    hamiltonian: np.ndarray,
    operators: List[np.ndarray],
    n_states: int = 1,
) -> SubspaceResult:
    """
    Quantum Subspace Expansion (QSE).
    
    Mathematical Framework
    ----------------------
    1. Reference state: |ψ₀⟩ (e.g., from VQE)
    2. Subspace basis: {|ψ₀⟩, Ô₁|ψ₀⟩, Ô₂|ψ₀⟩, ...}
    3. Build subspace Hamiltonian: H_ij = ⟨ψᵢ|H|ψⱼ⟩
    4. Diagonalize to find low-energy states
    
    Advantages:
    - Post-VQE correction without additional optimization
    - Access to excited states
    - Systematic improvement with more operators
    
    Parameters
    ----------
    reference_state : array
        Reference state vector (e.g., VQE result)
    hamiltonian : array
        Hamiltonian matrix
    operators : list
        List of operators to generate subspace
    n_states : int
        Number of states to compute
    
    Returns
    -------
    SubspaceResult
        Subspace eigenvalues and eigenvectors
    """
    # Build subspace basis
    basis_states = [reference_state]
    
    for op in operators:
        # Apply operator to reference
        new_state = op @ reference_state
        
        # Normalize
        norm = np.linalg.norm(new_state)
        if norm > 1e-10:
            new_state = new_state / norm
            basis_states.append(new_state)
    
    subspace_dim = len(basis_states)
    
    # Build subspace Hamiltonian and overlap matrices
    H_sub = np.zeros((subspace_dim, subspace_dim), dtype=complex)
    S_sub = np.zeros((subspace_dim, subspace_dim), dtype=complex)
    
    for i, state_i in enumerate(basis_states):
        for j, state_j in enumerate(basis_states):
            H_sub[i, j] = np.vdot(state_i, hamiltonian @ state_j)
            S_sub[i, j] = np.vdot(state_i, state_j)
    
    # Solve generalized eigenvalue problem: H c = E S c
    # For orthonormal basis, S ≈ I
    eigenvalues, eigenvectors = eigh(H_sub, S_sub)
    
    # Sort by energy
    idx = np.argsort(eigenvalues.real)
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Estimate convergence error (difference from reference)
    ref_energy = np.real(np.vdot(reference_state, hamiltonian @ reference_state))
    convergence_error = abs(eigenvalues[0].real - ref_energy)
    
    return SubspaceResult(
        energies=eigenvalues[:n_states].real,
        coefficients=eigenvectors[:, :n_states],
        subspace_dimension=subspace_dim,
        method="quantum_subspace_expansion",
        convergence_error=float(convergence_error),
        metadata={
            "n_operators": len(operators),
            "reference_energy": float(ref_energy),
        },
    )


def quantum_krylov_method(
    initial_state: np.ndarray,
    hamiltonian: np.ndarray,
    n_iterations: int = 10,
    n_states: int = 1,
) -> SubspaceResult:
    """
    Quantum Krylov subspace method.
    
    Mathematical Framework
    ----------------------
    Build Krylov subspace: K_n = span{|ψ₀⟩, H|ψ₀⟩, H²|ψ₀⟩, ..., Hⁿ⁻¹|ψ₀⟩}
    
    Use Lanczos algorithm:
    1. Start with |v₁⟩ = |ψ₀⟩
    2. For j = 1 to n:
       - |w⟩ = H|vⱼ⟩
       - αⱼ = ⟨vⱼ|w⟩
       - |w⟩ = |w⟩ - αⱼ|vⱼ⟩ - βⱼ₋₁|vⱼ₋₁⟩
       - βⱼ = ||w||
       - |vⱼ₊₁⟩ = |w⟩/βⱼ
    3. Diagonalize tridiagonal matrix
    
    Advantages:
    - Exponential convergence for gapped systems
    - Efficient for sparse Hamiltonians
    - Natural for time evolution
    
    Parameters
    ----------
    initial_state : array
        Initial state vector
    hamiltonian : array
        Hamiltonian matrix
    n_iterations : int
        Number of Krylov iterations
    n_states : int
        Number of states to compute
    
    Returns
    -------
    SubspaceResult
        Krylov subspace eigenvalues
    """
    n_dim = len(initial_state)
    
    # Lanczos vectors
    V = np.zeros((n_dim, n_iterations), dtype=complex)
    V[:, 0] = initial_state / np.linalg.norm(initial_state)
    
    # Tridiagonal matrix elements
    alpha = np.zeros(n_iterations)
    beta = np.zeros(n_iterations - 1)
    
    for j in range(n_iterations):
        # Apply Hamiltonian
        w = hamiltonian @ V[:, j]
        
        # Compute diagonal element
        alpha[j] = np.real(np.vdot(V[:, j], w))
        
        # Orthogonalize
        w = w - alpha[j] * V[:, j]
        if j > 0:
            w = w - beta[j-1] * V[:, j-1]
        
        # Compute off-diagonal element
        if j < n_iterations - 1:
            beta[j] = np.linalg.norm(w)
            
            if beta[j] < 1e-10:
                # Krylov subspace exhausted
                n_iterations = j + 1
                break
            
            V[:, j+1] = w / beta[j]
    
    # Build tridiagonal Hamiltonian
    H_krylov = np.diag(alpha[:n_iterations])
    if n_iterations > 1:
        H_krylov += np.diag(beta[:n_iterations-1], k=1)
        H_krylov += np.diag(beta[:n_iterations-1], k=-1)
    
    # Diagonalize
    eigenvalues, eigenvectors = eigh(H_krylov)
    
    # Estimate convergence (Ritz residual)
    if n_iterations > 1:
        convergence_error = abs(beta[-1] * eigenvectors[-1, 0])
    else:
        convergence_error = 0.0
    
    return SubspaceResult(
        energies=eigenvalues[:n_states],
        coefficients=eigenvectors[:, :n_states],
        subspace_dimension=n_iterations,
        method="quantum_krylov",
        convergence_error=float(convergence_error),
        metadata={
            "n_iterations": n_iterations,
            "krylov_dimension": n_iterations,
        },
    )


def subspace_search_vqe(
    hamiltonian: np.ndarray,
    ansatz_function: Callable,
    n_parameters: int,
    n_states: int = 2,
    n_samples: int = 100,
    seed: Optional[int] = None,
) -> SubspaceResult:
    """
    Subspace-Search VQE (SSVQE) for multiple states.
    
    Mathematical Framework
    ----------------------
    Optimize multiple orthogonal states simultaneously:
    
    Cost = Σₖ wₖ ⟨ψₖ|H|ψₖ⟩ + λ Σₖ<ₗ |⟨ψₖ|ψₗ⟩|²
    
    where wₖ are weights and λ enforces orthogonality.
    
    Advantages:
    - Better than sequential optimization
    - Natural orthogonality constraints
    - Access to excited states
    
    Parameters
    ----------
    hamiltonian : array
        Hamiltonian matrix
    ansatz_function : callable
        Function that takes parameters and returns state
    n_parameters : int
        Number of parameters per state
    n_states : int
        Number of states to optimize
    n_samples : int
        Number of optimization samples
    seed : int, optional
        Random seed
    
    Returns
    -------
    SubspaceResult
        Optimized states and energies
    """
    rng = np.random.default_rng(seed)
    
    # Initialize parameters for each state
    best_params = rng.uniform(-np.pi, np.pi, size=(n_states, n_parameters))
    
    def cost_function(params_flat: np.ndarray) -> float:
        """Cost function with orthogonality penalty."""
        params = params_flat.reshape(n_states, n_parameters)
        
        # Generate states
        states = [ansatz_function(params[k]) for k in range(n_states)]
        
        # Energy terms
        energy_cost = 0.0
        for k, state in enumerate(states):
            weight = 1.0  # Could use different weights
            energy = np.real(np.vdot(state, hamiltonian @ state))
            energy_cost += weight * energy
        
        # Orthogonality penalty
        orthog_penalty = 0.0
        penalty_strength = 10.0
        for k in range(n_states):
            for l in range(k+1, n_states):
                overlap = abs(np.vdot(states[k], states[l]))**2
                orthog_penalty += penalty_strength * overlap
        
        return energy_cost + orthog_penalty
    
    # Simple optimization (random search + local refinement)
    best_cost = cost_function(best_params.flatten())
    
    for _ in range(n_samples):
        # Random trial
        trial_params = rng.uniform(-np.pi, np.pi, size=(n_states, n_parameters))
        trial_cost = cost_function(trial_params.flatten())
        
        if trial_cost < best_cost:
            best_params = trial_params
            best_cost = trial_cost
    
    # Local refinement
    step = 0.1
    for _ in range(10):
        improved = False
        for k in range(n_states):
            for i in range(n_parameters):
                for sign in [-1, 1]:
                    trial_params = best_params.copy()
                    trial_params[k, i] += sign * step
                    trial_cost = cost_function(trial_params.flatten())
                    
                    if trial_cost < best_cost:
                        best_params = trial_params
                        best_cost = trial_cost
                        improved = True
        
        if not improved:
            step *= 0.5
    
    # Extract final states and energies
    final_states = [ansatz_function(best_params[k]) for k in range(n_states)]
    energies = np.array([
        np.real(np.vdot(state, hamiltonian @ state))
        for state in final_states
    ])
    
    # Check orthogonality
    overlaps = np.zeros((n_states, n_states))
    for k in range(n_states):
        for l in range(n_states):
            overlaps[k, l] = abs(np.vdot(final_states[k], final_states[l]))**2
    
    return SubspaceResult(
        energies=energies,
        coefficients=np.eye(n_states),  # States are basis vectors
        subspace_dimension=n_states,
        method="subspace_search_vqe",
        convergence_error=float(np.max(overlaps - np.eye(n_states))),
        metadata={
            "n_samples": n_samples,
            "final_cost": float(best_cost),
            "orthogonality_matrix": overlaps.tolist(),
        },
    )


def quantum_imaginary_time_evolution(
    initial_state: np.ndarray,
    hamiltonian: np.ndarray,
    beta: float,
    n_steps: int = 10,
) -> SubspaceResult:
    """
    Quantum imaginary time evolution for ground state preparation.
    
    Mathematical Framework
    ----------------------
    Imaginary time evolution: |ψ(β)⟩ = e^(-βH)|ψ₀⟩ / ||e^(-βH)|ψ₀⟩||
    
    As β → ∞, |ψ(β)⟩ → |ψ_gs⟩ (ground state)
    
    Implementation via Trotter:
    e^(-βH) ≈ [e^(-δβH)]^n where δβ = β/n
    
    Parameters
    ----------
    initial_state : array
        Initial state vector
    hamiltonian : array
        Hamiltonian matrix
    beta : float
        Imaginary time
    n_steps : int
        Number of Trotter steps
    
    Returns
    -------
    SubspaceResult
        Ground state approximation
    """
    state = initial_state.copy()
    delta_beta = beta / n_steps
    
    energies_history = []
    
    for step in range(n_steps):
        # Apply e^(-δβH)
        from scipy.linalg import expm
        U = expm(-delta_beta * hamiltonian)
        state = U @ state
        
        # Normalize
        norm = np.linalg.norm(state)
        state = state / norm
        
        # Track energy
        energy = np.real(np.vdot(state, hamiltonian @ state))
        energies_history.append(energy)
    
    final_energy = energies_history[-1]
    
    # Estimate convergence from energy change
    if len(energies_history) > 1:
        convergence_error = abs(energies_history[-1] - energies_history[-2])
    else:
        convergence_error = 0.0
    
    return SubspaceResult(
        energies=np.array([final_energy]),
        coefficients=state.reshape(-1, 1),
        subspace_dimension=1,
        method="quantum_imaginary_time_evolution",
        convergence_error=float(convergence_error),
        metadata={
            "beta": beta,
            "n_steps": n_steps,
            "energy_history": energies_history,
        },
    )


def compare_subspace_methods(
    hamiltonian: np.ndarray,
    initial_state: np.ndarray,
    operators: Optional[List[np.ndarray]] = None,
    exact_ground_energy: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compare different quantum subspace methods.
    
    Parameters
    ----------
    hamiltonian : array
        Hamiltonian matrix
    initial_state : array
        Initial/reference state
    operators : list, optional
        Operators for QSE
    exact_ground_energy : float, optional
        Exact ground state energy for comparison
    
    Returns
    -------
    dict
        Comparison results
    """
    results = {}
    
    # Quantum Krylov
    result_krylov = quantum_krylov_method(initial_state, hamiltonian, n_iterations=10)
    results["krylov"] = result_krylov.to_dict()
    
    # QSE if operators provided
    if operators is not None:
        result_qse = quantum_subspace_expansion(
            initial_state, hamiltonian, operators
        )
        results["qse"] = result_qse.to_dict()
    
    # Imaginary time evolution
    result_ite = quantum_imaginary_time_evolution(
        initial_state, hamiltonian, beta=5.0, n_steps=20
    )
    results["imaginary_time"] = result_ite.to_dict()
    
    # Compare to exact if provided
    if exact_ground_energy is not None:
        for method in results:
            gs_energy = results[method]["ground_state_energy"]
            results[method]["error_vs_exact"] = abs(gs_energy - exact_ground_energy)
    
    return results


# Made with Bob