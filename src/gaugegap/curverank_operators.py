"""CurveRank: candidate Hilbert-Polya operator construction.

These are toy truncated operators for spectral screening, not a proof of the
Riemann Hypothesis.
"""
from __future__ import annotations

import numpy as np


def berry_keating_xp(n_basis: int, L: float = 1.0) -> np.ndarray:
    """Truncated Berry-Keating xp-type operator on a finite interval [0, L].

    Uses a position-space discretization of the symmetrized xp operator:
        H = (1/2)(xp + px) = -i(x d/dx + 1/2)
    on [0, L] with Dirichlet-like boundary conditions.

    Returns a Hermitian matrix whose eigenvalues can be compared against
    Riemann zeta zero imaginary parts.
    """
    if n_basis < 2:
        raise ValueError("n_basis must be at least 2")

    dx = L / (n_basis + 1)
    x = np.array([dx * (k + 1) for k in range(n_basis)])

    H = np.zeros((n_basis, n_basis), dtype=np.complex128)

    for i in range(n_basis):
        H[i, i] = -0.5j

    for i in range(n_basis):
        for j in range(n_basis):
            if i == j:
                continue
            H[i, j] = -1j * x[i] * _sinc_derivative_element(i, j, n_basis, dx)

    H = 0.5 * (H + H.conj().T)
    return H


def _sinc_derivative_element(i: int, j: int, n: int, dx: float) -> float:
    if i == j:
        return 0.0
    return ((-1.0) ** (i - j)) / ((i - j) * dx)


def berry_keating_xp_interval(n_basis: int, L: float = 1.0):
    """Certified interval-matrix form of the Berry-Keating xp operator.

    Builds the *same* symmetrized operator as :func:`berry_keating_xp`, but in
    exact (mpmath) interval arithmetic so that downstream certified eigenvalue
    enclosures are rigorous rather than floating-point estimates.

    After symmetrization the operator is purely imaginary Hermitian with
    entries ``H_ij = i * M_ij`` where ``M`` is the real antisymmetric matrix
    ``M_ij = -0.5 * s_ij * (x_i + x_j)`` (and ``M_ii = 0``), with
    ``s_ij = (-1)^(i-j) / ((i-j) * dx)``.  A complex Hermitian matrix
    ``H = i*M`` has the same spectrum (each eigenvalue doubled) as the real
    symmetric ``2n x 2n`` matrix ``[[0, -M], [M, 0]]``; we return that real
    embedding so it can be fed to
    :func:`gaugegap.rigorous.interval_arithmetic.verified_hermitian_eigenvalues`.

    Use :func:`gaugegap.curverank_certified.certified_xp_spectrum` to recover
    the ``n`` (un-doubled) certified eigenvalue enclosures of the operator.

    Returns
    -------
    IntervalMatrix
        A real symmetric ``2*n_basis x 2*n_basis`` interval matrix.
    """
    if n_basis < 2:
        raise ValueError("n_basis must be at least 2")

    import mpmath as mp  # local import: keeps the float-only API dependency-free
    from gaugegap.rigorous.interval_arithmetic import Interval, IntervalMatrix

    n = n_basis
    dx = mp.mpf(L) / (n + 1)
    x = [dx * (k + 1) for k in range(n)]

    # Real antisymmetric coefficient matrix M (imaginary part of H), exact.
    M = [[mp.mpf(0) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            s_ij = mp.mpf((-1) ** (i - j)) / ((i - j) * dx)
            M[i][j] = mp.mpf("-0.5") * s_ij * (x[i] + x[j])

    dim = 2 * n
    zero = Interval(mp.mpf(0), mp.mpf(0))
    entries = [[zero for _ in range(dim)] for _ in range(dim)]
    for i in range(n):
        for j in range(n):
            # Top-right block = -M, bottom-left block = +M.
            neg = -M[i][j]
            entries[i][j + n] = Interval(neg, neg)
            entries[i + n][j] = Interval(M[i][j], M[i][j])
    return IntervalMatrix(entries)


def quantum_graph_laplacian(
    edges: list[tuple[int, int]],
    lengths: list[float],
    n_modes: int,
) -> np.ndarray:
    """Spectral operator from a quantum graph (negative Laplacian).

    Constructs a truncated matrix from the secular equation of a metric graph.
    For a simple star graph, this yields eigenvalues related to the graph's
    spectral zeta function.

    Parameters
    ----------
    edges : list of (int, int)
        Vertex pairs defining graph edges.
    lengths : list of float
        Metric length of each edge.
    n_modes : int
        Number of basis functions (Fourier modes per edge).
    """
    if len(edges) != len(lengths):
        raise ValueError("edges and lengths must have the same length")
    if n_modes < 1:
        raise ValueError("n_modes must be at least 1")

    n_edges = len(edges)
    dim = n_edges * n_modes
    H = np.zeros((dim, dim), dtype=np.float64)

    for e_idx, length in enumerate(lengths):
        for m in range(n_modes):
            k = (m + 1) * np.pi / length
            row = e_idx * n_modes + m
            H[row, row] = k * k

    vertices: dict[int, list[int]] = {}
    for e_idx, (u, v) in enumerate(edges):
        vertices.setdefault(u, []).append(e_idx)
        vertices.setdefault(v, []).append(e_idx)

    coupling_strength = 1.0
    for vertex, edge_list in vertices.items():
        for i_idx in range(len(edge_list)):
            for j_idx in range(i_idx + 1, len(edge_list)):
                e_i = edge_list[i_idx]
                e_j = edge_list[j_idx]
                for m in range(n_modes):
                    row = e_i * n_modes + m
                    col = e_j * n_modes + m
                    H[row, col] += coupling_strength
                    H[col, row] += coupling_strength

    return H


def dirac_rindler_truncated(
    n_basis: int,
    acceleration: float = 1.0,
    mass: float = 0.0,
) -> np.ndarray:
    """Truncated Dirac-type operator in Rindler coordinates.

    Motivated by the Berry-Keating / Sierra construction where the
    Rindler Hamiltonian's spectrum should encode zeta zero information
    under appropriate boundary conditions.

    Parameters
    ----------
    n_basis : int
        Truncation size.
    acceleration : float
        Rindler acceleration parameter.
    mass : float
        Fermion mass parameter.
    """
    if n_basis < 2:
        raise ValueError("n_basis must be at least 2")

    dx = 1.0 / (n_basis + 1)
    xi = np.array([dx * (k + 1) for k in range(n_basis)])

    dim = 2 * n_basis
    H = np.zeros((dim, dim), dtype=np.complex128)

    for i in range(n_basis):
        if mass != 0:
            H[i, i + n_basis] = mass
            H[i + n_basis, i] = mass

    for i in range(n_basis):
        rindler_x = np.exp(acceleration * xi[i])
        for j in range(n_basis):
            if i != j:
                deriv = _sinc_derivative_element(i, j, n_basis, dx)
                H[i, j + n_basis] += -1j * rindler_x * deriv
                H[j + n_basis, i] += 1j * rindler_x * deriv

    H = 0.5 * (H + H.conj().T)
    return H


def generate_candidate_family(
    family: str,
    n_basis_range: list[int],
    **kwargs,
) -> list[dict[str, object]]:
    """Generate a family of candidate operators at varying truncations."""
    builders = {
        "xp": lambda n: berry_keating_xp(n, kwargs.get("L", 1.0)),
        "quantum_graph": lambda n: quantum_graph_laplacian(
            kwargs.get("edges", [(0, 1), (0, 2), (0, 3)]),
            kwargs.get("lengths", [1.0, np.sqrt(2), np.sqrt(3)]),
            n,
        ),
        "dirac_rindler": lambda n: dirac_rindler_truncated(
            n,
            kwargs.get("acceleration", 1.0),
            kwargs.get("mass", 0.0),
        ),
    }

    if family not in builders:
        raise ValueError(f"unknown family '{family}', choose from {list(builders)}")

    results = []
    for n in n_basis_range:
        H = builders[family](n)
        results.append({
            "family": family,
            "n_basis": n,
            "operator": H,
            "dim": H.shape[0],
        })
    return results
