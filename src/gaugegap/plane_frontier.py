"""Verification-first audit of the (72,108) plane-Jacobian frontier.

This module transcribes the Newton polygons in GGHV Proposition 4.3 and tests a
specific simultaneous-covector proof route. It supplies an exact rational
certificate excluding parameter degree 1 and independently reproduces the
reported parameter-degree-2 obstruction over two large prime fields.

The degree-2 modular result is evidence, not a proof over Q: reduction modulo a
finite set of primes cannot exclude rational solutions whose denominators vanish
at those primes. Nothing here eliminates the complete (72,108) case or proves
JC(2).
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import itertools
import json
from math import comb
from typing import Mapping, Sequence

import numpy as np

Point = tuple[int, int]
PRIMES = (2_147_483_629, 2_147_483_587)
DEGREE2_SUPPORT: tuple[Point, ...] = ((0, 1), (1, 0), (3, 5))
P_VERTICES: tuple[Point, ...] = ((0, 0), (1, 0), (8, 14), (8, 16), (0, 8))
Q_VERTICES: tuple[Point, ...] = ((0, 0), (2, 1), (12, 21), (12, 24), (0, 12))
DEGREE1_CERTIFICATE: dict[Point, int] = {
    (0, 8): 2_516_085,
    (1, 9): -19_739_720,
    (2, 1): -218_790,
    (2, 10): 67_474_836,
    (3, 11): -130_876_200,
    (4, 12): 156_726_570,
    (5, 13): -117_338_760,
    (6, 14): 52_072_020,
    (7, 15): -11_143_704,
    (9, 17): 308_880,
}
CLAIM_BOUNDARY = (
    "The exact degree-1 certificate closes one polynomial-covector route in the "
    "declared H-restricted system. The degree-2 result is a two-prime modular "
    "reproduction only. These results do not cover every interior coefficient, "
    "eliminate (72,108), raise the global degree bound, or solve JC(2)."
)


def _cross(o: Point, a: Point, b: Point) -> int:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def lattice_points(vertices: Sequence[Point]) -> tuple[Point, ...]:
    points = sorted(set(vertices))
    lower: list[Point] = []
    upper: list[Point] = []
    for point in points:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    for point in reversed(points):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    hull = lower[:-1] + upper[:-1]

    def inside(point: Point) -> bool:
        return all(
            _cross(hull[index], hull[(index + 1) % len(hull)], point) >= 0
            for index in range(len(hull))
        )

    return tuple(
        (x, y)
        for x in range(max(x for x, _ in vertices) + 1)
        for y in range(max(y for _, y in vertices) + 1)
        if inside((x, y))
    )


P_POINTS = lattice_points(P_VERTICES)
Q_POINTS = tuple(sorted(lattice_points(Q_VERTICES)))
FORCED_TOP = frozenset((k, 8 + k) for k in range(9))
LOWER_OPERATORS = tuple(
    sorted(point for point in P_POINTS if point not in FORCED_TOP and point != (0, 0))
)


def _in_pool(point: Point) -> bool:
    return point[0] - point[1] <= 2 and point[0] <= 24 and point[1] <= 44


def _bracket_rows(terms: Mapping[Point, int]) -> dict[Point, dict[int, int]]:
    rows: dict[Point, dict[int, int]] = {}
    for column, (alpha, beta) in enumerate(Q_POINTS):
        for (p, q), coefficient in terms.items():
            factor = p * beta - q * alpha
            output = (p + alpha - 1, q + beta - 1)
            if factor and _in_pool(output):
                row = rows.setdefault(output, {})
                row[column] = row.get(column, 0) + coefficient * factor
    return rows


def _forced_polynomial() -> dict[Point, int]:
    terms = {
        (k, 8 + k): comb(8, k) * (-1) ** (8 - k)
        for k in range(9)
    }
    terms[(1, 0)] = 1
    return terms


def _apply_exact(
    vector: Sequence[Fraction], operator: dict[int, dict[int, int]]
) -> list[Fraction]:
    output = [Fraction(0)] * len(Q_POINTS)
    for row, columns in operator.items():
        value = vector[row]
        if value:
            for column, coefficient in columns.items():
                output[column] += value * coefficient
    return output


@dataclass
class ExactContext:
    row_points: tuple[Point, ...]
    row_index: dict[Point, int]
    rank: int
    pivots: tuple[int, ...]
    transform: list[list[Fraction]]
    kernel: list[list[Fraction]]
    operators: tuple[Point, ...]
    operator_maps: dict[Point, dict[int, dict[int, int]]]
    particulars: dict[Point, list[Fraction]]

    def solve(self, rhs: Sequence[Fraction]) -> list[Fraction] | None:
        values = [
            sum(
                self.transform[index][column] * rhs[column]
                for column in range(len(Q_POINTS))
                if rhs[column]
            )
            for index in range(len(Q_POINTS))
        ]
        if any(values[index] for index in range(self.rank, len(Q_POINTS))):
            return None
        solution = [Fraction(0)] * len(self.row_points)
        for row, pivot in enumerate(self.pivots):
            solution[pivot] = values[row]
        return solution


def build_exact_context() -> ExactContext:
    base_rows = _bracket_rows(_forced_polynomial())
    row_points = tuple(sorted(set(base_rows) | {(2, 0)}))
    row_index = {point: index for index, point in enumerate(row_points)}
    column_count = len(row_points)
    matrix = [[Fraction(0)] * column_count for _ in Q_POINTS]
    for point, entries in base_rows.items():
        for column, value in entries.items():
            matrix[column][row_index[point]] = Fraction(value)

    work = [
        matrix[index]
        + [Fraction(index == identity) for identity in range(len(Q_POINTS))]
        for index in range(len(Q_POINTS))
    ]
    pivots: list[int] = []
    rank = 0
    for column in range(column_count):
        selected = next(
            (
                row
                for row in range(rank, len(Q_POINTS))
                if work[row][column]
            ),
            None,
        )
        if selected is None:
            continue
        work[rank], work[selected] = work[selected], work[rank]
        inverse = 1 / work[rank][column]
        work[rank] = [value * inverse for value in work[rank]]
        for row in range(len(Q_POINTS)):
            if row != rank and work[row][column]:
                factor = work[row][column]
                work[row] = [
                    left - factor * right
                    for left, right in zip(work[row], work[rank])
                ]
        pivots.append(column)
        rank += 1
        if rank == len(Q_POINTS):
            break

    transform = [row[column_count:] for row in work]
    reduced = [row[:column_count] for row in work[:rank]]
    pivot_set = set(pivots)
    kernel: list[list[Fraction]] = []
    for free in (
        column for column in range(column_count) if column not in pivot_set
    ):
        vector = [Fraction(0)] * column_count
        vector[free] = 1
        for row, pivot in enumerate(pivots):
            vector[pivot] = -reduced[row][free]
        kernel.append(vector)

    operator_maps: dict[Point, dict[int, dict[int, int]]] = {}
    for operator in LOWER_OPERATORS:
        sparse = _bracket_rows({operator: 1})
        kept = {
            row_index[point]: entries
            for point, entries in sparse.items()
            if point in row_index
        }
        if kept:
            operator_maps[operator] = kept
    operators = tuple(sorted(operator_maps))

    lambda_zero = [Fraction(0)] * column_count
    for point, value in (
        ((2, 0), 576),
        ((9, 16), 24),
        ((16, 32), 51),
        ((17, 33), 612),
        ((18, 34), 4148),
    ):
        if point in row_index:
            lambda_zero[row_index[point]] = Fraction(value)

    context = ExactContext(
        row_points,
        row_index,
        rank,
        tuple(pivots),
        transform,
        kernel,
        operators,
        operator_maps,
        {},
    )
    for operator in operators:
        rhs = [
            -value
            for value in _apply_exact(lambda_zero, operator_maps[operator])
        ]
        solution = context.solve(rhs)
        if solution is None:
            raise ArithmeticError(f"first-order solve failed for {operator}")
        context.particulars[operator] = solution
    return context


@dataclass(frozen=True)
class ExactCertificate:
    operator: Point
    nonzero_rows: int
    annihilates_kernel_image: bool
    rhs_pairing: int
    verified: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "operator": list(self.operator),
            "nonzero_rows": self.nonzero_rows,
            "annihilates_kernel_image": self.annihilates_kernel_image,
            "rhs_pairing": self.rhs_pairing,
            "verified": self.verified,
            "certificate": {
                f"{x},{y}": value
                for (x, y), value in sorted(DEGREE1_CERTIFICATE.items())
            },
        }


def verify_degree1_certificate(context: ExactContext) -> ExactCertificate:
    operator = (1, 0)
    operator_map = context.operator_maps[operator]
    weights = [
        Fraction(DEGREE1_CERTIFICATE.get(point, 0))
        for point in Q_POINTS
    ]
    annihilates = True
    for kernel_vector in context.kernel:
        image = _apply_exact(kernel_vector, operator_map)
        if sum(
            weight * value for weight, value in zip(weights, image)
        ):
            annihilates = False
            break
    rhs = [
        -value
        for value in _apply_exact(context.particulars[operator], operator_map)
    ]
    pairing = sum(weight * value for weight, value in zip(weights, rhs))
    if pairing.denominator != 1:
        raise ArithmeticError("degree-1 certificate pairing is not integral")
    return ExactCertificate(
        operator,
        len(DEGREE1_CERTIFICATE),
        annihilates,
        pairing.numerator,
        annihilates and pairing != 0,
    )


def _mod_fraction(value: Fraction, prime: int) -> int:
    return (
        (value.numerator % prime)
        * pow(value.denominator % prime, prime - 2, prime)
        % prime
    )


def _matmul_mod(
    left: np.ndarray, right: np.ndarray, prime: int
) -> np.ndarray:
    high, low = right >> 16, right & 0xFFFF
    return (((left @ high) % prime) * 65536 + left @ low) % prime


@dataclass
class ModularContext:
    prime: int
    exact: ExactContext
    transform: np.ndarray
    kernel: np.ndarray
    matrices: dict[Point, np.ndarray]
    particulars: dict[Point, np.ndarray]

    @property
    def kernel_dimension(self) -> int:
        return self.kernel.shape[0]

    def solve_many(self, rhs: np.ndarray) -> np.ndarray:
        values = _matmul_mod(
            self.transform, rhs % self.prime, self.prime
        )
        solution = np.zeros(
            (len(self.exact.row_points), rhs.shape[1]), dtype=np.int64
        )
        solution[
            np.asarray(self.exact.pivots, dtype=np.int64)
        ] = values[: self.exact.rank]
        return solution

    def apply(self, operator: Point, vector: np.ndarray) -> np.ndarray:
        return self.matrices[operator] @ vector % self.prime


def build_modular_context(
    exact: ExactContext, prime: int
) -> ModularContext:
    transform = np.asarray(
        [
            [_mod_fraction(value, prime) for value in row]
            for row in exact.transform
        ],
        dtype=np.int64,
    )
    kernel = np.asarray(
        [
            [_mod_fraction(value, prime) for value in row]
            for row in exact.kernel
        ],
        dtype=np.int64,
    )
    matrices: dict[Point, np.ndarray] = {}
    for operator, sparse in exact.operator_maps.items():
        matrix = np.zeros(
            (len(Q_POINTS), len(exact.row_points)), dtype=np.int64
        )
        for row, entries in sparse.items():
            for column, value in entries.items():
                matrix[column, row] = value % prime
        matrices[operator] = matrix
    particulars = {
        operator: np.asarray(
            [_mod_fraction(value, prime) for value in vector],
            dtype=np.int64,
        )
        for operator, vector in exact.particulars.items()
    }
    return ModularContext(
        prime, exact, transform, kernel, matrices, particulars
    )


def _decompositions(
    multiset: tuple[Point, ...],
) -> tuple[tuple[Point, tuple[Point, ...]], ...]:
    output: list[tuple[Point, tuple[Point, ...]]] = []
    for element in sorted(set(multiset)):
        rest = list(multiset)
        rest.remove(element)
        output.append((element, tuple(sorted(rest))))
    return tuple(output)


def _feasible_mod(matrix: np.ndarray, prime: int) -> tuple[bool, int]:
    work = matrix % prime
    rows, augmented = work.shape
    columns = augmented - 1
    rank = 0
    for column in range(columns):
        if rank == rows:
            break
        candidates = np.nonzero(work[rank:, column])[0]
        if candidates.size == 0:
            continue
        selected = rank + int(candidates[0])
        if selected != rank:
            work[[rank, selected]] = work[[selected, rank]]
        work[rank] = (
            work[rank]
            * pow(int(work[rank, column]), prime - 2, prime)
            % prime
        )
        below = np.nonzero(work[rank + 1 :, column])[0]
        if below.size:
            indices = below + rank + 1
            work[indices] = (
                work[indices]
                - work[indices, column][:, None]
                * work[rank][None, :]
            ) % prime
        rank += 1
    if rank < rows:
        tail = work[rank:]
        inconsistent = np.any(
            (tail[:, :columns].any(axis=1) == 0)
            & (tail[:, columns] != 0)
        )
        return not bool(inconsistent), rank
    return True, rank


@dataclass(frozen=True)
class ModularEvidence:
    prime: int
    support: tuple[Point, ...]
    rows: int
    columns: int
    rank: int
    infeasible: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "prime": self.prime,
            "support": [list(point) for point in self.support],
            "rows": self.rows,
            "columns": self.columns,
            "rank": self.rank,
            "infeasible": self.infeasible,
            "proof_status": "FINITE_FIELD_EVIDENCE_NOT_Q_CERTIFICATE",
        }


def degree2_modular_evidence(
    context: ModularContext,
    support: Sequence[Point] = DEGREE2_SUPPORT,
) -> ModularEvidence:
    selected = tuple(sorted(set(support)))
    prime = context.prime
    dimension = context.kernel_dimension
    first_cache: dict[Point, np.ndarray] = {}
    pair_cache: dict[tuple[Point, Point], np.ndarray] = {}

    def first(operator: Point) -> np.ndarray:
        if operator not in first_cache:
            image = _matmul_mod(
                context.matrices[operator], context.kernel.T, prime
            )
            first_cache[operator] = context.solve_many(-image % prime)
        return first_cache[operator]

    def pair(pair_key: tuple[Point, Point]) -> np.ndarray:
        if pair_key not in pair_cache:
            left, right = pair_key
            if left == right:
                source = context.apply(left, context.particulars[left])
            else:
                source = (
                    context.apply(right, context.particulars[left])
                    + context.apply(left, context.particulars[right])
                ) % prime
            pair_cache[pair_key] = context.solve_many(
                -source[:, None] % prime
            )[:, 0]
        return pair_cache[pair_key]

    keys = [("u", point) for point in selected] + [
        ("v", pair_key)
        for pair_key in itertools.combinations_with_replacement(selected, 2)
    ]
    offsets = {
        key: index * dimension for index, key in enumerate(keys)
    }
    width = len(keys) * dimension
    blocks: list[np.ndarray] = []

    for gamma in itertools.combinations_with_replacement(selected, 3):
        matrix = np.zeros(
            (len(Q_POINTS), width + 1), dtype=np.int64
        )
        rhs = np.zeros(len(Q_POINTS), dtype=np.int64)
        for operator, pair_key in _decompositions(gamma):
            rhs = (
                rhs - context.apply(operator, pair(pair_key))
            ) % prime
            kernel_image = _matmul_mod(
                context.matrices[operator], context.kernel.T, prime
            )
            start = offsets[("v", pair_key)]
            matrix[:, start : start + dimension] = (
                matrix[:, start : start + dimension] + kernel_image
            ) % prime
            for left, right in (
                (pair_key[0], pair_key[1]),
                (pair_key[1], pair_key[0]),
            ):
                correction = (
                    context.matrices[operator] @ first(right)
                ) % prime
                start = offsets[("u", left)]
                matrix[:, start : start + dimension] = (
                    matrix[:, start : start + dimension] + correction
                ) % prime
                if pair_key[0] == pair_key[1]:
                    break
        matrix[:, width] = rhs
        blocks.append(matrix)

    augmented = np.vstack(blocks)
    feasible, rank = _feasible_mod(augmented, prime)
    return ModularEvidence(
        prime,
        selected,
        augmented.shape[0],
        augmented.shape[1],
        rank,
        not feasible,
    )


@dataclass(frozen=True)
class PlaneFrontierAudit:
    p_points: int
    q_points: int
    operators: int
    base_rank: int
    kernel_dimension: int
    degree1: ExactCertificate
    degree2: tuple[ModularEvidence, ...]
    claim_boundary: str = CLAIM_BOUNDARY

    @property
    def passed(self) -> bool:
        return (
            (
                self.p_points,
                self.q_points,
                self.operators,
                self.base_rank,
                self.kernel_dimension,
            )
            == (61, 125, 51, 124, 165)
            and self.degree1.verified
            and all(item.infeasible for item in self.degree2)
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": "gaugegap.plane_frontier_audit.v1",
            "evidence_label": "INDEPENDENT_REPRODUCTION",
            "source": (
                "GGHV Proposition 4.3 reduced (8,28) / (72,108) frontier"
            ),
            "p_vertices": [list(point) for point in P_VERTICES],
            "q_vertices": [list(point) for point in Q_VERTICES],
            "p_lattice_points": self.p_points,
            "q_lattice_points": self.q_points,
            "lower_operators": self.operators,
            "base_rank": self.base_rank,
            "base_kernel_dimension": self.kernel_dimension,
            "degree1_exact_certificate": self.degree1.to_dict(),
            "degree2_modular_evidence": [
                item.to_dict() for item in self.degree2
            ],
            "passed": self.passed,
            "claim_boundary": self.claim_boundary,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        )
        payload["audit_digest"] = hashlib.sha256(
            canonical.encode()
        ).hexdigest()
        return payload


def run_plane_frontier_audit() -> PlaneFrontierAudit:
    exact = build_exact_context()
    degree1 = verify_degree1_certificate(exact)
    degree2 = tuple(
        degree2_modular_evidence(build_modular_context(exact, prime))
        for prime in PRIMES
    )
    return PlaneFrontierAudit(
        len(P_POINTS),
        len(Q_POINTS),
        len(LOWER_OPERATORS),
        exact.rank,
        len(exact.kernel),
        degree1,
        degree2,
    )


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"
