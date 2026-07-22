"""Structured exact reconstruction for Counterexample Forge benchmark 0001.

This module does not receive the benchmark's final coefficient tuple.  It searches
an explicitly declared one-parameter family obtained by reducing the
constant-Jacobian coefficient equations for a sparse polynomial ansatz, then
uses the public exact collision constraints as the falsification predicate.

The result is therefore labelled REDISCOVERED within a declared ansatz, not a
blind discovery and not a new mathematical result.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Iterable, Sequence

from .counterexample_forge import (
    CounterexampleVerification,
    Polynomial,
    PolynomialMap,
    canonical_json,
    jacobian_benchmark_witnesses,
    verify_polynomial_counterexample,
)


RECONSTRUCTION_BOUNDARY = (
    "REDISCOVERED means the published coefficient tuple was recovered without "
    "supplying that tuple to the search. The search is restricted to a declared "
    "sparse ansatz and algebraically reduced one-parameter family; it is not blind "
    "search, minimality evidence, or a new mathematical discovery."
)


@dataclass(frozen=True)
class ReconstructionCoefficients:
    """Exact coefficients for the declared sparse ansatz."""

    a: Fraction
    b: Fraction
    c: Fraction
    d: Fraction
    e: Fraction

    def to_dict(self) -> dict[str, object]:
        return {
            name: {"numerator": value.numerator, "denominator": value.denominator}
            for name, value in (
                ("a", self.a),
                ("b", self.b),
                ("c", self.c),
                ("d", self.d),
                ("e", self.e),
            )
        }


@dataclass(frozen=True)
class ReconstructionTrial:
    parameter_e: Fraction
    coefficients: ReconstructionCoefficients
    candidate_digest: str
    determinant: Fraction | None
    collision_passed: bool
    verified: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "parameter_e": {
                "numerator": self.parameter_e.numerator,
                "denominator": self.parameter_e.denominator,
            },
            "coefficients": self.coefficients.to_dict(),
            "candidate_digest": self.candidate_digest,
            "determinant": None
            if self.determinant is None
            else {
                "numerator": self.determinant.numerator,
                "denominator": self.determinant.denominator,
            },
            "collision_passed": self.collision_passed,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class ReconstructionResult:
    attempted: int
    parameter_values: tuple[int, ...]
    trials: tuple[ReconstructionTrial, ...]
    solutions: tuple[PolynomialMap, ...]
    verifications: tuple[CounterexampleVerification, ...]
    release_label: str = "REDISCOVERED"
    claim_boundary: str = RECONSTRUCTION_BOUNDARY

    @property
    def unique_solution(self) -> PolynomialMap | None:
        return self.solutions[0] if len(self.solutions) == 1 else None

    def to_dict(self) -> dict[str, object]:
        solution_payloads: list[dict[str, object]] = []
        for candidate, verification in zip(self.solutions, self.verifications):
            solution_payloads.append(
                {
                    "candidate": candidate.to_dict(),
                    "candidate_digest": candidate.digest(),
                    "verification": verification.to_dict(),
                }
            )
        payload: dict[str, object] = {
            "schema": "gaugegap.counterexample_reconstruction.v1",
            "problem_id": "counterexample-forge-0001",
            "release_label": self.release_label,
            "method": "exact_structured_one_parameter_reconstruction",
            "attempted": self.attempted,
            "parameter_values": list(self.parameter_values),
            "ansatz": {
                "t": "1 + x*y",
                "F1": "t^3*z + y^2*t*(a + b*x*y)",
                "F2": "y + c*x*t^2*z + c*x*y^2*(a + b*x*y)",
                "F3": "d*x + e*x^2*y - x^3*z",
                "constant_jacobian_reduction": {
                    "a": "-4*e/3",
                    "b": "-e",
                    "c": "-9/e",
                    "d": "-2*e/3",
                    "restriction": "e != 0",
                },
            },
            "trials": [trial.to_dict() for trial in self.trials],
            "solutions": solution_payloads,
            "claim_boundary": self.claim_boundary,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["reconstruction_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def coefficients_from_parameter(parameter_e: int | Fraction) -> ReconstructionCoefficients:
    e = parameter_e if isinstance(parameter_e, Fraction) else Fraction(parameter_e, 1)
    if e == 0:
        raise ValueError("the reduced constant-Jacobian family requires e != 0")
    return ReconstructionCoefficients(
        a=Fraction(-4, 3) * e,
        b=-e,
        c=Fraction(-9, 1) / e,
        d=Fraction(-2, 3) * e,
        e=e,
    )


def candidate_from_parameter(parameter_e: int | Fraction) -> PolynomialMap:
    """Instantiate the declared ansatz from one exact search parameter."""

    coefficients = coefficients_from_parameter(parameter_e)
    variables = ("x", "y", "z")
    x = Polynomial.variable(variables, 0)
    y = Polynomial.variable(variables, 1)
    z = Polynomial.variable(variables, 2)
    t = 1 + x * y
    f1 = t**3 * z + y**2 * t * (coefficients.a + coefficients.b * x * y)
    f2 = (
        y
        + coefficients.c * x * t**2 * z
        + coefficients.c * x * y**2 * (coefficients.a + coefficients.b * x * y)
    )
    f3 = coefficients.d * x + coefficients.e * x**2 * y - x**3 * z
    return PolynomialMap(
        variables,
        (f1, f2, f3),
        name="jacobian-three-variable-public-benchmark",
    )


def reconstruct_jacobian_benchmark(
    parameter_values: Iterable[int] = range(-8, 9),
    *,
    witnesses: Sequence[Sequence[int | Fraction]] | None = None,
) -> ReconstructionResult:
    """Search the reduced exact family and retain only fully verified collisions."""

    values = tuple(sorted(set(int(value) for value in parameter_values if int(value) != 0)))
    if not values:
        raise ValueError("at least one nonzero integer parameter value is required")
    exact_witnesses = tuple(witnesses) if witnesses is not None else jacobian_benchmark_witnesses()

    trials: list[ReconstructionTrial] = []
    solutions: list[PolynomialMap] = []
    verifications: list[CounterexampleVerification] = []
    for value in values:
        coefficients = coefficients_from_parameter(value)
        candidate = candidate_from_parameter(value)
        verification = verify_polynomial_counterexample(candidate, exact_witnesses)
        collision_gate = next(gate for gate in verification.gates if gate.name == "exact_collision")
        trials.append(
            ReconstructionTrial(
                parameter_e=Fraction(value, 1),
                coefficients=coefficients,
                candidate_digest=candidate.digest(),
                determinant=verification.determinant,
                collision_passed=collision_gate.passed,
                verified=verification.passed,
            )
        )
        if verification.passed:
            solutions.append(candidate)
            verifications.append(verification)

    return ReconstructionResult(
        attempted=len(values),
        parameter_values=values,
        trials=tuple(trials),
        solutions=tuple(solutions),
        verifications=tuple(verifications),
    )


def reconstruction_json(result: ReconstructionResult) -> str:
    return canonical_json(result.to_dict())
