"""Exact rational mirror of the Lean InfoGap no-hiding statements.

Restates every node of the ``infogap-no-hiding`` track of
``formal/lean/dag.json`` over ``fractions.Fraction`` and checks it exactly on a
finite sample of normalised inputs. Like the Anomaly Forge mirror, this catches
a wrong statement; the kernel check is ``lake build``.

The Hadamard amplitude ``h`` is irrational, but it appears in every statement
only through ``h ** 2``, so the mirror carries ``H_SQUARED = 1/2`` exactly and
never needs ``h`` itself. That is faithful precisely because no statement
mentions ``h`` outside a square.

CLAIM BOUNDARY: exact algebraic probability identities for the implemented
three-qubit circuit; not a formalisation of the general no-hiding theorem.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Callable

Q = Fraction

#: ``h ** 2`` for the Hadamard amplitude, the only way ``h`` enters.
H_SQUARED = Q(1, 2)

#: Exactly normalised rational inputs ``(ar, ai, br, bi)``.
INPUTS: tuple[tuple[Q, Q, Q, Q], ...] = (
    (Q(1), Q(0), Q(0), Q(0)),
    (Q(0), Q(1), Q(0), Q(0)),
    (Q(0), Q(0), Q(1), Q(0)),
    (Q(3, 5), Q(4, 5), Q(0), Q(0)),
    (Q(0), Q(3, 5), Q(0), Q(4, 5)),
    (Q(1, 2), Q(1, 2), Q(1, 2), Q(1, 2)),
    (Q(2, 3), Q(1, 3), Q(2, 3), Q(0)),
    (Q(0), Q(0), Q(5, 13), Q(12, 13)),
    (Q(12, 13), Q(0), Q(0), Q(5, 13)),
)


def pair_probability(x: Q, y: Q) -> Q:
    return x**2 + y**2


def input_norm(ar: Q, ai: Q, br: Q, bi: Q) -> Q:
    return ar**2 + ai**2 + br**2 + bi**2


def branch_weight(h_squared: Q, ar: Q, ai: Q, br: Q, bi: Q) -> Q:
    """``(h*ar)^2 + (h*ai)^2 + (h*br)^2 + (h*bi)^2``, with ``h`` squared out."""
    return h_squared * (ar**2 + ai**2 + br**2 + bi**2)


def recovered_pair(h_squared: Q, x: Q, y: Q) -> Q:
    return 2 * (h_squared * (x**2 + y**2))


def _normalised() -> tuple[tuple[Q, Q, Q, Q], ...]:
    return tuple(item for item in INPUTS if input_norm(*item) == 1)


def b01() -> bool:
    return all(
        pair_probability(ar, ai) + pair_probability(br, bi) == 1
        for ar, ai, br, bi in _normalised()
    )


def b02() -> bool:
    return all(
        branch_weight(H_SQUARED, *item) == Q(1, 2) for item in _normalised()
    )


def b03() -> bool:
    return all(
        branch_weight(H_SQUARED, *item) + branch_weight(H_SQUARED, *item) == 1
        for item in _normalised()
    )


def b04() -> bool:
    return all(
        recovered_pair(H_SQUARED, ar, ai) == pair_probability(ar, ai)
        for ar, ai, _, _ in _normalised()
    )


def b05() -> bool:
    return all(
        recovered_pair(H_SQUARED, br, bi) == pair_probability(br, bi)
        for _, _, br, bi in _normalised()
    )


def b06() -> bool:
    return all(
        recovered_pair(H_SQUARED, ar, ai) + recovered_pair(H_SQUARED, br, bi) == 1
        for ar, ai, br, bi in _normalised()
    )


def b07() -> bool:
    """The measured system statistics do not depend on the input at all."""
    weights = {branch_weight(H_SQUARED, *item) for item in _normalised()}
    return weights == {Q(1, 2)}


NODE_CHECKS: dict[str, Callable[[], bool]] = {
    "B01": b01,
    "B02": b02,
    "B03": b03,
    "B04": b04,
    "B05": b05,
    "B06": b06,
    "B07": b07,
}
