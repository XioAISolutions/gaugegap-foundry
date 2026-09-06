"""Exact mirror of the Lean Hadamard Gram statements.

Restates every node of the ``hadamard-gram`` track of ``formal/lean/dag.json``
over Python integers and checks it *exhaustively* over all pairs of ±1 vectors
up to ``MAX_LENGTH``. Unlike the sampled mirrors for the other tracks, this one
is a complete check of the statement on a finite slice of its domain -- which is
still not a proof of the universally quantified Lean statement; ``lake build``
is what supplies that.

CLAIM BOUNDARY: statements about a single pair of finite ±1 vectors of equal
length. Not the Hadamard conjecture, and not the ``4 | n`` condition.
"""
from __future__ import annotations

from itertools import product
from typing import Callable, Iterator

#: Vectors up to this length are enumerated exhaustively.
MAX_LENGTH = 6

Vector = tuple[int, ...]


def signs(length: int) -> Iterator[Vector]:
    return product((1, -1), repeat=length)


def equal_length_pairs(max_length: int = MAX_LENGTH) -> Iterator[tuple[Vector, Vector]]:
    for length in range(max_length + 1):
        for u in signs(length):
            for v in signs(length):
                yield u, v


def disagree(a: int, b: int) -> int:
    return 0 if a == b else 1


def inner(u: Vector, v: Vector) -> int:
    return sum(a * b for a, b in zip(u, v))


def mismatches(u: Vector, v: Vector) -> int:
    return sum(disagree(a, b) for a, b in zip(u, v))


def c01() -> bool:
    return all(0 <= disagree(a, b) <= 1 for a in (1, -1) for b in (1, -1))


def c02() -> bool:
    return all(a * b == 1 - 2 * disagree(a, b) for a in (1, -1) for b in (1, -1))


def c03() -> bool:
    return all(mismatches(u, v) >= 0 for u, v in equal_length_pairs())


def c04() -> bool:
    return all(
        inner(u, v) == len(u) - 2 * mismatches(u, v) for u, v in equal_length_pairs()
    )


def c05() -> bool:
    return all(
        mismatches(u, u) == 0
        for length in range(MAX_LENGTH + 1)
        for u in signs(length)
    )


def c06() -> bool:
    return all(
        inner(u, u) == len(u)
        for length in range(MAX_LENGTH + 1)
        for u in signs(length)
    )


def _orthogonal_pairs() -> Iterator[tuple[Vector, Vector]]:
    for u, v in equal_length_pairs():
        if inner(u, v) == 0:
            yield u, v


def c07() -> bool:
    return all(len(u) == 2 * mismatches(u, v) for u, v in _orthogonal_pairs())


def c08() -> bool:
    return all(len(u) % 2 == 0 for u, v in _orthogonal_pairs())


def orthogonal_pair_count() -> int:
    """Non-vacuity witness: C07 and C08 quantify over a non-empty set."""
    return sum(1 for _ in _orthogonal_pairs())


NODE_CHECKS: dict[str, Callable[[], bool]] = {
    "C01": c01,
    "C02": c02,
    "C03": c03,
    "C04": c04,
    "C05": c05,
    "C06": c06,
    "C07": c07,
    "C08": c08,
}
