"""Finite compactification toy spectra.

The goal is educational and auditable: demonstrate how a compact hidden
dimension creates discrete Kaluza-Klein and winding towers, and how a small
radius can make those modes invisible below a finite detector cutoff.  This is
not a string-vacuum calculation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable

CLAIM_BOUNDARY = (
    "finite toy compactification spectrum only; not evidence for string theory, "
    "not a Calabi-Yau vacuum construction, and not a prediction of observed "
    "particle masses or extra dimensions"
)


@dataclass(frozen=True)
class CompactMode:
    geometry: str
    momentum_numbers: tuple[int, ...]
    winding_numbers: tuple[int, ...]
    mass_squared: float
    mass: float
    visible_below_cutoff: bool

    def summary(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["momentum_numbers"] = list(self.momentum_numbers)
        payload["winding_numbers"] = list(self.winding_numbers)
        return payload


@dataclass(frozen=True)
class CompactificationReport:
    schema: str
    benchmark_id: str
    geometry: str
    radii: tuple[float, ...]
    cutoff: float
    max_mode: int
    alpha_prime: float
    mode_count: int
    visible_mode_count: int
    first_excited_mass: float
    effective_dimension_label: str
    passed: bool
    modes: tuple[CompactMode, ...]
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "benchmark_id": self.benchmark_id,
            "geometry": self.geometry,
            "radii": list(self.radii),
            "cutoff": self.cutoff,
            "max_mode": self.max_mode,
            "alpha_prime": self.alpha_prime,
            "mode_count": self.mode_count,
            "visible_mode_count": self.visible_mode_count,
            "first_excited_mass": self.first_excited_mass,
            "effective_dimension_label": self.effective_dimension_label,
            "passed": self.passed,
            "modes": [mode.summary() for mode in self.modes],
            "claim_boundary": self.claim_boundary,
        }


def _integer_vectors(dimensions: int, max_mode: int) -> Iterable[tuple[int, ...]]:
    if dimensions == 1:
        for value in range(-max_mode, max_mode + 1):
            yield (value,)
        return
    previous = list(_integer_vectors(dimensions - 1, max_mode))
    for value in range(-max_mode, max_mode + 1):
        for tail in previous:
            yield (value, *tail)


def _mass_squared(
    momentum: tuple[int, ...],
    winding: tuple[int, ...],
    radii: tuple[float, ...],
    alpha_prime: float,
    base_mass: float,
) -> float:
    total = base_mass * base_mass
    for number, radius in zip(momentum, radii):
        total += (number / radius) ** 2
    for number, radius in zip(winding, radii):
        total += (number * radius / alpha_prime) ** 2
    return float(total)


def compact_spectrum(
    *,
    geometry: str = "circle",
    radii: tuple[float, ...] = (0.08,),
    cutoff: float = 8.0,
    max_mode: int = 3,
    alpha_prime: float = 0.005,
    include_winding: bool = True,
    base_mass: float = 0.0,
) -> CompactificationReport:
    if not radii or any(radius <= 0.0 or not math.isfinite(radius) for radius in radii):
        raise ValueError("radii must be finite and positive")
    if cutoff <= 0.0 or not math.isfinite(cutoff):
        raise ValueError("cutoff must be finite and positive")
    if max_mode < 1:
        raise ValueError("max_mode must be positive")
    if alpha_prime <= 0.0 or not math.isfinite(alpha_prime):
        raise ValueError("alpha_prime must be finite and positive")
    dimension = len(radii)
    momenta = list(_integer_vectors(dimension, max_mode))
    windings = list(_integer_vectors(dimension, max_mode)) if include_winding else [(0,) * dimension]
    modes: list[CompactMode] = []
    for momentum in momenta:
        for winding in windings:
            mass_squared = _mass_squared(momentum, winding, radii, alpha_prime, base_mass)
            mass = math.sqrt(max(mass_squared, 0.0))
            modes.append(
                CompactMode(
                    geometry=geometry,
                    momentum_numbers=momentum,
                    winding_numbers=winding,
                    mass_squared=mass_squared,
                    mass=mass,
                    visible_below_cutoff=mass <= cutoff,
                )
            )
    modes.sort(key=lambda mode: (mode.mass, mode.momentum_numbers, mode.winding_numbers))
    excited = next((mode.mass for mode in modes if mode.mass > 1e-12), math.inf)
    visible = tuple(mode for mode in modes if mode.visible_below_cutoff)
    effective = "4D-only below cutoff" if len(visible) == 1 else f"4D + {len(visible) - 1} compact modes"
    return CompactificationReport(
        schema="gaugegap.compactification_forge.v1",
        benchmark_id="compact-0001-hidden-circle" if dimension == 1 else "compact-0002-hidden-torus",
        geometry=geometry,
        radii=radii,
        cutoff=cutoff,
        max_mode=max_mode,
        alpha_prime=alpha_prime,
        mode_count=len(modes),
        visible_mode_count=len(visible),
        first_excited_mass=float(excited),
        effective_dimension_label=effective,
        passed=bool(modes and modes[0].mass == 0.0 and excited > 0.0),
        modes=tuple(modes),
    )


def run_compactification_suite(
    *,
    circle_radius: float = 0.08,
    torus_radii: tuple[float, float] = (0.08, 0.09),
    cutoff: float = 8.0,
    max_mode: int = 3,
    alpha_prime: float = 0.005,
) -> tuple[CompactificationReport, ...]:
    return (
        compact_spectrum(
            geometry="S1 circle",
            radii=(circle_radius,),
            cutoff=cutoff,
            max_mode=max_mode,
            alpha_prime=alpha_prime,
            include_winding=True,
        ),
        compact_spectrum(
            geometry="T2 torus",
            radii=torus_radii,
            cutoff=cutoff,
            max_mode=max_mode,
            alpha_prime=alpha_prime,
            include_winding=True,
        ),
    )
