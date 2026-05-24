from __future__ import annotations

import importlib.util

import numpy as np


def qiskit_available() -> bool:
    return importlib.util.find_spec("qiskit") is not None


def z2_dual_chain_sparse_pauli(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    periodic: bool = False,
):
    if n_sites <= 1:
        raise ValueError("n_sites must be greater than 1")

    try:
        from qiskit.quantum_info import SparsePauliOp
    except ImportError as exc:
        raise RuntimeError("Install Qiskit extras with: python -m pip install -e '.[quantum]'") from exc

    terms: list[tuple[str, complex]] = []
    last_bond = n_sites if periodic else n_sites - 1

    for site in range(last_bond):
        terms.append((pauli_label(n_sites, {site: "Z", (site + 1) % n_sites: "Z"}), -exchange_coupling))

    for site in range(n_sites):
        terms.append((pauli_label(n_sites, {site: "X"}), -transverse_field))

    return SparsePauliOp.from_list(terms)


def qiskit_matrix(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    periodic: bool = False,
) -> np.ndarray:
    operator = z2_dual_chain_sparse_pauli(
        n_sites=n_sites,
        exchange_coupling=exchange_coupling,
        transverse_field=transverse_field,
        periodic=periodic,
    )
    return np.asarray(operator.to_matrix())


def qiskit_mass_gap(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    periodic: bool = False,
) -> tuple[float, float, float]:
    matrix = qiskit_matrix(
        n_sites=n_sites,
        exchange_coupling=exchange_coupling,
        transverse_field=transverse_field,
        periodic=periodic,
    )
    eigenvalues = np.linalg.eigvalsh(matrix)
    ground = float(eigenvalues[0].real)
    first = float(eigenvalues[1].real)
    return first - ground, ground, first


def pauli_label(n_sites: int, site_ops: dict[int, str]) -> str:
    label = ["I"] * n_sites
    for site, op in site_ops.items():
        label[n_sites - 1 - site] = op
    return "".join(label)
