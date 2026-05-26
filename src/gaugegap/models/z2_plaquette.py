from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

CLAIM_BOUNDARY = (
    "Finite Z2 lattice gauge toy benchmark only; no continuum Yang-Mills "
    "mass-gap claim."
)
MAX_EXACT_QUBITS = 12


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
    if isinstance(n_plaquettes, bool) or not isinstance(n_plaquettes, int) or n_plaquettes < 1:
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


def validate_parameters(plaquette_coupling: float, transverse_field: float) -> tuple[float, float]:
    return (
        _finite_float("plaquette_coupling", plaquette_coupling),
        _finite_float("transverse_field", transverse_field),
    )


def pauli_label(n_qubits: int, site_ops: dict[int, str]) -> str:
    if isinstance(n_qubits, bool) or not isinstance(n_qubits, int) or n_qubits <= 0:
        raise ValueError("n_qubits must be positive")
    label = ["I"] * n_qubits
    for site, op in site_ops.items():
        if isinstance(site, bool) or not isinstance(site, int) or site < 0 or site >= n_qubits:
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

    coupling, field = validate_parameters(plaquette_coupling, transverse_field)
    layout = open_plaquette_chain_layout(n_plaquettes)
    terms: list[tuple[str, float]] = []
    for plaquette in layout.plaquettes:
        terms.append((pauli_label(layout.n_qubits, {link: "Z" for link in plaquette}), -coupling))
    for link in range(layout.n_qubits):
        terms.append((pauli_label(layout.n_qubits, {link: "X"}), -field))
    return terms


def hamiltonian_dense(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
    *,
    max_qubits: int | None = MAX_EXACT_QUBITS,
) -> np.ndarray:
    """Build the finite Z2 plaquette Hamiltonian as a dense matrix."""

    coupling, field = validate_parameters(plaquette_coupling, transverse_field)
    layout = open_plaquette_chain_layout(n_plaquettes)
    _validate_exact_size(layout, max_qubits)
    dim = 1 << layout.n_qubits
    matrix = np.zeros((dim, dim), dtype=np.float64)

    for state in range(dim):
        diagonal = 0.0
        for plaquette in layout.plaquettes:
            parity = 1
            for link in plaquette:
                parity *= _spin_z(state, link)
            diagonal += -coupling * parity
        matrix[state, state] = diagonal

        for link in range(layout.n_qubits):
            flipped = state ^ (1 << link)
            matrix[flipped, state] += -field

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


def ground_state(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> tuple[np.ndarray, np.ndarray]:
    """Return eigenvalues and a normalized ground-state vector."""

    matrix = hamiltonian_dense(
        n_plaquettes=n_plaquettes,
        plaquette_coupling=plaquette_coupling,
        transverse_field=transverse_field,
    )
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    return eigenvalues, eigenvectors[:, 0]


def state_observables(state: np.ndarray, layout: Z2PlaquetteLayout) -> dict[str, object]:
    """Measure plaquette-Z and link-X expectations on a statevector."""

    vector = np.asarray(state, dtype=np.complex128)
    dim = 1 << layout.n_qubits
    if vector.shape != (dim,):
        raise ValueError("state shape must match layout dimension")
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("state must have positive finite norm")
    vector = vector / norm
    probabilities = np.abs(vector) ** 2

    plaquette_z: list[float] = []
    for plaquette in layout.plaquettes:
        value = 0.0
        for basis, probability in enumerate(probabilities):
            parity = 1
            for link in plaquette:
                parity *= _spin_z(basis, link)
            value += float(probability) * parity
        plaquette_z.append(float(value))

    link_x: list[float] = []
    for link in range(layout.n_qubits):
        bit = 1 << link
        value = 0.0 + 0.0j
        for basis, amplitude in enumerate(vector):
            value += np.conj(vector[basis ^ bit]) * amplitude
        link_x.append(float(np.real_if_close(value)))

    return {
        "plaquette_z": plaquette_z,
        "mean_plaquette_z": float(np.mean(plaquette_z)) if plaquette_z else math.nan,
        "link_x": link_x,
        "mean_link_x": float(np.mean(link_x)) if link_x else math.nan,
    }


def ground_state_observables(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> dict[str, object]:
    _, state = ground_state(
        n_plaquettes=n_plaquettes,
        plaquette_coupling=plaquette_coupling,
        transverse_field=transverse_field,
    )
    layout = open_plaquette_chain_layout(n_plaquettes)
    return state_observables(state, layout)


def model_metadata(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> dict[str, object]:
    coupling, field = validate_parameters(plaquette_coupling, transverse_field)
    layout = open_plaquette_chain_layout(n_plaquettes)
    return {
        "model": "z2_open_plaquette_chain",
        "n_plaquettes": layout.n_plaquettes,
        "n_links": layout.n_links,
        "n_qubits": layout.n_qubits,
        "plaquettes": [list(item) for item in layout.plaquettes],
        "boundary": layout.boundary,
        "plaquette_coupling": coupling,
        "transverse_field": field,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _spin_z(state: int, site: int) -> int:
    return -1 if state & (1 << site) else 1


def _finite_float(name: str, value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _validate_exact_size(layout: Z2PlaquetteLayout, max_qubits: int | None) -> None:
    if max_qubits is None:
        return
    if isinstance(max_qubits, bool) or not isinstance(max_qubits, int) or max_qubits < 1:
        raise ValueError("max_qubits must be a positive integer or None")
    if layout.n_qubits > max_qubits:
        raise ValueError(
            "dense exact Hamiltonian would require "
            f"{layout.n_qubits} qubits; max_qubits is {max_qubits}"
        )
