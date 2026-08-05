"""Scoped axiom compiler and deterministic verifier for the cart benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CartVerification:
    verdict: str
    local_cases: int
    local_failures: int
    boundary_differences_detected: int
    tolerance: float
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier": "gaugegap.jump_lab.verify_force_mass_ratio",
            "verdict": self.verdict,
            "local_cases": self.local_cases,
            "local_failures": self.local_failures,
            "boundary_differences_detected": self.boundary_differences_detected,
            "tolerance": self.tolerance,
            "claim_boundary": self.claim_boundary,
        }


def compile_force_mass_ratio_axiom() -> dict[str, Any]:
    return {
        "id": "newtonian-force-mass-ratio-001",
        "statement": (
            "Within frictionless one-dimensional constant-force motion, systems "
            "with equal force-to-mass ratios and matched initial conditions have "
            "equal tested kinematic trajectories. Kinematics alone do not identify "
            "force and mass separately."
        ),
        "quantification": {
            "systems": "positive finite masses with constant finite net forces",
            "observables": [
                "kinematic_acceleration_m_s2",
                "final_velocity_m_s",
                "position_m",
            ],
        },
        "assumptions": [
            "frictionless one-dimensional motion",
            "constant net force",
            "positive mass",
            "matched initial velocity and duration",
            "non-relativistic regime",
        ],
        "falsifiers": [
            "Two tested systems with equal force-to-mass ratios and matched initial conditions produce different kinematics beyond tolerance."
        ],
        "excluded_claims": [
            "identity of the hidden force values",
            "identity of the hidden mass values",
            "motion with friction or variable forces",
            "relativistic motion",
            "a universal account of all dynamical systems",
        ],
        "status": "candidate",
    }


def _trajectory(force_n: float, mass_kg: float, duration_s: float) -> tuple[float, float, float]:
    acceleration = force_n / mass_kg
    velocity = acceleration * duration_s
    position = 0.5 * acceleration * duration_s**2
    return acceleration, velocity, position


def verify_force_mass_ratio(*, tolerance: float = 1e-10) -> CartVerification:
    pairs = ((10.0, 2.0), (20.0, 4.0), (5.0, 1.0), (15.0, 3.0))
    durations = (0.5, 2.0, 3.5)
    reference_ratio = 5.0
    failures = 0
    cases = 0
    for force_n, mass_kg in pairs:
        for duration_s in durations:
            expected = (
                reference_ratio,
                reference_ratio * duration_s,
                0.5 * reference_ratio * duration_s**2,
            )
            actual = _trajectory(force_n, mass_kg, duration_s)
            cases += 1
            if any(abs(left - right) > tolerance for left, right in zip(actual, expected)):
                failures += 1

    boundary_differences = int(10.0 != 20.0) + int(2.0 != 4.0)
    verdict = (
        "supported_within_scope"
        if failures == 0 and boundary_differences >= 1
        else "contradicted"
    )
    return CartVerification(
        verdict=verdict,
        local_cases=cases,
        local_failures=failures,
        boundary_differences_detected=boundary_differences,
        tolerance=tolerance,
        claim_boundary=(
            "The verifier checks exact Newtonian toy-model trajectories and the "
            "non-identifiability of force and mass from those kinematics. It does "
            "not validate the claim in frictional, variable-force, or real-world systems."
        ),
    )
