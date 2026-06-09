"""
Gauge-Invariant Quantum Error Correction for Lattice Gauge Theories

Mathematical Framework
----------------------
Quantum error correction for gauge theories must preserve gauge invariance.
Standard QEC codes may violate Gauss's law, leading to unphysical states.

1. Gauge-Invariant Stabilizer Codes:
   Stabilizers commute with gauge generators:
   [Sᵢ, Gⱼ] = 0 for all stabilizers Sᵢ and gauge generators Gⱼ
   
   For Z2 gauge theory:
   - Gauge generators: Gᵥ = ∏ₗ∈∂ᵥ σᶻₗ (vertex operators)
   - Stabilizers must preserve even/odd parity at vertices

2. Syndrome Extraction:
   Measure stabilizers without collapsing gauge-invariant subspace:
   - Use ancilla qubits
   - Apply controlled operations
   - Measure ancillas to detect errors
   
3. Error Recovery:
   Apply corrections that maintain gauge invariance:
   - Pauli errors: X, Y, Z on links
   - Recovery operators: gauge-covariant transformations
   - Logical operators: Wilson loops, string operators

4. Logical Qubit Encoding:
   Encode logical information in gauge-invariant subspace:
   - Logical |0⟩_L and |1⟩_L both satisfy Gauss's law
   - Logical operators: non-contractible Wilson loops
   - Code distance: minimum weight of logical operator

Topological Codes for Gauge Theories
-------------------------------------
1. Toric Code (Z2 gauge theory):
   - Plaquette stabilizers: Bₚ = ∏ₗ∈∂p σᶻₗ
   - Vertex stabilizers: Aᵥ = ∏ₗ∈∂ᵥ σˣₗ
   - Logical operators: non-contractible loops
   - Code distance: system size L

2. Color Code:
   - Three types of plaquettes (RGB)
   - Higher code distance
   - Transversal gates for fault tolerance

3. Subsystem Codes:
   - Gauge qubits + logical qubits
   - Reduced syndrome measurement overhead
   - Natural for gauge theories

Physics Motivation
------------------
Errors in gauge theory simulations can:
- Violate Gauss's law (unphysical charge)
- Break gauge invariance
- Corrupt Wilson loop measurements
- Introduce spurious confinement/deconfinement

Gauge-invariant QEC ensures:
- Physical states throughout computation
- Reliable gauge-invariant observables
- Scalable quantum simulation
- Fault-tolerant gauge theory computation

Claim Boundary Compliance
-------------------------
This is quantum error correction for finite lattice gauge theories.
It provides fault-tolerant quantum computation infrastructure but
does not constitute proofs of Millennium Prize problems. All codes
are for finite systems with specified parameters.

References
----------
- Kitaev (2003). Fault-tolerant quantum computation by anyons
- Bombin & Martin-Delgado (2006). Topological quantum distillation
- Zohar & Burrello (2015). Formulation of lattice gauge theories for quantum simulations
- Cong et al. (2022). Quantum error correction with gauge symmetries
- Raychaudhuri & Brennen (2023). Protected gates for topological quantum field theories
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass
from itertools import combinations


@dataclass
class QECCode:
    """Quantum error correction code specification."""
    
    n_physical: int
    """Number of physical qubits"""
    
    n_logical: int
    """Number of logical qubits"""
    
    code_distance: int
    """Minimum weight of logical operator"""
    
    stabilizers: List[str]
    """Stabilizer generators (Pauli strings)"""
    
    logical_operators: Dict[str, List[str]]
    """Logical X and Z operators"""
    
    gauge_generators: Optional[List[str]] = None
    """Gauge symmetry generators"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "n_physical": self.n_physical,
            "n_logical": self.n_logical,
            "code_distance": self.code_distance,
            "n_stabilizers": len(self.stabilizers),
            "gauge_invariant": self.gauge_generators is not None,
        }


@dataclass
class SyndromeResult:
    """Result of syndrome measurement."""
    
    syndrome: np.ndarray
    """Syndrome bit string"""
    
    error_detected: bool
    """Whether error was detected"""
    
    error_type: Optional[str]
    """Type of error if identified"""
    
    correction_applied: bool
    """Whether correction was applied"""
    
    gauge_invariance_preserved: bool
    """Whether gauge invariance maintained"""
    
    metadata: Dict[str, Any]
    """Additional information"""


def z2_toric_code(
    lattice_size: Tuple[int, int],
) -> QECCode:
    """
    Construct Z2 toric code for lattice gauge theory.
    
    Mathematical Framework
    ----------------------
    On L×L lattice with periodic boundary conditions:
    
    Physical qubits: Links of lattice (2L² qubits)
    
    Stabilizers:
    - Vertex (star): Aᵥ = ∏ₗ∈∂ᵥ σˣₗ (L² operators)
    - Plaquette: Bₚ = ∏ₗ∈∂p σᶻₗ (L² operators)
    
    Logical qubits: 2 (from topology)
    - X₁, X₂: horizontal and vertical loops
    - Z₁, Z₂: dual loops
    
    Code distance: L (minimum loop size)
    
    Gauge interpretation:
    - Bₚ = gauge-invariant plaquette operators
    - Aᵥ = Gauss's law constraints
    - Physical states: Aᵥ|ψ⟩ = |ψ⟩, Bₚ|ψ⟩ = |ψ⟩
    
    Parameters
    ----------
    lattice_size : tuple
        (rows, cols) lattice dimensions
    
    Returns
    -------
    QECCode
        Toric code specification
    """
    rows, cols = lattice_size
    n_vertices = rows * cols
    n_plaquettes = rows * cols
    n_links = 2 * rows * cols  # Horizontal + vertical
    
    # Build stabilizers
    stabilizers = []
    
    # Vertex stabilizers (star operators)
    for v_row in range(rows):
        for v_col in range(cols):
            # Links around vertex
            links = _vertex_links(v_row, v_col, rows, cols)
            pauli_str = _pauli_string_from_links(links, n_links, 'X')
            stabilizers.append(pauli_str)
    
    # Plaquette stabilizers
    for p_row in range(rows):
        for p_col in range(cols):
            # Links around plaquette
            links = _plaquette_links(p_row, p_col, rows, cols)
            pauli_str = _pauli_string_from_links(links, n_links, 'Z')
            stabilizers.append(pauli_str)
    
    # Logical operators (non-contractible loops)
    logical_ops = {
        "X": [
            _horizontal_loop(0, cols, rows, cols),  # X₁
            _vertical_loop(0, rows, rows, cols),    # X₂
        ],
        "Z": [
            _vertical_loop_dual(0, rows, rows, cols),    # Z₁
            _horizontal_loop_dual(0, cols, rows, cols),  # Z₂
        ],
    }
    
    # Gauge generators (vertex operators for Z2)
    gauge_gens = [stabilizers[i] for i in range(n_vertices)]
    
    return QECCode(
        n_physical=n_links,
        n_logical=2,
        code_distance=min(rows, cols),
        stabilizers=stabilizers,
        logical_operators=logical_ops,
        gauge_generators=gauge_gens,
    )


def measure_syndrome(
    state: np.ndarray,
    stabilizers: List[str],
    gauge_generators: Optional[List[str]] = None,
) -> SyndromeResult:
    """
    Measure stabilizer syndrome while preserving gauge invariance.
    
    Mathematical Framework
    ----------------------
    For each stabilizer Sᵢ:
    1. Measure eigenvalue: sᵢ = ⟨ψ|Sᵢ|ψ⟩ ∈ {±1}
    2. Syndrome: s = (s₁, s₂, ..., sₙ)
    3. Error detected if any sᵢ = -1
    
    Gauge invariance check:
    - Verify ⟨ψ|Gⱼ|ψ⟩ = +1 for all gauge generators Gⱼ
    - If violated, state is unphysical
    
    Parameters
    ----------
    state : array
        Quantum state vector
    stabilizers : list
        Stabilizer Pauli strings
    gauge_generators : list, optional
        Gauge symmetry generators
    
    Returns
    -------
    SyndromeResult
        Syndrome measurement result
    """
    n_qubits = int(np.log2(len(state)))
    syndrome = np.zeros(len(stabilizers), dtype=int)
    
    # Measure each stabilizer
    for i, stab_str in enumerate(stabilizers):
        stab_matrix = _pauli_string_to_matrix(stab_str, n_qubits)
        expectation = np.real(np.vdot(state, stab_matrix @ state))
        
        # Eigenvalue should be ±1
        if expectation > 0:
            syndrome[i] = 0  # +1 eigenvalue (no error)
        else:
            syndrome[i] = 1  # -1 eigenvalue (error detected)
    
    error_detected = np.any(syndrome == 1)
    
    # Check gauge invariance if generators provided
    gauge_invariant = True
    if gauge_generators is not None:
        for gauge_gen in gauge_generators:
            gauge_matrix = _pauli_string_to_matrix(gauge_gen, n_qubits)
            expectation = np.real(np.vdot(state, gauge_matrix @ state))
            if abs(expectation - 1.0) > 1e-6:
                gauge_invariant = False
                break
    
    # Identify error type from syndrome
    error_type = None
    if error_detected:
        error_type = _decode_syndrome(syndrome, stabilizers)
    
    return SyndromeResult(
        syndrome=syndrome,
        error_detected=bool(error_detected),
        error_type=error_type,
        correction_applied=False,
        gauge_invariance_preserved=gauge_invariant,
        metadata={
            "syndrome_weight": int(np.sum(syndrome)),
            "n_stabilizers": len(stabilizers),
        },
    )


def apply_error_correction(
    state: np.ndarray,
    syndrome_result: SyndromeResult,
    stabilizers: List[str],
    decoder: str = "lookup",
) -> Tuple[np.ndarray, SyndromeResult]:
    """
    Apply error correction based on syndrome.
    
    Mathematical Framework
    ----------------------
    1. Decode syndrome to identify error location
    2. Apply recovery operator R
    3. Verify correction: measure syndrome again
    
    Decoders:
    - Lookup table: Pre-computed for small codes
    - Minimum weight: Find minimum weight Pauli matching syndrome
    - MWPM: Minimum weight perfect matching (for surface codes)
    
    Gauge invariance:
    - Recovery operators must commute with gauge generators
    - Or apply gauge transformation after correction
    
    Parameters
    ----------
    state : array
        Quantum state with error
    syndrome_result : SyndromeResult
        Measured syndrome
    stabilizers : list
        Stabilizer generators
    decoder : str
        Decoding algorithm
    
    Returns
    -------
    corrected_state : array
        State after correction
    new_syndrome : SyndromeResult
        Syndrome after correction
    """
    if not syndrome_result.error_detected:
        # No error, return original state
        syndrome_result.correction_applied = False
        return state, syndrome_result
    
    n_qubits = int(np.log2(len(state)))
    
    # Decode syndrome to find recovery operator
    if decoder == "lookup":
        recovery_op = _lookup_decoder(syndrome_result.syndrome, stabilizers, n_qubits)
    elif decoder == "minimum_weight":
        recovery_op = _minimum_weight_decoder(syndrome_result.syndrome, stabilizers, n_qubits)
    else:
        raise ValueError(f"Unknown decoder: {decoder}")
    
    # Apply recovery
    recovery_matrix = _pauli_string_to_matrix(recovery_op, n_qubits)
    corrected_state = recovery_matrix @ state
    corrected_state = corrected_state / np.linalg.norm(corrected_state)
    
    # Measure syndrome again to verify correction
    new_syndrome = measure_syndrome(corrected_state, stabilizers)
    new_syndrome.correction_applied = True
    new_syndrome.metadata["recovery_operator"] = recovery_op
    
    return corrected_state, new_syndrome


def logical_operator_expectation(
    state: np.ndarray,
    logical_op: str,
) -> float:
    """
    Compute expectation value of logical operator.
    
    For encoded logical qubit, measure logical observables:
    ⟨X_L⟩, ⟨Z_L⟩
    
    Parameters
    ----------
    state : array
        Encoded quantum state
    logical_op : str
        Logical operator (Pauli string)
    
    Returns
    -------
    float
        Expectation value
    """
    n_qubits = int(np.log2(len(state)))
    op_matrix = _pauli_string_to_matrix(logical_op, n_qubits)
    return float(np.real(np.vdot(state, op_matrix @ state)))


# Helper functions

def _vertex_links(v_row: int, v_col: int, rows: int, cols: int) -> List[int]:
    """Get link indices around a vertex."""
    # Simplified: return 4 links around vertex
    # In full implementation, handle boundary conditions
    links = []
    # Horizontal links
    h_left = v_row * cols + v_col
    h_right = v_row * cols + ((v_col + 1) % cols)
    # Vertical links
    v_down = rows * cols + v_row * cols + v_col
    v_up = rows * cols + ((v_row + 1) % rows) * cols + v_col
    return [h_left, h_right, v_down, v_up]


def _plaquette_links(p_row: int, p_col: int, rows: int, cols: int) -> List[int]:
    """Get link indices around a plaquette."""
    links = []
    # Bottom horizontal
    links.append(p_row * cols + p_col)
    # Right vertical
    links.append(rows * cols + p_row * cols + ((p_col + 1) % cols))
    # Top horizontal
    links.append(((p_row + 1) % rows) * cols + p_col)
    # Left vertical
    links.append(rows * cols + p_row * cols + p_col)
    return links


def _pauli_string_from_links(links: List[int], n_qubits: int, pauli: str) -> str:
    """Construct Pauli string with specified Pauli on given links."""
    pauli_list = ['I'] * n_qubits
    for link in links:
        if 0 <= link < n_qubits:
            pauli_list[n_qubits - 1 - link] = pauli
    return ''.join(pauli_list)


def _horizontal_loop(row: int, cols: int, rows: int, total_cols: int) -> str:
    """Construct horizontal loop operator."""
    n_qubits = 2 * rows * cols
    links = [row * cols + c for c in range(cols)]
    return _pauli_string_from_links(links, n_qubits, 'X')


def _vertical_loop(col: int, rows: int, total_rows: int, cols: int) -> str:
    """Construct vertical loop operator."""
    n_qubits = 2 * rows * cols
    links = [rows * cols + r * cols + col for r in range(rows)]
    return _pauli_string_from_links(links, n_qubits, 'X')


def _horizontal_loop_dual(row: int, cols: int, rows: int, total_cols: int) -> str:
    """Construct dual horizontal loop (Z operator)."""
    n_qubits = 2 * rows * cols
    links = [rows * cols + row * cols + c for c in range(cols)]
    return _pauli_string_from_links(links, n_qubits, 'Z')


def _vertical_loop_dual(col: int, rows: int, total_rows: int, cols: int) -> str:
    """Construct dual vertical loop (Z operator)."""
    n_qubits = 2 * rows * cols
    links = [r * cols + col for r in range(rows)]
    return _pauli_string_from_links(links, n_qubits, 'Z')


def _pauli_string_to_matrix(pauli_str: str, n_qubits: int) -> np.ndarray:
    """Convert Pauli string to matrix."""
    # Pauli matrices
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    
    pauli_dict = {'I': I, 'X': X, 'Y': Y, 'Z': Z}
    
    # Build tensor product
    matrix = np.array([[1]], dtype=complex)
    for char in pauli_str:
        matrix = np.kron(matrix, pauli_dict[char])
    
    return matrix


def _decode_syndrome(syndrome: np.ndarray, stabilizers: List[str]) -> str:
    """Decode syndrome to identify error type."""
    if np.sum(syndrome) == 0:
        return "no_error"
    elif np.sum(syndrome) == 1:
        return "single_stabilizer_violation"
    else:
        return "multiple_stabilizer_violations"


def _lookup_decoder(
    syndrome: np.ndarray,
    stabilizers: List[str],
    n_qubits: int,
) -> str:
    """Lookup table decoder for small codes."""
    # Simplified: return identity if no error
    if np.sum(syndrome) == 0:
        return 'I' * n_qubits
    
    # For demonstration, apply X on first qubit
    pauli_list = ['I'] * n_qubits
    pauli_list[-1] = 'X'
    return ''.join(pauli_list)


def _minimum_weight_decoder(
    syndrome: np.ndarray,
    stabilizers: List[str],
    n_qubits: int,
) -> str:
    """Minimum weight decoder."""
    # Simplified implementation
    return _lookup_decoder(syndrome, stabilizers, n_qubits)


# Made with Bob