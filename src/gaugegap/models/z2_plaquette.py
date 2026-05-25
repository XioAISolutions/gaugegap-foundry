from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

CLAIM_BOUNDARY = (
    "Finite Z2 lattice gauge toy benchmark only; no continuum Yang-Mills "
    "mass-gap claim."
)


@dataclass(frozen=True)
class Z2PlaquetteLayout:
    """Open chain of square plaquettes represented by link qubits.

    The one-plaquette layout has 4 links/qubits. A two-plaquette layout has 7
    links/qubits because adjacent plaquettes share one link. This is a tiny
    finite gauge benchmark designed to keep exact diagonalization and Pauli
    export transparent.
    """

    n_plaquettes: int
    plaquettes: tuple[tuple[int, int, int, int], ...]
    n_links: int
    boundary: str = "open-plaquette-chain"

    @property
    def n_qubits(self) -> int:
        return self.n_links


def open_plaquette_chain_layout(n_plaquettes: int = 1) -> Z2PlaquetteLayout:
    if not isinstance(n_plaquettes, int) or n_plaquettes < 1:
        raise ValueError("n_plaquettes must be a positive integer")
    plaquettes = tuple(
        (3 * index, 3 * index + 1, 3 * index + 2, 3 * index + 3)
        for index in range(n_plaquettes)
    )
    return Z2PlaquetteLayout(
        n_plaquettes=n_plaquettes,
        plaquettes=plaquettes,
        n_links=3 * n_plaquettes + 1,
    )


def validate_parameters(plaquette_coupling: float, transverse_field: float) -> None:
    if not math.isfinite(float(plaquette_coupling)):
        raise ValueError("plaquette_coupling must be finite")
    if not math.isfinite(float(transverse_field)):
        raise ValueError("transverse_field must be finite")


def pauli_label(n_qubits: int, site_ops: dict[int, str]) -> str:
    if n_qubits <= 0:
        raise ValueError("n_qubits must be positive")
    label = ["I"] * n_qubits
    for site, op in site_ops.items():
        if site < 0 or site >= n_qubits:
            raise ValueError(f"site {site} is outside 0..{n_qubits - 1}")
        if op not in {"I", "X", "Y", "Z"}:
            raise ValueError(f"unsupported Pauli operator: {op}")
        label[n_qubits - 1 - site] = op
    return "".join(label)


def pauli_terms(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> list[tuple[str, float]]:
    """Return Pauli-label terms for H = -J sum_p prod Z_l - h sum_l X_l."""

    validate_parameters(plaquette_coupling, transverse_field)
    layout = open_plaquette_chain_layout(n_plaquettes)
    terms: list[tuple[str, float]] = []
    for plaquette in layout.plaquettes:
        terms.append((pauli_label(layout.n_qubits, {link: "Z" for link in plaquette}), -float(plaquette_coupling)))
    for link in range(layout.n_qubits):
        terms.append((pauli_label(layout.n_qubits, {link: "X"}), -float(transverse_field)))
    return terms


def hamiltonian_dense(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> np.ndarray:
    """Build the finite Z2 plaquette Hamiltonian as a dense matrix."""

    validate_parameters(plaquette_coupling, transverse_field)
    layout = open_plaquette_chain_layout(n_plaquettes)
    dim = 1 << layout.n_qubits
    matrix = np.zeros((dim, dim), dtype=np.float64)

    for state in range(dim):
        diagonal = 0.0
        for plaquette in layout.plaquettes:
            parity = 1
            for link in plaquette:
                parity *= _spin_z(state, link)
            diagonal += -float(plaquette_coupling) * parity
        matrix[state, state] = diagonal

        for link in range(layout.n_qubits):
            flipped = state ^ (1 << link)
            matrix[flipped, state] += -float(transverse_field)

    return matrix


def spectrum(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> np.ndarray:
    return np.linalg.eigvalsh(
        hamiltonian_dense(
            n_plaquettes=n_plaquettes,
            plaquette_coupling=plaquette_coupling,
            transverse_field=transverse_field,
        )
    )


def mass_gap(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> tuple[float, float, float]:
    eig = spectrum(
        n_plaquettes=n_plaquettes,
        plaquette_coupling=plaquette_coupling,
        transverse_field=transverse_field,
    )
    if eig.size < 2:
        raise ValueError("at least two eigenvalues are required to compute a gap")
    ground = float(eig[0])
    first = float(eig[1])
    return first - ground, ground, first


def model_metadata(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> dict[str, object]:
    layout = open_plaquette_chain_layout(n_plaquettes)
    return {
        "model": "z2_open_plaquette_chain",
        "n_plaquettes": layout.n_plaquettes,
        "n_links": layout.n_links,
        "n_qubits": layout.n_qubits,
        "plaquettes": [list(item) for item in layout.plaquettes],
        "boundary": layout.boundary,
        "plaquette_coupling": float(plaquette_coupling),
        "transverse_field": float(transverse_field),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _spin_z(state: int, site: int) -> int:
    return -1 if state & (1 << site) else 1
