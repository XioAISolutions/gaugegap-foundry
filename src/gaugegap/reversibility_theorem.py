"""Exact mirror of the Lean logical-reversibility statements.

Restates every node of the ``landauer-reversibility`` track of
``formal/lean/dag.json`` in Python and checks it by exhaustion over the whole
finite domain -- four inputs for ``AND``, eight for ``Toffoli`` and ``Fredkin``.

The track exists because Landauer's principle is a statement about *logically
irreversible* operations, and which operations those are is a combinatorial
question that can be settled exactly. ``gaugegap.quantum.landauer`` already
computes the energy floor; this supplies the entropy that goes into it, without
a single floating-point rounding on the way.

Two things this module deliberately does *not* do. It does not assert
``P.T @ P == I`` for an arbitrary matrix ``P`` -- that is true, vacuous, and
says nothing about Toffoli; it builds the specific 8x8 permutation matrix of
the specific gate and checks that one, over the integers. And it does not
translate any of this into a statement about gauge theory: a truncated Hilbert
space in a lattice simulation is an approximation in a model, not a physical
erasure.

CLAIM BOUNDARY: exact combinatorics and integer linear algebra for named finite
Boolean functions, plus the Shannon entropy those fibre counts determine, held
as an exact rational combination of base-2 logarithms of integers. The thermal
statement it feeds is Landauer's, and lives in ``gaugegap.quantum.landauer``.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Callable, Dict, Sequence, Tuple

Q = Fraction

Bit2 = Tuple[bool, bool]
Bit3 = Tuple[bool, bool, bool]
Matrix = Tuple[Tuple[int, ...], ...]

#: An exact entropy: ``{p: c}`` means ``sum(c * log2(p))`` over *primes* ``p``.
#: Shannon entropies of rational distributions are exactly of this shape, and
#: are generally irrational, so this keeps them exact instead of rounding them
#: to a float. Keying on primes puts every entropy in a canonical form -- the
#: logarithms of distinct primes are rationally independent, so two entropies
#: are equal exactly when their combinations are, and ``==`` is a real test.
Log2Combo = Dict[int, Q]

#: All four inputs of AND, and all eight of Toffoli and Fredkin, in a fixed
#: order -- the order the permutation matrices below are indexed by.
INPUTS_2: Tuple[Bit2, ...] = tuple(
    (bool(a), bool(b)) for a in (0, 1) for b in (0, 1)
)
INPUTS_3: Tuple[Bit3, ...] = tuple(
    (bool(a), bool(b), bool(c)) for a in (0, 1) for b in (0, 1) for c in (0, 1)
)


def and_gate(p: Bit2) -> bool:
    """Classical AND, mirroring ``GaugeGap.Reversibility.andGate``."""
    a, b = p
    return a and b


def toffoli(x: Bit3) -> Bit3:
    """Controlled-controlled-NOT, mirroring ``GaugeGap.Reversibility.toffoli``."""
    a, b, c = x
    return (a, b, c != (a and b))


def fredkin(x: Bit3) -> Bit3:
    """Controlled-SWAP, mirroring ``GaugeGap.Reversibility.fredkin``."""
    a, b, c = x
    return (a, c, b) if a else (a, b, c)


# --------------------------------------------------------------------------
# Node checks (E01-E07), each exhaustive over the gate's whole domain.
# --------------------------------------------------------------------------


def e01() -> bool:
    """AND is not injective, and two named inputs witness it."""
    witnessed = (
        and_gate((False, False)) == and_gate((False, True))
        and (False, False) != (False, True)
    )
    collisions = any(
        and_gate(p) == and_gate(q)
        for i, p in enumerate(INPUTS_2)
        for q in INPUTS_2[i + 1:]
    )
    return witnessed and collisions


def fibre_sizes() -> Dict[bool, int]:
    """How many inputs land on each output of AND."""
    sizes = {False: 0, True: 0}
    for p in INPUTS_2:
        sizes[and_gate(p)] += 1
    return sizes


def e02() -> bool:
    """Exactly three inputs map to ``False`` and one to ``True``.

    The enumeration is checked for exhaustiveness first, mirroring the Lean
    node's first conjunct: counts over a sample would say nothing.
    """
    exhaustive = set(INPUTS_2) == {
        (a, b) for a in (False, True) for b in (False, True)
    }
    return exhaustive and fibre_sizes() == {False: 3, True: 1}


def e03() -> bool:
    """Toffoli is an involution."""
    return all(toffoli(toffoli(x)) == x for x in INPUTS_3)


def e04() -> bool:
    """Toffoli is a bijection: eight distinct images on eight inputs."""
    images = [toffoli(x) for x in INPUTS_3]
    return len(set(images)) == len(INPUTS_3) == len(images)


def e05() -> bool:
    """With the target bit cleared, Toffoli's third output is the AND."""
    return all(
        toffoli((a, b, False))[2] == and_gate((a, b))
        for a, b in INPUTS_2
    )


def e06() -> bool:
    """Toffoli is reversible because it carries its inputs forward."""
    return all(
        toffoli(x)[0] == x[0] and toffoli(x)[1] == x[1] for x in INPUTS_3
    )


def e07() -> bool:
    """Fredkin is an involution too."""
    return all(fredkin(fredkin(x)) == x for x in INPUTS_3)


NODE_CHECKS: dict[str, Callable[[], bool]] = {
    "E01": e01,
    "E02": e02,
    "E03": e03,
    "E04": e04,
    "E05": e05,
    "E06": e06,
    "E07": e07,
}


# --------------------------------------------------------------------------
# Exact entropy accounting, from the fibre counts E02 pins down.
# --------------------------------------------------------------------------


def _prime_factors(n: int) -> Dict[int, int]:
    """The exponents of ``n``'s prime factorisation. ``n`` here is a count of
    outcomes, so it is small and trial division is the whole algorithm."""
    if n < 1:
        raise ValueError("only positive integers have a logarithm here")
    factors: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def _combo_add(target: Log2Combo, n: int, coeff: Q) -> None:
    """Add ``coeff * log2(n)``, split over primes so the result stays canonical."""
    if n == 1 or coeff == 0:          # log2 1 = 0, so it never contributes
        return
    for prime, exponent in _prime_factors(n).items():
        total = target.get(prime, Q(0)) + coeff * exponent
        if total == 0:
            target.pop(prime, None)
        else:
            target[prime] = total


def shannon_entropy_bits(counts: Sequence[int]) -> Log2Combo:
    """Shannon entropy, in bits, of the distribution ``counts`` induces.

    For counts ``c_i`` summing to ``N`` the entropy is
    ``log2 N - sum_i (c_i / N) log2 c_i``, which is exactly a rational
    combination of base-2 logarithms of primes -- so it is returned as one
    rather than evaluated.
    """
    total = sum(counts)
    if total <= 0:
        raise ValueError("entropy needs at least one outcome")
    combo: Log2Combo = {}
    _combo_add(combo, total, Q(1))
    for c in counts:
        if c < 0:
            raise ValueError("counts must be non-negative")
        if c:
            _combo_add(combo, c, -Q(c, total))
    return combo


def combo_to_float(combo: Log2Combo) -> float:
    """Evaluate an exact entropy numerically. The only rounding in the module."""
    return float(sum(float(coeff) * math.log2(n) for n, coeff in combo.items()))


def and_output_entropy_bits() -> Log2Combo:
    """H(Y) for AND on uniform inputs: ``2 - (3/4) log2 3``."""
    sizes = fibre_sizes()
    return shannon_entropy_bits((sizes[False], sizes[True]))


def and_conditional_entropy_bits() -> Log2Combo:
    """H(X | Y) for AND on uniform inputs, the information the gate destroys.

    AND is a function, so ``H(X, Y) = H(X) = 2`` bits exactly, and therefore
    ``H(X | Y) = 2 - H(Y) = (3/4) log2 3``. That is about 1.1887218755 bits --
    an irrational number, not the 1.1887 it is often quoted as, and not the
    0.5 that averaging the two fibres by hand produces.
    """
    combo: Log2Combo = {}
    _combo_add(combo, 2, Q(2))                       # H(X) = 2 bits = 2 log2 2
    for n, coeff in and_output_entropy_bits().items():
        _combo_add(combo, n, -coeff)
    return combo


def and_erasure_floor(temperature: float = 1.0, k_B: float = 1.0) -> float:
    """The Landauer floor for one uniform AND evaluation, in the same units as
    ``k_B * temperature``.

    Delegates the physics to :func:`gaugegap.quantum.landauer.landauer_bound`;
    all this contributes is the exact entropy, converted from bits to nats.
    """
    from gaugegap.quantum.landauer import landauer_bound

    bits = combo_to_float(and_conditional_entropy_bits())
    return landauer_bound(bits * math.log(2.0), temperature, k_B)


# --------------------------------------------------------------------------
# Integer permutation matrices for the *specific* reversible gates.
# --------------------------------------------------------------------------


def permutation_matrix(gate: Callable[[Bit3], Bit3]) -> Matrix:
    """The 8x8 matrix of ``gate`` in the computational basis, over the integers.

    ``P[i][j] = 1`` exactly when ``gate`` sends basis state ``j`` to ``i``.
    Raises if the gate is not a permutation, so the construction itself is
    part of the check.
    """
    index = {x: i for i, x in enumerate(INPUTS_3)}
    rows = [[0] * len(INPUTS_3) for _ in INPUTS_3]
    hit = set()
    for j, x in enumerate(INPUTS_3):
        i = index[gate(x)]
        if i in hit:
            raise ValueError("gate is not injective, so it has no permutation matrix")
        hit.add(i)
        rows[i][j] = 1
    return tuple(tuple(row) for row in rows)


def transpose(m: Matrix) -> Matrix:
    return tuple(zip(*m))


def matmul(a: Matrix, b: Matrix) -> Matrix:
    bt = transpose(b)
    return tuple(
        tuple(sum(x * y for x, y in zip(row, col)) for col in bt) for row in a
    )


def identity(n: int) -> Matrix:
    return tuple(
        tuple(1 if i == j else 0 for j in range(n)) for i in range(n)
    )


def is_orthogonal(m: Matrix) -> bool:
    """``Mᵀ M = I``, checked with exact integer arithmetic."""
    return matmul(transpose(m), m) == identity(len(m))


def gate_is_orthogonal(gate: Callable[[Bit3], Bit3]) -> bool:
    """Build this gate's own permutation matrix, then check it is orthogonal."""
    return is_orthogonal(permutation_matrix(gate))


def mirror_summary() -> dict[str, object]:
    """A reportable summary of the track, for the forge gate and the docs."""
    conditional = and_conditional_entropy_bits()
    return {
        "schema": "gaugegap.reversibility_mirror.v1",
        "nodes": {node_id: check() for node_id, check in sorted(NODE_CHECKS.items())},
        "and_fibre_sizes": {str(k): v for k, v in fibre_sizes().items()},
        "and_conditional_entropy_bits_exact": {
            str(n): str(c) for n, c in conditional.items()
        },
        "and_conditional_entropy_bits": combo_to_float(conditional),
        "toffoli_orthogonal": gate_is_orthogonal(toffoli),
        "fredkin_orthogonal": gate_is_orthogonal(fredkin),
        "claim_boundary": (
            "exhaustive finite check of named Boolean gates plus exact integer "
            "linear algebra; the thermal bound is Landauer's and lives in "
            "gaugegap.quantum.landauer; no gauge-theory claim is made"
        ),
    }
