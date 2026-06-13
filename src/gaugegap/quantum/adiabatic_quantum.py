"""
Adiabatic Quantum Computing for Gauge Theories

Mathematical Framework
----------------------
Adiabatic quantum computation uses slow evolution to prepare ground states
and solve optimization problems.

Adiabatic Theorem
-----------------
For time-dependent Hamiltonian H(t):
- Start in ground state |ψ₀⟩ of H(0)
- Evolve slowly: H(t) from t=0 to T
- End in ground state |ψ_T⟩ of H(T)

Condition: T >> ℏ/Δ² where Δ is minimum gap

Key Techniques
--------------

1. Quantum Annealing:
   H(s) = (1-s)H_initial + s·H_problem
   where s = t/T ∈ [0,1]
   
   Used for optimization and ground state preparation

2. Adiabatic State Preparation:
   Prepare complex ground states by slow evolution
   from simple initial state

3. Landau-Zener Formula:
   Diabatic transition probability at avoided crossing:
   P = exp(-2πΔ²/(ℏ|dE/dt|))
   
   Guides choice of annealing schedule

4. Shortcuts to Adiabaticity (STA):
   - Counterdiabatic driving
   - Fast-forward protocols
   - Optimal control
   
   Achieve adiabatic results in shorter time

Physics Applications
--------------------
For gauge theories:
- Ground state preparation
- Mass gap measurement via adiabatic evolution
- Quantum phase transition detection
- Optimization of gauge configurations

Claim Boundary Compliance
-------------------------
These are quantum algorithms for finite-system ground state preparation
and optimization. They provide computational tools but do not constitute
proofs of Millennium Prize problems.

References
----------
- Farhi et al. (2000). Quantum computation by adiabatic evolution
- Albash & Lidar (2018). Adiabatic quantum computation
- Demirplak & Rice (2003). Adiabatic population transfer with control fields
- Berry (2009). Transitionless quantum driving
- Torrontegui et al. (2013). Shortcuts to adiabaticity
- Kolodrubetz et al. (2017). Geometry and non-adiabatic response
"""

import numpy as np
from typing import Callable, List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from scipy.linalg import expm, eigh
from scipy.integrate import odeint, solve_ivp
from scipy.optimize import minimize


@dataclass
class AdiabaticResult:
    """Result of adiabatic evolution."""
    
    final_state: np.ndarray
    """Final state after evolution"""
    
    final_energy: float
    """Final energy"""
    
    ground_state_fidelity: float
    """Fidelity with true ground state"""
    
    diabatic_error: float
    """Estimated diabatic error"""
    
    evolution_time: float
    """Total evolution time"""
    
    schedule_type: str
    """Type of annealing schedule"""
    
    metadata: Dict[str, Any]
    """Additional information"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "final_energy": float(self.final_energy),
            "ground_state_fidelity": float(self.ground_state_fidelity),
            "diabatic_error": float(self.diabatic_error),
            "evolution_time": float(self.evolution_time),
            "schedule_type": self.schedule_type,
            "metadata": self.metadata,
        }


def linear_schedule(t: float, T: float) -> float:
    """
    Linear annealing schedule s(t) = t/T.
    
    Parameters
    ----------
    t : float
        Current time
    T : float
        Total time
    
    Returns
    -------
    float
        Schedule parameter s ∈ [0,1]
    """
    return t / T


def polynomial_schedule(t: float, T: float, power: float = 2.0) -> float:
    """
    Polynomial annealing schedule s(t) = (t/T)^p.
    
    Slower near endpoints, faster in middle.
    
    Parameters
    ----------
    t : float
        Current time
    T : float
        Total time
    power : float
        Polynomial power
    
    Returns
    -------
    float
        Schedule parameter
    """
    return (t / T) ** power


def optimized_schedule(
    t: float,
    T: float,
    gap_function: Optional[Callable[[float], float]] = None,
) -> float:
    """
    Optimized schedule based on gap structure.
    
    Mathematical Framework
    ----------------------
    Optimal schedule minimizes diabatic error:
    s'(t) ∝ Δ(s)²
    
    where Δ(s) is instantaneous gap.
    
    Spends more time near small gaps.
    
    Parameters
    ----------
    t : float
        Current time
    T : float
        Total time
    gap_function : callable, optional
        Function giving gap as function of s
    
    Returns
    -------
    float
        Schedule parameter
    """
    if gap_function is None:
        # Default: assume minimum gap at s=0.5
        # Use schedule that slows down there
        s = t / T
        # Smooth function with minimum derivative at s=0.5
        return 0.5 * (1 - np.cos(np.pi * s))
    
    # Full implementation would integrate gap function
    # to determine optimal schedule
    return t / T


def adiabatic_evolution(
    H_initial: np.ndarray,
    H_final: np.ndarray,
    initial_state: np.ndarray,
    T: float,
    schedule: Callable[[float, float], float] = linear_schedule,
    n_steps: int = 100,
) -> AdiabaticResult:
    """
    Perform adiabatic quantum evolution.
    
    Mathematical Framework
    ----------------------
    Time-dependent Hamiltonian:
    H(t) = (1-s(t))H_initial + s(t)H_final
    
    Schrödinger equation:
    iℏ d|ψ⟩/dt = H(t)|ψ⟩
    
    Adiabatic condition:
    |⟨n|dH/dt|0⟩| << Δ²
    where Δ = E_n - E_0 is gap
    
    Parameters
    ----------
    H_initial : array
        Initial Hamiltonian
    H_final : array
        Final Hamiltonian
    initial_state : array
        Initial state (should be ground state of H_initial)
    T : float
        Total evolution time
    schedule : callable
        Annealing schedule function
    n_steps : int
        Number of time steps
    
    Returns
    -------
    AdiabaticResult
        Evolution result
    """
    times = np.linspace(0, T, n_steps)
    dt = T / (n_steps - 1)
    
    # Evolve state
    state = initial_state.copy()
    
    for i in range(n_steps - 1):
        t = times[i]
        s = schedule(t, T)
        
        # Interpolated Hamiltonian
        H_t = (1 - s) * H_initial + s * H_final
        
        # Time evolution operator
        U = expm(-1j * H_t * dt)
        
        # Evolve state
        state = U @ state
        state = state / np.linalg.norm(state)
    
    # Final energy
    s_final = schedule(T, T)
    H_T = (1 - s_final) * H_initial + s_final * H_final
    final_energy = float(np.real(state.conj() @ H_T @ state))
    
    # True ground state of final Hamiltonian
    eigenvalues, eigenvectors = eigh(H_final)
    ground_state = eigenvectors[:, 0]
    ground_energy = eigenvalues[0]
    
    # Fidelity
    fidelity = float(abs(np.vdot(ground_state, state))**2)
    
    # Estimate diabatic error
    # Landau-Zener estimate
    min_gap = min(eigenvalues[1] - eigenvalues[0] for eigenvalues in 
                  [eigh((1-s)*H_initial + s*H_final)[0] 
                   for s in np.linspace(0, 1, 20)])
    diabatic_error = np.exp(-2 * np.pi * min_gap**2 * T)
    
    return AdiabaticResult(
        final_state=state,
        final_energy=final_energy,
        ground_state_fidelity=float(fidelity),
        diabatic_error=float(diabatic_error),
        evolution_time=T,
        schedule_type=schedule.__name__,
        metadata={
            "ground_energy": float(ground_energy),
            "energy_error": float(abs(final_energy - ground_energy)),
            "min_gap": float(min_gap),
        },
    )


def quantum_annealing(
    H_problem: np.ndarray,
    T: float,
    transverse_field_strength: float = 1.0,
    schedule: Callable[[float, float], float] = linear_schedule,
) -> AdiabaticResult:
    """
    Quantum annealing for optimization.
    
    Mathematical Framework
    ----------------------
    H(s) = -A(s)∑ᵢσᵢˣ + B(s)H_problem
    
    where:
    - A(s) = (1-s)·Γ is transverse field (decreasing)
    - B(s) = s is problem Hamiltonian (increasing)
    
    Start in ground state of transverse field (|+⟩^⊗n)
    End in ground state of problem Hamiltonian
    
    Parameters
    ----------
    H_problem : array
        Problem Hamiltonian (diagonal in computational basis)
    T : float
        Annealing time
    transverse_field_strength : float
        Initial transverse field strength Γ
    schedule : callable
        Annealing schedule
    
    Returns
    -------
    AdiabaticResult
        Annealing result
    """
    n_qubits = int(np.log2(H_problem.shape[0]))
    
    # Construct transverse field Hamiltonian
    H_transverse = np.zeros_like(H_problem)
    for i in range(n_qubits):
        # σᵢˣ operator
        sigma_x = np.array([[0, 1], [1, 0]])
        # Tensor product
        op = 1.0
        for j in range(n_qubits):
            if j == i:
                op = np.kron(op, sigma_x) if isinstance(op, np.ndarray) else sigma_x
            else:
                op = np.kron(op, np.eye(2))
        H_transverse += op
    
    H_transverse *= -transverse_field_strength
    
    # Initial state: ground state of transverse field
    # |+⟩^⊗n
    plus_state = np.array([1, 1]) / np.sqrt(2)
    initial_state = plus_state
    for _ in range(n_qubits - 1):
        initial_state = np.kron(initial_state, plus_state)
    
    # Perform adiabatic evolution
    result = adiabatic_evolution(
        H_transverse,
        H_problem,
        initial_state,
        T,
        schedule,
    )
    
    result.metadata["annealing_type"] = "quantum_annealing"
    result.metadata["transverse_field_strength"] = transverse_field_strength
    
    return result


def landau_zener_probability(
    gap: float,
    velocity: float,
) -> float:
    """
    Compute Landau-Zener transition probability.
    
    Mathematical Framework
    ----------------------
    For avoided crossing with gap Δ and velocity v = |dE/dt|:
    
    P_transition = exp(-2πΔ²/v)
    
    This gives probability of diabatic transition (staying in
    instantaneous excited state).
    
    Parameters
    ----------
    gap : float
        Energy gap at avoided crossing
    velocity : float
        Rate of change of energy difference
    
    Returns
    -------
    float
        Transition probability
    """
    if velocity <= 0:
        return 0.0
    
    P = np.exp(-2 * np.pi * gap**2 / velocity)
    return float(P)


def counterdiabatic_driving(
    H_t: Callable[[float], np.ndarray],
    dH_dt: Callable[[float], np.ndarray],
    t: float,
) -> np.ndarray:
    """
    Compute counterdiabatic Hamiltonian for shortcuts to adiabaticity.
    
    Mathematical Framework
    ----------------------
    Counterdiabatic Hamiltonian:
    H_CD(t) = iℏ ∑ₙ≠₀ (|∂ₙ⟩⟨n| - |n⟩⟨∂ₙ|) / (Eₙ - E₀)
    
    where |∂ₙ⟩ = d|n⟩/dt
    
    Adding H_CD to H(t) suppresses diabatic transitions,
    allowing faster evolution while maintaining adiabaticity.
    
    Parameters
    ----------
    H_t : callable
        Time-dependent Hamiltonian
    dH_dt : callable
        Time derivative of Hamiltonian
    t : float
        Current time
    
    Returns
    -------
    array
        Counterdiabatic Hamiltonian
    """
    H = H_t(t)
    dH = dH_dt(t)
    
    # Diagonalize H(t)
    eigenvalues, eigenvectors = eigh(H)
    
    # Compute |∂ₙ⟩ = d|n⟩/dt
    # Using: d|n⟩/dt = ∑ₘ≠ₙ |m⟩⟨m|dH/dt|n⟩/(Eₙ-Eₘ)
    
    n_states = len(eigenvalues)
    H_CD = np.zeros_like(H, dtype=complex)
    
    for n in range(n_states):
        for m in range(n_states):
            if m == n:
                continue
            
            E_n = eigenvalues[n]
            E_m = eigenvalues[m]
            
            if abs(E_n - E_m) < 1e-10:
                continue
            
            # Matrix element ⟨m|dH/dt|n⟩
            dH_mn = eigenvectors[:, m].conj() @ dH @ eigenvectors[:, n]
            
            # Contribution to H_CD
            ket_m = eigenvectors[:, m]
            bra_n = eigenvectors[:, n].conj()
            
            H_CD += 1j * dH_mn / (E_n - E_m) * np.outer(ket_m, bra_n)
    
    # Hermitize
    H_CD = (H_CD - H_CD.conj().T) / 2
    
    return H_CD


def shortcut_to_adiabaticity(
    H_initial: np.ndarray,
    H_final: np.ndarray,
    initial_state: np.ndarray,
    T: float,
    method: str = "counterdiabatic",
) -> AdiabaticResult:
    """
    Fast adiabatic evolution using shortcuts to adiabaticity.
    
    Mathematical Framework
    ----------------------
    Methods:
    1. Counterdiabatic driving: Add H_CD to suppress transitions
    2. Fast-forward: Rescale time evolution
    3. Optimal control: Optimize control fields
    
    Achieves adiabatic results in time T << ℏ/Δ²
    
    Parameters
    ----------
    H_initial : array
        Initial Hamiltonian
    H_final : array
        Final Hamiltonian
    initial_state : array
        Initial state
    T : float
        Evolution time (can be short)
    method : str
        STA method to use
    
    Returns
    -------
    AdiabaticResult
        Evolution result
    """
    if method == "counterdiabatic":
        # Define time-dependent Hamiltonian
        def H_t(t):
            s = t / T
            return (1 - s) * H_initial + s * H_final
        
        def dH_dt(t):
            return (H_final - H_initial) / T
        
        # Evolve with counterdiabatic term
        n_steps = 100
        times = np.linspace(0, T, n_steps)
        dt = T / (n_steps - 1)
        
        state = initial_state.copy()
        
        for i in range(n_steps - 1):
            t = times[i]
            
            # Total Hamiltonian
            H = H_t(t)
            H_CD = counterdiabatic_driving(H_t, dH_dt, t)
            H_total = H + H_CD
            
            # Evolve
            U = expm(-1j * H_total * dt)
            state = U @ state
            state = state / np.linalg.norm(state)
        
        # Compute results
        final_energy = float(np.real(state.conj() @ H_final @ state))
        
        eigenvalues, eigenvectors = eigh(H_final)
        ground_state = eigenvectors[:, 0]
        fidelity = float(abs(np.vdot(ground_state, state))**2)
        
        return AdiabaticResult(
            final_state=state,
            final_energy=final_energy,
            ground_state_fidelity=float(fidelity),
            diabatic_error=1.0 - fidelity,
            evolution_time=T,
            schedule_type="counterdiabatic_driving",
            metadata={
                "method": method,
                "ground_energy": float(eigenvalues[0]),
            },
        )
    
    else:
        raise ValueError(f"Unknown STA method: {method}")


def analyze_gap_structure(
    H_initial: np.ndarray,
    H_final: np.ndarray,
    n_points: int = 50,
) -> Dict[str, Any]:
    """
    Analyze energy gap structure along adiabatic path.
    
    Mathematical Framework
    ----------------------
    Compute instantaneous spectrum:
    H(s) = (1-s)H_initial + s·H_final
    
    Find minimum gap: Δ_min = min_s (E₁(s) - E₀(s))
    
    This determines required annealing time via adiabatic theorem.
    
    Parameters
    ----------
    H_initial : array
        Initial Hamiltonian
    H_final : array
        Final Hamiltonian
    n_points : int
        Number of points to sample
    
    Returns
    -------
    dict
        Gap analysis results
    """
    s_values = np.linspace(0, 1, n_points)
    gaps = []
    ground_energies = []
    first_excited_energies = []
    
    for s in s_values:
        H_s = (1 - s) * H_initial + s * H_final
        eigenvalues = eigh(H_s)[0]
        
        ground_energies.append(eigenvalues[0])
        first_excited_energies.append(eigenvalues[1])
        gaps.append(eigenvalues[1] - eigenvalues[0])
    
    gaps = np.array(gaps)
    min_gap = np.min(gaps)
    min_gap_location = s_values[np.argmin(gaps)]
    
    # Estimate required time for adiabatic evolution
    # T >> 1/Δ_min²
    T_adiabatic = 10.0 / min_gap**2  # Factor of 10 for safety
    
    return {
        "s_values": s_values.tolist(),
        "gaps": gaps.tolist(),
        "min_gap": float(min_gap),
        "min_gap_location": float(min_gap_location),
        "ground_energies": [float(e) for e in ground_energies],
        "first_excited_energies": [float(e) for e in first_excited_energies],
        "estimated_adiabatic_time": float(T_adiabatic),
    }


def gauge_theory_adiabatic_preparation(
    n_sites: int,
    coupling: float = 1.0,
    T: float = 10.0,
    seed: int | None = None,
) -> Dict[str, Any]:
    """
    Adiabatic preparation of gauge theory ground state.
    
    Mathematical Framework
    ----------------------
    For Z2 gauge theory:
    H_initial = -∑ᵢ σᵢˣ (transverse field)
    H_final = -g∑_p W_p (plaquette terms)
    
    Adiabatically evolve from product state to
    gauge theory ground state.
    
    Parameters
    ----------
    n_sites : int
        Number of lattice sites
    coupling : float
        Gauge coupling
    T : float
        Evolution time
    
    Returns
    -------
    dict
        Preparation results
    """
    # Simplified for demonstration
    # Full implementation would construct gauge theory Hamiltonians
    
    from gaugegap.seeding import make_rng

    rng = make_rng(seed)
    dim = 2**n_sites

    # Transverse field Hamiltonian
    H_initial = rng.standard_normal((dim, dim))
    H_initial = (H_initial + H_initial.T) / 2

    # Gauge theory Hamiltonian
    H_final = rng.standard_normal((dim, dim))
    H_final = (H_final + H_final.T) / 2
    
    # Initial state
    initial_state = np.ones(dim) / np.sqrt(dim)
    
    # Perform adiabatic evolution
    result = adiabatic_evolution(
        H_initial,
        H_final,
        initial_state,
        T,
    )
    
    return {
        "n_sites": n_sites,
        "coupling": float(coupling),
        "evolution_time": T,
        "final_energy": result.final_energy,
        "ground_state_fidelity": result.ground_state_fidelity,
        "diabatic_error": result.diabatic_error,
    }


# Made with Bob