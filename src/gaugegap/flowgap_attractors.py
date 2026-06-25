"""Attractor Forge: deterministic finite-time nonlinear-dynamics benchmarks.

This module provides a shared interface for three-dimensional autonomous systems,
with Rössler, Lorenz, and Thomas attractors registered by default.  It includes
fixed-step RK4 integration, fixed-point stability, Poincaré sections, variational
Lyapunov spectra, short-horizon step-halving checks, sensitivity diagnostics,
recurrence/correlation estimates, and discharged Lean/Coq divergence bounds.

CLAIM BOUNDARY: all outputs are finite-time numerical diagnostics of finite ODE
integrations.  Positive finite-time Lyapunov estimates, fractal-dimension fits,
plots, and bifurcation samples are evidence about the configured numerical run;
they are not formal proofs of chaos, global attractors, ergodicity, or continuum
physics.  The emitted formal certificates prove only the stated algebraic
phase-volume divergence bounds for the model equations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import numpy as np

Array = np.ndarray
RHS = Callable[[Array, Mapping[str, float]], Array]
Jacobian = Callable[[Array, Mapping[str, float]], Array]
Divergence = Callable[[Array, Mapping[str, float]], float]
FixedPoints = Callable[[Mapping[str, float]], list[Array]]


@dataclass(frozen=True)
class AttractorSystem:
    name: str
    parameter_names: tuple[str, ...]
    default_parameters: Mapping[str, float]
    default_state: tuple[float, float, float]
    rhs: RHS
    jacobian: Jacobian
    divergence: Divergence
    fixed_points: FixedPoints
    description: str

    def parameters(self, overrides: Mapping[str, float] | None = None) -> dict[str, float]:
        values = {key: float(value) for key, value in self.default_parameters.items()}
        if overrides:
            unknown = set(overrides) - set(self.parameter_names)
            if unknown:
                raise ValueError(f"unknown parameters for {self.name}: {sorted(unknown)}")
            values.update({key: float(value) for key, value in overrides.items()})
        if not all(np.isfinite(value) for value in values.values()):
            raise ValueError("all parameters must be finite")
        return values


def _rossler_rhs(state: Array, p: Mapping[str, float]) -> Array:
    x, y, z = state
    return np.array([-y - z, x + p["a"] * y, p["b"] + z * (x - p["c"])], dtype=float)


def _rossler_jacobian(state: Array, p: Mapping[str, float]) -> Array:
    x, _y, z = state
    return np.array(
        [[0.0, -1.0, -1.0], [1.0, p["a"], 0.0], [z, 0.0, x - p["c"]]],
        dtype=float,
    )


def _rossler_divergence(state: Array, p: Mapping[str, float]) -> float:
    return float(p["a"] + state[0] - p["c"])


def _rossler_fixed_points(p: Mapping[str, float]) -> list[Array]:
    a, b, c = p["a"], p["b"], p["c"]
    if abs(a) < 1e-15:
        if abs(c) < 1e-15:
            return []
        z = b / c
        return [np.array([0.0, -z, z], dtype=float)]
    discriminant = c * c - 4.0 * a * b
    if discriminant < 0.0:
        return []
    root = float(np.sqrt(discriminant))
    points = []
    for sign in (-1.0, 1.0):
        z = (c + sign * root) / (2.0 * a)
        points.append(np.array([a * z, -z, z], dtype=float))
    return points


def _lorenz_rhs(state: Array, p: Mapping[str, float]) -> Array:
    x, y, z = state
    return np.array(
        [p["sigma"] * (y - x), x * (p["rho"] - z) - y, x * y - p["beta"] * z],
        dtype=float,
    )


def _lorenz_jacobian(state: Array, p: Mapping[str, float]) -> Array:
    x, y, z = state
    return np.array(
        [[-p["sigma"], p["sigma"], 0.0], [p["rho"] - z, -1.0, -x], [y, x, -p["beta"]]],
        dtype=float,
    )


def _lorenz_divergence(_state: Array, p: Mapping[str, float]) -> float:
    return float(-(p["sigma"] + 1.0 + p["beta"]))


def _lorenz_fixed_points(p: Mapping[str, float]) -> list[Array]:
    points = [np.zeros(3, dtype=float)]
    if p["rho"] > 1.0 and p["beta"] >= 0.0:
        value = float(np.sqrt(p["beta"] * (p["rho"] - 1.0)))
        points.extend(
            [np.array([value, value, p["rho"] - 1.0]), np.array([-value, -value, p["rho"] - 1.0])]
        )
    return points


def _thomas_rhs(state: Array, p: Mapping[str, float]) -> Array:
    x, y, z = state
    b = p["b"]
    return np.array([np.sin(y) - b * x, np.sin(z) - b * y, np.sin(x) - b * z], dtype=float)


def _thomas_jacobian(state: Array, p: Mapping[str, float]) -> Array:
    x, y, z = state
    b = p["b"]
    return np.array([[-b, np.cos(y), 0.0], [0.0, -b, np.cos(z)], [np.cos(x), 0.0, -b]], dtype=float)


def _thomas_divergence(_state: Array, p: Mapping[str, float]) -> float:
    return float(-3.0 * p["b"])


def _thomas_fixed_points(_p: Mapping[str, float]) -> list[Array]:
    # The origin is exact for every b.  Additional roots can exist and are not
    # claimed here because locating all of them is a separate root-isolation task.
    return [np.zeros(3, dtype=float)]


SYSTEMS: dict[str, AttractorSystem] = {
    "rossler": AttractorSystem(
        name="rossler",
        parameter_names=("a", "b", "c"),
        default_parameters={"a": 0.2, "b": 0.2, "c": 5.7},
        default_state=(0.0, 1.0, 0.0),
        rhs=_rossler_rhs,
        jacobian=_rossler_jacobian,
        divergence=_rossler_divergence,
        fixed_points=_rossler_fixed_points,
        description="Rössler three-variable spiral/fold oscillator",
    ),
    "lorenz": AttractorSystem(
        name="lorenz",
        parameter_names=("sigma", "rho", "beta"),
        default_parameters={"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0},
        default_state=(1.0, 1.0, 1.0),
        rhs=_lorenz_rhs,
        jacobian=_lorenz_jacobian,
        divergence=_lorenz_divergence,
        fixed_points=_lorenz_fixed_points,
        description="Lorenz convection-model butterfly system",
    ),
    "thomas": AttractorSystem(
        name="thomas",
        parameter_names=("b",),
        default_parameters={"b": 0.208186},
        default_state=(0.1, 0.0, 0.0),
        rhs=_thomas_rhs,
        jacobian=_thomas_jacobian,
        divergence=_thomas_divergence,
        fixed_points=_thomas_fixed_points,
        description="Thomas cyclically symmetric sinusoidal flow",
    ),
}


def get_system(name: str) -> AttractorSystem:
    try:
        return SYSTEMS[name.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown attractor system {name!r}; choose from {sorted(SYSTEMS)}") from exc


def _state(value: Sequence[float]) -> Array:
    array = np.asarray(value, dtype=float)
    if array.shape != (3,) or not np.all(np.isfinite(array)):
        raise ValueError("state must contain exactly three finite values")
    return array


def rk4_step(system: AttractorSystem, state: Sequence[float], dt: float, params: Mapping[str, float]) -> Array:
    """One deterministic classical fourth-order Runge–Kutta step."""
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    x = _state(state)
    k1 = system.rhs(x, params)
    k2 = system.rhs(x + 0.5 * dt * k1, params)
    k3 = system.rhs(x + 0.5 * dt * k2, params)
    k4 = system.rhs(x + dt * k3, params)
    return x + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrate(
    system: AttractorSystem,
    params: Mapping[str, float],
    initial_state: Sequence[float],
    *,
    dt: float,
    steps: int,
    sample_every: int = 1,
) -> tuple[Array, Array]:
    """Integrate a finite trajectory and return sampled times and states."""
    if steps < 1:
        raise ValueError("steps must be positive")
    if sample_every < 1:
        raise ValueError("sample_every must be positive")
    x = _state(initial_state)
    samples = 1 + steps // sample_every
    times = np.empty(samples, dtype=float)
    states = np.empty((samples, 3), dtype=float)
    times[0], states[0] = 0.0, x
    cursor = 1
    for step in range(1, steps + 1):
        x = rk4_step(system, x, dt, params)
        if not np.all(np.isfinite(x)):
            raise FloatingPointError(f"trajectory became non-finite at step {step}")
        if step % sample_every == 0:
            times[cursor] = step * dt
            states[cursor] = x
            cursor += 1
    return times[:cursor], states[:cursor]


def fixed_point_analysis(system: AttractorSystem, params: Mapping[str, float]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for point in system.fixed_points(params):
        residual = system.rhs(point, params)
        eigenvalues = np.linalg.eigvals(system.jacobian(point, params))
        records.append(
            {
                "point": [float(v) for v in point],
                "residual_norm": float(np.linalg.norm(residual)),
                "jacobian_eigenvalues": [
                    {"real": float(value.real), "imag": float(value.imag)} for value in eigenvalues
                ],
                "linearly_stable": bool(np.all(eigenvalues.real < 0.0)),
            }
        )
    return records


def poincare_section(
    states: Array,
    *,
    axis: int = 0,
    level: float = 0.0,
    direction: int = 1,
) -> Array:
    """Linearly interpolate section crossings of ``state[axis] = level``."""
    values = np.asarray(states, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("states must have shape (n, 3)")
    if axis not in (0, 1, 2) or direction not in (-1, 0, 1):
        raise ValueError("axis must be 0..2 and direction must be -1, 0, or 1")
    crossings: list[Array] = []
    shifted = values[:, axis] - float(level)
    for index in range(len(values) - 1):
        left, right = shifted[index], shifted[index + 1]
        delta = right - left
        if delta == 0.0:
            continue
        crossed = (left <= 0.0 < right) or (left >= 0.0 > right)
        if not crossed or (direction > 0 and delta <= 0.0) or (direction < 0 and delta >= 0.0):
            continue
        weight = -left / delta
        crossings.append(values[index] + weight * (values[index + 1] - values[index]))
    return np.asarray(crossings, dtype=float).reshape((-1, 3))


def local_maxima(values: Sequence[float]) -> Array:
    data = np.asarray(values, dtype=float)
    if data.size < 3:
        return np.empty(0, dtype=float)
    mask = (data[1:-1] > data[:-2]) & (data[1:-1] >= data[2:])
    return data[1:-1][mask]


def _rk4_state_tangent(
    system: AttractorSystem,
    state: Array,
    tangent: Array,
    dt: float,
    params: Mapping[str, float],
) -> tuple[Array, Array]:
    def derivative(x: Array, q: Array) -> tuple[Array, Array]:
        return system.rhs(x, params), system.jacobian(x, params) @ q

    x1, q1 = derivative(state, tangent)
    x2, q2 = derivative(state + 0.5 * dt * x1, tangent + 0.5 * dt * q1)
    x3, q3 = derivative(state + 0.5 * dt * x2, tangent + 0.5 * dt * q2)
    x4, q4 = derivative(state + dt * x3, tangent + dt * q3)
    return (
        state + (dt / 6.0) * (x1 + 2.0 * x2 + 2.0 * x3 + x4),
        tangent + (dt / 6.0) * (q1 + 2.0 * q2 + 2.0 * q3 + q4),
    )


def lyapunov_spectrum(
    system: AttractorSystem,
    params: Mapping[str, float],
    initial_state: Sequence[float],
    *,
    dt: float,
    steps: int,
    transient_steps: int = 0,
    renormalize_every: int = 10,
) -> Array:
    """Finite-time Benettin/QR estimate of all three Lyapunov exponents."""
    if steps <= transient_steps or renormalize_every < 1:
        raise ValueError("steps must exceed transient_steps and renormalize_every must be positive")
    state = _state(initial_state)
    tangent = np.eye(3, dtype=float)
    totals = np.zeros(3, dtype=float)
    elapsed = 0.0
    for step in range(1, steps + 1):
        state, tangent = _rk4_state_tangent(system, state, tangent, dt, params)
        if step % renormalize_every:
            continue
        q, r = np.linalg.qr(tangent)
        diagonal = np.maximum(np.abs(np.diag(r)), np.finfo(float).tiny)
        if step > transient_steps:
            totals += np.log(diagonal)
            elapsed += renormalize_every * dt
        tangent = q
    if elapsed <= 0.0:
        raise ValueError("no post-transient QR windows were accumulated")
    return np.sort(totals / elapsed)[::-1]


def kaplan_yorke_dimension(exponents: Sequence[float]) -> float:
    values = np.sort(np.asarray(exponents, dtype=float))[::-1]
    cumulative = 0.0
    for index, value in enumerate(values):
        next_sum = cumulative + value
        if next_sum < 0.0:
            if index == 0:
                return 0.0
            return float(index + cumulative / abs(value))
        cumulative = next_sum
    return float(len(values))


def step_halving_check(
    system: AttractorSystem,
    params: Mapping[str, float],
    initial_state: Sequence[float],
    *,
    dt: float,
    horizon: float = 1.0,
) -> dict[str, float]:
    """Short-horizon RK4 consistency check, separated from long chaotic divergence."""
    if horizon <= 0.0:
        raise ValueError("horizon must be positive")
    endpoints = []
    for divisor in (1, 2, 4):
        local_dt = dt / divisor
        steps = max(1, int(round(horizon / local_dt)))
        _, states = integrate(system, params, initial_state, dt=local_dt, steps=steps)
        endpoints.append(states[-1])
    error_coarse = float(np.linalg.norm(endpoints[0] - endpoints[1]))
    error_fine = float(np.linalg.norm(endpoints[1] - endpoints[2]))
    order = float(np.log2(error_coarse / error_fine)) if error_coarse > 0.0 and error_fine > 0.0 else float("nan")
    return {
        "horizon": float(horizon),
        "dt": float(dt),
        "error_dt_vs_half": error_coarse,
        "error_half_vs_quarter": error_fine,
        "observed_order": order,
    }


def sensitivity_diagnostic(
    system: AttractorSystem,
    params: Mapping[str, float],
    initial_state: Sequence[float],
    *,
    dt: float,
    steps: int,
    perturbation: float = 1e-9,
    threshold: float = 1.0,
) -> dict[str, object]:
    first = _state(initial_state)
    second = first.copy()
    second[0] += perturbation
    separations = np.empty(steps + 1, dtype=float)
    separations[0] = perturbation
    crossing_time: float | None = None
    for step in range(1, steps + 1):
        first = rk4_step(system, first, dt, params)
        second = rk4_step(system, second, dt, params)
        separations[step] = np.linalg.norm(second - first)
        if crossing_time is None and separations[step] >= threshold:
            crossing_time = step * dt
    return {
        "initial_perturbation": float(perturbation),
        "threshold": float(threshold),
        "threshold_crossing_time": crossing_time,
        "final_separation": float(separations[-1]),
        "maximum_separation": float(np.max(separations)),
    }


def spectral_peaks(values: Sequence[float], dt: float, *, count: int = 8) -> list[dict[str, float]]:
    data = np.asarray(values, dtype=float)
    if data.size < 4:
        return []
    centered = data - np.mean(data)
    amplitudes = np.abs(np.fft.rfft(centered))
    frequencies = np.fft.rfftfreq(data.size, d=dt)
    amplitudes[0] = 0.0
    indices = np.argsort(amplitudes)[::-1][:count]
    return [
        {"frequency": float(frequencies[index]), "amplitude": float(amplitudes[index])}
        for index in indices
        if amplitudes[index] > 0.0
    ]


def recurrence_and_correlation_estimates(
    states: Array,
    *,
    max_points: int = 500,
) -> dict[str, object]:
    """Finite sampled recurrence rate and log-log correlation-dimension fit."""
    values = np.asarray(states, dtype=float)
    if len(values) < 10:
        return {"recurrence_rate": float("nan"), "correlation_dimension": float("nan"), "fit_r2": float("nan")}
    stride = max(1, len(values) // max_points)
    sample = values[::stride][:max_points]
    scale = np.std(sample, axis=0)
    scale[scale == 0.0] = 1.0
    sample = (sample - np.mean(sample, axis=0)) / scale
    differences = sample[:, None, :] - sample[None, :, :]
    distances = np.linalg.norm(differences, axis=2)
    upper = distances[np.triu_indices(len(sample), k=1)]
    positive = upper[upper > 0.0]
    if positive.size < 20:
        return {"recurrence_rate": float("nan"), "correlation_dimension": float("nan"), "fit_r2": float("nan")}
    threshold = float(np.quantile(positive, 0.10))
    recurrence_rate = float(np.mean(positive <= threshold))
    radii = np.quantile(positive, np.linspace(0.03, 0.25, 10))
    counts = np.array([np.mean(positive <= radius) for radius in radii])
    mask = (radii > 0.0) & (counts > 0.0) & (counts < 1.0)
    if np.count_nonzero(mask) < 3:
        dimension, r2 = float("nan"), float("nan")
    else:
        x = np.log(radii[mask])
        y = np.log(counts[mask])
        slope, intercept = np.polyfit(x, y, 1)
        prediction = slope * x + intercept
        residual = np.sum((y - prediction) ** 2)
        total = np.sum((y - np.mean(y)) ** 2)
        dimension = float(slope)
        r2 = float(1.0 - residual / total) if total > 0.0 else float("nan")
    return {
        "sample_points": int(len(sample)),
        "normalized_distance_threshold": threshold,
        "recurrence_rate": recurrence_rate,
        "correlation_dimension": dimension,
        "fit_r2": r2,
        "claim_boundary": "finite sampled numerical estimates; not proofs of a fractal invariant",
    }


def emit_divergence_certificate(system_name: str) -> tuple[str, str, str]:
    """Emit hole-free Lean/Coq proofs for the exact divergence statement used."""
    name = system_name.lower()
    if name == "rossler":
        statement = "In x <= c-a-delta with delta >= 0, div f = a+x-c <= -delta."
        lean = """import Mathlib.Tactic

namespace FlowGap.Rossler

theorem contracting_region (a c x delta : ℝ)
    (hx : x ≤ c - a - delta) (hdelta : delta ≥ 0) :
    a + x - c ≤ -delta := by
  linarith

end FlowGap.Rossler
"""
        coq = """Require Import Reals. Require Import Lra.
Open Scope R_scope.
Section FlowGap_Rossler.
Variables a c x delta : R.
Hypothesis hx : x <= c - a - delta.
Hypothesis hdelta : delta >= 0.
Theorem contracting_region : a + x - c <= -delta.
Proof. lra. Qed.
End FlowGap_Rossler.
"""
    elif name == "lorenz":
        statement = "For sigma,beta >= 0, div f = -(sigma+1+beta) <= -1."
        lean = """import Mathlib.Tactic

namespace FlowGap.Lorenz

theorem global_volume_contraction (sigma beta : ℝ)
    (hsigma : sigma ≥ 0) (hbeta : beta ≥ 0) :
    -(sigma + 1 + beta) ≤ -1 := by
  linarith

end FlowGap.Lorenz
"""
        coq = """Require Import Reals. Require Import Lra.
Open Scope R_scope.
Section FlowGap_Lorenz.
Variables sigma beta : R.
Hypothesis hsigma : sigma >= 0.
Hypothesis hbeta : beta >= 0.
Theorem global_volume_contraction : -(sigma + 1 + beta) <= -1.
Proof. lra. Qed.
End FlowGap_Lorenz.
"""
    elif name == "thomas":
        statement = "For b > 0, div f = -3b < 0."
        lean = """import Mathlib.Tactic

namespace FlowGap.Thomas

theorem global_volume_contraction (b : ℝ) (hb : b > 0) :
    -3 * b < 0 := by
  nlinarith

end FlowGap.Thomas
"""
        coq = """Require Import Reals. Require Import Lra.
Open Scope R_scope.
Section FlowGap_Thomas.
Variable b : R.
Hypothesis hb : b > 0.
Theorem global_volume_contraction : -3 * b < 0.
Proof. nra. Qed.
End FlowGap_Thomas.
"""
    else:
        raise ValueError(f"no divergence certificate registered for {system_name!r}")
    return lean, coq, statement


def parameter_sweep(
    system: AttractorSystem,
    base_params: Mapping[str, float],
    parameter: str,
    values: Sequence[float],
    initial_state: Sequence[float],
    *,
    dt: float,
    steps: int,
    transient_steps: int,
    coordinate: int = 0,
    keep_maxima: int = 80,
) -> list[tuple[float, float]]:
    """Finite bifurcation-style sample using post-transient local maxima."""
    if parameter not in system.parameter_names:
        raise ValueError(f"{parameter!r} is not a parameter of {system.name}")
    points: list[tuple[float, float]] = []
    for value in values:
        params = dict(base_params)
        params[parameter] = float(value)
        _, states = integrate(system, params, initial_state, dt=dt, steps=steps)
        retained = states[min(transient_steps, len(states) - 1) :, coordinate]
        maxima = local_maxima(retained)
        for maximum in maxima[-keep_maxima:]:
            points.append((float(value), float(maximum)))
    return points


@dataclass
class AttractorAnalysis:
    system: str
    parameters: dict[str, float]
    initial_state: list[float]
    dt: float
    steps: int
    transient_steps: int
    times: Array
    trajectory: Array
    fixed_points: list[dict[str, object]]
    divergence: dict[str, float]
    poincare: Array
    lyapunov_exponents: Array
    kaplan_yorke_dimension: float
    convergence: dict[str, float]
    sensitivity: dict[str, object]
    spectral_peaks: list[dict[str, float]]
    recurrence: dict[str, object]
    lean4: str
    coq: str
    certificate_statement: str

    def summary(self) -> dict[str, object]:
        return {
            "kind": "flowgap_attractor_forge",
            "system": self.system,
            "parameters": self.parameters,
            "initial_state": self.initial_state,
            "dt": self.dt,
            "steps": self.steps,
            "transient_steps": self.transient_steps,
            "sample_count": int(len(self.trajectory)),
            "fixed_points": self.fixed_points,
            "divergence": self.divergence,
            "poincare_crossings": int(len(self.poincare)),
            "lyapunov_exponents": [float(value) for value in self.lyapunov_exponents],
            "kaplan_yorke_dimension": self.kaplan_yorke_dimension,
            "convergence": self.convergence,
            "sensitivity": self.sensitivity,
            "spectral_peaks": self.spectral_peaks,
            "recurrence": self.recurrence,
            "certificate_statement": self.certificate_statement,
            "certificate_hole_free": "sorry" not in self.lean4 and "Admitted" not in self.coq,
            "claim_boundary": (
                "finite-time deterministic ODE diagnostics only; Lyapunov, dimension, recurrence, "
                "Poincare, spectrum, and bifurcation outputs are numerical evidence, not formal proofs "
                "of chaos/global attraction/ergodicity; formal certificates cover only the stated "
                "algebraic divergence bound"
            ),
        }


def analyze_attractor(
    system_name: str = "rossler",
    *,
    parameter_overrides: Mapping[str, float] | None = None,
    initial_state: Sequence[float] | None = None,
    dt: float = 0.01,
    steps: int = 30000,
    transient_steps: int = 5000,
    sample_every: int = 1,
    lyapunov_steps: int | None = None,
    poincare_axis: int = 0,
    poincare_level: float = 0.0,
    poincare_direction: int = 1,
) -> AttractorAnalysis:
    system = get_system(system_name)
    params = system.parameters(parameter_overrides)
    state0 = _state(initial_state if initial_state is not None else system.default_state)
    if transient_steps < 0 or transient_steps >= steps:
        raise ValueError("transient_steps must satisfy 0 <= transient_steps < steps")
    times, trajectory = integrate(
        system, params, state0, dt=dt, steps=steps, sample_every=sample_every
    )
    transient_index = min(len(trajectory) - 1, transient_steps // sample_every)
    retained = trajectory[transient_index:]
    divergences = np.array([system.divergence(state, params) for state in retained], dtype=float)
    section = poincare_section(
        retained, axis=poincare_axis, level=poincare_level, direction=poincare_direction
    )
    exponents = lyapunov_spectrum(
        system,
        params,
        state0,
        dt=dt,
        steps=lyapunov_steps or steps,
        transient_steps=min(transient_steps, (lyapunov_steps or steps) // 2),
    )
    lean, coq, statement = emit_divergence_certificate(system.name)
    return AttractorAnalysis(
        system=system.name,
        parameters=params,
        initial_state=[float(value) for value in state0],
        dt=float(dt),
        steps=int(steps),
        transient_steps=int(transient_steps),
        times=times,
        trajectory=trajectory,
        fixed_points=fixed_point_analysis(system, params),
        divergence={
            "minimum": float(np.min(divergences)),
            "maximum": float(np.max(divergences)),
            "mean": float(np.mean(divergences)),
            "fraction_negative": float(np.mean(divergences < 0.0)),
        },
        poincare=section,
        lyapunov_exponents=exponents,
        kaplan_yorke_dimension=kaplan_yorke_dimension(exponents),
        convergence=step_halving_check(system, params, state0, dt=dt, horizon=min(1.0, steps * dt)),
        sensitivity=sensitivity_diagnostic(
            system, params, state0, dt=dt, steps=min(steps, max(1000, transient_steps * 2))
        ),
        spectral_peaks=spectral_peaks(retained[:, 0], dt * sample_every),
        recurrence=recurrence_and_correlation_estimates(retained),
        lean4=lean,
        coq=coq,
        certificate_statement=statement,
    )
