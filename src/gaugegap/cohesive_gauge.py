"""Finite computational gauge-groupoid model inspired by cohesive HoTT.

Configurations are objects, gauge transformations are paths, and a registered
endpoint observable is transported along those paths. This executable audit is
not a proof of univalence and not a compiled cohesive-HoTT development.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math

import numpy as np


CLAIM_BOUNDARY = (
    "finite computational U(1) gauge groupoid and transport audit; "
    "not a proof of univalence, not a cohesive-HoTT model, and not a QFT construction theorem"
)


@dataclass(frozen=True)
class U1Configuration:
    matter: tuple[complex, ...]
    links: tuple[complex, ...]

    def __post_init__(self) -> None:
        if len(self.links) != max(0, len(self.matter) - 1):
            raise ValueError("open chain requires one fewer link than matter sites")


@dataclass(frozen=True)
class GaugePath:
    phases: tuple[float, ...]

    def identity_like(self) -> "GaugePath":
        return GaugePath(tuple(0.0 for _ in self.phases))

    def inverse(self) -> "GaugePath":
        return GaugePath(tuple(-phase for phase in self.phases))

    def compose(self, other: "GaugePath") -> "GaugePath":
        if len(self.phases) != len(other.phases):
            raise ValueError("gauge paths have different site counts")
        return GaugePath(tuple(a + b for a, b in zip(self.phases, other.phases)))


@dataclass(frozen=True)
class GaugeCoherenceCertificate:
    identity_residual: float
    inverse_residual: float
    associativity_residual: float
    observable_transport_residual: float
    passed: bool
    tolerance: float
    implementation_status: str = "finite_computational_groupoid"
    claim_boundary: str = CLAIM_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _unit(phase: float) -> complex:
    return complex(math.cos(phase), math.sin(phase))


def act(configuration: U1Configuration, path: GaugePath) -> U1Configuration:
    if len(path.phases) != len(configuration.matter):
        raise ValueError("one gauge phase is required per matter site")
    g = tuple(_unit(phase) for phase in path.phases)
    matter = tuple(g_n * psi for g_n, psi in zip(g, configuration.matter))
    links = tuple(
        g[n] * configuration.links[n] * g[n + 1].conjugate()
        for n in range(len(configuration.links))
    )
    return U1Configuration(matter, links)


def endpoint_correlator(configuration: U1Configuration) -> complex:
    if not configuration.matter:
        return 0j
    transporter = 1.0 + 0.0j
    for link in configuration.links:
        transporter *= link
    return configuration.matter[0].conjugate() * transporter * configuration.matter[-1]


def configuration_distance(a: U1Configuration, b: U1Configuration) -> float:
    av = np.asarray((*a.matter, *a.links), dtype=complex)
    bv = np.asarray((*b.matter, *b.links), dtype=complex)
    return float(np.linalg.norm(av - bv))


def audit_gauge_coherence(
    configuration: U1Configuration | None = None,
    a: GaugePath | None = None,
    b: GaugePath | None = None,
    c: GaugePath | None = None,
    tolerance: float = 1e-12,
) -> GaugeCoherenceCertificate:
    configuration = configuration or U1Configuration(
        matter=(1.0 + 0.2j, -0.4 + 0.9j, 0.3 - 0.1j),
        links=(np.exp(0.4j), np.exp(-0.7j)),
    )
    a = a or GaugePath((0.2, -0.1, 0.7))
    b = b or GaugePath((-0.3, 0.4, 0.1))
    c = c or GaugePath((0.5, -0.2, -0.6))
    identity = configuration_distance(act(configuration, a.identity_like()), configuration)
    inverse = configuration_distance(act(act(configuration, a), a.inverse()), configuration)
    left = act(configuration, a.compose(b).compose(c))
    right = act(configuration, a.compose(b.compose(c)))
    associativity = configuration_distance(left, right)
    transported = endpoint_correlator(act(configuration, a))
    original = endpoint_correlator(configuration)
    observable = abs(transported - original) / max(abs(original), np.finfo(float).tiny)
    passed = max(identity, inverse, associativity, observable) <= tolerance
    return GaugeCoherenceCertificate(
        identity,
        inverse,
        associativity,
        float(observable),
        passed,
        tolerance,
    )
