"""GaugeGap: compact U(1) lattice gauge Hamiltonian in the electric basis.

This is a finite-system benchmark for U(1) pure gauge theory on a small
lattice, not a continuum Yang-Mills result.
"""
from __future__ import annotations

import numpy as np


def u1_link_operators(truncation: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return electric-field and raising/lowering operators for one U(1) link.

    The electric basis |m> has m in [-truncation, truncation].
    Dimension = 2 * truncation + 1.

    Returns (E, U_plus, U_minus) where:
    - E is diagonal with eigenvalues m
    - U_plus raises m -> m+1 (periodic: wraps truncation -> -truncation)
    - U_minus = U_plus^dagger
    """
    dim = 2 * truncation + 1
    E = np.diag(np.arange(-truncation, truncation + 1, dtype=np.float64))

    U_plus = np.zeros((dim, dim), dtype=np.float64)
    for m in range(-truncation, truncation):
        row = m + truncation + 1
        col = m + truncation
        U_plus[row, col] = 1.0
    U_plus[0, dim - 1] = 1.0

    U_minus = U_plus.T.copy()

    return E, U_plus, U_minus


def u1_plaquette_hamiltonian(
    n_links: int,
    g_electric: float,
    g_magnetic: float,
    truncation: int,
) -> np.ndarray:
    """Compact U(1) lattice gauge Hamiltonian for a 1D ring of links.

    H = (g_e^2 / 2) sum_l E_l^2  -  g_m sum_p (U_p + U_p^dagger)

    where the plaquette term for a 1D ring couples adjacent links:
    U_p = U_l U_{l+1}^dagger (analogous to a Wilson plaquette on a ladder).

    Parameters
    ----------
    n_links : int
        Number of gauge links on the ring (>= 2).
    g_electric : float
        Electric coupling constant.
    g_magnetic : float
        Magnetic (plaquette) coupling constant.
    truncation : int
        Electric field truncation: m in [-truncation, truncation].
    """
    if n_links < 2:
        raise ValueError("n_links must be at least 2")
    if truncation < 1:
        raise ValueError("truncation must be at least 1")

    link_dim = 2 * truncation + 1
    total_dim = link_dim ** n_links

    E_ops, U_plus_ops, U_minus_ops = [], [], []
    for _ in range(n_links):
        e, up, um = u1_link_operators(truncation)
        E_ops.append(e)
        U_plus_ops.append(up)
        U_minus_ops.append(um)

    H = np.zeros((total_dim, total_dim), dtype=np.float64)

    for l in range(n_links):
        op = _embed_operator(E_ops[l] @ E_ops[l], l, n_links, link_dim)
        H += (g_electric ** 2 / 2.0) * op

    for l in range(n_links):
        l2 = (l + 1) % n_links
        plaq = _embed_two_operators(
            U_plus_ops[l], U_minus_ops[l2], l, l2, n_links, link_dim
        )
        H -= g_magnetic * (plaq + plaq.T)

    return H


def _embed_operator(
    op: np.ndarray, site: int, n_sites: int, site_dim: int
) -> np.ndarray:
    total_dim = site_dim ** n_sites
    result = np.zeros((total_dim, total_dim), dtype=np.float64)

    block_outer = site_dim ** (n_sites - site - 1)
    block_inner = site_dim ** site

    for i in range(op.shape[0]):
        for j in range(op.shape[1]):
            if abs(op[i, j]) < 1e-15:
                continue
            for outer in range(site_dim ** (n_sites - site - 1)):
                for inner in range(site_dim ** site):
                    row = outer * (site_dim ** (site + 1)) + i * block_inner + inner
                    col = outer * (site_dim ** (site + 1)) + j * block_inner + inner
                    result[row, col] += op[i, j]

    return result


def _embed_two_operators(
    op_a: np.ndarray,
    op_b: np.ndarray,
    site_a: int,
    site_b: int,
    n_sites: int,
    site_dim: int,
) -> np.ndarray:
    if site_a == site_b:
        return _embed_operator(op_a @ op_b, site_a, n_sites, site_dim)

    total_dim = site_dim ** n_sites
    result = np.zeros((total_dim, total_dim), dtype=np.float64)

    A_full = _embed_operator(op_a, site_a, n_sites, site_dim)
    B_full = _embed_operator(op_b, site_b, n_sites, site_dim)
    result = A_full @ B_full

    return result


def u1_spectrum(
    n_links: int,
    g_electric: float,
    g_magnetic: float,
    truncation: int,
) -> np.ndarray:
    H = u1_plaquette_hamiltonian(n_links, g_electric, g_magnetic, truncation)
    return np.linalg.eigvalsh(H)


def u1_mass_gap(
    n_links: int,
    g_electric: float,
    g_magnetic: float,
    truncation: int,
) -> tuple[float, float, float]:
    eigenvalues = u1_spectrum(n_links, g_electric, g_magnetic, truncation)
    if eigenvalues.size < 2:
        raise ValueError("at least two eigenvalues are required to compute a gap")
    ground = float(eigenvalues[0])
    first = float(eigenvalues[1])
    return first - ground, ground, first


def u1_electric_field_expectation(
    state: np.ndarray,
    link: int,
    n_links: int,
    truncation: int,
) -> float:
    """Expectation value <state| E_link^2 |state> for a given link."""
    link_dim = 2 * truncation + 1
    E, _, _ = u1_link_operators(truncation)
    E2 = E @ E
    E2_full = _embed_operator(E2, link, n_links, link_dim)
    return float(state.conj() @ E2_full @ state)


def u1_wilson_loop_expectation(
    state: np.ndarray,
    links: list[int],
    n_links: int,
    truncation: int,
) -> complex:
    """Expectation of a product of U operators around a path."""
    link_dim = 2 * truncation + 1
    total_dim = link_dim ** n_links
    product = np.eye(total_dim, dtype=np.complex128)

    for l in links:
        _, U_plus, _ = u1_link_operators(truncation)
        U_full = _embed_operator(U_plus, l, n_links, link_dim)
        product = product @ U_full

    return complex(state.conj() @ product @ state)
