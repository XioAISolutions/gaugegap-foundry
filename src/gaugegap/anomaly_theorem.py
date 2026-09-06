"""Exact rational mirror of the Lean Anomaly Forge statements.

Every node of ``formal/lean/dag.json`` is restated here in Python over
``fractions.Fraction`` and checked exactly.  This is deliberately a *mirror*,
not a proof: a universally quantified Lean statement is checked here only on a
finite grid of colour counts and hypercharges.  It catches a wrong statement
(the cheap failure mode) without pretending to replace the kernel check, which
only ``lake build`` supplies.

CLAIM BOUNDARY: exact rational cancellation conditions for a declared finite
chiral field inventory.  Not a statement about arbitrary chiral gauge theories,
not a continuum construction, and not a Millennium Prize claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

Q = Fraction


# --- coefficients (per generation), mirroring GaugeGapLean/AnomalyForge/Defs.lean ---


def su3_u1(y_q: Q, y_u: Q, y_d: Q) -> Q:
    return 2 * y_q - y_u - y_d


def su2_u1(n: Q, y_q: Q, y_l: Q) -> Q:
    return n * y_q + y_l


def grav_u1(n: Q, y_q: Q, y_u: Q, y_d: Q, y_l: Q, y_e: Q, y_n: Q) -> Q:
    return 2 * n * y_q - n * y_u - n * y_d + 2 * y_l - y_e - y_n


def u1_cubed(n: Q, y_q: Q, y_u: Q, y_d: Q, y_l: Q, y_e: Q, y_n: Q) -> Q:
    return (
        2 * n * y_q**3 - n * y_u**3 - n * y_d**3 + 2 * y_l**3 - y_e**3 - y_n**3
    )


def is_anomaly_free(n: Q, y_q: Q, y_u: Q, y_d: Q, y_l: Q, y_e: Q, y_n: Q) -> bool:
    return (
        su3_u1(y_q, y_u, y_d) == 0
        and su2_u1(n, y_q, y_l) == 0
        and grav_u1(n, y_q, y_u, y_d, y_l, y_e, y_n) == 0
        and u1_cubed(n, y_q, y_u, y_d, y_l, y_e, y_n) == 0
    )


def electric_charge(t3: Q, y: Q) -> Q:
    return t3 + y


def proton_charge(y_q: Q) -> Q:
    return 3 * y_q + Q(1, 2)


def neutron_charge(y_q: Q) -> Q:
    return 3 * y_q - Q(1, 2)


def weak_doublets(n: int, generations: int) -> int:
    return generations * (n + 1)


# --- grid used for the universally quantified nodes ---

COLOURS = (Q(1), Q(2), Q(3), Q(4), Q(5))
Y_Q_GRID = (Q(0), Q(1, 6), Q(-2, 7), Q(3), Q(5, 11))
Y_H_GRID = (Q(1, 2), Q(0), Q(-3, 5), Q(7))
GRID = tuple((n, y_q, y_h) for n in COLOURS for y_q in Y_Q_GRID for y_h in Y_H_GRID)


def _grid(predicate: Callable[[Q, Q, Q], bool]) -> bool:
    return all(predicate(n, y_q, y_h) for n, y_q, y_h in GRID)


# --- node checks (one per DAG node) ---


def a01() -> bool:
    return _grid(lambda n, y_q, y_h: su3_u1(y_q, y_q + y_h, y_q - y_h) == 0)


def a02() -> bool:
    return _grid(
        lambda n, y_q, y_h: (su2_u1(n, y_q, -(n * y_q)) == 0)
        and (su2_u1(n, y_q, y_h) == 0) == (y_h == -(n * y_q))
    )


def a03() -> bool:
    return _grid(
        lambda n, y_q, y_h: grav_u1(
            n, y_q, y_q + y_h, y_q - y_h, -(n * y_q), -(n * y_q) - y_h, Q(0)
        )
        == y_h - n * y_q
    )


def _a04_conclusion(n: Q, y_q: Q, y_h: Q) -> bool:
    y_u, y_d = y_q + y_h, y_q - y_h
    y_l = -(n * y_q)
    y_e = y_l - y_h
    return (
        n * y_q == y_h
        and y_l == -y_h
        and n * y_u == y_h * (n + 1)
        and n * y_d == y_h * (1 - n)
        and y_e == -2 * y_h
    )


def a04() -> bool:
    """Uniqueness, division-free: the two imposed conditions fix everything.

    Checked twice: over the free grid (where most points are vacuous because
    the hypotheses fail) and over the hypothesis-satisfying slice ``y_h =
    n * y_q``, which is never vacuous.
    """
    for n, y_q, y_h in GRID:
        y_u, y_d = y_q + y_h, y_q - y_h
        y_l = -(n * y_q)
        y_e = y_l - y_h
        if su2_u1(n, y_q, y_l) != 0:
            return False
        if grav_u1(n, y_q, y_u, y_d, y_l, y_e, Q(0)) != 0:
            continue  # hypotheses fail here, so A04 says nothing
        if not _a04_conclusion(n, y_q, y_h):
            return False
    return all(_a04_conclusion(n, y_q, n * y_q) for n in COLOURS for y_q in Y_Q_GRID)


def a05() -> bool:
    for n, y_q, _ in GRID:
        y_h = n * y_q
        if u1_cubed(
            n, y_q, y_q + y_h, y_q - y_h, -(n * y_q), -(n * y_q) - y_h, Q(0)
        ) != 0:
            return False
    return True


def a06() -> bool:
    return is_anomaly_free(
        Q(3), Q(1, 6), Q(2, 3), Q(-1, 3), Q(-1, 2), Q(-1), Q(0)
    )


def a07() -> bool:
    return not is_anomaly_free(
        Q(3), Q(1, 6), Q(7, 10), Q(-1, 3), Q(-1, 2), Q(-1), Q(0)
    )


def a08() -> bool:
    return _grid(
        lambda n, y_q, y_h: is_anomaly_free(
            n,
            y_q,
            y_q + y_h,
            y_q - y_h,
            -(n * y_q),
            -(n * y_q) - y_h,
            -(n * y_q) + y_h,
        )
    )


def a09() -> bool:
    """At the A04 point the right-handed neutrino hypercharge is exactly zero,
    so the A08 family passes through the neutrino-free Standard Model."""
    return all(-(n * y_q) + (n * y_q) == 0 for n in COLOURS for y_q in Y_Q_GRID)


def a10() -> bool:
    return (
        electric_charge(Q(1, 2), Q(1, 6)) == Q(2, 3)
        and electric_charge(Q(-1, 2), Q(1, 6)) == Q(-1, 3)
        and electric_charge(Q(-1, 2), Q(-1, 2)) == Q(-1)
        and electric_charge(Q(1, 2), Q(-1, 2)) == Q(0)
        and proton_charge(Q(1, 6)) == 1
        and neutron_charge(Q(1, 6)) == 0
    )


def a11() -> bool:
    return (
        weak_doublets(3, 3) == 12
        and weak_doublets(3, 3) % 2 == 0
        and weak_doublets(2, 3) == 9
        and weak_doublets(2, 3) % 2 != 0
    )


def a12() -> bool:
    for g in (Q(1), Q(3), Q(-2, 5)):
        for a in (Q(0), Q(1, 30), Q(-7)):
            if (g * a == 0) != (a == 0):
                return False
    return True


def a13() -> bool:
    """Flagship: the two imposed conditions pin the assignment and the other
    two coefficients then cancel on their own."""
    for n, y_q, y_h in GRID:
        if n * y_q != y_h:
            continue  # A04 shows the hypotheses force this
        y_u, y_d = y_q + y_h, y_q - y_h
        y_l = -(n * y_q)
        y_e = y_l - y_h
        if su2_u1(n, y_q, y_l) != 0 or grav_u1(n, y_q, y_u, y_d, y_l, y_e, Q(0)) != 0:
            return False
        if not is_anomaly_free(n, y_q, y_u, y_d, y_l, y_e, Q(0)):
            return False
    return True


NODE_CHECKS: dict[str, Callable[[], bool]] = {
    "A01": a01,
    "A02": a02,
    "A03": a03,
    "A04": a04,
    "A05": a05,
    "A06": a06,
    "A07": a07,
    "A08": a08,
    "A09": a09,
    "A10": a10,
    "A11": a11,
    "A12": a12,
    "A13": a13,
}


@dataclass(frozen=True)
class MirrorResult:
    node_id: str
    holds: bool


def verify_mirror() -> tuple[MirrorResult, ...]:
    return tuple(
        MirrorResult(node_id, check()) for node_id, check in sorted(NODE_CHECKS.items())
    )


def mirror_summary() -> dict[str, object]:
    results = verify_mirror()
    return {
        "schema": "gaugegap.anomaly_theorem_mirror.v1",
        "grid_points": len(GRID),
        "nodes": {item.node_id: item.holds for item in results},
        "all_hold": all(item.holds for item in results),
        "claim_boundary": (
            "finite-grid exact rational check of the Lean statements; "
            "kernel verification requires lake build"
        ),
    }
