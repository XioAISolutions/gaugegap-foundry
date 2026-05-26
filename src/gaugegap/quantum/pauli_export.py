from __future__ import annotations

import numpy as np

from gaugegap.models.z2_plaquette import pauli_terms


def qiskit_available() -> bool:
    try:
        import qiskit  # noqa: F401
    except ImportError:
        return False
    return True


def z2_plaquette_sparse_pauli(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
):
    """Return a Qiskit SparsePauliOp for the finite Z2 plaquette model."""

    try:
        from qiskit.quantum_info import SparsePauliOp
    except ImportError as exc:
        raise RuntimeError("Install Qiskit extras with: python -m pip install -e '.[quantum]'") from exc
    return SparsePauliOp.from_list(
        [(label, complex(coeff)) for label, coeff in pauli_terms(n_plaquettes, plaquette_coupling, transverse_field)]
    )


def qiskit_matrix(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> np.ndarray:
    operator = z2_plaquette_sparse_pauli(
        n_plaquettes=n_plaquettes,
        plaquette_coupling=plaquette_coupling,
        transverse_field=transverse_field,
    )
    return np.asarray(operator.to_matrix())


def pauli_terms_to_dense(terms: list[tuple[str, float | complex]]) -> np.ndarray:
    if not terms:
        raise ValueError("terms must not be empty")
    n_qubits = len(terms[0][0])
    if any(len(label) != n_qubits for label, _ in terms):
        raise ValueError("all Pauli labels must have the same length")

    dim = 1 << n_qubits
    matrix = np.zeros((dim, dim), dtype=np.complex128)
    for label, coeff in terms:
        matrix += complex(coeff) * _pauli_label_matrix(label)
    return np.real_if_close(matrix)


def z2_plaquette_pauli_dense(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
) -> np.ndarray:
    return pauli_terms_to_dense(pauli_terms(n_plaquettes, plaquette_coupling, transverse_field))


def _pauli_label_matrix(label: str) -> np.ndarray:
    mats = {
        "I": np.array([[1, 0], [0, 1]], dtype=np.complex128),
        "X": np.array([[0, 1], [1, 0]], dtype=np.complex128),
        "Y": np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
        "Z": np.array([[1, 0], [0, -1]], dtype=np.complex128),
    }
    result = np.array([[1]], dtype=np.complex128)
    for op in label:
        try:
            factor = mats[op]
        except KeyError as exc:
            raise ValueError(f"unsupported Pauli operator in label {label!r}: {op}") from exc
        result = np.kron(result, factor)
    return result
