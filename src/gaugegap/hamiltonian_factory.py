"""Canonical Hamiltonian construction and audit surface for GaugeGap models.

The factory gives every supported finite model one normalized entry point and one
common audit contract. Prototype models remain explicitly labelled as such;
normalizing construction does not upgrade their scientific maturity.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

import numpy as np


@dataclass(frozen=True)
class HamiltonianArtifact:
    model_id: str
    matrix: np.ndarray
    parameters: Mapping[str, object]
    implementation_status: str
    claim_boundary: str
    metadata: Mapping[str, object]

    @property
    def dimension(self) -> int:
        return int(self.matrix.shape[0])

    def digest(self) -> str:
        hasher = hashlib.sha256()
        hasher.update(self.model_id.encode("utf-8"))
        hasher.update(json.dumps(dict(self.parameters), sort_keys=True, default=str).encode("utf-8"))
        array = np.ascontiguousarray(self.matrix)
        hasher.update(str(array.dtype).encode("ascii"))
        hasher.update(str(array.shape).encode("ascii"))
        hasher.update(array.view(np.uint8))
        return hasher.hexdigest()


@dataclass(frozen=True)
class HamiltonianAudit:
    model_id: str
    dimension: int
    finite: bool
    square: bool
    hermiticity_residual: float
    hermitian: bool
    spectral_gap: float | None
    ground_energy: float | None
    first_excited_energy: float | None
    trace_real: float | None
    trace_imaginary: float | None
    matrix_digest: str
    implementation_status: str
    claim_boundary: str

    def summary(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "dimension": self.dimension,
            "finite": self.finite,
            "square": self.square,
            "hermiticity_residual": self.hermiticity_residual,
            "hermitian": self.hermitian,
            "spectral_gap": self.spectral_gap,
            "ground_energy": self.ground_energy,
            "first_excited_energy": self.first_excited_energy,
            "trace_real": self.trace_real,
            "trace_imaginary": self.trace_imaginary,
            "matrix_digest": self.matrix_digest,
            "implementation_status": self.implementation_status,
            "claim_boundary": self.claim_boundary,
        }


def registered_models() -> tuple[str, ...]:
    return (
        "z2-plaquette",
        "u1-plaquette",
        "su2-one-plaquette-verified",
        "su2-pure-prototype",
        "su3-pure-prototype",
    )


def build_hamiltonian(model_id: str, **parameters: object) -> HamiltonianArtifact:
    """Build one registered finite Hamiltonian with normalized metadata."""
    model = model_id.lower()
    if model == "z2-plaquette":
        from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY, hamiltonian_dense, model_metadata

        params = {
            "n_plaquettes": int(parameters.get("n_plaquettes", 1)),
            "plaquette_coupling": float(parameters.get("plaquette_coupling", 1.0)),
            "transverse_field": float(parameters.get("transverse_field", 0.2)),
        }
        matrix = hamiltonian_dense(**params)
        metadata = model_metadata(**params)
        return HamiltonianArtifact(
            model_id=model,
            matrix=np.asarray(matrix, dtype=np.complex128),
            parameters=params,
            implementation_status="finite_reference",
            claim_boundary=CLAIM_BOUNDARY,
            metadata=metadata,
        )

    if model == "u1-plaquette":
        from gaugegap.gaugegap_u1 import u1_plaquette_hamiltonian

        params = {
            "n_links": int(parameters.get("n_links", 2)),
            "g_electric": float(parameters.get("g_electric", 1.0)),
            "g_magnetic": float(parameters.get("g_magnetic", 0.5)),
            "truncation": int(parameters.get("truncation", 1)),
        }
        matrix = u1_plaquette_hamiltonian(**params)
        return HamiltonianArtifact(
            model_id=model,
            matrix=np.asarray(matrix, dtype=np.complex128),
            parameters=params,
            implementation_status="finite_truncated_reference",
            claim_boundary=(
                "finite compact U(1) electric-basis truncation only; no continuum "
                "gauge-theory or universal mass-gap claim"
            ),
            metadata={
                "link_dimension": 2 * params["truncation"] + 1,
                "hilbert_dimension": int(matrix.shape[0]),
            },
        )

    if model == "su2-one-plaquette-verified":
        from gaugegap.verified_su2_gap import (
            CLAIM_BOUNDARY,
            GaugeInvariantBasis,
            dense_float,
            direct_matrix_exact,
            fraction_text,
        )

        params = {
            "max_two_j": int(parameters.get("max_two_j", 1)),
            "electric": str(parameters.get("electric", "1")),
            "magnetic": str(parameters.get("magnetic", "1/2")),
        }
        basis = GaugeInvariantBasis(params["max_two_j"])
        exact_matrix = direct_matrix_exact(
            basis,
            electric=params["electric"],
            magnetic=params["magnetic"],
        )
        matrix = dense_float(exact_matrix)
        return HamiltonianArtifact(
            model_id=model,
            matrix=np.asarray(matrix, dtype=np.complex128),
            parameters=params,
            implementation_status="finite_verified_reference",
            claim_boundary=CLAIM_BOUNDARY,
            metadata={
                "basis": basis.summary(),
                "hilbert_dimension": basis.dimension,
                "gauge_invariant_by_construction": True,
                "gauss_law_residual": "0",
                "magnetic_term_complete": True,
                "exact_rational_matrix": [
                    [fraction_text(value) for value in row] for row in exact_matrix
                ],
            },
        )

    if model == "su2-pure-prototype":
        from gaugegap.gaugegap_su2_pure import SU2PureGaugeConfig, SU2PureGaugeLattice

        params = {
            "nx": int(parameters.get("nx", 2)),
            "ny": int(parameters.get("ny", 2)),
            "g_electric": float(parameters.get("g_electric", 1.0)),
            "g_magnetic": float(parameters.get("g_magnetic", 1.0)),
            "j_max": float(parameters.get("j_max", 0.5)),
            "boundary": str(parameters.get("boundary", "periodic")),
        }
        lattice = SU2PureGaugeLattice(SU2PureGaugeConfig(**params))
        matrix = lattice.hamiltonian_dense()
        return HamiltonianArtifact(
            model_id=model,
            matrix=np.asarray(matrix, dtype=np.complex128),
            parameters=params,
            implementation_status="prototype_scaffold",
            claim_boundary=(
                "finite SU(2) prototype with a diagonal magnetic stand-in; not a "
                "complete Wilson-plaquette implementation and not continuum Yang-Mills"
            ),
            metadata={
                "n_links": lattice.n_links,
                "n_plaquettes": lattice.n_plaquettes,
                "hilbert_dimension": lattice.hilbert_dim,
                "magnetic_term_complete": False,
            },
        )

    if model == "su3-pure-prototype":
        from gaugegap.gaugegap_su3_pure import (
            CLAIM_BOUNDARY,
            IMPLEMENTATION_STATUS,
            SU3PureGaugeConfig,
            SU3PureGaugeLattice,
        )

        params = {
            "nx": int(parameters.get("nx", 2)),
            "ny": int(parameters.get("ny", 2)),
            "g_electric": float(parameters.get("g_electric", 1.0)),
            "g_magnetic": float(parameters.get("g_magnetic", 1.0)),
            "truncation": float(parameters.get("truncation", 0.5)),
            "boundary": str(parameters.get("boundary", "periodic")),
        }
        lattice = SU3PureGaugeLattice(SU3PureGaugeConfig(**params))
        matrix = lattice.hamiltonian_dense()
        return HamiltonianArtifact(
            model_id=model,
            matrix=np.asarray(matrix, dtype=np.complex128),
            parameters=params,
            implementation_status=IMPLEMENTATION_STATUS,
            claim_boundary=CLAIM_BOUNDARY,
            metadata={
                "n_links": lattice.n_links,
                "n_plaquettes": lattice.n_plaquettes,
                "hilbert_dimension": lattice.hilbert_dim,
                "gauss_law_verified": False,
                "magnetic_term_complete": False,
            },
        )

    raise ValueError(f"unknown model {model_id!r}; choose from {registered_models()}")


def audit_hamiltonian(artifact: HamiltonianArtifact, *, tolerance: float = 1e-10) -> HamiltonianAudit:
    matrix = np.asarray(artifact.matrix, dtype=np.complex128)
    square = matrix.ndim == 2 and matrix.shape[0] == matrix.shape[1]
    finite = bool(np.all(np.isfinite(matrix)))
    if square:
        denominator = max(float(np.linalg.norm(matrix)), np.finfo(float).tiny)
        residual = float(np.linalg.norm(matrix - matrix.conj().T) / denominator)
    else:
        residual = float("inf")
    hermitian = bool(square and finite and residual <= tolerance)

    gap: float | None = None
    ground: float | None = None
    first: float | None = None
    if hermitian and matrix.shape[0] >= 2:
        eigenvalues = np.linalg.eigvalsh(matrix)
        ground = float(eigenvalues[0])
        first = float(eigenvalues[1])
        gap = first - ground

    trace = np.trace(matrix) if square else complex(float("nan"), float("nan"))
    return HamiltonianAudit(
        model_id=artifact.model_id,
        dimension=int(matrix.shape[0]) if matrix.ndim >= 1 else 0,
        finite=finite,
        square=square,
        hermiticity_residual=residual,
        hermitian=hermitian,
        spectral_gap=gap,
        ground_energy=ground,
        first_excited_energy=first,
        trace_real=float(trace.real) if np.isfinite(trace.real) else None,
        trace_imaginary=float(trace.imag) if np.isfinite(trace.imag) else None,
        matrix_digest=artifact.digest(),
        implementation_status=artifact.implementation_status,
        claim_boundary=artifact.claim_boundary,
    )


def build_and_audit(model_id: str, **parameters: object) -> tuple[HamiltonianArtifact, HamiltonianAudit]:
    artifact = build_hamiltonian(model_id, **parameters)
    return artifact, audit_hamiltonian(artifact)
