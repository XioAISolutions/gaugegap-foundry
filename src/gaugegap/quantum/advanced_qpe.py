"""
Advanced Quantum Phase Estimation for Gauge Theories

Mathematical Framework
----------------------
Quantum Phase Estimation (QPE) finds eigenvalues of unitary operators:

Given U|ψ⟩ = e^(iφ)|ψ⟩, estimate φ to n bits of precision.

Standard QPE:
1. Prepare |0⟩^⊗n ⊗ |ψ⟩
2. Apply Hadamards to ancilla qubits
3. Apply controlled-U^(2^k) operations
4. Inverse QFT on ancilla
5. Measure ancilla → binary representation of φ

For Hamiltonian H with U = e^(-iHt):
e^(-iHt)|ψ⟩ = e^(-iEt)|ψ⟩
→ Estimate E from phase φ = Et

Advanced Techniques
-------------------

1. Iterative QPE (IQPE):
   - Use single ancilla qubit
   - Iterate to build phase estimate
   - Reduced qubit overhead: n+1 instead of 2n
   - Bayesian inference for optimal measurements

2. Variational Quantum Phase Estimation (VQPE):
   - No ancilla qubits needed
   - Measure ⟨ψ|U|ψ⟩ for various angles
   - Classical optimization to extract phase
   - NISQ-friendly

3. Quantum Signal Processing (QSP):
   - Implement polynomial transformations of phase
   - Optimal query complexity
   - Heralded phase estimation
   - Amplitude amplification integration

4. Adaptive Phase Estimation:
   - Dynamically adjust measurement basis
   - Use previous results to inform next measurement
   - Optimal information gain
   - Faster convergence

Physics Applications
--------------------
For gauge theories:
- Energy spectrum of lattice Hamiltonians
- Mass gaps (E₁ - E₀)
- Excitation energies
- Thermal state preparation
- Real-time evolution phases

Advantages over VQE:
- Exponentially better scaling for precision
- No barren plateaus
- Deterministic (not variational)
- Access to full spectrum

Claim Boundary Compliance
-------------------------
QPE is a quantum algorithm for eigenvalue estimation on finite systems.
It provides spectral information for benchmarking but does not constitute
proofs of Millennium Prize problems. All results are for finite lattices
with specified parameters.

References
----------
- Kitaev (1995). Quantum measurements and the Abelian Stabilizer Problem
- Cleve et al. (1998). Quantum algorithms revisited
- Dobšíček et al. (2007). Arbitrary accuracy iterative quantum phase estimation
- Parrish et al. (2019). A Jacobi diagonalization and Anderson acceleration algorithm
- Martyn et al. (2021). Grand unification of quantum algorithms
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass
from scipy.optimize import minimize


@dataclass
class QPEResult:
    """Result of quantum phase estimation."""
    
    phase: float
    """Estimated phase φ"""
    
    energy: float
    """Estimated energy E = φ/t"""
    
    precision: int
    """Number of bits of precision"""
    
    success_probability: float
    """Probability of correct estimation"""
    
    n_measurements: int
    """Number of measurements used"""
    
    method: str
    """QPE method used"""
    
    metadata: Dict[str, Any]
    """Additional information"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "phase": float(self.phase),
            "energy": float(self.energy),
            "precision": self.precision,
            "success_probability": float(self.success_probability),
            "n_measurements": self.n_measurements,
            "method": self.method,
            "metadata": self.metadata,
        }


def standard_qpe(
    unitary: np.ndarray,
    eigenstate: np.ndarray,
    n_precision_bits: int = 8,
    time: float = 1.0,
) -> QPEResult:
    """
    Standard quantum phase estimation.
    
    Mathematical Framework
    ----------------------
    Circuit:
    |0⟩^⊗n ─H─●───────●─────── QFT† ─ Measure
              │       │
    |ψ⟩ ──────U^(2^0)─U^(2^1)─ ...
    
    Phase encoded in ancilla measurement outcome.
    
    Success probability: ≥ 4/π² ≈ 0.405 for exact eigenstate
    
    Parameters
    ----------
    unitary : array
        Unitary operator U
    eigenstate : array
        Eigenstate |ψ⟩ of U
    n_precision_bits : int
        Number of precision bits (ancilla qubits)
    time : float
        Evolution time (for Hamiltonian)
    
    Returns
    -------
    QPEResult
        Phase estimation result
    """
    # Verify eigenstate
    U_psi = unitary @ eigenstate
    phase_exact = np.angle(np.vdot(eigenstate, U_psi))
    
    # Simulate QPE circuit
    # In full implementation, would construct and execute quantum circuit
    
    # Discretize phase to n bits
    phase_discrete = np.round(phase_exact * 2**n_precision_bits / (2*np.pi))
    phase_estimate = phase_discrete * 2*np.pi / 2**n_precision_bits
    
    # Success probability (simplified)
    # Full calculation involves Fourier analysis
    delta = abs(phase_exact - phase_estimate)
    success_prob = (np.sin(np.pi * delta / (2*np.pi / 2**n_precision_bits)) / 
                    (np.pi * delta / (2*np.pi / 2**n_precision_bits)))**2 if delta > 1e-10 else 1.0
    
    # Convert phase to energy
    energy = phase_estimate / time
    
    # Number of measurements: 2n controlled-U operations + QFT
    n_measurements = 2 * n_precision_bits + n_precision_bits
    
    return QPEResult(
        phase=float(phase_estimate),
        energy=float(energy),
        precision=n_precision_bits,
        success_probability=float(success_prob),
        n_measurements=n_measurements,
        method="standard_qpe",
        metadata={
            "exact_phase": float(phase_exact),
            "discretization_error": float(abs(phase_exact - phase_estimate)),
        },
    )


def iterative_qpe(
    unitary: np.ndarray,
    eigenstate: np.ndarray,
    n_iterations: int = 8,
    time: float = 1.0,
) -> QPEResult:
    """
    Iterative quantum phase estimation (IQPE).
    
    Mathematical Framework
    ----------------------
    Use single ancilla qubit, iterate to build phase estimate:
    
    Iteration k:
    1. Prepare |+⟩ ⊗ |ψ⟩
    2. Apply controlled-U^(2^k)
    3. Rotate ancilla by previous estimate
    4. Measure ancilla
    5. Update phase estimate
    
    Advantages:
    - Only n+1 qubits (vs 2n for standard QPE)
    - Adaptive measurements
    - Bayesian inference possible
    
    Complexity: O(n) measurements for n bits precision
    
    Parameters
    ----------
    unitary : array
        Unitary operator
    eigenstate : array
        Eigenstate
    n_iterations : int
        Number of iterations (precision bits)
    time : float
        Evolution time
    
    Returns
    -------
    QPEResult
        Phase estimation result
    """
    # Exact phase for simulation
    U_psi = unitary @ eigenstate
    phase_exact = np.angle(np.vdot(eigenstate, U_psi))
    
    # Iterative estimation
    phase_estimate = 0.0
    
    for k in range(n_iterations):
        # Power of unitary
        power = 2**k
        U_power = np.linalg.matrix_power(unitary, power)
        
        # Apply to eigenstate
        U_psi_k = U_power @ eigenstate
        
        # Measure phase (simplified)
        phase_k = np.angle(np.vdot(eigenstate, U_psi_k))
        
        # Update estimate (binary search)
        bit_k = 1 if phase_k > 0 else 0
        phase_estimate += bit_k * 2*np.pi / 2**(k+1)
    
    # Wrap to [0, 2π)
    phase_estimate = phase_estimate % (2*np.pi)
    
    # Success probability
    error = abs(phase_exact - phase_estimate)
    success_prob = 1.0 - error / (2*np.pi)
    
    energy = phase_estimate / time
    
    return QPEResult(
        phase=float(phase_estimate),
        energy=float(energy),
        precision=n_iterations,
        success_probability=float(max(0.0, success_prob)),
        n_measurements=n_iterations,
        method="iterative_qpe",
        metadata={
            "exact_phase": float(phase_exact),
            "error": float(error),
        },
    )


def variational_qpe(
    unitary: np.ndarray,
    initial_state: np.ndarray,
    n_angles: int = 10,
    time: float = 1.0,
) -> QPEResult:
    """
    Variational quantum phase estimation (VQPE).
    
    Mathematical Framework
    ----------------------
    No ancilla qubits needed. Measure:
    
    f(θ) = Re[⟨ψ|e^(iθ)U|ψ⟩]
    
    For eigenstate with phase φ:
    f(θ) = cos(θ - φ)
    
    Maximum at θ = φ → estimate phase
    
    Advantages:
    - NISQ-friendly (no ancillas)
    - Robust to noise
    - Can use imperfect initial state
    
    Disadvantages:
    - Classical optimization required
    - Polynomial scaling (not exponential)
    
    Parameters
    ----------
    unitary : array
        Unitary operator
    initial_state : array
        Initial state (need not be eigenstate)
    n_angles : int
        Number of angles to sample
    time : float
        Evolution time
    
    Returns
    -------
    QPEResult
        Phase estimation result
    """
    # Sample angles
    angles = np.linspace(0, 2*np.pi, n_angles)
    
    # Measure overlap for each angle
    overlaps = []
    for theta in angles:
        # Compute ⟨ψ|e^(iθ)U|ψ⟩
        U_psi = unitary @ initial_state
        overlap = np.vdot(initial_state, np.exp(1j * theta) * U_psi)
        overlaps.append(np.real(overlap))
    
    overlaps = np.array(overlaps)
    
    # Find maximum
    max_idx = np.argmax(overlaps)
    phase_estimate = angles[max_idx]
    
    # Refine with optimization
    def objective(theta):
        U_psi = unitary @ initial_state
        overlap = np.vdot(initial_state, np.exp(1j * theta[0]) * U_psi)
        return -np.real(overlap)  # Minimize negative
    
    result = minimize(objective, [phase_estimate], method='BFGS')
    phase_estimate = result.x[0] % (2*np.pi)
    
    # Success probability (overlap with eigenstate)
    U_psi = unitary @ initial_state
    exact_phase = np.angle(np.vdot(initial_state, U_psi))
    success_prob = abs(np.vdot(initial_state, U_psi / np.linalg.norm(U_psi)))**2
    
    energy = phase_estimate / time
    
    return QPEResult(
        phase=float(phase_estimate),
        energy=float(energy),
        precision=int(np.log2(n_angles)),
        success_probability=float(success_prob),
        n_measurements=n_angles,
        method="variational_qpe",
        metadata={
            "n_angles_sampled": n_angles,
            "max_overlap": float(np.max(overlaps)),
        },
    )


def adaptive_qpe(
    unitary: np.ndarray,
    eigenstate: np.ndarray,
    target_precision: float = 0.01,
    max_measurements: int = 100,
    time: float = 1.0,
) -> QPEResult:
    """
    Adaptive quantum phase estimation with Bayesian inference.
    
    Mathematical Framework
    ----------------------
    Bayesian approach:
    1. Prior distribution: P(φ) = uniform on [0, 2π)
    2. Measurement outcome: m with probability P(m|φ)
    3. Update: P(φ|m) ∝ P(m|φ) P(φ)
    4. Choose next measurement to maximize information gain
    5. Repeat until uncertainty < target
    
    Information gain: I = H(P(φ)) - E[H(P(φ|m))]
    where H is Shannon entropy
    
    Advantages:
    - Optimal measurement strategy
    - Faster convergence than fixed protocol
    - Handles noise adaptively
    
    Parameters
    ----------
    unitary : array
        Unitary operator
    eigenstate : array
        Eigenstate
    target_precision : float
        Target precision (standard deviation)
    max_measurements : int
        Maximum measurements allowed
    time : float
        Evolution time
    
    Returns
    -------
    QPEResult
        Phase estimation result
    """
    # Exact phase
    U_psi = unitary @ eigenstate
    phase_exact = np.angle(np.vdot(eigenstate, U_psi))
    
    # Bayesian estimation
    # Discretize phase space
    n_grid = 1000
    phases = np.linspace(0, 2*np.pi, n_grid)
    
    # Prior: uniform
    prior = np.ones(n_grid) / n_grid
    posterior = prior.copy()
    
    n_measurements = 0
    current_std = np.pi  # Initial uncertainty
    
    while current_std > target_precision and n_measurements < max_measurements:
        # Choose measurement (simplified: use power of 2)
        power = 2**n_measurements
        
        # Simulate measurement
        U_power = np.linalg.matrix_power(unitary, power)
        U_psi_power = U_power @ eigenstate
        phase_power = np.angle(np.vdot(eigenstate, U_psi_power))
        
        # Measurement outcome (binary)
        outcome = 1 if phase_power > 0 else 0
        
        # Update posterior (simplified)
        # Full implementation would use proper likelihood
        if outcome == 1:
            likelihood = np.cos(phases * power)
        else:
            likelihood = -np.cos(phases * power)
        
        likelihood = np.maximum(likelihood, 0)
        posterior = posterior * likelihood
        posterior = posterior / np.sum(posterior)
        
        # Compute current estimate and uncertainty
        phase_estimate = np.sum(phases * posterior)
        phase_variance = np.sum((phases - phase_estimate)**2 * posterior)
        current_std = np.sqrt(phase_variance)
        
        n_measurements += 1
    
    # Final estimate
    phase_estimate = np.sum(phases * posterior)
    
    # Success probability (from posterior concentration)
    success_prob = 1.0 - current_std / np.pi
    
    energy = phase_estimate / time
    
    return QPEResult(
        phase=float(phase_estimate),
        energy=float(energy),
        precision=int(-np.log2(current_std / (2*np.pi))),
        success_probability=float(max(0.0, success_prob)),
        n_measurements=n_measurements,
        method="adaptive_qpe",
        metadata={
            "exact_phase": float(phase_exact),
            "final_std": float(current_std),
            "target_precision": target_precision,
        },
    )


def qpe_for_hamiltonian(
    hamiltonian: np.ndarray,
    eigenstate: np.ndarray,
    time: float = 1.0,
    method: str = "iterative",
    **kwargs,
) -> QPEResult:
    """
    Quantum phase estimation for Hamiltonian eigenvalue.
    
    Constructs U = e^(-iHt) and applies QPE.
    
    Parameters
    ----------
    hamiltonian : array
        Hamiltonian matrix
    eigenstate : array
        Eigenstate of H
    time : float
        Evolution time
    method : str
        QPE method: standard, iterative, variational, adaptive
    **kwargs
        Method-specific parameters
    
    Returns
    -------
    QPEResult
        Energy estimation result
    """
    # Construct time evolution operator
    from scipy.linalg import expm
    unitary = expm(-1j * hamiltonian * time)
    
    # Apply QPE
    if method == "standard":
        result = standard_qpe(unitary, eigenstate, time=time, **kwargs)
    elif method == "iterative":
        result = iterative_qpe(unitary, eigenstate, time=time, **kwargs)
    elif method == "variational":
        result = variational_qpe(unitary, eigenstate, time=time, **kwargs)
    elif method == "adaptive":
        result = adaptive_qpe(unitary, eigenstate, time=time, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Verify against exact eigenvalue
    exact_energy = np.real(np.vdot(eigenstate, hamiltonian @ eigenstate))
    result.metadata["exact_energy"] = float(exact_energy)
    result.metadata["energy_error"] = float(abs(result.energy - exact_energy))
    
    return result


def compare_qpe_methods(
    hamiltonian: np.ndarray,
    eigenstate: np.ndarray,
    time: float = 1.0,
) -> Dict[str, Any]:
    """
    Compare different QPE methods.
    
    Parameters
    ----------
    hamiltonian : array
        Hamiltonian matrix
    eigenstate : array
        Eigenstate
    time : float
        Evolution time
    
    Returns
    -------
    dict
        Comparison results
    """
    results = {}
    
    # Standard QPE
    result_std = qpe_for_hamiltonian(
        hamiltonian, eigenstate, time, method="standard", n_precision_bits=8
    )
    results["standard"] = result_std.to_dict()
    
    # Iterative QPE
    result_iter = qpe_for_hamiltonian(
        hamiltonian, eigenstate, time, method="iterative", n_iterations=8
    )
    results["iterative"] = result_iter.to_dict()
    
    # Variational QPE
    result_var = qpe_for_hamiltonian(
        hamiltonian, eigenstate, time, method="variational", n_angles=20
    )
    results["variational"] = result_var.to_dict()
    
    # Adaptive QPE
    result_adapt = qpe_for_hamiltonian(
        hamiltonian, eigenstate, time, method="adaptive", target_precision=0.01
    )
    results["adaptive"] = result_adapt.to_dict()
    
    # Summary comparison
    results["comparison"] = {
        "most_precise": min(results.keys(), key=lambda k: results[k]["energy_error"]),
        "fewest_measurements": min(results.keys(), key=lambda k: results[k]["n_measurements"]),
        "highest_success_prob": max(results.keys(), key=lambda k: results[k]["success_probability"]),
    }
    
    return results


# Made with Bob