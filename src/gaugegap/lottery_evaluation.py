"""Prospective outcome evaluation for Lottery Forge selections.

This module scores already-frozen candidate lines against a later observed draw.
It deliberately does not retune selection weights from the outcome.  Exact
single-line overlap probabilities use the hypergeometric null; family-level
maximum-hit diagnostics use a deterministic Monte Carlo null that preserves the
actual overlap structure among the frozen candidate lines.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import random
from typing import Iterable, Sequence


EVALUATION_CLAIM_BOUNDARY = (
    "Outcome evaluation is retrospective scoring of selections that were frozen before the draw. "
    "A post-hoc statistic is exploratory unless its metric and threshold were predeclared. "
    "Do not change model weights from one draw and then treat the same draw as validation."
)


@dataclass(frozen=True)
class LineOutcome:
    rank: int
    numbers: tuple[int, ...]
    matching_numbers: tuple[int, ...]
    hit_count: int
    bonus_hit: bool

    def summary(self) -> dict[str, object]:
        data = asdict(self)
        data["numbers"] = list(self.numbers)
        data["matching_numbers"] = list(self.matching_numbers)
        return data


@dataclass(frozen=True)
class FamilyNullResult:
    observed_max_hits: int
    empirical_p_value: float
    trials: int
    seed: int
    null_max_hit_counts: dict[int, int]

    def summary(self) -> dict[str, object]:
        return asdict(self)


def _validate_line(numbers: Iterable[int], *, pool_size: int, pick_count: int) -> tuple[int, ...]:
    values = tuple(sorted(map(int, numbers)))
    if len(values) != pick_count or len(set(values)) != pick_count:
        raise ValueError("invalid line length/duplicates")
    if values[0] < 1 or values[-1] > pool_size:
        raise ValueError("line outside pool")
    return values


def overlap_probability(*, pool_size: int, pick_count: int, hits: int) -> float:
    """Exact probability that two independent valid k-of-N sets overlap in exactly `hits`."""
    if pool_size < 2 or not 1 <= pick_count < pool_size:
        raise ValueError("invalid lottery specification")
    if hits < 0 or hits > pick_count:
        return 0.0
    remaining = pool_size - pick_count
    misses = pick_count - hits
    if misses > remaining:
        return 0.0
    return (
        math.comb(pick_count, hits)
        * math.comb(remaining, misses)
        / math.comb(pool_size, pick_count)
    )


def overlap_tail_probability(*, pool_size: int, pick_count: int, at_least_hits: int) -> float:
    """Exact probability of at least `at_least_hits` matches for one frozen line."""
    if at_least_hits <= 0:
        return 1.0
    return math.fsum(
        overlap_probability(pool_size=pool_size, pick_count=pick_count, hits=hits)
        for hits in range(at_least_hits, pick_count + 1)
    )


def evaluate_line(
    numbers: Iterable[int],
    draw: Iterable[int],
    *,
    pool_size: int,
    pick_count: int,
    rank: int = 1,
    bonus: int | None = None,
) -> LineOutcome:
    line = _validate_line(numbers, pool_size=pool_size, pick_count=pick_count)
    winning = _validate_line(draw, pool_size=pool_size, pick_count=pick_count)
    matching = tuple(sorted(set(line).intersection(winning)))
    bonus_hit = bonus is not None and int(bonus) in line and int(bonus) not in winning
    return LineOutcome(rank, line, matching, len(matching), bonus_hit)


def evaluate_ranked_lines(
    lines: Sequence[Iterable[int]],
    draw: Iterable[int],
    *,
    pool_size: int,
    pick_count: int,
    bonus: int | None = None,
) -> list[LineOutcome]:
    if not lines:
        raise ValueError("at least one frozen line is required")
    return [
        evaluate_line(
            line,
            draw,
            pool_size=pool_size,
            pick_count=pick_count,
            rank=index,
            bonus=bonus,
        )
        for index, line in enumerate(lines, start=1)
    ]


def fixed_family_max_hit_null(
    lines: Sequence[Iterable[int]],
    *,
    pool_size: int,
    pick_count: int,
    observed_max_hits: int,
    trials: int = 100_000,
    seed: int = 0,
) -> FamilyNullResult:
    """Monte Carlo null for the maximum hit count across a frozen line family.

    The frozen candidate geometry is kept exactly as-is, including overlap among
    lines. Only the future draw is randomized. This is suitable for evaluating a
    predeclared family-max metric; if the metric was chosen after seeing the draw,
    its p-value must be described as exploratory.
    """
    if trials < 1:
        raise ValueError("trials must be positive")
    frozen = [
        set(_validate_line(line, pool_size=pool_size, pick_count=pick_count))
        for line in lines
    ]
    if not frozen:
        raise ValueError("at least one frozen line is required")
    if not 0 <= observed_max_hits <= pick_count:
        raise ValueError("observed_max_hits outside valid range")

    rng = random.Random(seed)
    counts = {hits: 0 for hits in range(pick_count + 1)}
    extreme = 0
    population = range(1, pool_size + 1)
    for _ in range(trials):
        random_draw = set(rng.sample(population, pick_count))
        maximum = max(len(random_draw.intersection(line)) for line in frozen)
        counts[maximum] += 1
        if maximum >= observed_max_hits:
            extreme += 1
    return FamilyNullResult(
        observed_max_hits=observed_max_hits,
        empirical_p_value=(extreme + 1) / (trials + 1),
        trials=trials,
        seed=seed,
        null_max_hit_counts=counts,
    )
