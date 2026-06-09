"""
Dynamical Decoupling for Quantum Error Suppression

Mathematical Framework
----------------------
Dynamical decoupling (DD) applies periodic pulse sequences to suppress decoherence
during idle periods in quantum circuits.

For a system-bath Hamiltonian H = H_S + H_B + H_SB:
- H_S: system Hamiltonian
- H_B: bath Hamiltonian  
- H_SB: system-bath interaction

DD sequences apply unitaries U(t) such that:
∫₀ᵀ U†(t) H_SB U(t) dt ≈ 0

Common Sequences
----------------
1. **Hahn Echo (XY-2)**: X - τ - X
   Cancels first-order dephasing

2. **CPMG (Carr-Purcell-Meiboom-Gill)**: (X - τ - X - τ)ⁿ
   Cancels higher-order terms

3. **XY-4**: X - τ - Y - τ - X - τ - Y - τ
   Cancels both dephasing and amplitude damping

4. **XY-8**: Extension of XY-4 with 8 pulses
   Cancels even higher-order terms

5. **UR (Universal Robust)**: Optimized for specific noise
   Tailored to hardware characteristics

Physics Basis
-------------
For pure dephasing noise: H_SB = σ_z ⊗ B(t)
- X pulses flip qubit: σ_z → -σ_z
- Averages out dephasing over time

For amplitude damping: H_SB = σ_x ⊗ B_x(t) + σ_y ⊗ B_y(t)
- XY sequences required to average both components

Claim Boundary Compliance
-------------------------
DD is a proven error suppression technique that does not change the intended
quantum computation. It protects idle qubits from decoherence without altering
the logical circuit operation. All DD sequences preserve the identity operation
over the protected interval.

References
----------
- Viola & Lloyd (1998). Dynamical suppression of decoherence
- Khodjasteh & Lidar (2005). Fault-tolerant quantum dynamical decoupling
- Pokharel et al. (2018). Demonstration of fidelity improvement using DD
- Qiskit Pulse documentation on DD sequences
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np


class DDSequence(Enum):
    """Dynamical decoupling sequence types."""
    NONE = "none"
    HAHN_ECHO = "hahn_echo"  # XY-2
    CPMG = "cpmg"  # Carr-Purcell-Meiboom-Gill
    XY4 = "xy4"  # XY-4
    XY8 = "xy8"  # XY-8
    UR = "ur"  # Universal Robust


@dataclass
class DDConfig:
    """Configuration for dynamical decoupling."""
    
    sequence: DDSequence = DDSequence.XY4
    """DD sequence type"""
    
    spacing: str = "uniform"
    """Pulse spacing: 'uniform' or 'optimized'"""
    
    min_delay: float = 0.0
    """Minimum delay to apply DD (in gate times)"""
    
    pulse_alignment: int = 16
    """Pulse alignment constraint (hardware dependent)"""
    
    skip_reset_qubits: bool = True
    """Skip DD on qubits being reset"""


@dataclass
class DDStats:
    """Statistics about DD application."""
    
    n_qubits_protected: int
    """Number of qubits with DD applied"""
    
    n_sequences_inserted: int
    """Total number of DD sequences inserted"""
    
    avg_sequence_length: float
    """Average number of pulses per sequence"""
    
    total_pulses_added: int
    """Total DD pulses added to circuit"""
    
    idle_time_protected: float
    """Total idle time protected (in gate times)"""
    
    sequence_type: str
    """DD sequence type used"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "n_qubits_protected": self.n_qubits_protected,
            "n_sequences_inserted": self.n_sequences_inserted,
            "avg_sequence_length": self.avg_sequence_length,
            "total_pulses_added": self.total_pulses_added,
            "idle_time_protected": self.idle_time_protected,
            "sequence_type": self.sequence_type,
        }


def get_dd_sequence_gates(sequence: DDSequence) -> List[str]:
    """
    Get gate sequence for a DD protocol.
    
    Parameters
    ----------
    sequence : DDSequence
        DD sequence type
    
    Returns
    -------
    list
        List of gate names in sequence
    
    Examples
    --------
    >>> get_dd_sequence_gates(DDSequence.XY4)
    ['x', 'y', 'x', 'y']
    """
    if sequence == DDSequence.NONE:
        return []
    elif sequence == DDSequence.HAHN_ECHO:
        return ['x', 'x']
    elif sequence == DDSequence.CPMG:
        return ['x', 'x', 'x', 'x']  # Can be repeated
    elif sequence == DDSequence.XY4:
        return ['x', 'y', 'x', 'y']
    elif sequence == DDSequence.XY8:
        return ['x', 'y', 'x', 'y', 'y', 'x', 'y', 'x']
    elif sequence == DDSequence.UR:
        # Universal Robust sequence (simplified)
        return ['x', 'y', 'x', 'y', 'y', 'x', 'y', 'x']
    else:
        raise ValueError(f"Unknown DD sequence: {sequence}")


def calculate_dd_spacing(
    idle_duration: float,
    n_pulses: int,
    spacing: str = "uniform",
) -> List[float]:
    """
    Calculate pulse spacing for DD sequence.
    
    Parameters
    ----------
    idle_duration : float
        Total idle time to protect
    n_pulses : int
        Number of DD pulses
    spacing : str
        Spacing strategy: 'uniform' or 'optimized'
    
    Returns
    -------
    list
        Delay times before each pulse
    
    Notes
    -----
    Uniform spacing: equal delays between pulses
    Optimized spacing: Uhrig DD spacing for optimal dephasing suppression
    """
    if n_pulses == 0:
        return []
    
    if spacing == "uniform":
        # Equal spacing: τ/(n+1) between pulses
        delay = idle_duration / (n_pulses + 1)
        return [delay] * (n_pulses + 1)
    
    elif spacing == "optimized":
        # Uhrig DD: optimal for pure dephasing
        # t_k = T * sin²(πk/(2n+2)) for k=1..n
        delays = []
        for k in range(n_pulses + 1):
            if k == 0:
                t_k = idle_duration * np.sin(np.pi / (2 * n_pulses + 2))**2
            else:
                t_k = idle_duration * (
                    np.sin(np.pi * (k + 1) / (2 * n_pulses + 2))**2 -
                    np.sin(np.pi * k / (2 * n_pulses + 2))**2
                )
            delays.append(t_k)
        return delays
    
    else:
        raise ValueError(f"Unknown spacing strategy: {spacing}")


def apply_dd_to_circuit(
    circuit,
    config: Optional[DDConfig] = None,
) -> Tuple[Any, DDStats]:
    """
    Apply dynamical decoupling to idle qubits in a circuit.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit to protect with DD
    config : DDConfig, optional
        DD configuration
    
    Returns
    -------
    protected_circuit : QuantumCircuit
        Circuit with DD sequences inserted
    stats : DDStats
        Statistics about DD application
    
    Raises
    ------
    RuntimeError
        If Qiskit is not installed
    
    Notes
    -----
    This function identifies idle periods in the circuit and inserts
    DD sequences to suppress decoherence. The circuit depth will increase,
    but fidelity should improve on real hardware.
    """
    try:
        from qiskit import QuantumCircuit
        from qiskit.transpiler import PassManager
        from qiskit.transpiler.passes import PadDynamicalDecoupling
        from qiskit.circuit.library import XGate, YGate
    except ImportError as exc:
        raise RuntimeError(
            "Install Qiskit extras with: python -m pip install -e '.[quantum]'"
        ) from exc
    
    if config is None:
        config = DDConfig()
    
    # Get DD sequence
    gate_names = get_dd_sequence_gates(config.sequence)
    
    if not gate_names:
        # No DD requested
        return circuit.copy(), DDStats(
            n_qubits_protected=0,
            n_sequences_inserted=0,
            avg_sequence_length=0.0,
            total_pulses_added=0,
            idle_time_protected=0.0,
            sequence_type="none",
        )
    
    # Convert gate names to Qiskit gates
    gate_map = {'x': XGate(), 'y': YGate()}
    dd_sequence = [gate_map[g] for g in gate_names]
    
    # Create DD pass
    dd_pass = PadDynamicalDecoupling(
        durations=None,  # Will use default durations
        dd_sequence=dd_sequence,
        skip_reset_qubits=config.skip_reset_qubits,
    )
    
    # Apply DD
    pm = PassManager([dd_pass])
    protected = pm.run(circuit)
    
    # Calculate statistics
    original_ops = circuit.count_ops()
    protected_ops = protected.count_ops()
    
    n_dd_pulses = sum(
        protected_ops.get(g, 0) - original_ops.get(g, 0)
        for g in ['x', 'y']
    )
    
    n_sequences = n_dd_pulses // len(gate_names) if gate_names else 0
    
    stats = DDStats(
        n_qubits_protected=circuit.num_qubits,
        n_sequences_inserted=n_sequences,
        avg_sequence_length=len(gate_names),
        total_pulses_added=n_dd_pulses,
        idle_time_protected=float(n_sequences * len(gate_names)),
        sequence_type=config.sequence.value,
    )
    
    return protected, stats


def estimate_dd_improvement(
    circuit,
    t1: float = 100e-6,
    t2: float = 50e-6,
    gate_time: float = 50e-9,
    sequence: DDSequence = DDSequence.XY4,
) -> Dict[str, Any]:
    """
    Estimate fidelity improvement from DD.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit to analyze
    t1 : float
        Amplitude damping time (seconds)
    t2 : float
        Dephasing time (seconds)
    gate_time : float
        Single-qubit gate duration (seconds)
    sequence : DDSequence
        DD sequence to use
    
    Returns
    -------
    dict
        Estimated fidelity with and without DD
    
    Notes
    -----
    This is a simplified model. Actual improvement depends on:
    - Noise spectrum
    - DD sequence choice
    - Pulse imperfections
    - Hardware constraints
    """
    # Estimate circuit duration
    depth = circuit.depth()
    duration = depth * gate_time
    
    # Fidelity without DD (exponential decay)
    f_no_dd = np.exp(-duration / t2)  # Dephasing dominates
    
    # DD suppression factor (sequence dependent)
    suppression_factors = {
        DDSequence.NONE: 1.0,
        DDSequence.HAHN_ECHO: 2.0,
        DDSequence.CPMG: 4.0,
        DDSequence.XY4: 8.0,
        DDSequence.XY8: 16.0,
        DDSequence.UR: 20.0,
    }
    
    factor = suppression_factors.get(sequence, 1.0)
    effective_t2 = t2 * factor
    
    # Fidelity with DD
    f_with_dd = np.exp(-duration / effective_t2)
    
    return {
        "fidelity_no_dd": float(f_no_dd),
        "fidelity_with_dd": float(f_with_dd),
        "improvement_factor": float(f_with_dd / f_no_dd),
        "effective_t2_multiplier": float(factor),
        "sequence": sequence.value,
        "circuit_duration_us": duration * 1e6,
    }


# Made with Bob