"""Exact, fail-closed counterexample verification for finite algebraic witnesses.

Counterexample Forge does not certify candidates from floating-point evidence or
model confidence.  A candidate advances only when its executable falsification
predicate is discharged with exact arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Iterable, Mapping, Sequence


CLAIM_BOUNDARY = (
    "This module verifies an explicit finite algebraic witness over exact rationals. "
    "Verification of a previously published map is REPRODUCED evidence, not an "
    "original discovery, and it does not resolve any separately open lower-dimensional case."
)

Monomial = tuple[int, ...]
Term = tuple[Monomial, Fraction]
ExactScalar = int | Fraction


def _fraction(value: ExactScalar) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("exact polynomial coefficients and points must be int or Fraction")
    return Fraction(value, 1)


def _fraction_dict(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


@dataclass(frozen=True)
class Polynomial:
    """Sparse multivariate polynomial with canonical exact-rational terms."""

    variables: tuple[str, ...]
    terms: tuple[Term, ...]

    def __post_init__(self) -> None:
        if not self.variables:
            raise ValueError("a polynomial requires at least one variable")
        if len(set(self.variables)) != len(self.variables):
            raise ValueError("variable names must be unique")
        normalized: dict[Monomial, Fraction] = {}
        for powers, coefficient in self.terms:
            if len(powers) != len(self.variables):
                raise ValueError("monomial dimension does not match variables")
            if any(power < 0 for power in powers):
                raise ValueError("negative exponents are not polynomial terms")
            exact = _fraction(coefficient)
            if exact:
                normalized[powers] = normalized.get(powers, Fraction(0)) + exact
        canonical = tuple(
            (powers, coefficient)
            for powers, coefficient in sorted(normalized.items())
            if coefficient
        )
        object.__setattr__(self, "terms", canonical)

    @classmethod
    def zero(cls, variables: Sequence[str]) -> "Polynomial":
        return cls(tuple(variables), ())

    @classmethod
    def constant(cls, variables: Sequence[str], value: ExactScalar) -> "Polynomial":
        exact = _fraction(value)
        if not exact:
            return cls.zero(variables)
        return cls(tuple(variables), (((0,) * len(tuple(variables)), exact),))

    @classmethod
    def variable(cls, variables: Sequence[str], index: int) -> "Polynomial":
        names = tuple(variables)
        if index < 0 or index >= len(names):
            raise IndexError("variable index out of range")
        powers = [0] * len(names)
        powers[index] = 1
        return cls(names, ((tuple(powers), Fraction(1)),))

    def _coerce(self, other: "Polynomial | ExactScalar") -> "Polynomial":
        if isinstance(other, Polynomial):
            if other.variables != self.variables:
                raise ValueError("polynomial variable sets must match")
            return other
        return Polynomial.constant(self.variables, other)

    def __add__(self, other: "Polynomial | ExactScalar") -> "Polynomial":
        rhs = self._coerce(other)
        return Polynomial(self.variables, self.terms + rhs.terms)

    def __radd__(self, other: "Polynomial | ExactScalar") -> "Polynomial":
        return self + other

    def __neg__(self) -> "Polynomial":
        return Polynomial(self.variables, tuple((powers, -coefficient) for powers, coefficient in self.terms))

    def __sub__(self, other: "Polynomial | ExactScalar") -> "Polynomial":
        return self + (-self._coerce(other))

    def __rsub__(self, other: "Polynomial | ExactScalar") -> "Polynomial":
        return self._coerce(other) - self

    def __mul__(self, other: "Polynomial | ExactScalar") -> "Polynomial":
        rhs = self._coerce(other)
        products: list[Term] = []
        for left_powers, left_coefficient in self.terms:
            for right_powers, right_coefficient in rhs.terms:
                powers = tuple(a + b for a, b in zip(left_powers, right_powers))
                products.append((powers, left_coefficient * right_coefficient))
        return Polynomial(self.variables, tuple(products))

    def __rmul__(self, other: "Polynomial | ExactScalar") -> "Polynomial":
        return self * other

    def __pow__(self, exponent: int) -> "Polynomial":
        if not isinstance(exponent, int) or exponent < 0:
            raise ValueError("polynomial exponent must be a non-negative integer")
        result = Polynomial.constant(self.variables, 1)
        base = self
        power = exponent
        while power:
            if power & 1:
                result = result * base
            base = base * base
            power //= 2
        return result

    def derivative(self, index: int) -> "Polynomial":
        if index < 0 or index >= len(self.variables):
            raise IndexError("variable index out of range")
        derived: list[Term] = []
        for powers, coefficient in self.terms:
            exponent = powers[index]
            if exponent == 0:
                continue
            next_powers = list(powers)
            next_powers[index] -= 1
            derived.append((tuple(next_powers), coefficient * exponent))
        return Polynomial(self.variables, tuple(derived))

    def evaluate(self, point: Sequence[ExactScalar]) -> Fraction:
        if len(point) != len(self.variables):
            raise ValueError("point dimension does not match polynomial")
        exact_point = tuple(_fraction(value) for value in point)
        total = Fraction(0)
        for powers, coefficient in self.terms:
            term = coefficient
            for value, power in zip(exact_point, powers):
                term *= value**power
            total += term
        return total

    @property
    def is_constant(self) -> bool:
        return all(not any(powers) for powers, _ in self.terms)

    @property
    def constant_value(self) -> Fraction | None:
        if not self.is_constant:
            return None
        if not self.terms:
            return Fraction(0)
        return self.terms[0][1]

    @property
    def total_degree(self) -> int:
        return max((sum(powers) for powers, _ in self.terms), default=0)

    def to_dict(self) -> dict[str, object]:
        return {
            "variables": list(self.variables),
            "terms": [
                {"powers": list(powers), "coefficient": _fraction_dict(coefficient)}
                for powers, coefficient in self.terms
            ],
        }


@dataclass(frozen=True)
class PolynomialMap:
    variables: tuple[str, ...]
    coordinates: tuple[Polynomial, ...]
    name: str = "unnamed-polynomial-map"

    def __post_init__(self) -> None:
        if not self.coordinates:
            raise ValueError("a polynomial map requires coordinates")
        for coordinate in self.coordinates:
            if coordinate.variables != self.variables:
                raise ValueError("coordinate variables must match the map")

    def evaluate(self, point: Sequence[ExactScalar]) -> tuple[Fraction, ...]:
        return tuple(coordinate.evaluate(point) for coordinate in self.coordinates)

    def jacobian(self) -> tuple[tuple[Polynomial, ...], ...]:
        return tuple(
            tuple(coordinate.derivative(index) for index in range(len(self.variables)))
            for coordinate in self.coordinates
        )

    def jacobian_determinant(self) -> Polynomial:
        matrix = self.jacobian()
        if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
            raise NotImplementedError("v1 exact determinant supports 3x3 polynomial maps")
        a, b, c = matrix[0]
        d, e, f = matrix[1]
        g, h, i = matrix[2]
        return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)

    def complexity(self) -> dict[str, int]:
        coefficients = [coefficient for coordinate in self.coordinates for _, coefficient in coordinate.terms]
        coefficient_bits = sum(
            max(1, abs(value.numerator).bit_length()) + max(1, value.denominator.bit_length())
            for value in coefficients
        )
        return {
            "coordinates": len(self.coordinates),
            "terms": sum(len(coordinate.terms) for coordinate in self.coordinates),
            "max_total_degree": max(coordinate.total_degree for coordinate in self.coordinates),
            "coefficient_bit_length_total": coefficient_bits,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.polynomial_map.v1",
            "name": self.name,
            "variables": list(self.variables),
            "coordinates": [coordinate.to_dict() for coordinate in self.coordinates],
            "complexity": self.complexity(),
        }

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VerificationGate:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class CounterexampleVerification:
    candidate_digest: str
    passed: bool
    determinant: Fraction | None
    common_image: tuple[Fraction, ...] | None
    gates: tuple[VerificationGate, ...]
    claim_boundary: str = CLAIM_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.counterexample_verification.v1",
            "candidate_digest": self.candidate_digest,
            "passed": self.passed,
            "determinant": None if self.determinant is None else _fraction_dict(self.determinant),
            "common_image": None
            if self.common_image is None
            else [_fraction_dict(value) for value in self.common_image],
            "gates": [gate.to_dict() for gate in self.gates],
            "claim_boundary": self.claim_boundary,
        }


def verify_polynomial_counterexample(
    candidate: PolynomialMap,
    witnesses: Sequence[Sequence[ExactScalar]],
    *,
    expected_determinant: ExactScalar | None = None,
) -> CounterexampleVerification:
    """Verify a constant nonzero Jacobian and an exact collision witness."""

    gates: list[VerificationGate] = []
    determinant_polynomial = candidate.jacobian_determinant()
    determinant = determinant_polynomial.constant_value
    gates.append(
        VerificationGate(
            "constant_nonzero_jacobian",
            determinant is not None and determinant != 0,
            "Jacobian determinant is an exact nonzero constant."
            if determinant is not None and determinant != 0
            else "Jacobian determinant is zero or depends on the variables.",
        )
    )

    if expected_determinant is not None:
        expected = _fraction(expected_determinant)
        gates.append(
            VerificationGate(
                "expected_determinant",
                determinant == expected,
                f"det(JF) == {expected}" if determinant == expected else f"det(JF) != {expected}",
            )
        )

    exact_witnesses: tuple[tuple[Fraction, ...], ...]
    try:
        exact_witnesses = tuple(tuple(_fraction(value) for value in point) for point in witnesses)
        valid_dimensions = len(exact_witnesses) >= 2 and all(
            len(point) == len(candidate.variables) for point in exact_witnesses
        )
    except (TypeError, ValueError):
        exact_witnesses = ()
        valid_dimensions = False
    gates.append(
        VerificationGate(
            "witness_shape",
            valid_dimensions,
            "At least two exact witnesses have the declared dimension."
            if valid_dimensions
            else "Witnesses must be exact and match the declared dimension.",
        )
    )

    distinct = valid_dimensions and len(set(exact_witnesses)) == len(exact_witnesses)
    gates.append(
        VerificationGate(
            "distinct_witnesses",
            distinct,
            "Witness points are pairwise distinct." if distinct else "Witness points are not pairwise distinct.",
        )
    )

    images: tuple[tuple[Fraction, ...], ...] = ()
    collision = False
    common_image: tuple[Fraction, ...] | None = None
    if valid_dimensions:
        images = tuple(candidate.evaluate(point) for point in exact_witnesses)
        collision = len(set(images)) == 1
        if collision:
            common_image = images[0]
    gates.append(
        VerificationGate(
            "exact_collision",
            collision,
            "All witness points have the same exact image."
            if collision
            else "Witness images are not exactly equal.",
        )
    )

    passed = all(gate.passed for gate in gates)
    return CounterexampleVerification(
        candidate_digest=candidate.digest(),
        passed=passed,
        determinant=determinant,
        common_image=common_image,
        gates=tuple(gates),
    )


def jacobian_benchmark_map() -> PolynomialMap:
    """Return the public three-variable Jacobian counterexample benchmark."""

    variables = ("x", "y", "z")
    x = Polynomial.variable(variables, 0)
    y = Polynomial.variable(variables, 1)
    z = Polynomial.variable(variables, 2)
    t = 1 + x * y
    f1 = t**3 * z + y**2 * t * (4 + 3 * x * y)
    f2 = y + 3 * x * t**2 * z + 3 * x * y**2 * (4 + 3 * x * y)
    f3 = 2 * x - 3 * x**2 * y - x**3 * z
    return PolynomialMap(variables, (f1, f2, f3), name="jacobian-three-variable-public-benchmark")


def jacobian_benchmark_witnesses() -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    return (
        (Fraction(0), Fraction(0), Fraction(-1, 4)),
        (Fraction(1), Fraction(-3, 2), Fraction(13, 2)),
        (Fraction(-1), Fraction(3, 2), Fraction(13, 2)),
    )


def build_counterexample_proofpack(
    candidate: PolynomialMap,
    witnesses: Sequence[Sequence[ExactScalar]],
    verification: CounterexampleVerification,
    *,
    release_label: str = "REPRODUCED",
    problem_id: str = "counterexample-forge-0001",
) -> dict[str, object]:
    if release_label not in {"REPRODUCED", "REDISCOVERED", "DISCOVERED"}:
        raise ValueError("release_label must be REPRODUCED, REDISCOVERED, or DISCOVERED")
    exact_witnesses = tuple(tuple(_fraction(value) for value in point) for point in witnesses)
    payload: dict[str, object] = {
        "schema": "gaugegap.counterexample_proofpack.v1",
        "problem_id": problem_id,
        "release_label": release_label,
        "candidate": candidate.to_dict(),
        "candidate_digest": candidate.digest(),
        "witnesses": [
            [_fraction_dict(value) for value in point]
            for point in exact_witnesses
        ],
        "verification": verification.to_dict(),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["proofpack_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
