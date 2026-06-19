"""Operator registry: one abstraction point for the certified/quantum pipeline.

Maps a named candidate-operator family to (a) its float Hermitian matrix builder
and (b) its certified eigenvalue-enclosure builder, plus metadata controlling the
formal-proof and DSL stages. Registered families reuse the tight, exact-arithmetic
enclosures in ``curverank_certified``; an arbitrary Hermitian matrix can be
certified through the general ``verified_hermitian_eigenvalues`` kernel via
:func:`build_certified_general`.

CLAIM BOUNDARY: this is finite-operator spectral screening infrastructure. The
certified enclosures are rigorous; nothing here proves the Riemann Hypothesis or
any Millennium Prize problem.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

import numpy as np

from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    IntervalMatrix,
    verified_hermitian_eigenvalues,
)
from gaugegap.curverank_operators import (
    berry_keating_xp,
    dirac_rindler_truncated,
    quantum_graph_laplacian,
)
from gaugegap.curverank_certified import (
    certified_xp_spectrum,
    certified_dirac_rindler_spectrum,
    certified_quantum_graph_spectrum,
    _collapse_doubled_spectrum,
)

# Default quantum-graph geometry (star graph with three incommensurate edges),
# matching curverank_certified._DEFAULT_GRAPH_EDGES.
_DEFAULT_GRAPH_EDGES = [(0, 1), (0, 2), (0, 3)]
_DEFAULT_GRAPH_LENGTHS = [1.0, float(np.sqrt(2)), float(np.sqrt(3))]


@dataclass(frozen=True)
class OperatorSpec:
    """A registered candidate operator family.

    Attributes
    ----------
    name : human-facing operator name (e.g. ``"berry_keating_xp"``).
    build : callable(n) -> float Hermitian matrix.
    certified : callable(n) -> certified eigenvalue enclosures (List[Interval]).
    formal_family : key for ``certified_family_mismatch`` / formal proofs, or None
        when no formal family is registered (the formal stage then skips).
    dsl_form : a Spectra ``operator`` expression template (uses ``{n}``), or None
        when the DSL has no form for this operator (the DSL stage then skips).
    size_kw : the size keyword this operator takes (``"n_basis"`` or ``"n_modes"``).
    """

    name: str
    build: Callable[..., np.ndarray]
    certified: Callable[..., List[Interval]]
    formal_family: Optional[str]
    dsl_form: Optional[str]
    size_kw: str


def _xp_spec() -> OperatorSpec:
    return OperatorSpec(
        name="berry_keating_xp",
        build=lambda n, **kw: berry_keating_xp(n, kw.get("L", 1.0)),
        certified=lambda n, **kw: certified_xp_spectrum(n, kw.get("L", 1.0)),
        formal_family="xp",
        dsl_form="berry_keating(n={n})",
        size_kw="n_basis",
    )


def _dirac_spec() -> OperatorSpec:
    return OperatorSpec(
        name="dirac_rindler",
        build=lambda n, **kw: dirac_rindler_truncated(
            n, kw.get("acceleration", 1.0), kw.get("mass", 0.0)
        ),
        certified=lambda n, **kw: certified_dirac_rindler_spectrum(
            n, kw.get("acceleration", 1.0), kw.get("mass", 0.0)
        ),
        formal_family="dirac_rindler",
        dsl_form=None,
        size_kw="n_basis",
    )


def _quantum_graph_spec() -> OperatorSpec:
    return OperatorSpec(
        name="quantum_graph",
        build=lambda n, **kw: quantum_graph_laplacian(
            kw.get("edges", _DEFAULT_GRAPH_EDGES),
            kw.get("lengths", _DEFAULT_GRAPH_LENGTHS),
            n,
        ),
        certified=lambda n, **kw: certified_quantum_graph_spectrum(
            kw.get("edges", _DEFAULT_GRAPH_EDGES),
            kw.get("lengths", _DEFAULT_GRAPH_LENGTHS),
            n,
        ),
        formal_family="quantum_graph",
        dsl_form=None,
        size_kw="n_modes",
    )


_REGISTRY = {
    "xp": _xp_spec,
    "berry_keating_xp": _xp_spec,
    "berry_keating": _xp_spec,
    "dirac_rindler": _dirac_spec,
    "quantum_graph": _quantum_graph_spec,
}


def list_operators() -> list[str]:
    """Canonical registered operator names (deduplicated)."""
    seen = []
    for spec_factory in (_xp_spec, _dirac_spec, _quantum_graph_spec):
        name = spec_factory().name
        if name not in seen:
            seen.append(name)
    return seen


def get_operator(name: str) -> OperatorSpec:
    """Return the :class:`OperatorSpec` for ``name`` (several aliases accepted)."""
    key = name.strip().lower()
    if key not in _REGISTRY:
        raise ValueError(
            f"unknown operator {name!r}; choose from {list_operators()}"
        )
    return _REGISTRY[key]()


def build_certified_general(
    H: np.ndarray, *, error: float = 1e-12
) -> List[Interval]:
    """Certified eigenvalue enclosures for an ARBITRARY Hermitian matrix.

    Routes through the general residual-bound kernel
    ``verified_hermitian_eigenvalues`` (rigorous; not a floating-point estimate).
    Real-symmetric matrices are certified directly; genuinely complex Hermitian
    matrices are certified via the real ``2N x 2N`` embedding and the doubled
    spectrum is collapsed back to ``N`` operator enclosures.
    """
    H = np.asarray(H)
    if not np.allclose(H, H.conj().T, atol=1e-9):
        raise ValueError("matrix is not Hermitian")
    if np.iscomplexobj(H) and np.linalg.norm(H.imag) > 1e-12:
        re = np.ascontiguousarray(H.real)
        im = np.ascontiguousarray(H.imag)
        # Real symmetric embedding [[re, -im], [im, re]] (eigenvalues doubled).
        top = np.hstack([re, -im])
        bottom = np.hstack([im, re])
        embedding = np.vstack([top, bottom])
        doubled = verified_hermitian_eigenvalues(
            IntervalMatrix.from_numpy(embedding, error)
        )
        return _collapse_doubled_spectrum(doubled)
    real = np.ascontiguousarray(H.real if np.iscomplexobj(H) else H)
    return verified_hermitian_eigenvalues(IntervalMatrix.from_numpy(real, error))


def certified_for(
    spec: OperatorSpec, n: int, *, prefer_registered: bool = True, **kwargs
) -> List[Interval]:
    """Certified enclosures for a spec at size ``n``.

    Uses the spec's tight registered enclosure when available; otherwise falls
    back to :func:`build_certified_general` on the built matrix.
    """
    if prefer_registered and spec.certified is not None:
        return spec.certified(n, **kwargs)
    return build_certified_general(spec.build(n, **kwargs))
