"""Bounded search for Williamson quadruples, verified with exact integers.

Hadamard Forge's constructor set emits matrices from closed-form classical
families.  This module does something different: it *searches* a declared finite
space and reports what the search found, so a result can carry the
``REDISCOVERED`` label rather than ``REPRODUCED``.

The space is the Williamson family.  For odd ``n``, four symmetric circulant
``+-1`` matrices ``A, B, C, D`` of order ``n`` satisfying

    A^2 + B^2 + C^2 + D^2 == 4n * I

assemble into a Hadamard matrix of order ``4n`` through the Williamson array.
Because the matrices are circulant and symmetric, that identity is equivalent to
a purely integer condition on the periodic autocorrelations of their first rows:

    R_a(s) + R_b(s) + R_c(s) + R_d(s) == 0   for every shift s = 1 .. n-1

which is what the search actually solves, in exact integer arithmetic.

Search structure
----------------
1. enumerate symmetric ``+-1`` first rows (fixing ``a[0] = +1``: negating a row
   changes neither ``A^2`` nor the autocorrelation, so the other half of the
   space is redundant);
2. compute every periodic autocorrelation exactly as integers;
3. discard rows whose power spectral density exceeds ``4n`` at any frequency --
   a necessary condition, used only to prune;
4. partition the survivors by row sum. At frequency zero the same density
   identity reads ``sa^2 + sb^2 + sc^2 + sd^2 == 4n`` for the four row sums, so
   only a handful of magnitude multisets can occur and each fixes which groups a
   quadruple may draw from;
5. within an admissible partition, meet in the middle on autocorrelation sums.

Steps 3 to 5 are heuristics for *finding* a candidate. Nothing they produce is
trusted: the quadruple's autocorrelation identity is re-checked in exact Python
integers, and the assembled matrix then goes through the same fail-closed gates
as any other witness.

CLAIM BOUNDARY:
A successful search establishes the exact existence of one Hadamard matrix of
order ``4n``. An exhausted search establishes only that *no symmetric Williamson
quadruple of that order exists* -- other constructions may still produce a
Hadamard matrix of the same order, and several do. Neither outcome bears on the
Hadamard conjecture.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Iterable, Sequence

import numpy as np

from gaugegap.hadamard_forge import HadamardForgeError, HadamardWitness


CLAIM_BOUNDARY = (
    "Bounded search over the symmetric Williamson family only. A found quadruple is "
    "verified exactly and certifies the existence of one Hadamard matrix of order 4n. "
    "An exhausted search certifies only that this family contains no quadruple for that "
    "order; it is not a statement that no Hadamard matrix of that order exists, and it "
    "is not a statement about the Hadamard conjecture."
)

OUTCOME_FOUND = "QUADRUPLE_FOUND"
OUTCOME_EXHAUSTED = "FAMILY_EXHAUSTED_NO_QUADRUPLE"
OUTCOME_BUDGET = "SEARCH_BUDGET_EXCEEDED"

# Enumerating symmetric rows costs 2 ** ((n - 1) / 2) candidates; the default
# budget keeps a single search in the seconds range.
DEFAULT_CANDIDATE_BUDGET = 1 << 22

# The meet-in-the-middle indexes one pair sum per key; the default keeps the key
# table well under a gigabyte. A split that would exceed it stops the search with
# SEARCH_BUDGET_EXCEEDED rather than attempting the allocation.
DEFAULT_PAIR_BUDGET = 1 << 25


def symmetric_rows(n: int) -> np.ndarray:
    """Every symmetric ``+-1`` row of length ``n`` with ``row[0] = +1``.

    Symmetry means ``row[j] == row[n - j]``, so the free entries are
    ``row[1 .. (n-1)/2]`` and the enumeration has ``2 ** ((n-1)/2)`` members.
    """

    if n < 1 or n % 2 == 0:
        raise HadamardForgeError("Williamson rows are defined for odd n")
    half = (n - 1) // 2
    count = 1 << half
    rows = np.ones((count, n), dtype=np.int8)
    if half:
        # Bit j of the enumeration index selects the sign of free entry j + 1.
        index = np.arange(count, dtype=np.int64)
        bits = ((index[:, None] >> np.arange(half)[None, :]) & 1).astype(np.int8)
        signs = 1 - 2 * bits
        rows[:, 1 : half + 1] = signs
        rows[:, half + 1 :] = signs[:, ::-1]
    return rows


def periodic_autocorrelations(rows: np.ndarray) -> np.ndarray:
    """Exact integer periodic autocorrelations for shifts ``1 .. (n-1)/2``.

    ``R(s) == R(n - s)`` for every real sequence, so the second half carries no
    information. Accumulation stays in ``int64``; no floating point is involved.
    """

    count, n = rows.shape
    half = (n - 1) // 2
    values = rows.astype(np.int64)
    result = np.empty((count, half), dtype=np.int64)
    for shift in range(1, half + 1):
        result[:, shift - 1] = (values * np.roll(values, -shift, axis=1)).sum(axis=1)
    return result


def _psd_admissible(rows: np.ndarray, n: int) -> np.ndarray:
    """Rows whose power spectral density never exceeds ``4n``.

    Necessary because the four densities are non-negative and sum to ``4n`` at
    every frequency. Evaluated in floating point with a slack of one, purely to
    prune the search: every surviving candidate is re-checked exactly.
    """

    spectrum = np.fft.rfft(rows.astype(np.float64), axis=1)
    density = (spectrum.real**2 + spectrum.imag**2)[:, 1:]
    if density.size == 0:
        return np.ones(len(rows), dtype=bool)
    return density.max(axis=1) <= 4 * n + 1.0


def exact_autocorrelation(row: Sequence[int]) -> tuple[int, ...]:
    """Pure-Python exact autocorrelation, used to re-check a found quadruple."""

    n = len(row)
    return tuple(
        sum(row[j] * row[(j + shift) % n] for j in range(n))
        for shift in range(1, (n - 1) // 2 + 1)
    )


def row_sum_partitions(n: int) -> tuple[tuple[int, ...], ...]:
    """Row-sum magnitude multisets admissible for order ``4n``.

    At frequency zero the density identity is ``sa^2 + sb^2 + sc^2 + sd^2 == 4n``.
    Row sums of odd-length ``+-1`` rows are odd, so only a few multisets qualify,
    and each one restricts which groups a quadruple may be drawn from.
    """

    limit = int((4 * n) ** 0.5)
    odds = [value for value in range(1, limit + 1, 2)]
    return tuple(
        combo
        for combo in itertools.combinations_with_replacement(odds, 4)
        if sum(value * value for value in combo) == 4 * n
    )


def _encode(vectors: np.ndarray, n: int) -> np.ndarray:
    """Pack autocorrelation vectors into fixed-width integer keys.

    Entries lie in ``[-n, n]``, so each fits in one base-``(2n+1)`` digit and
    eight digits fit in an ``int64``. Packing makes the meet-in-the-middle a
    vectorized set intersection instead of a Python dict of tuples.
    """

    base = 2 * n + 1
    shifted = vectors.astype(np.int64) + n
    if shifted.shape[1] == 0:
        # n == 1 has no nonzero shifts, so every vector carries the same key.
        return np.zeros((len(shifted), 1), dtype=np.int64)
    words = []
    for start in range(0, shifted.shape[1], 8):
        chunk = shifted[:, start : start + 8]
        word = np.zeros(len(shifted), dtype=np.int64)
        for column in range(chunk.shape[1]):
            word = word * base + chunk[:, column]
        words.append(word)
    return np.stack(words, axis=1)


def _as_keys(encoded: np.ndarray) -> np.ndarray:
    """View packed words as opaque fixed-width keys for set operations."""

    contiguous = np.ascontiguousarray(encoded)
    return contiguous.view(
        np.dtype((np.void, contiguous.dtype.itemsize * contiguous.shape[1]))
    ).ravel()


def _match_pairs(
    left: np.ndarray,
    right: np.ndarray,
    n: int,
    *,
    chunk: int = 256,
) -> tuple[int, int, int, int, int] | None:
    """Find ``(i, j, k, m)`` with ``L_i + L_j + R_k + R_m == 0``, or ``None``.

    ``left`` and ``right`` are autocorrelation blocks. All ``left`` pair sums are
    indexed once as packed keys; ``right`` pair sums are streamed and probed
    against the negated index. Both sides are built in chunks, so peak memory is
    the key table (a couple of machine words per indexed pair) rather than the
    full block of autocorrelation vectors. Returns the four indices plus the
    number of indexed pair sums.
    """

    if not len(left) or not len(right):
        return None
    columns = len(left)
    width = _encode(left[:1], n).shape[1]
    index_keys = np.empty((columns * columns, width), dtype=np.int64)
    for start in range(0, columns, chunk):
        block = left[start : start + chunk]
        sums = (block[:, None, :] + left[None, :, :]).reshape(len(block) * columns, -1)
        index_keys[start * columns : (start + len(block)) * columns] = _encode(sums, n)

    keys = _as_keys(index_keys)
    order = np.argsort(keys, kind="stable")
    sorted_keys = keys[order]

    for start in range(0, len(right), chunk):
        block = right[start : start + chunk]
        block_sums = (block[:, None, :] + right[None, :, :]).reshape(
            len(block) * len(right), -1
        )
        probe = _as_keys(_encode(-block_sums, n))
        position = np.searchsorted(sorted_keys, probe)
        position = np.clip(position, 0, len(sorted_keys) - 1)
        hit = sorted_keys[position] == probe
        if not hit.any():
            continue
        first = int(np.flatnonzero(hit)[0])
        left_pair = int(order[position[first]])
        i, j = divmod(left_pair, columns)
        k, m = divmod(first, len(right))
        return i, j, start + k, m, len(keys)
    return None


@dataclass(frozen=True)
class WilliamsonSearch:
    """What the search examined and what it concluded."""

    n: int
    order: int
    outcome: str
    quadruple: tuple[tuple[int, ...], ...] | None
    space_size: int
    enumerated: int
    psd_survivors: int
    partitions: tuple[tuple[int, ...], ...]
    pair_sums: int
    claim_boundary: str = CLAIM_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.williamson_search.v1",
            "n": self.n,
            "order": self.order,
            "outcome": self.outcome,
            "quadruple": None
            if self.quadruple is None
            else [list(row) for row in self.quadruple],
            "search_space": {
                "family": "symmetric circulant Williamson quadruples",
                "symmetric_rows_with_leading_plus_one": self.space_size,
                "rows_enumerated": self.enumerated,
                "rows_surviving_psd_bound": self.psd_survivors,
                "admissible_row_sum_partitions": [list(part) for part in self.partitions],
                "pair_sums_indexed": self.pair_sums,
            },
            "arithmetic": "exact_integer_autocorrelation",
            "claim_boundary": self.claim_boundary,
        }


def search_williamson_quadruple(
    n: int,
    *,
    candidate_budget: int = DEFAULT_CANDIDATE_BUDGET,
    pair_budget: int = DEFAULT_PAIR_BUDGET,
) -> WilliamsonSearch:
    """Search the symmetric Williamson family of order ``4n``.

    The search is exhaustive over the declared space when it completes: a
    ``FAMILY_EXHAUSTED_NO_QUADRUPLE`` outcome means no symmetric quadruple
    exists for that ``n``, not that no Hadamard matrix of order ``4n`` does.
    """

    if n < 1 or n % 2 == 0:
        raise HadamardForgeError("Williamson quadruples are defined for odd n")
    space_size = 1 << ((n - 1) // 2)
    partitions = row_sum_partitions(n)
    if space_size > candidate_budget:
        return WilliamsonSearch(
            n=n,
            order=4 * n,
            outcome=OUTCOME_BUDGET,
            quadruple=None,
            space_size=space_size,
            enumerated=0,
            psd_survivors=0,
            partitions=partitions,
            pair_sums=0,
        )

    rows = symmetric_rows(n)
    survivors = rows[_psd_admissible(rows, n)]
    correlations = periodic_autocorrelations(survivors)
    magnitudes = np.abs(survivors.astype(np.int64).sum(axis=1))
    groups = {
        magnitude: np.flatnonzero(magnitudes == magnitude)
        for magnitude in np.unique(magnitudes)
    }

    indexed = 0
    over_budget = False
    for partition in partitions:
        # Each way of splitting the four magnitudes into two pairs gives one
        # meet-in-the-middle problem; all three splits are tried.
        for left_pair, right_pair in (
            ((0, 1), (2, 3)),
            ((0, 2), (1, 3)),
            ((0, 3), (1, 2)),
        ):
            left_ids = _concat_groups(groups, [partition[i] for i in left_pair])
            right_ids = _concat_groups(groups, [partition[i] for i in right_pair])
            if left_ids is None or right_ids is None:
                continue
            if len(left_ids) ** 2 > pair_budget:
                # Refuse the allocation instead of failing mid-search: an
                # unexamined split cannot support an exhaustion claim.
                over_budget = True
                continue
            match = _match_pairs(correlations[left_ids], correlations[right_ids], n)
            if match is None:
                continue
            i, j, k, m, pair_count = match
            indexed += pair_count
            quadruple = tuple(
                tuple(int(value) for value in survivors[position])
                for position in (
                    left_ids[i],
                    left_ids[j],
                    right_ids[k],
                    right_ids[m],
                )
            )
            # Re-check in exact Python integers: the numpy pass is a search tool,
            # never a certificate.
            if not quadruple_is_valid(quadruple):
                raise HadamardForgeError(
                    "search returned a quadruple that fails the exact autocorrelation identity"
                )
            return WilliamsonSearch(
                n=n,
                order=4 * n,
                outcome=OUTCOME_FOUND,
                quadruple=quadruple,
                space_size=space_size,
                enumerated=len(rows),
                psd_survivors=len(survivors),
                partitions=partitions,
                pair_sums=indexed,
            )

    return WilliamsonSearch(
        n=n,
        order=4 * n,
        outcome=OUTCOME_BUDGET if over_budget else OUTCOME_EXHAUSTED,
        quadruple=None,
        space_size=space_size,
        enumerated=len(rows),
        psd_survivors=len(survivors),
        partitions=partitions,
        pair_sums=indexed,
    )


def _concat_groups(
    groups: dict[int, np.ndarray], magnitudes: Sequence[int]
) -> np.ndarray | None:
    """Row indices whose row-sum magnitude is one of ``magnitudes``."""

    blocks = [groups[magnitude] for magnitude in magnitudes if magnitude in groups]
    if len(blocks) != len(magnitudes):
        return None
    joined = np.unique(np.concatenate(blocks))
    return joined if len(joined) else None


def quadruple_is_valid(quadruple: Sequence[Sequence[int]]) -> bool:
    """Exact check of the Williamson condition on four first rows."""

    rows = [list(row) for row in quadruple]
    if len(rows) != 4:
        return False
    n = len(rows[0])
    if any(len(row) != n for row in rows):
        return False
    if any(value not in (1, -1) for row in rows for value in row):
        return False
    if any(row[j] != row[n - j] for row in rows for j in range(1, n)):
        return False
    totals = [sum(values) for values in zip(*(exact_autocorrelation(row) for row in rows))]
    return all(total == 0 for total in totals)


def _circulant(row: Sequence[int]) -> list[list[int]]:
    n = len(row)
    return [[row[(column - index) % n] for column in range(n)] for index in range(n)]


def williamson_witness(
    quadruple: Sequence[Sequence[int]],
    *,
    name: str | None = None,
    provenance: str | None = None,
) -> HadamardWitness:
    """Assemble the Williamson array for a quadruple into a witness of order ``4n``.

        H = [[ A,  B,  C,  D],
             [-B,  A, -D,  C],
             [-C,  D,  A, -B],
             [-D, -C,  B,  A]]

    The result is returned unverified: callers run the standard gates on it.
    """

    if not quadruple_is_valid(quadruple):
        raise HadamardForgeError("quadruple fails the exact Williamson condition")
    a, b, c, d = (_circulant(row) for row in quadruple)
    n = len(quadruple[0])
    order = 4 * n

    def negate(block: list[list[int]]) -> list[list[int]]:
        return [[-value for value in row] for row in block]

    layout = [
        [a, b, c, d],
        [negate(b), a, negate(d), c],
        [negate(c), d, a, negate(b)],
        [negate(d), negate(c), b, a],
    ]
    signs = [[0] * order for _ in range(order)]
    for block_row, blocks in enumerate(layout):
        for block_column, block in enumerate(blocks):
            for i in range(n):
                target = signs[block_row * n + i]
                source = block[i]
                for j in range(n):
                    target[block_column * n + j] = source[j]
    return HadamardWitness.from_signs(
        signs,
        name=name or f"williamson-{order}",
        provenance=provenance or f"search:williamson(n={n})",
    )


def williamson_search_orders(limit: int, *, candidate_budget: int = DEFAULT_CANDIDATE_BUDGET) -> tuple[int, ...]:
    """Orders ``4n <= limit`` (``n`` odd) whose family fits the search budget.

    Being searchable is not a promise of success: the family is genuinely empty
    for some orders, and the search reports that outcome rather than hiding it.
    """

    return tuple(
        4 * n
        for n in range(1, limit // 4 + 1, 2)
        if 4 * n <= limit and (1 << ((n - 1) // 2)) <= candidate_budget
    )


def iter_quadruple_rows(search: WilliamsonSearch) -> Iterable[tuple[int, ...]]:
    if search.quadruple is None:
        return iter(())
    return iter(search.quadruple)


__all__ = [
    "CLAIM_BOUNDARY",
    "DEFAULT_CANDIDATE_BUDGET",
    "DEFAULT_PAIR_BUDGET",
    "OUTCOME_BUDGET",
    "OUTCOME_EXHAUSTED",
    "OUTCOME_FOUND",
    "WilliamsonSearch",
    "exact_autocorrelation",
    "iter_quadruple_rows",
    "periodic_autocorrelations",
    "quadruple_is_valid",
    "row_sum_partitions",
    "search_williamson_quadruple",
    "symmetric_rows",
    "williamson_search_orders",
    "williamson_witness",
]
