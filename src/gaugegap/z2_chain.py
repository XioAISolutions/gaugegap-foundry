from __future__ import annotations

import numpy as np


def hamiltonian_dense(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    periodic: bool = False,
) -> np.ndarray:
    """Return a dense transverse-field Ising Hamiltonian.

    This is a Z2 dual-chain sanity benchmark for the GaugeGap pipeline, not a
    continuum Yang-Mills Hamiltonian.
    """
    if n_sites <= 1:
        raise ValueError("n_sites must be greater than 1")

    dim = 1 << n_sites
    matrix = np.zeros((dim, dim), dtype=np.float64)
    last_bond = n_sites if periodic else n_sites - 1

    for state in range(dim):
        diagonal = 0.0
        for site in range(last_bond):
            left = _spin_z(state, site)
            right = _spin_z(state, (site + 1) % n_sites)
            diagonal += -exchange_coupling * left * right
        matrix[state, state] = diagonal

        for site in range(n_sites):
            flipped = state ^ (1 << site)
            matrix[flipped, state] += -transverse_field

    return matrix


def spectrum(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    periodic: bool = False,
) -> np.ndarray:
    matrix = hamiltonian_dense(
        n_sites=n_sites,
        exchange_coupling=exchange_coupling,
        transverse_field=transverse_field,
        periodic=periodic,
    )
    return np.linalg.eigvalsh(matrix)


def mass_gap(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    periodic: bool = False,
) -> tuple[float, float, float]:
    eigenvalues = spectrum(
        n_sites=n_sites,
        exchange_coupling=exchange_coupling,
        transverse_field=transverse_field,
        periodic=periodic,
    )
    if eigenvalues.size < 2:
        raise ValueError("at least two eigenvalues are required to compute a gap")
    ground = float(eigenvalues[0])
    first = float(eigenvalues[1])
    return first - ground, ground, first


def _spin_z(state: int, site: int) -> int:
    return -1 if state & (1 << site) else 1
