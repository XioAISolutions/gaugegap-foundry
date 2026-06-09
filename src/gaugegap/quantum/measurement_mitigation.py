"""
Measurement Error Mitigation via Calibration Matrices

Mathematical Framework
----------------------
Measurement errors are the dominant error source on NISQ devices.
For n qubits, measurement produces noisy distribution p_noisy instead of ideal p_ideal.

The relationship is linear:
p_noisy = M · p_ideal

where M is the 2ⁿ × 2ⁿ calibration matrix (confusion matrix).

Mitigation inverts this relationship:
p_mitigated = M⁻¹ · p_noisy

Calibration Matrix Construction
-------------------------------
For each basis state |i⟩:
1. Prepare |i⟩
2. Measure many times
3. M_ij = P(measure j | prepared i)

For n qubits, requires 2ⁿ calibration circuits.

Tensor Product Approximation
----------------------------
Full calibration scales exponentially. For independent qubits:
M = M₁ ⊗ M₂ ⊗ ... ⊗ Mₙ

where each Mᵢ is 2×2 single-qubit calibration matrix.
Reduces calibration from 2ⁿ to 2n circuits.

Least Squares Mitigation
------------------------
For overconstrained systems, use least squares:
p_mitigated = argmin_p ||M·p - p_noisy||²

subject to: p ≥ 0, Σp = 1

Physics Basis
-------------
Measurement errors arise from:
- Readout crosstalk between qubits
- Finite measurement fidelity
- State preparation errors
- Thermal excitation during readout

Typical single-qubit assignment fidelity: 95-99%
Mitigation can improve to effective 99.5-99.9%

Claim Boundary Compliance
-------------------------
Measurement error mitigation corrects known hardware imperfections.
It does not change the quantum computation, only post-processes classical
measurement outcomes. All mitigation overhead is reported.

References
----------
- Bravyi et al. (2021). Mitigating measurement errors in multiqubit experiments
- Nachman et al. (2020). Unfolding quantum computer readout noise
- Nation et al. (2021). Scalable mitigation of measurement errors on quantum computers
- IBM Qiskit Ignis documentation
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
from scipy.linalg import lstsq


@dataclass
class CalibrationMatrix:
    """Measurement calibration matrix."""
    
    matrix: np.ndarray
    """Calibration matrix M where M_ij = P(measure j | prepared i)"""
    
    n_qubits: int
    """Number of qubits"""
    
    method: str
    """Calibration method: 'full' or 'tensor'"""
    
    fidelity: float
    """Average measurement fidelity"""
    
    condition_number: float
    """Condition number of matrix (stability indicator)"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "n_qubits": self.n_qubits,
            "method": self.method,
            "fidelity": float(self.fidelity),
            "condition_number": float(self.condition_number),
            "matrix_shape": self.matrix.shape,
        }


@dataclass
class MitigationResult:
    """Result of measurement error mitigation."""
    
    mitigated_counts: Dict[str, float]
    """Mitigated measurement counts"""
    
    raw_counts: Dict[str, int]
    """Raw measurement counts"""
    
    total_shots: int
    """Total number of shots"""
    
    calibration_overhead: int
    """Number of calibration circuits"""
    
    method: str
    """Mitigation method used"""
    
    fidelity_improvement: float
    """Estimated fidelity improvement"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "mitigated_counts": self.mitigated_counts,
            "raw_counts": self.raw_counts,
            "total_shots": self.total_shots,
            "calibration_overhead": self.calibration_overhead,
            "method": self.method,
            "fidelity_improvement": float(self.fidelity_improvement),
        }


def build_full_calibration_matrix(
    n_qubits: int,
    backend,
    shots: int = 1024,
) -> CalibrationMatrix:
    """
    Build full 2ⁿ × 2ⁿ calibration matrix.
    
    Parameters
    ----------
    n_qubits : int
        Number of qubits
    backend : Backend
        Quantum backend for calibration
    shots : int
        Shots per calibration circuit
    
    Returns
    -------
    CalibrationMatrix
        Full calibration matrix
    
    Notes
    -----
    Requires 2ⁿ calibration circuits. Exponentially expensive but most accurate.
    """
    try:
        from qiskit import QuantumCircuit, transpile
    except ImportError as exc:
        raise RuntimeError(
            "Install Qiskit extras with: python -m pip install -e '.[quantum]'"
        ) from exc
    
    dim = 2**n_qubits
    matrix = np.zeros((dim, dim))
    
    # For each basis state
    for i in range(dim):
        # Create circuit preparing |i⟩
        qc = QuantumCircuit(n_qubits, n_qubits)
        
        # Prepare basis state by applying X gates
        for qubit in range(n_qubits):
            if (i >> qubit) & 1:
                qc.x(qubit)
        
        qc.measure_all()
        
        # Execute
        compiled = transpile(qc, backend)
        job = backend.run(compiled, shots=shots)
        counts = job.result().get_counts()
        
        # Fill matrix column
        for bitstring, count in counts.items():
            j = int(bitstring, 2)
            matrix[j, i] = count / shots
    
    # Calculate fidelity (diagonal average)
    fidelity = np.mean(np.diag(matrix))
    
    # Calculate condition number
    cond = np.linalg.cond(matrix)
    
    return CalibrationMatrix(
        matrix=matrix,
        n_qubits=n_qubits,
        method="full",
        fidelity=float(fidelity),
        condition_number=float(cond),
    )


def build_tensor_calibration_matrix(
    n_qubits: int,
    backend,
    shots: int = 1024,
) -> CalibrationMatrix:
    """
    Build tensor product calibration matrix M = M₁ ⊗ M₂ ⊗ ... ⊗ Mₙ.
    
    Parameters
    ----------
    n_qubits : int
        Number of qubits
    backend : Backend
        Quantum backend for calibration
    shots : int
        Shots per calibration circuit
    
    Returns
    -------
    CalibrationMatrix
        Tensor product calibration matrix
    
    Notes
    -----
    Requires only 2n calibration circuits. Assumes independent qubit errors.
    """
    try:
        from qiskit import QuantumCircuit, transpile
    except ImportError as exc:
        raise RuntimeError(
            "Install Qiskit extras with: python -m pip install -e '.[quantum]'"
        ) from exc
    
    single_qubit_matrices = []
    
    # Calibrate each qubit independently
    for qubit in range(n_qubits):
        M_q = np.zeros((2, 2))
        
        # Prepare |0⟩ and measure
        qc0 = QuantumCircuit(n_qubits, n_qubits)
        qc0.measure(qubit, qubit)
        
        compiled0 = transpile(qc0, backend)
        job0 = backend.run(compiled0, shots=shots)
        counts0 = job0.result().get_counts()
        
        # Extract qubit measurement
        for bitstring, count in counts0.items():
            bit = int(bitstring[-(qubit+1)])
            M_q[bit, 0] += count / shots
        
        # Prepare |1⟩ and measure
        qc1 = QuantumCircuit(n_qubits, n_qubits)
        qc1.x(qubit)
        qc1.measure(qubit, qubit)
        
        compiled1 = transpile(qc1, backend)
        job1 = backend.run(compiled1, shots=shots)
        counts1 = job1.result().get_counts()
        
        for bitstring, count in counts1.items():
            bit = int(bitstring[-(qubit+1)])
            M_q[bit, 1] += count / shots
        
        single_qubit_matrices.append(M_q)
    
    # Tensor product
    matrix = single_qubit_matrices[0]
    for M_q in single_qubit_matrices[1:]:
        matrix = np.kron(matrix, M_q)
    
    # Calculate fidelity
    fidelity = np.mean(np.diag(matrix))
    
    # Calculate condition number
    cond = np.linalg.cond(matrix)
    
    return CalibrationMatrix(
        matrix=matrix,
        n_qubits=n_qubits,
        method="tensor",
        fidelity=float(fidelity),
        condition_number=float(cond),
    )


def mitigate_counts(
    counts: Dict[str, int],
    calibration: CalibrationMatrix,
    method: str = "least_squares",
) -> MitigationResult:
    """
    Mitigate measurement errors using calibration matrix.
    
    Parameters
    ----------
    counts : dict
        Raw measurement counts
    calibration : CalibrationMatrix
        Calibration matrix
    method : str
        Mitigation method: 'inverse' or 'least_squares'
    
    Returns
    -------
    MitigationResult
        Mitigated counts and statistics
    
    Notes
    -----
    'inverse': Direct matrix inversion (fast but can give negative probabilities)
    'least_squares': Constrained optimization (slower but guarantees valid probabilities)
    """
    n_qubits = calibration.n_qubits
    dim = 2**n_qubits
    total_shots = sum(counts.values())
    
    # Convert counts to probability vector
    p_noisy = np.zeros(dim)
    for bitstring, count in counts.items():
        idx = int(bitstring, 2)
        p_noisy[idx] = count / total_shots
    
    if method == "inverse":
        # Direct inversion
        M_inv = np.linalg.pinv(calibration.matrix)
        p_mitigated = M_inv @ p_noisy
        
        # Clip negative values and renormalize
        p_mitigated = np.maximum(p_mitigated, 0)
        p_mitigated /= np.sum(p_mitigated)
    
    elif method == "least_squares":
        # Constrained least squares
        p_mitigated = _constrained_least_squares(
            calibration.matrix,
            p_noisy,
        )
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Convert back to counts
    mitigated_counts = {}
    for i in range(dim):
        if p_mitigated[i] > 1e-10:  # Skip negligible probabilities
            bitstring = format(i, f'0{n_qubits}b')
            mitigated_counts[bitstring] = float(p_mitigated[i] * total_shots)
    
    # Estimate fidelity improvement
    raw_fidelity = calibration.fidelity
    mitigated_fidelity = min(1.0, raw_fidelity / (1 - raw_fidelity + 1e-10))
    improvement = mitigated_fidelity / raw_fidelity
    
    # Calibration overhead
    overhead = dim if calibration.method == "full" else 2 * n_qubits
    
    return MitigationResult(
        mitigated_counts=mitigated_counts,
        raw_counts=counts,
        total_shots=total_shots,
        calibration_overhead=overhead,
        method=method,
        fidelity_improvement=float(improvement),
    )


def _constrained_least_squares(
    M: np.ndarray,
    p_noisy: np.ndarray,
) -> np.ndarray:
    """
    Solve constrained least squares: min ||M·p - p_noisy||² s.t. p ≥ 0, Σp = 1.
    
    Parameters
    ----------
    M : array
        Calibration matrix
    p_noisy : array
        Noisy probability distribution
    
    Returns
    -------
    array
        Mitigated probability distribution
    """
    dim = len(p_noisy)
    
    # Objective: ||M·p - p_noisy||²
    def objective(p):
        return np.sum((M @ p - p_noisy)**2)
    
    # Gradient
    def gradient(p):
        return 2 * M.T @ (M @ p - p_noisy)
    
    # Constraints
    constraints = [
        {'type': 'eq', 'fun': lambda p: np.sum(p) - 1},  # Σp = 1
    ]
    
    # Bounds: p ≥ 0
    bounds = [(0, 1) for _ in range(dim)]
    
    # Initial guess: uniform distribution
    p0 = np.ones(dim) / dim
    
    # Optimize
    result = minimize(
        objective,
        p0,
        method='SLSQP',
        jac=gradient,
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 1000},
    )
    
    if not result.success:
        # Fall back to unconstrained solution using numpy
        p_unconstrained = np.linalg.lstsq(M, p_noisy, rcond=None)[0]
        p_unconstrained = np.maximum(p_unconstrained, 0)
        return p_unconstrained / np.sum(p_unconstrained)
    
    return result.x


def estimate_mitigation_benefit(
    n_qubits: int,
    raw_fidelity: float = 0.97,
    method: str = "tensor",
) -> Dict[str, Any]:
    """
    Estimate benefit of measurement error mitigation.
    
    Parameters
    ----------
    n_qubits : int
        Number of qubits
    raw_fidelity : float
        Raw measurement fidelity per qubit
    method : str
        Calibration method
    
    Returns
    -------
    dict
        Estimated improvements
    """
    # Multi-qubit fidelity (assuming independent errors)
    multi_qubit_fidelity = raw_fidelity**n_qubits
    
    # Mitigation can approach single-qubit fidelity
    mitigated_fidelity = raw_fidelity**(n_qubits / 2)  # Heuristic
    
    # Calibration overhead
    if method == "full":
        overhead = 2**n_qubits
    else:  # tensor
        overhead = 2 * n_qubits
    
    return {
        "n_qubits": n_qubits,
        "raw_multi_qubit_fidelity": float(multi_qubit_fidelity),
        "mitigated_fidelity": float(mitigated_fidelity),
        "improvement_factor": float(mitigated_fidelity / multi_qubit_fidelity),
        "calibration_overhead": overhead,
        "method": method,
    }


# Made with Bob