"""Certified Berry-Keating spectral-screening pipeline.

This orchestration layer wires together the rigorous interval-arithmetic
machinery (``gaugegap.rigorous``) and the CurveRank operator/zero builders so
that the headline "Berry-Keating impossibility" result is computed as a
*machine-checked certified bound* rather than a floating-point estimate.

Pipeline
--------
1. ``berry_keating_xp_interval``     -> exact interval matrix (real embedding)
2. ``verified_hermitian_eigenvalues`` -> certified eigenvalue enclosures
3. collapse the doubled embedding spectrum -> the operator's n enclosures
4. ``certified_spectral_mismatch`` vs ``riemann_zero_intervals``
                                     -> certified lower bound on M_n

CLAIM BOUNDARY:
This certifies that a *finite truncation* of the Berry-Keating xp operator is
provably separated from the first k Riemann zeros.  It does NOT extrapolate to
a continuum/infinite limit and does NOT claim to prove or disprove the Riemann
Hypothesis or the Hilbert-Polya conjecture.
"""
from __future__ import annotations

from typing import List

from gaugegap.curverank_operators import (
    berry_keating_xp_interval,
    dirac_rindler_interval,
    quantum_graph_laplacian_interval,
)
from gaugegap.curverank_spectral import (
    certified_spectral_mismatch,
    riemann_zero_intervals,
)
from gaugegap.rigorous.interval_arithmetic import Interval, verified_hermitian_eigenvalues


def _collapse_doubled_spectrum(enclosures: List[Interval]) -> List[Interval]:
    """Collapse the doubled spectrum of the real embedding to operator eigenvalues.

    The ``2n x 2n`` real embedding of the complex Hermitian xp operator has each
    eigenvalue with multiplicity two.  Sorted ascending, consecutive pairs
    ``(2k, 2k+1)`` bracket the k-th operator eigenvalue; we merge each pair into
    a single enclosure (union of the two), which still rigorously contains it.
    """
    if len(enclosures) % 2 != 0:
        raise ValueError("expected an even number of enclosures from the embedding")
    merged: List[Interval] = []
    for k in range(len(enclosures) // 2):
        a = enclosures[2 * k]
        b = enclosures[2 * k + 1]
        merged.append(Interval(min(a.lower, b.lower), max(a.upper, b.upper)))
    return merged


def certified_xp_spectrum(n_basis: int, L: float = 1.0) -> List[Interval]:
    """Return certified eigenvalue enclosures of the n-truncated xp operator."""
    embedding = berry_keating_xp_interval(n_basis, L)
    doubled = verified_hermitian_eigenvalues(embedding)
    return _collapse_doubled_spectrum(doubled)


def certified_xp_mismatch(n_basis: int, k_zeros: int, L: float = 1.0) -> Interval:
    """Certified enclosure of the spectral mismatch ``M_n`` for the xp operator.

    The lower endpoint is a rigorous lower bound on how far the operator's
    spectrum is from the first ``k_zeros`` Riemann zeros.
    """
    eig_intervals = certified_xp_spectrum(n_basis, L)
    zero_intervals = riemann_zero_intervals(k_zeros)
    return certified_spectral_mismatch(eig_intervals, zero_intervals)


def certified_dirac_rindler_spectrum(
    n_basis: int, acceleration: float = 1.0, mass: float = 0.0
) -> List[Interval]:
    """Certified eigenvalue enclosures of the truncated Dirac-Rindler operator."""
    embedding = dirac_rindler_interval(n_basis, acceleration, mass)
    doubled = verified_hermitian_eigenvalues(embedding)
    return _collapse_doubled_spectrum(doubled)


def certified_quantum_graph_spectrum(
    edges, lengths, n_modes: int
) -> List[Interval]:
    """Certified eigenvalue enclosures of a quantum-graph Laplacian.

    The operator is real symmetric, so the verified enclosures apply directly
    (no degenerate-pair collapse).
    """
    matrix = quantum_graph_laplacian_interval(edges, lengths, n_modes)
    return verified_hermitian_eigenvalues(matrix)


# Default quantum-graph geometry (star graph with three incommensurate edges).
_DEFAULT_GRAPH_EDGES = [(0, 1), (0, 2), (0, 3)]


def certified_family_mismatch(family: str, n: int, k_zeros: int, **kwargs) -> Interval:
    """Certified spectral mismatch ``M_n`` for a named candidate operator family.

    Parameters
    ----------
    family : {"xp", "dirac_rindler", "quantum_graph"}
        Candidate operator family.
    n : int
        Truncation size (``n_basis`` for xp/dirac, ``n_modes`` for quantum_graph).
    k_zeros : int
        Number of Riemann zeros to compare against.
    """
    if family == "xp":
        eigs = certified_xp_spectrum(n, kwargs.get("L", 1.0))
    elif family == "dirac_rindler":
        eigs = certified_dirac_rindler_spectrum(
            n, kwargs.get("acceleration", 1.0), kwargs.get("mass", 0.0)
        )
    elif family == "quantum_graph":
        import numpy as np

        edges = kwargs.get("edges", _DEFAULT_GRAPH_EDGES)
        lengths = kwargs.get("lengths", [1.0, float(np.sqrt(2)), float(np.sqrt(3))])
        eigs = certified_quantum_graph_spectrum(edges, lengths, n)
    else:
        raise ValueError(
            f"unknown family {family!r}; choose from "
            "'xp', 'dirac_rindler', 'quantum_graph'"
        )
    return certified_spectral_mismatch(eigs, riemann_zero_intervals(k_zeros))
