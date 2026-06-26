"""Validated finite-time enclosures for the registered three-dimensional flows.

This module implements a small Picard-inclusion interval stepper for Rössler,
Lorenz, and Thomas systems.  A successful step proves that the exact solution
starting in the supplied interval box remains inside the reported tube over the
configured finite time step and ends inside the reported endpoint box.

It does not prove a global attractor, chaos, ergodicity, or long-time boundedness.
Wrapping growth is expected; failure to validate is reported rather than hidden.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import mpmath as mp
import numpy as np

from gaugegap.rigorous.interval_arithmetic import Interval


CLAIM_BOUNDARY = (
    "validated finite-step interval ODE enclosure only; repeated enclosures may "
    "grow from wrapping and do not establish a global strange attractor"
)


def _exact(value: float | mp.mpf) -> Interval:
    return Interval.from_bounds(value, value)


def _hull(left: Interval, right: Interval) -> Interval:
    return Interval.from_bounds(min(left.lower, right.lower), max(left.upper, right.upper))


def _inflate(value: Interval, absolute: float, relative: float) -> Interval:
    radius = mp.mpf(absolute) + mp.mpf(relative) * max(abs(value.lower), abs(value.upper), mp.mpf(1))
    return Interval.from_bounds(value.lower - radius, value.upper + radius)


def _iv_sin(value: Interval) -> Interval:
    result = mp.iv.sin(mp.iv.mpf([value.lower, value.upper]))
    return Interval.from_bounds(mp.mpf(result.a), mp.mpf(result.b))


@dataclass(frozen=True)
class IntervalBox:
    components: tuple[Interval, ...]

    def __post_init__(self) -> None:
        if len(self.components) != 3:
            raise ValueError("validated dynamics currently require a three-dimensional box")

    @classmethod
    def from_point(cls, point: Sequence[float], radius: float = 0.0) -> "IntervalBox":
        values = np.asarray(point, dtype=float)
        if values.shape != (3,) or not np.all(np.isfinite(values)):
            raise ValueError("point must contain exactly three finite values")
        if radius < 0.0 or not np.isfinite(radius):
            raise ValueError("radius must be finite and non-negative")
        return cls(tuple(Interval.from_float(float(value), radius) for value in values))

    @classmethod
    def from_bounds(cls, bounds: Sequence[Sequence[float]]) -> "IntervalBox":
        if len(bounds) != 3:
            raise ValueError("bounds must contain three [lower, upper] pairs")
        return cls(tuple(Interval.from_bounds(pair[0], pair[1]) for pair in bounds))

    def midpoint(self) -> np.ndarray:
        return np.array([float(component.midpoint()) for component in self.components])

    def widths(self) -> np.ndarray:
        return np.array([float(component.width()) for component in self.components])

    def maximum_width(self) -> float:
        return float(max(component.width() for component in self.components))

    def contains_point(self, point: Sequence[float]) -> bool:
        values = np.asarray(point, dtype=float)
        return values.shape == (3,) and all(
            interval.lower <= value <= interval.upper
            for interval, value in zip(self.components, values)
        )

    def subset_of(self, other: "IntervalBox") -> bool:
        return all(
            outer.lower <= inner.lower and inner.upper <= outer.upper
            for inner, outer in zip(self.components, other.components)
        )

    def hull(self, other: "IntervalBox") -> "IntervalBox":
        return IntervalBox(tuple(_hull(left, right) for left, right in zip(self.components, other.components)))

    def inflated(self, absolute: float = 1e-30, relative: float = 1e-12) -> "IntervalBox":
        return IntervalBox(tuple(_inflate(value, absolute, relative) for value in self.components))

    def add(self, other: "IntervalBox") -> "IntervalBox":
        return IntervalBox(tuple(left + right for left, right in zip(self.components, other.components)))

    def scale_interval(self, scalar: Interval) -> "IntervalBox":
        return IntervalBox(tuple(component * scalar for component in self.components))

    def to_bounds(self) -> list[list[float]]:
        return [[float(value.lower), float(value.upper)] for value in self.components]


@dataclass(frozen=True)
class ValidatedStep:
    system: str
    dt: float
    initial: IntervalBox
    tube: IntervalBox
    endpoint: IntervalBox
    validated: bool
    iterations: int
    maximum_tube_width: float
    maximum_endpoint_width: float
    reason: str
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, object]:
        return {
            "system": self.system,
            "dt": self.dt,
            "initial": self.initial.to_bounds(),
            "tube": self.tube.to_bounds(),
            "endpoint": self.endpoint.to_bounds(),
            "validated": self.validated,
            "iterations": self.iterations,
            "maximum_tube_width": self.maximum_tube_width,
            "maximum_endpoint_width": self.maximum_endpoint_width,
            "reason": self.reason,
            "claim_boundary": self.claim_boundary,
        }


def interval_rhs(
    system_name: str,
    box: IntervalBox,
    params: Mapping[str, float],
) -> IntervalBox:
    name = system_name.lower()
    x, y, z = box.components
    if name == "rossler":
        a, b, c = (_exact(params[key]) for key in ("a", "b", "c"))
        return IntervalBox((-y - z, x + a * y, b + z * (x - c)))
    if name == "lorenz":
        sigma, rho, beta = (_exact(params[key]) for key in ("sigma", "rho", "beta"))
        return IntervalBox((sigma * (y - x), x * (rho - z) - y, x * y - beta * z))
    if name == "thomas":
        b = _exact(params["b"])
        return IntervalBox((_iv_sin(y) - b * x, _iv_sin(z) - b * y, _iv_sin(x) - b * z))
    raise ValueError(f"unsupported validated system {system_name!r}")


def picard_enclosure_step(
    system_name: str,
    initial: IntervalBox,
    params: Mapping[str, float],
    *,
    dt: float,
    max_iterations: int = 32,
    absolute_inflation: float = 1e-30,
    relative_inflation: float = 1e-10,
    maximum_width: float = 1e6,
) -> ValidatedStep:
    """Attempt a validated one-step Picard enclosure.

    The inclusion test is ``X0 + [0, dt] f(B) subset B``.  When it succeeds,
    standard Picard existence/uniqueness arguments for the smooth registered
    vector fields place the exact solution tube inside ``B``.
    """
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if maximum_width <= 0.0:
        raise ValueError("maximum_width must be positive")

    time_tube = Interval.from_bounds(0.0, dt)
    time_endpoint = _exact(dt)
    first_image = initial.add(interval_rhs(system_name, initial, params).scale_interval(time_tube))
    candidate = initial.hull(first_image).inflated(absolute_inflation, relative_inflation)

    validated = False
    reason = "Picard inclusion did not close"
    used_iterations = 0
    for iteration in range(1, max_iterations + 1):
        used_iterations = iteration
        image = initial.add(interval_rhs(system_name, candidate, params).scale_interval(time_tube))
        if image.subset_of(candidate):
            validated = True
            reason = "Picard image is contained in the interval tube"
            break
        candidate = candidate.hull(image).inflated(absolute_inflation, relative_inflation)
        if candidate.maximum_width() > maximum_width:
            reason = "interval tube exceeded maximum_width before inclusion closed"
            break

    endpoint = initial.add(interval_rhs(system_name, candidate, params).scale_interval(time_endpoint))
    return ValidatedStep(
        system=system_name.lower(),
        dt=float(dt),
        initial=initial,
        tube=candidate,
        endpoint=endpoint,
        validated=validated,
        iterations=used_iterations,
        maximum_tube_width=candidate.maximum_width(),
        maximum_endpoint_width=endpoint.maximum_width(),
        reason=reason,
    )


def validated_trajectory(
    system_name: str,
    initial: IntervalBox,
    params: Mapping[str, float],
    *,
    dt: float,
    steps: int,
    max_iterations: int = 32,
    maximum_width: float = 1e6,
) -> tuple[ValidatedStep, ...]:
    """Chain validated endpoint boxes until failure or ``steps`` are complete."""
    if steps < 1:
        raise ValueError("steps must be positive")
    current = initial
    records: list[ValidatedStep] = []
    for _ in range(steps):
        record = picard_enclosure_step(
            system_name,
            current,
            params,
            dt=dt,
            max_iterations=max_iterations,
            maximum_width=maximum_width,
        )
        records.append(record)
        if not record.validated:
            break
        current = record.endpoint
    return tuple(records)
