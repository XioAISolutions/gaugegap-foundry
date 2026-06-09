"""
Quantum Computing Suite for Gauge Theories

This module provides comprehensive quantum computing capabilities including:
- Quantum information theory (entanglement, Fisher information)
- Topological quantum computing (anyonic braiding, Fibonacci anyons)
- Adiabatic quantum computing (annealing, shortcuts to adiabaticity)
- Quantum optimal control (GRAPE, CRAB, Krotov)
- Quantum metrology (Heisenberg limit, adaptive sensing)
- Quantum walks (discrete/continuous-time, search algorithms)
- Advanced compilation (Solovay-Kitaev, KAK decomposition)
- Quantum complexity theory (BQP, query complexity)
"""

from gaugegap.quantum.qiskit_validation import (
    QISKIT_CLAIM_BOUNDARY,
    QiskitValidationConfig,
    validate_qiskit_candidate,
)
from gaugegap.quantum.pauli_grouping import (
    pauli_commutes,
    group_pauli_terms,
    estimate_measurement_reduction,
    qiskit_grouped_measurement,
)

# Advanced quantum modules
from gaugegap.quantum import quantum_information
from gaugegap.quantum import topological_quantum
from gaugegap.quantum import adiabatic_quantum
from gaugegap.quantum import optimal_control
from gaugegap.quantum import quantum_metrology
from gaugegap.quantum import quantum_walks
from gaugegap.quantum import advanced_compilation
from gaugegap.quantum import quantum_complexity

__all__ = [
    # Core validation and grouping
    "QISKIT_CLAIM_BOUNDARY",
    "QiskitValidationConfig",
    "validate_qiskit_candidate",
    "pauli_commutes",
    "group_pauli_terms",
    "estimate_measurement_reduction",
    "qiskit_grouped_measurement",
    # Advanced quantum modules
    "quantum_information",
    "topological_quantum",
    "adiabatic_quantum",
    "optimal_control",
    "quantum_metrology",
    "quantum_walks",
    "advanced_compilation",
    "quantum_complexity",
]
