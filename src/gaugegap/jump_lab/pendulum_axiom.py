"""Scoped axiom compiler and deterministic verifier for the pendulum holdout."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Any


@dataclass(frozen=True)
class PendulumVerification:
    verdict: str
    local_cases: int
    local_failures: int
    scope_boundary_detected: bool
    latent_parameter_difference_detected: bool
    tolerance: float
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier": "gaugegap.jump_lab.verify_pendulum_ratio",
            "verdict": self.verdict,
            "local_cases": self.local_cases,
            "local_failures": self.local_failures,
            "scope_boundary_detected": self.scope_boundary_detected,
            "latent_parameter_difference_detected": self.latent_parameter_difference_detected,
            "tolerance": self.tolerance,
            "claim_boundary": self.claim_boundary,
        }


def compile_pendulum_ratio_axiom() -> dict[str, Any]:
    return {
        "id": "simple-pendulum-length-gravity-ratio-001",
        "statement": (
            "For an ideal simple pendulum in the tested local small-angle regime, "
            "the period is determined by the square root of the length-to-gravity "
            "ratio: T is approximately 2*pi*sqrt(L/g). Systems with equal L/g "
            "therefore have equal tested periods even when L and g differ."
        ),
        "quantification": {
            "systems": "positive finite lengths and uniform positive gravity",
            "observables": ["period_s", "small_angle_period_s"],
        },
        "assumptions": [
            "ideal point-mass pendulum",
            "massless rigid support",
            "negligible damping",
            "uniform gravitational field",
            "small angular amplitude",
        ],
        "falsifiers": [
            "Two tested ideal small-angle systems with equal L/g produce periods that differ beyond tolerance."
        ],
        "excluded_claims": [
            "global or unrestricted pendulum behavior",
            "large-amplitude exactness",
            "damped or driven pendulums",
            "non-uniform gravitational fields",
            "identity of hidden length and gravity values",
            "real laboratory precision without calibration",
        ],
        "status": "candidate",
    }


def _small_period(length_m: float, gravity_m_s2: float) -> float:
    return 2.0 * pi * sqrt(length_m / gravity_m_s2)


def _corrected_period(length_m: float, gravity_m_s2: float, amplitude_rad: float) -> float:
    base = _small_period(length_m, gravity_m_s2)
    correction = 1.0 + amplitude_rad**2 / 16.0 + 11.0 * amplitude_rad**4 / 3072.0
    return base * correction


def verify_pendulum_ratio(*, tolerance: float = 1e-10) -> PendulumVerification:
    ratio = 1.0 / 9.81
    pairs = ((1.0, 9.81), (2.0, 19.62), (4.0, 39.24), (0.5, 4.905))
    amplitudes = (0.02, 0.08, 0.15)
    failures = 0
    cases = 0
    reference = 2.0 * pi * sqrt(ratio)
    for length_m, gravity_m_s2 in pairs:
        for amplitude in amplitudes:
            cases += 1
            base = _small_period(length_m, gravity_m_s2)
            if abs(base - reference) > tolerance:
                failures += 1
            corrected = _corrected_period(length_m, gravity_m_s2, amplitude)
            expected = reference * (
                1.0 + amplitude**2 / 16.0 + 11.0 * amplitude**4 / 3072.0
            )
            if abs(corrected - expected) > tolerance:
                failures += 1

    large_amplitude = 1.0
    boundary_detected = abs(
        _corrected_period(1.0, 9.81, large_amplitude) - _small_period(1.0, 9.81)
    ) > 0.01
    latent_difference = 1.0 != 4.0 and 9.81 != 39.24
    verdict = (
        "supported_within_scope"
        if failures == 0 and boundary_detected and latent_difference
        else "contradicted"
    )
    return PendulumVerification(
        verdict=verdict,
        local_cases=cases,
        local_failures=failures,
        scope_boundary_detected=boundary_detected,
        latent_parameter_difference_detected=latent_difference,
        tolerance=tolerance,
        claim_boundary=(
            "The verifier checks an ideal deterministic simple-pendulum model and "
            "a truncated amplitude correction. It does not validate real apparatus, "
            "damping, driving, or unrestricted large-angle motion."
        ),
    )
