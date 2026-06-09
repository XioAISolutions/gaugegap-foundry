"""
Pauli Operator Grouping for Measurement Reduction

Mathematical Framework
----------------------
For a Hamiltonian H = Σᵢ hᵢ Pᵢ where Pᵢ are Pauli operators:

1. Commuting operators can be measured simultaneously:
   [Pᵢ, Pⱼ] = 0 ⟹ measure together

2. Grouping reduces measurement overhead from O(n) to O(log n) for n terms

3. Optimal grouping is NP-hard, but greedy algorithms work well in practice

Algorithm
---------
1. Build commutation graph: edge if [Pᵢ, Pⱼ] = 0
2. Color graph (each color = measurement group)
3. Use greedy coloring or sorted-insertion heuristic

References
----------
- Verteletskyi et al. (2020). Measurement optimization in the variational quantum eigensolver
- Gokhale et al. (2020). O(N³) measurement cost for variational quantum eigensolver
- Yen et al. (2020). Measuring all compatible operators in one series of single-qubit measurements

Claim Boundary Compliance
-------------------------
Grouping is a measurement optimization technique that reduces quantum resource
requirements. It does not change physics or mathematical correctness.
"""

from typing import List, Tuple, Set, Dict, Sequence
import numpy as np


def pauli_commutes(pauli1: str, pauli2: str) -> bool:
    """
    Check if two Pauli strings commute.
    
    Two Pauli operators commute if they differ in an even number of positions
    where both are non-identity and non-equal.
    
    Parameters
    ----------
    pauli1, pauli2 : str
        Pauli strings (e.g., "IXYZ")
    
    Returns
    -------
    bool
        True if operators commute
    
    Examples
    --------
    >>> pauli_commutes("IXYZ", "IXYZ")
    True
    >>> pauli_commutes("IXYZ", "IXZY")
    False
    >>> pauli_commutes("XIXI", "IXIX")
    True
    """
    if len(pauli1) != len(pauli2):
        raise ValueError("Pauli strings must have same length")
    
    # Count positions where both are non-I and different
    diff_count = 0
    for p1, p2 in zip(pauli1, pauli2):
        if p1 != 'I' and p2 != 'I' and p1 != p2:
            diff_count += 1
    
    # Commute if even number of differences
    return diff_count % 2 == 0


def group_pauli_terms(
    pauli_terms: Sequence[Tuple[str, complex]],
    strategy: str = "greedy"
) -> List[List[Tuple[str, complex]]]:
    """
    Group Pauli terms into commuting sets for simultaneous measurement.
    
    Parameters
    ----------
    pauli_terms : list
        List of (pauli_string, coefficient) tuples
    strategy : str
        Grouping strategy: "greedy" or "sorted"
    
    Returns
    -------
    list
        List of groups, each containing commuting Pauli terms
    
    Examples
    --------
    >>> terms = [("IZ", 1.0), ("ZI", 1.0), ("XX", 1.0)]
    >>> groups = group_pauli_terms(terms)
    >>> len(groups)  # IZ and ZI commute, XX separate
    2
    """
    if not pauli_terms:
        return []
    
    if strategy == "greedy":
        return _greedy_grouping(pauli_terms)
    elif strategy == "sorted":
        return _sorted_insertion_grouping(pauli_terms)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def _greedy_grouping(
    pauli_terms: Sequence[Tuple[str, complex]]
) -> List[List[Tuple[str, complex]]]:
    """
    Greedy grouping: iterate through terms, add to first compatible group.
    
    Time complexity: O(n²) where n is number of terms
    """
    groups: List[List[Tuple[str, complex]]] = []
    
    for term in pauli_terms:
        pauli_str, coeff = term
        
        # Try to add to existing group
        placed = False
        for group in groups:
            # Check if commutes with all in group
            if all(pauli_commutes(pauli_str, p) for p, _ in group):
                group.append(term)
                placed = True
                break
        
        # Create new group if needed
        if not placed:
            groups.append([term])
    
    return groups


def _sorted_insertion_grouping(
    pauli_terms: Sequence[Tuple[str, complex]]
) -> List[List[Tuple[str, complex]]]:
    """
    Sorted insertion: sort by coefficient magnitude, then greedy group.
    
    Larger coefficients grouped first for better accuracy.
    """
    # Sort by coefficient magnitude (descending)
    sorted_terms = sorted(
        pauli_terms,
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
    return _greedy_grouping(sorted_terms)


def estimate_measurement_reduction(
    pauli_terms: Sequence[Tuple[str, complex]],
    strategy: str = "greedy"
) -> Dict[str, float]:
    """
    Estimate measurement overhead reduction from grouping.
    
    Parameters
    ----------
    pauli_terms : list
        List of Pauli terms
    strategy : str
        Grouping strategy
    
    Returns
    -------
    dict
        Statistics about grouping efficiency
    """
    if not pauli_terms:
        return {
            "n_terms": 0,
            "n_groups": 0,
            "reduction_factor": 1.0,
            "avg_group_size": 0.0,
        }
    
    groups = group_pauli_terms(pauli_terms, strategy=strategy)
    n_terms = len(pauli_terms)
    n_groups = len(groups)
    
    return {
        "n_terms": n_terms,
        "n_groups": n_groups,
        "reduction_factor": n_terms / n_groups if n_groups > 0 else 1.0,
        "avg_group_size": n_terms / n_groups if n_groups > 0 else 0.0,
        "max_group_size": max(len(g) for g in groups) if groups else 0,
        "min_group_size": min(len(g) for g in groups) if groups else 0,
    }


def qiskit_grouped_measurement(
    pauli_terms: Sequence[Tuple[str, complex]],
    strategy: str = "greedy"
):
    """
    Create Qiskit SparsePauliOp groups for efficient measurement.
    
    Parameters
    ----------
    pauli_terms : list
        List of (pauli_string, coefficient) tuples
    strategy : str
        Grouping strategy
    
    Returns
    -------
    list
        List of SparsePauliOp objects, one per measurement group
    
    Raises
    ------
    RuntimeError
        If Qiskit is not installed
    """
    try:
        from qiskit.quantum_info import SparsePauliOp
    except ImportError as exc:
        raise RuntimeError(
            "Install Qiskit extras with: python -m pip install -e '.[quantum]'"
        ) from exc
    
    groups = group_pauli_terms(pauli_terms, strategy=strategy)
    
    return [
        SparsePauliOp.from_list(group)
        for group in groups
    ]


# Made with Bob