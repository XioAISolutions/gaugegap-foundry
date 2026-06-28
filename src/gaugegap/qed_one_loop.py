"""Finite, renormalized one-loop QED benchmarks in Euclidean momentum space.

This module is deliberately narrow:
- vacuum polarization uses the standard renormalized Feynman-parameter scalar
  for spacelike momentum Q^2 >= 0;
- fermion dressing functions use a finite momentum-subtraction (MOM) convention;
- the longitudinal vertex is reconstructed with the Ball--Chiu construction,
  so the Ward--Takahashi identity is an algebraic audit target;
- the Pauli form factor uses the standard one-loop spacelike parameter integral.

It is a perturbative one-loop benchmark, not a nonperturbative construction of QED.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Iterable

import numpy as np


CLAIM_BOUNDARY = (
    "continuum perturbative one-loop QED in a declared Euclidean MOM convention; "
    "not nonperturbative QED, not a continuum existence theorem, and not evidence "
    "for the Yang--Mills mass gap"
)


@dataclass(frozen=True)
class QEDParameters:
    alpha: float = 1.0 / 137.035999084
    fermion_mass: float = 1.0
    renormalization_scale_squared: float = 0.0
    quadrature_order: int = 160
    scheme: str = "euclidean_mom"

    def __post_init__(self) -> None:
        if not (0.0 < self.alpha < 1.0):
            raise ValueError("alpha must lie in (0, 1)")
        if self.fermion_mass <= 0.0:
            raise ValueError("fermion_mass must be positive")
        if self.renormalization_scale_squared < 0.0:
            raise ValueError("renormalization_scale_squared must be nonnegative")
        if self.quadrature_order < 16:
            raise ValueError("quadrature_order must be at least 16")


@dataclass(frozen=True)
class VacuumPolarizationResult:
    q_squared: float
    scalar: float
    effective_alpha: float
    transversality_residual: float


@dataclass(frozen=True)
class SelfEnergyResult:
    p_squared: float
    vector_dressing: float
    scalar_dressing: float
    subtraction_point: float


@dataclass(frozen=True)
class VertexResult:
    q_squared: float
    f1_zero_normalization: float
    pauli_f2: float
    schwinger_limit: float


@dataclass(frozen=True)
class WardAudit:
    p: tuple[float, float, float, float]
    k: tuple[float, float, float, float]
    vacuum_transversality_residual: float
    ward_takahashi_residual: float
    charge_normalization_residual: float
    pauli_zero_residual: float
    passed: bool
    tolerance: float
    claim_boundary: str = CLAIM_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _integrate_01(function, order: int) -> float:
    nodes, weights = np.polynomial.legendre.leggauss(order)
    x = 0.5 * (nodes + 1.0)
    return float(0.5 * np.dot(weights, function(x)))


def vacuum_polarization_scalar(q_squared: float, params: QEDParameters = QEDParameters()) -> float:
    """Return the renormalized spacelike scalar Pi_R(Q^2), with Pi_R(0)=0."""
    if q_squared < 0.0:
        raise ValueError("q_squared is spacelike Q^2 and must be nonnegative")
    m2 = params.fermion_mass**2
    value = _integrate_01(
        lambda x: x * (1.0 - x) * np.log1p(q_squared * x * (1.0 - x) / m2),
        params.quadrature_order,
    )
    return 2.0 * params.alpha * value / math.pi


def vacuum_polarization_tensor(q: Iterable[float], params: QEDParameters = QEDParameters()) -> np.ndarray:
    vector = np.asarray(tuple(q), dtype=float)
    if vector.shape != (4,):
        raise ValueError("q must be a Euclidean four-vector")
    q2 = float(vector @ vector)
    scalar = vacuum_polarization_scalar(q2, params)
    return (q2 * np.eye(4) - np.outer(vector, vector)) * scalar


def vacuum_polarization(q: Iterable[float], params: QEDParameters = QEDParameters()) -> VacuumPolarizationResult:
    vector = np.asarray(tuple(q), dtype=float)
    tensor = vacuum_polarization_tensor(vector, params)
    numerator = float(np.linalg.norm(vector @ tensor))
    denominator = max(float(np.linalg.norm(tensor)), np.finfo(float).tiny)
    q2 = float(vector @ vector)
    scalar = vacuum_polarization_scalar(q2, params)
    return VacuumPolarizationResult(q2, scalar, params.alpha / (1.0 - scalar), numerator / denominator)


def _mom_denominator(x: np.ndarray, p_squared: float, mass_squared: float) -> np.ndarray:
    return x * mass_squared + x * (1.0 - x) * p_squared


def self_energy_dressings(p_squared: float, params: QEDParameters = QEDParameters()) -> SelfEnergyResult:
    """Finite MOM dressing functions with A(mu^2)=1 and B(mu^2)=m."""
    if p_squared < 0.0:
        raise ValueError("p_squared must be nonnegative in Euclidean signature")
    m = params.fermion_mass
    mu2 = params.renormalization_scale_squared
    eps = np.finfo(float).tiny

    def log_ratio(x: np.ndarray) -> np.ndarray:
        dp = _mom_denominator(x, p_squared, m * m)
        dm = _mom_denominator(x, mu2, m * m)
        return np.log(np.maximum(dp, eps) / np.maximum(dm, eps))

    vector_shift = _integrate_01(lambda x: (1.0 - x) * log_ratio(x), params.quadrature_order)
    scalar_shift = _integrate_01(log_ratio, params.quadrature_order)
    a = 1.0 + params.alpha * vector_shift / (2.0 * math.pi)
    b = m * (1.0 - params.alpha * scalar_shift / math.pi)
    return SelfEnergyResult(p_squared, a, b, mu2)


def pauli_form_factor(q_squared: float, params: QEDParameters = QEDParameters()) -> float:
    """One-loop spacelike Pauli form factor, with F2(0)=alpha/(2*pi)."""
    if q_squared < 0.0:
        raise ValueError("q_squared must be nonnegative")
    ratio = q_squared / (params.fermion_mass**2)
    value = _integrate_01(
        lambda z: z * (1.0 - z) ** 2 / ((1.0 - z) ** 2 + z * ratio),
        params.quadrature_order,
    )
    return params.alpha * value / math.pi


def vertex_form_factors(q_squared: float, params: QEDParameters = QEDParameters()) -> VertexResult:
    f2 = pauli_form_factor(q_squared, params)
    return VertexResult(q_squared, 1.0, f2, params.alpha / (2.0 * math.pi))


def euclidean_gamma_matrices() -> tuple[np.ndarray, ...]:
    i = 1j
    zero = np.zeros((2, 2), dtype=complex)
    identity = np.eye(2, dtype=complex)
    sigma = (
        np.array([[0, 1], [1, 0]], dtype=complex),
        np.array([[0, -i], [i, 0]], dtype=complex),
        np.array([[1, 0], [0, -1]], dtype=complex),
    )
    gammas = [np.block([[zero, -i * s], [i * s, zero]]) for s in sigma]
    gammas.append(np.block([[zero, identity], [identity, zero]]))
    return tuple(gammas)


_GAMMAS = euclidean_gamma_matrices()
_ID4 = np.eye(4, dtype=complex)


def slash(momentum: Iterable[float]) -> np.ndarray:
    p = np.asarray(tuple(momentum), dtype=float)
    if p.shape != (4,):
        raise ValueError("momentum must be a Euclidean four-vector")
    result = np.zeros((4, 4), dtype=complex)
    for component, gamma in zip(p, _GAMMAS):
        result += component * gamma
    return result


def inverse_propagator(momentum: Iterable[float], params: QEDParameters = QEDParameters()) -> np.ndarray:
    p = np.asarray(tuple(momentum), dtype=float)
    dressing = self_energy_dressings(float(p @ p), params)
    return dressing.vector_dressing * slash(p) + dressing.scalar_dressing * _ID4


def ball_chiu_vertex(p: Iterable[float], k: Iterable[float], params: QEDParameters = QEDParameters()) -> tuple[np.ndarray, ...]:
    pv = np.asarray(tuple(p), dtype=float)
    kv = np.asarray(tuple(k), dtype=float)
    if pv.shape != (4,) or kv.shape != (4,):
        raise ValueError("p and k must be Euclidean four-vectors")
    p2, k2 = float(pv @ pv), float(kv @ kv)
    dp, dk = self_energy_dressings(p2, params), self_energy_dressings(k2, params)
    delta = p2 - k2
    if abs(delta) < 1e-12:
        step = 1e-6 * max(1.0, p2)
        plus = self_energy_dressings(p2 + step, params)
        minus_point = max(0.0, p2 - step)
        minus = self_energy_dressings(minus_point, params)
        width = p2 + step - minus_point
        d_a = (plus.vector_dressing - minus.vector_dressing) / width
        d_b = (plus.scalar_dressing - minus.scalar_dressing) / width
    else:
        d_a = (dp.vector_dressing - dk.vector_dressing) / delta
        d_b = (dp.scalar_dressing - dk.scalar_dressing) / delta
    mean_a = 0.5 * (dp.vector_dressing + dk.vector_dressing)
    sum_slash = slash(pv) + slash(kv)
    return tuple(
        mean_a * _GAMMAS[mu]
        + (pv[mu] + kv[mu]) * (0.5 * d_a * sum_slash + d_b * _ID4)
        for mu in range(4)
    )


def ward_takahashi_residual(p: Iterable[float], k: Iterable[float], params: QEDParameters = QEDParameters()) -> float:
    pv = np.asarray(tuple(p), dtype=float)
    kv = np.asarray(tuple(k), dtype=float)
    contracted = np.zeros((4, 4), dtype=complex)
    for component, vertex in zip(pv - kv, ball_chiu_vertex(pv, kv, params)):
        contracted += component * vertex
    target = inverse_propagator(pv, params) - inverse_propagator(kv, params)
    return float(np.linalg.norm(contracted - target) / max(np.linalg.norm(target), np.finfo(float).tiny))


def audit_qed(
    p: Iterable[float] = (0.7, 0.2, 0.1, 0.4),
    k: Iterable[float] = (0.1, -0.3, 0.2, 0.5),
    params: QEDParameters = QEDParameters(),
    tolerance: float = 1e-10,
) -> WardAudit:
    pv, kv = tuple(float(v) for v in p), tuple(float(v) for v in k)
    q = np.asarray(pv) - np.asarray(kv)
    vacuum = vacuum_polarization(q, params)
    ward = ward_takahashi_residual(pv, kv, params)
    charge = abs(vertex_form_factors(0.0, params).f1_zero_normalization - 1.0)
    pauli = abs(pauli_form_factor(0.0, params) - params.alpha / (2.0 * math.pi))
    passed = max(vacuum.transversality_residual, ward, charge, pauli) <= tolerance
    return WardAudit(pv, kv, vacuum.transversality_residual, ward, charge, pauli, passed, tolerance)


def scan_qed(q_squared_values: Iterable[float], params: QEDParameters = QEDParameters()) -> list[dict[str, float]]:
    rows = []
    for q2 in q_squared_values:
        q2f = float(q2)
        pi = vacuum_polarization_scalar(q2f, params)
        rows.append({
            "q_squared": q2f,
            "vacuum_polarization": pi,
            "effective_alpha": params.alpha / (1.0 - pi),
            "pauli_f2": pauli_form_factor(q2f, params),
        })
    return rows
