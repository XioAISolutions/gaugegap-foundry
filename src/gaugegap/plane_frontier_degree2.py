"""Exact parameter-degree-2 certificate for the (72,108) frontier route."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
import hashlib
import itertools
import json
from math import gcd, lcm
from typing import Mapping, Sequence

from .plane_frontier import (
    DEGREE2_SUPPORT,
    PRIMES,
    Q_POINTS,
    ExactContext,
    Point,
    _apply_exact,
    _decompositions,
    build_exact_context,
)

DEGREE2_BOUNDARY = (
    "This exact left-null certificate proves that no parameter-degree-2 "
    "polynomial covector satisfies the declared H-restricted subsystem on "
    "support {(0,1),(1,0),(3,5)}. It does not exclude higher-degree, rational, "
    "or chartwise certificates; cover all simultaneous interior coefficients; "
    "eliminate (72,108); raise the global degree bound; or solve JC(2)."
)

RowRecord = tuple[dict[int, Fraction], Fraction, tuple[Point, ...], Point]


def _apply_columns(
    context: ExactContext,
    operator: Point,
    vectors: Sequence[Sequence[Fraction]],
) -> list[list[Fraction]]:
    return [
        _apply_exact(vector, context.operator_maps[operator])
        for vector in vectors
    ]


def build_degree2_rows(
    context: ExactContext,
    support: Sequence[Point] = DEGREE2_SUPPORT,
) -> tuple[tuple[Point, ...], int, list[RowRecord]]:
    selected = tuple(sorted(set(support)))
    dimension = len(context.kernel)
    first_cache: dict[Point, list[list[Fraction]]] = {}
    pair_cache: dict[tuple[Point, Point], list[Fraction]] = {}

    def first(operator: Point) -> list[list[Fraction]]:
        if operator not in first_cache:
            columns = []
            for image in _apply_columns(context, operator, context.kernel):
                solution = context.solve([-value for value in image])
                if solution is None:
                    raise ArithmeticError(
                        f"degree-2 first correction failed for {operator}"
                    )
                columns.append(solution)
            first_cache[operator] = columns
        return first_cache[operator]

    def pair(pair_key: tuple[Point, Point]) -> list[Fraction]:
        if pair_key not in pair_cache:
            left, right = pair_key
            if left == right:
                source = _apply_exact(
                    context.particulars[left], context.operator_maps[left]
                )
            else:
                first_source = _apply_exact(
                    context.particulars[left], context.operator_maps[right]
                )
                second_source = _apply_exact(
                    context.particulars[right], context.operator_maps[left]
                )
                source = [
                    first_value + second_value
                    for first_value, second_value in zip(
                        first_source, second_source
                    )
                ]
            solution = context.solve([-value for value in source])
            if solution is None:
                raise ArithmeticError(
                    f"degree-2 pair correction failed for {pair_key}"
                )
            pair_cache[pair_key] = solution
        return pair_cache[pair_key]

    keys = [("u", point) for point in selected] + [
        ("v", pair_key)
        for pair_key in itertools.combinations_with_replacement(selected, 2)
    ]
    offsets = {
        key: index * dimension for index, key in enumerate(keys)
    }
    width = len(keys) * dimension
    rows: list[RowRecord] = []

    for gamma in itertools.combinations_with_replacement(selected, 3):
        right_side = [Fraction(0)] * len(Q_POINTS)
        row_maps: list[dict[int, Fraction]] = [
            {} for _ in Q_POINTS
        ]
        for operator, pair_key in _decompositions(gamma):
            pair_image = _apply_exact(
                pair(pair_key), context.operator_maps[operator]
            )
            right_side = [
                current - value
                for current, value in zip(right_side, pair_image)
            ]

            start = offsets[("v", pair_key)]
            for basis, column in enumerate(
                _apply_columns(context, operator, context.kernel)
            ):
                for row, value in enumerate(column):
                    if value:
                        row_maps[row][start + basis] = (
                            row_maps[row].get(start + basis, Fraction(0))
                            + value
                        )

            for left, right in (
                (pair_key[0], pair_key[1]),
                (pair_key[1], pair_key[0]),
            ):
                start = offsets[("u", left)]
                for basis, column in enumerate(
                    _apply_columns(context, operator, first(right))
                ):
                    for row, value in enumerate(column):
                        if value:
                            row_maps[row][start + basis] = (
                                row_maps[row].get(
                                    start + basis, Fraction(0)
                                )
                                + value
                            )
                if pair_key[0] == pair_key[1]:
                    break

        rows.extend(
            (row_maps[index], right_side[index], gamma, Q_POINTS[index])
            for index in range(len(Q_POINTS))
        )
    return selected, width, rows


def _mod_fraction(value: Fraction, prime: int) -> int:
    return (
        value.numerator
        * pow(value.denominator % prime, prime - 2, prime)
        % prime
    )


def select_contradictory_rows(
    rows: Sequence[RowRecord], prime: int = PRIMES[0]
) -> tuple[tuple[int, ...], int]:
    reduced: dict[int, tuple[dict[int, int], int, int]] = {}
    pivots: list[int] = []
    for index, (coefficients, right_side, _, _) in enumerate(rows):
        active = {
            column: _mod_fraction(value, prime)
            for column, value in coefficients.items()
            if _mod_fraction(value, prime)
        }
        rhs = _mod_fraction(right_side, prime)
        while active:
            pivot = min(active)
            if pivot in reduced:
                existing, existing_rhs, _ = reduced[pivot]
                factor = active[pivot]
                for column, value in existing.items():
                    updated = (
                        active.get(column, 0) - factor * value
                    ) % prime
                    if updated:
                        active[column] = updated
                    else:
                        active.pop(column, None)
                rhs = (rhs - factor * existing_rhs) % prime
                continue
            inverse = pow(active[pivot], prime - 2, prime)
            normalized = {
                column: value * inverse % prime
                for column, value in active.items()
            }
            reduced[pivot] = (
                normalized,
                rhs * inverse % prime,
                index,
            )
            pivots.append(index)
            break
        else:
            if rhs:
                return tuple(pivots + [index]), len(reduced)
    raise ArithmeticError("no modular contradiction found")


@dataclass(frozen=True)
class CertificateRow:
    gamma: tuple[Point, ...]
    q_point: Point
    coefficient: int
    original_row_id: int

    def to_dict(self) -> dict[str, object]:
        return {
            "gamma": [list(point) for point in self.gamma],
            "q_point": list(self.q_point),
            "coefficient": self.coefficient,
            "original_row_id": self.original_row_id,
        }


@dataclass(frozen=True)
class ExactDegree2Certificate:
    support: tuple[Point, ...]
    total_equations: int
    total_unknowns: int
    selected_rows: int
    active_columns: int
    exact_rank_before_contradiction: int
    certificate_rows: tuple[CertificateRow, ...]
    rhs_pairing: int
    verified: bool
    claim_boundary: str = DEGREE2_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": "gaugegap.plane_frontier_degree2_exact.v1",
            "evidence_label": "DERIVED_EXACT",
            "novelty_status": "UNESTABLISHED",
            "support": [list(point) for point in self.support],
            "total_equations": self.total_equations,
            "total_unknowns": self.total_unknowns,
            "selected_rows": self.selected_rows,
            "active_columns": self.active_columns,
            "exact_rank_before_contradiction": (
                self.exact_rank_before_contradiction
            ),
            "certificate_nonzero_rows": len(self.certificate_rows),
            "certificate_rows": [
                row.to_dict() for row in self.certificate_rows
            ],
            "rhs_pairing": self.rhs_pairing,
            "verified": self.verified,
            "claim_boundary": self.claim_boundary,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        )
        payload["certificate_digest"] = hashlib.sha256(
            canonical.encode()
        ).hexdigest()
        return payload


def derive_degree2_exact_certificate(
    context: ExactContext | None = None,
    support: Sequence[Point] = DEGREE2_SUPPORT,
) -> ExactDegree2Certificate:
    exact = context or build_exact_context()
    selected, width, rows = build_degree2_rows(exact, support)
    selected_ids, modular_rank = select_contradictory_rows(rows)

    reduced: dict[
        int,
        tuple[
            dict[int, Fraction],
            Fraction,
            dict[int, Fraction],
        ],
    ] = {}
    contradiction: tuple[
        Fraction, dict[int, Fraction]
    ] | None = None

    for position, row_id in enumerate(selected_ids):
        coefficients = dict(rows[row_id][0])
        right_side = rows[row_id][1]
        provenance = {position: Fraction(1)}
        while coefficients:
            pivot = min(coefficients)
            if pivot in reduced:
                existing, existing_rhs, existing_provenance = reduced[pivot]
                factor = coefficients[pivot]
                for column, value in existing.items():
                    updated = (
                        coefficients.get(column, Fraction(0))
                        - factor * value
                    )
                    if updated:
                        coefficients[column] = updated
                    else:
                        coefficients.pop(column, None)
                right_side -= factor * existing_rhs
                for key, value in existing_provenance.items():
                    updated = (
                        provenance.get(key, Fraction(0))
                        - factor * value
                    )
                    if updated:
                        provenance[key] = updated
                    else:
                        provenance.pop(key, None)
                continue
            inverse = 1 / coefficients[pivot]
            reduced[pivot] = (
                {
                    column: value * inverse
                    for column, value in coefficients.items()
                },
                right_side * inverse,
                {
                    key: value * inverse
                    for key, value in provenance.items()
                },
            )
            break
        else:
            if right_side:
                contradiction = (right_side, provenance)
                break

    if contradiction is None:
        raise ArithmeticError(
            "modular row selection did not lift to an exact contradiction"
        )
    _, provenance = contradiction
    denominator = 1
    for value in provenance.values():
        denominator = lcm(denominator, value.denominator)
    integer_weights = {
        key: int(value * denominator)
        for key, value in provenance.items()
    }
    divisor = reduce(
        gcd,
        (abs(value) for value in integer_weights.values() if value),
        0,
    )
    if divisor > 1:
        integer_weights = {
            key: value // divisor
            for key, value in integer_weights.items()
        }

    residual: dict[int, Fraction] = {}
    rhs_pairing = Fraction(0)
    certificate_rows: list[CertificateRow] = []
    for selected_position, coefficient in integer_weights.items():
        row_id = selected_ids[selected_position]
        row, rhs, gamma, q_point = rows[row_id]
        rhs_pairing += coefficient * rhs
        for column, value in row.items():
            updated = (
                residual.get(column, Fraction(0))
                + coefficient * value
            )
            if updated:
                residual[column] = updated
            else:
                residual.pop(column, None)
        certificate_rows.append(
            CertificateRow(gamma, q_point, coefficient, row_id)
        )

    if rhs_pairing.denominator != 1:
        raise ArithmeticError("degree-2 certificate pairing is not integral")
    verified = not residual and rhs_pairing != 0
    active_columns = len(
        {
            column
            for row_id in selected_ids
            for column in rows[row_id][0]
        }
    )
    if len(reduced) != modular_rank:
        raise ArithmeticError(
            "exact and modular selected-subsystem ranks disagree"
        )
    return ExactDegree2Certificate(
        support=selected,
        total_equations=len(rows),
        total_unknowns=width,
        selected_rows=len(selected_ids),
        active_columns=active_columns,
        exact_rank_before_contradiction=len(reduced),
        certificate_rows=tuple(certificate_rows),
        rhs_pairing=rhs_pairing.numerator,
        verified=verified,
    )


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"
