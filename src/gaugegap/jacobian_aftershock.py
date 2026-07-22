"""Exact Jacobian-aftershock search and verification.

This module derives and verifies a compact four-sheet Keller map inside the
normalized cubic weighted-lift family.  It also audits the family coefficient
factors exactly to identify the unique expanded-monomial minimum in that
normalization.

The mathematical identities are exact.  Historical priority and literature
novelty are not established by this module.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from math import gcd
from typing import Iterable, Sequence

from .counterexample_forge import (
    CounterexampleVerification,
    Polynomial,
    PolynomialMap,
    canonical_json,
    verify_polynomial_counterexample,
)


AFTERSHOCK_BOUNDARY = (
    "This track proves exact finite identities for a derived polynomial map and "
    "an exact monomial-count optimum inside one explicitly normalized cubic "
    "weighted-lift family. It does not establish literature priority, global "
    "minimality among all Keller maps, or a solution of any remaining open "
    "two-dimensional Jacobian problem."
)

# Coefficient numerators for the expanded normalized cubic weighted-lift map.
# Polynomials are represented in ascending powers of the seed parameter g.
# The generic map has 16 + 14 + 3 = 33 monomials.  Denominators are powers of
# g - 4, so g = 4 is excluded by the construction.
_CUBIC_F1_NUMERATORS: tuple[tuple[int, ...], ...] = (
    (0, 3),
    (0, 18, -3),
    (0, 3),
    (0, 108, -36, 3),
    (0, 60, -9),
    (0, 9),
    (0, 144, -42, 3),
    (8, 32, -4),
    (0, 3),
    (192, 136, -32, 1),
    (24, 6),
    (0, 3),
    (112, -48, 12, -1),
    (48, -18, 3),
    (128, -74, 16, -1),
    (-4, 1),
)

_CUBIC_F2_NUMERATORS: tuple[tuple[int, ...], ...] = (
    (0, 1),
    (0, 12, -2),
    (0, 3),
    (0, 36, -12, 1),
    (0, 28, -4),
    (0, 3),
    (0, 60, -16, 1),
    (24, 30, -3),
    (0, 1),
    (144, -28, 8, -1),
    (24, -6, 1),
    (192, -96, 18, -1),
    (-6, 1),
    (-2,),
)

# The third coordinate is x + ((6-g)/(g-4)) x^2 y + x^3 z.
_CUBIC_F3_MIDDLE_NUMERATOR = (6, -1)


@dataclass(frozen=True)
class CubicSeedMinimumCertificate:
    generic_term_count: int
    minimum_term_count: int
    unique_parameter: Fraction
    degree_drop_parameter: Fraction
    invalid_parameter: Fraction
    cancellation_ledger: tuple[tuple[tuple[int, ...], int], ...]
    claim_boundary: str = AFTERSHOCK_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.cubic_seed_minimum.v1",
            "generic_term_count": self.generic_term_count,
            "minimum_term_count": self.minimum_term_count,
            "unique_parameter": _fraction_dict(self.unique_parameter),
            "degree_drop_parameter": _fraction_dict(self.degree_drop_parameter),
            "invalid_parameter": _fraction_dict(self.invalid_parameter),
            "cancellation_ledger": [
                {"factor": list(factor), "coefficient_occurrences": occurrences}
                for factor, occurrences in self.cancellation_ledger
            ],
            "normalization": {
                "seed": "p_g(w)=(2+g/2)w+(-3-3g/2)w^2+g w^3",
                "u": "1+xy",
                "gamma": "1-((g-6)/(g-4))xy+x^2z",
                "first_output_scale": 2,
            },
            "claim_boundary": self.claim_boundary,
        }


@dataclass(frozen=True)
class AftershockResult:
    map_digest: str
    determinant: Fraction
    coordinate_term_counts: tuple[int, ...]
    coordinate_degrees: tuple[int, ...]
    collision_verification: CounterexampleVerification
    four_point_verification: CounterexampleVerification
    family_minimum: CubicSeedMinimumCertificate
    evidence_label: str = "DERIVED_EXACT"
    novelty_status: str = "UNESTABLISHED"
    claim_boundary: str = AFTERSHOCK_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": "gaugegap.jacobian_aftershock.v1",
            "problem_id": "counterexample-forge-0002",
            "evidence_label": self.evidence_label,
            "novelty_status": self.novelty_status,
            "map_digest": self.map_digest,
            "determinant": _fraction_dict(self.determinant),
            "coordinate_term_counts": list(self.coordinate_term_counts),
            "coordinate_degrees": list(self.coordinate_degrees),
            "collision_verification": self.collision_verification.to_dict(),
            "four_point_verification": self.four_point_verification.to_dict(),
            "family_minimum": self.family_minimum.to_dict(),
            "claim_boundary": self.claim_boundary,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["result_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return payload


def _fraction_dict(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def compact_four_sheet_map() -> PolynomialMap:
    """Return the 25-monomial integer-coefficient Keller map.

    Compact weighted form, with u = 1 + xy and gamma = 1 + x^2 z::

        H1 = [2u + u^2(9u^2 gamma^2 - 16u gamma + 5)] / x^2
        H2 = [1 + u(6u^2 gamma^2 - 12u gamma + 5)] / x
        H3 = x gamma

    The apparent quotients cancel identically.  The sparse representation below
    stores the expanded polynomials directly, so no division enters verification.
    """

    variables = ("x", "y", "z")
    h1 = Polynomial(
        variables,
        (
            ((6, 4, 2), Fraction(9)),
            ((5, 3, 2), Fraction(36)),
            ((4, 4, 1), Fraction(18)),
            ((4, 2, 2), Fraction(54)),
            ((3, 3, 1), Fraction(56)),
            ((3, 1, 2), Fraction(36)),
            ((2, 4, 0), Fraction(9)),
            ((2, 2, 1), Fraction(60)),
            ((2, 0, 2), Fraction(9)),
            ((1, 3, 0), Fraction(20)),
            ((1, 1, 1), Fraction(24)),
            ((0, 2, 0), Fraction(11)),
            ((0, 0, 1), Fraction(2)),
        ),
    )
    h2 = Polynomial(
        variables,
        (
            ((6, 3, 2), Fraction(6)),
            ((5, 2, 2), Fraction(18)),
            ((4, 3, 1), Fraction(12)),
            ((4, 1, 2), Fraction(18)),
            ((3, 2, 1), Fraction(24)),
            ((3, 0, 2), Fraction(6)),
            ((2, 3, 0), Fraction(6)),
            ((2, 1, 1), Fraction(12)),
            ((1, 2, 0), Fraction(6)),
            ((0, 1, 0), Fraction(-1)),
        ),
    )
    h3 = Polynomial(
        variables,
        (
            ((3, 0, 1), Fraction(1)),
            ((1, 0, 0), Fraction(1)),
        ),
    )
    return PolynomialMap(
        variables,
        (h1, h2, h3),
        name="jacobian-aftershock-compact-four-sheet-map",
    )


def compact_collision_witnesses() -> tuple[tuple[Fraction, ...], ...]:
    """Two short rational points with one exact image."""

    return (
        (Fraction(1, 3), Fraction(-10, 3), Fraction(18)),
        (Fraction(-1, 3), Fraction(14, 3), Fraction(-36)),
    )


def compact_collision_image() -> tuple[Fraction, ...]:
    return (Fraction(-20, 27), Fraction(-2, 9), Fraction(1))


def compact_four_point_witnesses() -> tuple[tuple[Fraction, ...], ...]:
    """A fully rational four-point fiber of the compact map."""

    return (
        (Fraction(9, 2), Fraction(-2, 9), Fraction(-748, 19683)),
        (Fraction(-28, 5), Fraction(2, 7), Fraction(-50, 1323)),
        (Fraction(4, 3), Fraction(0), Fraction(-1, 8)),
        (Fraction(-7, 30), Fraction(6), Fraction(-100)),
    )


def compact_four_point_image() -> tuple[Fraction, ...]:
    return (Fraction(0), Fraction(2, 9), Fraction(28, 27))


def cubic_seed_coefficients(parameter_g: int | Fraction) -> tuple[Fraction, Fraction, Fraction]:
    g = parameter_g if isinstance(parameter_g, Fraction) else Fraction(parameter_g, 1)
    return (Fraction(2) + g / 2, Fraction(-3) - 3 * g / 2, g)


def cubic_seed_endpoint_audit(parameter_g: int | Fraction) -> dict[str, Fraction]:
    """Return the exact endpoint, integral, and slope conditions for p_g."""

    a, b, g = cubic_seed_coefficients(parameter_g)
    return {
        "p(0)": Fraction(0),
        "p(1)": a + b + g,
        "integral_0_1": a / 2 + b / 3 + g / 4,
        "p_prime(1)": a + 2 * b + 3 * g,
    }


def _trim(poly: Sequence[Fraction | int]) -> tuple[Fraction, ...]:
    values = [value if isinstance(value, Fraction) else Fraction(value, 1) for value in poly]
    while len(values) > 1 and values[-1] == 0:
        values.pop()
    return tuple(values)


def _lcm(left: int, right: int) -> int:
    return abs(left * right) // gcd(left, right) if left and right else 0


def _normalize_integer_polynomial(poly: Sequence[Fraction | int]) -> tuple[int, ...]:
    values = _trim(poly)
    denominator_lcm = 1
    for value in values:
        denominator_lcm = _lcm(denominator_lcm, value.denominator)
    integers = [int(value * denominator_lcm) for value in values]
    content = 0
    for value in integers:
        content = gcd(content, abs(value))
    if content:
        integers = [value // content for value in integers]
    if integers[-1] < 0:
        integers = [-value for value in integers]
    return tuple(integers)


def _integer_divisors(value: int) -> tuple[int, ...]:
    value = abs(value)
    if value == 0:
        return (0,)
    divisors: set[int] = set()
    factor = 1
    while factor * factor <= value:
        if value % factor == 0:
            divisors.add(factor)
            divisors.add(value // factor)
        factor += 1
    return tuple(sorted(divisors))


def _poly_evaluate(poly: Sequence[Fraction | int], value: Fraction) -> Fraction:
    total = Fraction(0)
    for coefficient in reversed(_trim(poly)):
        total = total * value + coefficient
    return total


def _divide_by_linear(poly: Sequence[Fraction | int], root: Fraction) -> tuple[Fraction, ...]:
    values = list(reversed(_trim(poly)))
    synthetic: list[Fraction] = [values[0]]
    for coefficient in values[1:]:
        synthetic.append(coefficient + root * synthetic[-1])
    remainder = synthetic.pop()
    if remainder != 0:
        raise ValueError("root does not divide polynomial")
    return _trim(tuple(reversed(synthetic)))


def _rational_root(poly: Sequence[Fraction | int]) -> Fraction | None:
    normalized = _normalize_integer_polynomial(poly)
    if len(normalized) <= 1:
        return None
    if normalized[0] == 0:
        return Fraction(0)
    numerators = _integer_divisors(normalized[0])
    denominators = _integer_divisors(normalized[-1])
    candidates: set[Fraction] = set()
    for numerator in numerators:
        for denominator in denominators:
            if denominator == 0:
                continue
            candidates.add(Fraction(numerator, denominator))
            candidates.add(Fraction(-numerator, denominator))
    for candidate in sorted(candidates):
        if _poly_evaluate(normalized, candidate) == 0:
            return candidate
    return None


def _factor_over_q(poly: Sequence[Fraction | int]) -> tuple[tuple[int, ...], ...]:
    """Factor a degree-at-most-three polynomial over Q exactly."""

    remaining: tuple[Fraction, ...] = _trim(poly)
    factors: list[tuple[int, ...]] = []
    while len(remaining) > 1:
        root = _rational_root(remaining)
        if root is None:
            factors.append(_normalize_integer_polynomial(remaining))
            break
        factors.append(_normalize_integer_polynomial((-root, Fraction(1))))
        remaining = _divide_by_linear(remaining, root)
    return tuple(factors)


def factor_cancellation_ledger() -> tuple[tuple[tuple[int, ...], int], ...]:
    """Count how many expanded coefficients contain each irreducible factor."""

    ledger: Counter[tuple[int, ...]] = Counter()
    numerators = _CUBIC_F1_NUMERATORS + _CUBIC_F2_NUMERATORS + (_CUBIC_F3_MIDDLE_NUMERATOR,)
    for numerator in numerators:
        for factor in set(_factor_over_q(numerator)):
            ledger[factor] += 1
    return tuple(sorted(ledger.items(), key=lambda item: (-item[1], item[0])))


def cubic_seed_term_count(parameter_g: int | Fraction) -> int:
    """Return the exact expanded term count for a valid normalized cubic seed."""

    g = parameter_g if isinstance(parameter_g, Fraction) else Fraction(parameter_g, 1)
    if g == 0:
        raise ValueError("g=0 drops the seed degree below three")
    if g == 4:
        raise ValueError("g=4 makes the weighted-lift normalization singular")
    f1_terms = sum(_poly_evaluate(poly, g) != 0 for poly in _CUBIC_F1_NUMERATORS)
    f2_terms = sum(_poly_evaluate(poly, g) != 0 for poly in _CUBIC_F2_NUMERATORS)
    f3_terms = 2 if _poly_evaluate(_CUBIC_F3_MIDDLE_NUMERATOR, g) == 0 else 3
    return f1_terms + f2_terms + f3_terms


def exact_cubic_seed_minimum() -> CubicSeedMinimumCertificate:
    """Certify the unique global monomial minimum in the normalized cubic family.

    Every coefficient numerator has degree at most three.  Exact factorization
    shows that the factor g occurs in 17 coefficients but g=0 lowers the seed
    degree; g-6 occurs in eight coefficients; every other irreducible factor
    occurs in one coefficient only.  Hence g=6 is the unique valid parameter
    with eight simultaneous cancellations, reducing 33 generic monomials to 25.
    """

    ledger = factor_cancellation_ledger()
    counts = dict(ledger)
    if counts.get((0, 1)) != 17:
        raise AssertionError("degree-drop factor audit changed")
    if counts.get((-6, 1)) != 8:
        raise AssertionError("g=6 cancellation audit changed")
    if any(
        occurrences > 1
        for factor, occurrences in ledger
        if factor not in {(0, 1), (-6, 1)}
    ):
        raise AssertionError("unexpected shared coefficient factor")
    minimum = cubic_seed_term_count(Fraction(6))
    if minimum != 25:
        raise AssertionError("compact-map term count changed")
    return CubicSeedMinimumCertificate(
        generic_term_count=33,
        minimum_term_count=minimum,
        unique_parameter=Fraction(6),
        degree_drop_parameter=Fraction(0),
        invalid_parameter=Fraction(4),
        cancellation_ledger=ledger,
    )


def bounded_cubic_seed_search(
    *,
    max_numerator: int = 64,
    max_denominator: int = 64,
) -> tuple[Fraction, ...]:
    """Redundant exact bounded search used as a regression control."""

    if max_numerator < 1 or max_denominator < 1:
        raise ValueError("search bounds must be positive")
    values: set[Fraction] = set()
    for denominator in range(1, max_denominator + 1):
        for numerator in range(-max_numerator, max_numerator + 1):
            if gcd(abs(numerator), denominator) != 1:
                continue
            value = Fraction(numerator, denominator)
            if value not in {Fraction(0), Fraction(4)}:
                values.add(value)
    scored = [(cubic_seed_term_count(value), value) for value in values]
    minimum = min(score for score, _ in scored)
    return tuple(value for score, value in sorted(scored) if score == minimum)


def run_aftershock_audit() -> AftershockResult:
    candidate = compact_four_sheet_map()
    determinant = candidate.jacobian_determinant().constant_value
    if determinant is None:
        raise AssertionError("compact map Jacobian is not constant")

    collision = verify_polynomial_counterexample(
        candidate,
        compact_collision_witnesses(),
        expected_determinant=2,
    )
    four_point = verify_polynomial_counterexample(
        candidate,
        compact_four_point_witnesses(),
        expected_determinant=2,
    )
    if not collision.passed or collision.common_image != compact_collision_image():
        raise AssertionError("short collision certificate failed")
    if not four_point.passed or four_point.common_image != compact_four_point_image():
        raise AssertionError("four-point fiber certificate failed")

    return AftershockResult(
        map_digest=candidate.digest(),
        determinant=determinant,
        coordinate_term_counts=tuple(len(poly.terms) for poly in candidate.coordinates),
        coordinate_degrees=tuple(poly.total_degree for poly in candidate.coordinates),
        collision_verification=collision,
        four_point_verification=four_point,
        family_minimum=exact_cubic_seed_minimum(),
    )


def aftershock_json(result: AftershockResult) -> str:
    return canonical_json(result.to_dict())
