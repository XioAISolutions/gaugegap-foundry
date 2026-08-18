"""Robust, game-agnostic lottery selection heuristics.

This module does not predict draws. It ranks valid combinations for estimated
prize-sharing risk while guarding against optimizer artifacts (for example,
forcing every number above 31 simply because birthdays are popular).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import csv
import heapq
import math
import random
from pathlib import Path
from typing import Iterable, Mapping, Sequence

SELECTION_CLAIM_BOUNDARY = (
    "Selection scores do not change the probability that a valid combination is drawn. "
    "They are bounded heuristics for estimated human-choice/prize-sharing risk. Measured "
    "OLG popularity data covers only published top combinations; shape guardrails exist to "
    "prevent the optimizer from exploiting an unsupported proxy, not to predict random draws."
)


@dataclass(frozen=True)
class SelectionSpec:
    name: str
    pool_size: int
    pick_count: int
    birthday_cutoff: int = 31

    def validate(self) -> None:
        if self.pool_size < 2 or not 1 <= self.pick_count < self.pool_size:
            raise ValueError("invalid selection specification")
        if not 0 <= self.birthday_cutoff <= self.pool_size:
            raise ValueError("invalid birthday cutoff")


@dataclass(frozen=True)
class SelectionScore:
    numbers: tuple[int, ...]
    score: float
    crowd_penalty: float
    measured_popularity_penalty: float
    features: Mapping[str, float]
    components: Mapping[str, float]
    guardrails_passed: bool

    def summary(self) -> dict[str, object]:
        data = asdict(self)
        data["numbers"] = list(self.numbers)
        data["features"] = dict(self.features)
        data["components"] = dict(self.components)
        return data


def _validate_numbers(numbers: Iterable[int], spec: SelectionSpec) -> tuple[int, ...]:
    spec.validate()
    values = tuple(sorted(map(int, numbers)))
    if len(values) != spec.pick_count or len(set(values)) != spec.pick_count:
        raise ValueError("invalid combination length/duplicates")
    if values[0] < 1 or values[-1] > spec.pool_size:
        raise ValueError("combination outside game range")
    return values


def fibonacci_numbers(limit: int) -> frozenset[int]:
    if limit < 1:
        return frozenset()
    values = [1, 2]
    while values[-1] + values[-2] <= limit:
        values.append(values[-1] + values[-2])
    return frozenset(values)


def _longest_consecutive_run(values: Sequence[int]) -> int:
    best = current = 1
    for left, right in zip(values, values[1:]):
        if right == left + 1:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def _progressions(values: Sequence[int]) -> int:
    chosen = set(values)
    return sum(
        1
        for left, middle in combinations(values, 2)
        if (right := 2 * middle - left) > middle and right in chosen
    )


def combination_features(numbers: Iterable[int], spec: SelectionSpec) -> dict[str, float]:
    values = _validate_numbers(numbers, spec)
    chosen = set(values)
    fib = fibonacci_numbers(spec.pool_size)
    birthday_count = sum(value <= spec.birthday_cutoff for value in values)
    quartiles = [0, 0, 0, 0]
    for value in values:
        quartiles[min(3, (value - 1) * 4 // spec.pool_size)] += 1
    decade_bins: dict[int, int] = {}
    for value in values:
        decade_bins[(value - 1) // 10] = decade_bins.get((value - 1) // 10, 0) + 1
    max_in_ten = 0
    for start in range(1, max(2, spec.pool_size - 8)):
        max_in_ten = max(max_in_ten, sum(start <= value <= start + 9 for value in values))
    return {
        "birthday_count": float(birthday_count),
        "above_birthday_count": float(spec.pick_count - birthday_count),
        "all_birthday": float(all(value <= spec.birthday_cutoff for value in values)),
        "all_above_birthday": float(all(value > spec.birthday_cutoff for value in values)),
        "fibonacci_count": float(sum(value in fib for value in values)),
        "lucky_count": float(sum(value in {7, 11, 13} for value in values)),
        "round_count": float(sum(value % 5 == 0 for value in values)),
        "consecutive_pairs": float(sum(value + 1 in chosen for value in values)),
        "longest_consecutive_run": float(_longest_consecutive_run(values)),
        "three_term_progressions": float(_progressions(values)),
        "same_last_digit_pairs": float(sum(a % 10 == b % 10 for a, b in combinations(values, 2))),
        "odd_count": float(sum(value % 2 for value in values)),
        "range": float(values[-1] - values[0]),
        "quartiles_occupied": float(sum(count > 0 for count in quartiles)),
        "max_in_ten_window": float(max_in_ten),
        "max_in_decade_bin": float(max(decade_bins.values(), default=0)),
        "sum": float(sum(values)),
    }


def shape_guardrails(numbers: Iterable[int], spec: SelectionSpec) -> bool:
    """Reject proxy-exploitation extremes without claiming they are less drawable.

    Birthday-tail concentration is bounded relative to its expectation under a
    uniform fair draw. This stops the crowd-risk proxy from monotonically pushing
    selections upward simply because dates are commonly chosen by humans. The
    other constraints are broad shape sanity checks, not prediction features.
    """
    values = _validate_numbers(numbers, spec)
    f = combination_features(values, spec)
    if spec.birthday_cutoff and spec.birthday_cutoff < spec.pool_size:
        high_pool = spec.pool_size - spec.birthday_cutoff
        expected_high = spec.pick_count * high_pool / spec.pool_size
        max_high = min(spec.pick_count - 1, math.ceil(expected_high + 1.0))
        if f["above_birthday_count"] < 1 or f["above_birthday_count"] > max_high:
            return False
    if f["range"] < 0.55 * spec.pool_size:
        return False
    if f["longest_consecutive_run"] > 2:
        return False
    if f["odd_count"] in {0.0, float(spec.pick_count)}:
        return False
    if spec.pick_count >= 5 and f["quartiles_occupied"] < 3:
        return False
    if f["max_in_ten_window"] > max(3, math.ceil(spec.pick_count / 2)):
        return False
    return True


def load_popular_combinations(path: str | Path) -> dict[tuple[int, ...], int]:
    result: dict[tuple[int, ...], int] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            numbers = tuple(sorted(int(value) for value in row["numbers"].replace("-", " ").split()))
            plays = int(row["plays"].replace(",", ""))
            result[numbers] = plays
    return result


def measured_popularity_penalty(
    numbers: Iterable[int],
    popular_combinations: Mapping[tuple[int, ...], int] | None,
) -> float:
    if not popular_combinations:
        return 0.0
    values = tuple(sorted(map(int, numbers)))
    chosen = set(values)
    k = len(values)
    return max(
        math.log1p(max(0, int(plays))) * (len(chosen.intersection(combo)) / k) ** 4
        for combo, plays in popular_combinations.items()
    )


def crowd_risk_components(
    numbers: Iterable[int],
    spec: SelectionSpec,
    *,
    popular_combinations: Mapping[tuple[int, ...], int] | None = None,
    popularity_weight: float = 0.35,
) -> tuple[dict[str, float], dict[str, float]]:
    """Bound each behavioural proxy so no one feature can hijack the optimizer."""
    f = combination_features(numbers, spec)
    expected_birthdays = spec.pick_count * spec.birthday_cutoff / spec.pool_size
    free_birthdays = math.floor(expected_birthdays)
    components = {
        # Do not charge every date-range number. Only unusually birthday-heavy
        # shapes are penalized; otherwise the optimizer collapses to the high tail.
        "birthday": min(
            1.25,
            0.18 * max(0.0, f["birthday_count"] - free_birthdays)
            + 0.85 * f["all_birthday"],
        ),
        "all_above_birthday": 0.55 * f["all_above_birthday"],
        "fibonacci": min(1.00, 0.28 * f["fibonacci_count"]),
        "lucky": min(0.80, 0.35 * f["lucky_count"]),
        "round": min(0.55, 0.12 * f["round_count"]),
        "arithmetic_progression": min(1.40, 0.55 * f["three_term_progressions"]),
        "same_last_digit": min(0.75, 0.12 * f["same_last_digit_pairs"]),
        "long_run": max(0.0, min(1.40, 0.55 * (f["longest_consecutive_run"] - 2.0))),
        "measured_olg_overlap": popularity_weight
        * measured_popularity_penalty(numbers, popular_combinations),
    }
    return f, components


def score_selection(
    numbers: Iterable[int],
    spec: SelectionSpec,
    *,
    popular_combinations: Mapping[tuple[int, ...], int] | None = None,
    popularity_weight: float = 0.35,
) -> SelectionScore:
    values = _validate_numbers(numbers, spec)
    f, components = crowd_risk_components(
        values, spec, popular_combinations=popular_combinations, popularity_weight=popularity_weight
    )
    measured = measured_popularity_penalty(values, popular_combinations)
    penalty = math.fsum(components.values())
    guard = shape_guardrails(values, spec)
    score = -penalty - (1000.0 if not guard else 0.0)
    return SelectionScore(values, score, penalty, measured, f, components, guard)


def search_selections(
    spec: SelectionSpec,
    *,
    popular_combinations: Mapping[tuple[int, ...], int] | None = None,
    samples: int = 500_000,
    top_k: int = 20,
    seed: int = 20260818,
    exhaustive: bool = False,
    popularity_weight: float = 0.35,
) -> list[SelectionScore]:
    spec.validate()
    if samples < 1 or top_k < 1:
        raise ValueError("samples/top_k must be positive")
    total = math.comb(spec.pool_size, spec.pick_count)
    if exhaustive or total <= samples:
        iterator = combinations(range(1, spec.pool_size + 1), spec.pick_count)
    else:
        rng = random.Random(seed)
        seen: set[tuple[int, ...]] = set()
        target = min(samples, total)

        def sampled():
            while len(seen) < target:
                values = tuple(sorted(rng.sample(range(1, spec.pool_size + 1), spec.pick_count)))
                if values not in seen:
                    seen.add(values)
                    yield values

        iterator = sampled()

    heap: list[tuple[float, tuple[int, ...], SelectionScore]] = []
    for values in iterator:
        result = score_selection(
            values,
            spec,
            popular_combinations=popular_combinations,
            popularity_weight=popularity_weight,
        )
        if not result.guardrails_passed:
            continue
        entry = (result.score, tuple(-value for value in result.numbers), result)
        if len(heap) < top_k:
            heapq.heappush(heap, entry)
        elif entry[:2] > heap[0][:2]:
            heapq.heapreplace(heap, entry)
    return [entry[2] for entry in sorted(heap, key=lambda item: (item[0], item[1]), reverse=True)]


def diversify_selections(candidates: Sequence[SelectionScore], *, count: int, overlap_weight: float = 0.40) -> list[SelectionScore]:
    """Greedy maximum-marginal-relevance portfolio for users buying >1 chosen line."""
    if count < 1:
        raise ValueError("count must be positive")
    chosen: list[SelectionScore] = []
    remaining = list(candidates)
    while remaining and len(chosen) < count:
        def utility(candidate: SelectionScore) -> tuple[float, tuple[int, ...]]:
            if not chosen:
                overlap = 0.0
            else:
                overlap = max(
                    len(set(candidate.numbers).intersection(item.numbers)) / len(candidate.numbers)
                    for item in chosen
                )
            return candidate.score - overlap_weight * overlap, tuple(-n for n in candidate.numbers)
        best = max(remaining, key=utility)
        chosen.append(best)
        remaining.remove(best)
    return chosen
