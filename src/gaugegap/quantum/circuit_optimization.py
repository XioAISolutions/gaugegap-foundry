"""
Quantum Circuit Optimization Utilities

Mathematical Framework
----------------------
Circuit optimization reduces gate count and depth while preserving unitary equivalence:

1. Gate Cancellation:
   U U† = I (adjacent inverse gates cancel)
   
2. Gate Commutation:
   If [U, V] = 0, can reorder for better layout
   
3. Single-Qubit Gate Merging:
   Rz(θ₁)Rz(θ₂) = Rz(θ₁ + θ₂)
   
4. Two-Qubit Gate Reduction:
   CNOT-based circuits can be optimized via KAK decomposition

Claim Boundary Compliance
-------------------------
Circuit optimization preserves quantum state evolution and measurement outcomes.
It reduces resource requirements without changing physics or mathematical correctness.
Optimized circuits produce identical results to unoptimized versions (up to numerical precision).

References
----------
- Nielsen & Chuang (2010). Quantum Computation and Quantum Information
- Qiskit transpiler documentation
- Maslov (2016). Basic circuit compilation techniques for an ion-trap quantum machine
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class CircuitStats:
    """Statistics about a quantum circuit."""
    
    n_qubits: int
    depth: int
    gate_count: int
    two_qubit_gate_count: int
    gate_counts: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "n_qubits": self.n_qubits,
            "depth": self.depth,
            "gate_count": self.gate_count,
            "two_qubit_gate_count": self.two_qubit_gate_count,
            "gate_counts": dict(self.gate_counts),
        }


@dataclass
class OptimizationResult:
    """Result of circuit optimization."""
    
    original_stats: CircuitStats
    optimized_stats: CircuitStats
    gate_reduction: int
    depth_reduction: int
    two_qubit_reduction: int
    optimization_level: int
    
    def improvement_summary(self) -> Dict[str, float]:
        """Calculate improvement percentages."""
        orig_gates = self.original_stats.gate_count
        orig_depth = self.original_stats.depth
        orig_2q = self.original_stats.two_qubit_gate_count
        
        return {
            "gate_reduction_percent": 100 * self.gate_reduction / max(orig_gates, 1),
            "depth_reduction_percent": 100 * self.depth_reduction / max(orig_depth, 1),
            "two_qubit_reduction_percent": 100 * self.two_qubit_reduction / max(orig_2q, 1),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "original": self.original_stats.to_dict(),
            "optimized": self.optimized_stats.to_dict(),
            "gate_reduction": self.gate_reduction,
            "depth_reduction": self.depth_reduction,
            "two_qubit_reduction": self.two_qubit_reduction,
            "optimization_level": self.optimization_level,
            "improvement": self.improvement_summary(),
        }


def get_circuit_stats(circuit) -> CircuitStats:
    """
    Extract statistics from a Qiskit circuit.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Qiskit quantum circuit
    
    Returns
    -------
    CircuitStats
        Circuit statistics
    """
    gate_counts = dict(circuit.count_ops())
    
    # Count two-qubit gates
    two_qubit_gates = {'cx', 'cz', 'cy', 'swap', 'iswap', 'rzz', 'rxx', 'ryy', 'ecr'}
    two_qubit_count = sum(
        count for gate, count in gate_counts.items()
        if gate.lower() in two_qubit_gates
    )
    
    return CircuitStats(
        n_qubits=circuit.num_qubits,
        depth=circuit.depth(),
        gate_count=sum(gate_counts.values()),
        two_qubit_gate_count=two_qubit_count,
        gate_counts=gate_counts,
    )


def optimize_circuit(
    circuit,
    optimization_level: int = 2,
    basis_gates: Optional[List[str]] = None,
    coupling_map: Optional[List[List[int]]] = None,
) -> Tuple[Any, OptimizationResult]:
    """
    Optimize a quantum circuit using Qiskit transpiler.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit to optimize
    optimization_level : int
        Optimization level (0-3, higher = more optimization)
    basis_gates : list, optional
        Target basis gate set
    coupling_map : list, optional
        Hardware coupling map
    
    Returns
    -------
    optimized_circuit : QuantumCircuit
        Optimized circuit
    result : OptimizationResult
        Optimization statistics
    
    Raises
    ------
    RuntimeError
        If Qiskit is not installed
    """
    try:
        from qiskit import transpile
    except ImportError as exc:
        raise RuntimeError(
            "Install Qiskit extras with: python -m pip install -e '.[quantum]'"
        ) from exc
    
    # Get original stats
    original_stats = get_circuit_stats(circuit)
    
    # Transpile with optimization
    optimized = transpile(
        circuit,
        optimization_level=optimization_level,
        basis_gates=basis_gates,
        coupling_map=coupling_map,
    )
    
    # Get optimized stats
    optimized_stats = get_circuit_stats(optimized)
    
    # Calculate reductions
    result = OptimizationResult(
        original_stats=original_stats,
        optimized_stats=optimized_stats,
        gate_reduction=original_stats.gate_count - optimized_stats.gate_count,
        depth_reduction=original_stats.depth - optimized_stats.depth,
        two_qubit_reduction=original_stats.two_qubit_gate_count - optimized_stats.two_qubit_gate_count,
        optimization_level=optimization_level,
    )
    
    return optimized, result


def cancel_adjacent_inverses(circuit) -> Tuple[Any, int]:
    """
    Cancel adjacent inverse gate pairs (e.g., X followed by X).
    
    This is a simple optimization that removes U U† = I patterns.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit to optimize
    
    Returns
    -------
    optimized_circuit : QuantumCircuit
        Circuit with cancellations applied
    n_cancellations : int
        Number of gate pairs cancelled
    
    Note
    ----
    This is a simplified implementation. Full optimization requires
    DAG-based analysis as in Qiskit's transpiler.
    """
    try:
        from qiskit import QuantumCircuit
    except ImportError as exc:
        raise RuntimeError(
            "Install Qiskit extras with: python -m pip install -e '.[quantum]'"
        ) from exc
    
    # For now, use Qiskit's built-in optimization
    # A full implementation would analyze the DAG
    optimized, result = optimize_circuit(circuit, optimization_level=1)
    
    # Estimate cancellations from gate reduction
    n_cancellations = result.gate_reduction // 2
    
    return optimized, n_cancellations


def estimate_hardware_cost(
    circuit,
    backend_name: str = "ibm_generic",
    error_rates: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Estimate hardware execution cost and error rates.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit to analyze
    backend_name : str
        Target backend name
    error_rates : dict, optional
        Custom error rates (1q_gate, 2q_gate, readout)
    
    Returns
    -------
    dict
        Cost estimates including gate errors and total fidelity
    """
    stats = get_circuit_stats(circuit)
    
    # Default error rates (typical for IBM quantum systems)
    if error_rates is None:
        error_rates = {
            "1q_gate": 0.001,  # 0.1% single-qubit gate error
            "2q_gate": 0.01,   # 1% two-qubit gate error
            "readout": 0.01,   # 1% readout error
        }
    
    # Estimate single-qubit gates
    single_qubit_count = stats.gate_count - stats.two_qubit_gate_count
    
    # Estimate total error
    single_qubit_error = single_qubit_count * error_rates["1q_gate"]
    two_qubit_error = stats.two_qubit_gate_count * error_rates["2q_gate"]
    readout_error = stats.n_qubits * error_rates["readout"]
    
    total_error = single_qubit_error + two_qubit_error + readout_error
    
    # Estimate fidelity (1 - error for small errors)
    estimated_fidelity = max(0.0, 1.0 - total_error)
    
    return {
        "backend": backend_name,
        "n_qubits": stats.n_qubits,
        "depth": stats.depth,
        "single_qubit_gates": single_qubit_count,
        "two_qubit_gates": stats.two_qubit_gate_count,
        "single_qubit_error": single_qubit_error,
        "two_qubit_error": two_qubit_error,
        "readout_error": readout_error,
        "total_error": total_error,
        "estimated_fidelity": estimated_fidelity,
        "error_rates_used": error_rates,
    }


def suggest_optimization_strategy(
    circuit,
    target_backend: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Suggest optimization strategy based on circuit properties.
    
    Parameters
    ----------
    circuit : QuantumCircuit
        Circuit to analyze
    target_backend : str, optional
        Target backend name
    
    Returns
    -------
    dict
        Optimization recommendations
    """
    stats = get_circuit_stats(circuit)
    
    recommendations = []
    
    # Check circuit size
    if stats.n_qubits > 20:
        recommendations.append({
            "priority": "high",
            "issue": "Large qubit count",
            "suggestion": "Consider circuit partitioning or tensor network methods",
        })
    
    # Check depth
    if stats.depth > 100:
        recommendations.append({
            "priority": "high",
            "issue": "Deep circuit",
            "suggestion": "Apply gate cancellation and commutation optimization",
        })
    
    # Check two-qubit gate count
    two_qubit_ratio = stats.two_qubit_gate_count / max(stats.gate_count, 1)
    if two_qubit_ratio > 0.3:
        recommendations.append({
            "priority": "medium",
            "issue": "High two-qubit gate ratio",
            "suggestion": "Two-qubit gates have higher error rates; consider alternative decompositions",
        })
    
    # Suggest optimization level
    if stats.depth < 20 and stats.gate_count < 50:
        opt_level = 1
    elif stats.depth < 100 and stats.gate_count < 200:
        opt_level = 2
    else:
        opt_level = 3
    
    return {
        "circuit_stats": stats.to_dict(),
        "recommended_optimization_level": opt_level,
        "recommendations": recommendations,
        "target_backend": target_backend or "generic",
    }


# Made with Bob