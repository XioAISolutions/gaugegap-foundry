"""Compile and verify scoped candidate axioms from an elevator experiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import Intervention
from .elevator import EinsteinElevatorWorld


@dataclass(frozen=True)
class VerificationResult:
    verdict: str
    local_cases: int
    local_failures: int
    boundary_cases: int
    boundary_differences_detected: int
    tolerance: float
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "local_cases": self.local_cases,
            "local_failures": self.local_failures,
            "boundary_cases": self.boundary_cases,
            "boundary_differences_detected": self.boundary_differences_detected,
            "tolerance": self.tolerance,
            "notes": list(self.notes),
        }


def compile_local_equivalence_axiom() -> dict[str, Any]:
    return {
        "id": "A1-local-mechanical-equivalence",
        "statement": "Within the tested local enclosed Newtonian regime, a uniform downward gravitational field and an equal uniform upward frame acceleration produce equivalent local mechanical observables.",
        "assumptions": [
            "local enclosed cabin",
            "uniform gravity",
            "uniform linear acceleration",
            "matched effective acceleration",
            "non-relativistic mechanical measurements",
        ],
        "compared_observables": [
            "apparent_weight_n",
            "relative_drop_acceleration_m_s2",
            "floor_reaction_force_n",
        ],
        "excluded_claims": [
            "global equivalence",
            "equivalence relative to an external inertial reference",
            "equivalence in non-uniform fields with tidal gradients",
            "full general relativity",
            "all optical or quantum phenomena",
        ],
        "falsifiers": [
            "Under the stated assumptions and matched effective acceleration, any compared observable differs beyond tolerance."
        ],
        "status": "candidate",
    }


def verify_local_equivalence(*, tolerance: float = 1e-10) -> VerificationResult:
    local_cases = 0
    local_failures = 0
    for mass in (1.0, 35.0, 70.0, 125.0):
        for composition in ("steel", "aluminium"):
            a = EinsteinElevatorWorld("gravity")
            b = EinsteinElevatorWorld("acceleration")
            a.reset(seed=17)
            b.reset(seed=17)
            for world in (a, b):
                world.intervene(Intervention("change_object_mass", {"mass_kg": mass}))
                world.intervene(Intervention("change_object_composition", {"composition": composition}))
            oa, ob = a.observe(), b.observe()
            local_cases += 1
            for key in (
                "apparent_weight_n",
                "relative_drop_acceleration_m_s2",
                "floor_reaction_force_n",
            ):
                av = oa.sensor_readings[key]
                bv = ob.sensor_readings[key]
                if av is None or bv is None or abs(av - bv) > tolerance:
                    local_failures += 1
                    break

    a = EinsteinElevatorWorld("gravity")
    b = EinsteinElevatorWorld("acceleration")
    a.reset(seed=23)
    b.reset(seed=23)
    oa = a.intervene(Intervention("open_external_reference")).observation
    ob = b.intervene(Intervention("open_external_reference")).observation
    ext_a = oa.sensor_readings["external_cabin_acceleration_up_m_s2"]
    ext_b = ob.sensor_readings["external_cabin_acceleration_up_m_s2"]
    boundary_differences = int(
        ext_a is not None and ext_b is not None and abs(ext_a - ext_b) > tolerance
    )

    verdict = (
        "supported_within_scope"
        if local_failures == 0 and boundary_differences == 1
        else "contradicted_or_scope_unresolved"
    )
    return VerificationResult(
        verdict=verdict,
        local_cases=local_cases,
        local_failures=local_failures,
        boundary_cases=1,
        boundary_differences_detected=boundary_differences,
        tolerance=tolerance,
        notes=[
            "The result applies only to the implemented Newtonian local-mechanics world.",
            "The external-reference intervention intentionally breaks the local enclosure assumption.",
        ],
    )
