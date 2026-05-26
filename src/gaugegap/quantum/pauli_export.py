from __future__ import annotations

from collections.abc import Sequence
import math

import numpy as np

from gaugegap.models.z2_plaquette import MAX_EXACT_QUBITS, pauli_terms


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
        [
            (label, complex(coeff))
            for label, coeff in pauli_terms(n_plaquettes, plaquette_coupling, transverse_field)
        ]
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


def pauli_terms_to_dense(
    terms: Sequence[tuple[str, float | complex]],
    *,
    max_qubits: int | None = MAX_EXACT_QUBITS,
) -> np.ndarray:
    """Build a dense matrix from Qiskit-order Pauli labels.

    Labels are interpreted with the leftmost character acting on the highest
    indexed qubit, matching Qiskit's string convention. Thus qubit 0 is the
    rightmost character.
    """

    if not terms:
        raise ValueError("terms must not be empty")
    first_label = terms[0][0]
    if not isinstance(first_label, str) or not first_label:
        raise ValueError("Pauli labels must be non-empty strings")
    n_qubits = len(first_label)
    _validate_dense_size(n_qubits, max_qubits)

    dim = 1 << n_qubits
    matrix = np.zeros((dim, dim), dtype=np.complex128)
    for label, coeff in terms:
        _validate_label(label, n_qubits)
        c = _finite_complex(coeff)
        matrix += c * _pauli_label_matrix(label)
    return np.real_if_close(matrix)


def z2_plaquette_pauli_dense(
    n_plaquettes: int = 1,
    plaquette_coupling: float = 1.0,
    transverse_field: float = 0.2,
    *,
    max_qubits: int | None = MAX_EXACT_QUBITS,
) -> np.ndarray:
    return pauli_terms_to_dense(
        pauli_terms(n_plaquettes, plaquette_coupling, transverse_field),
        max_qubits=max_qubits,
    )


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


def _validate_label(label: str, n_qubits: int) -> None:
    if not isinstance(label, str) or not label:
        raise ValueError("Pauli labels must be non-empty strings")
    if len(label) != n_qubits:
        raise ValueError("all Pauli labels must have the same length")
    unsupported = sorted(set(label) - {"I", "X", "Y", "Z"})
    if unsupported:
        raise ValueError(f"unsupported Pauli operator(s): {''.join(unsupported)}")


def _validate_dense_size(n_qubits: int, max_qubits: int | None) -> None:
    if max_qubits is None:
        return
    if isinstance(max_qubits, bool) or not isinstance(max_qubits, int) or max_qubits < 1:
        raise ValueError("max_qubits must be a positive integer or None")
    if n_qubits > max_qubits:
        raise ValueError(
            "dense Pauli replica would require "
            f"{n_qubits} qubits; max_qubits is {max_qubits}"
        )


def _finite_complex(value: float | complex) -> complex:
    try:
        c = complex(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Pauli coefficients must be finite numbers") from exc
    if not (math.isfinite(c.real) and math.isfinite(c.imag)):
        raise ValueError("Pauli coefficients must be finite numbers")
    return c
