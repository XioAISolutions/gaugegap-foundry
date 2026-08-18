"""Verification-first lottery diagnostics and anti-crowd heuristics.

Historical anomalies, holdout prediction tests, and player-choice sharing-risk
heuristics are kept separate. Only corrected later-draw holdouts may open the
predictive gate; anti-crowd scores never change draw probability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from itertools import combinations
import heapq
import json
import math
import random
from typing import Iterable, Mapping, Sequence

import numpy as np

CLAIM_BOUNDARY = (
    "Finite historical diagnostics only. No reported pattern, score, rank, temporal mode, "
    "or anti-crowd heuristic changes the draw probability of a valid combination in a fair "
    "lottery. Predictive evidence requires a pre-declared rule to beat a chance null on later "
    "unseen draws after correction for the tested model/window family. Anti-crowd scores are "
    "sharing-risk heuristics; measured OLG top-combination counts cover only the combinations "
    "OLG publishes and are not a complete model of player choices."
)


@dataclass(frozen=True)
class LotterySpec:
    name: str = "lotto-6of49"
    pool_size: int = 49
    pick_count: int = 6

    def validate(self) -> None:
        if self.pool_size < 2 or not 1 <= self.pick_count < self.pool_size:
            raise ValueError("invalid lottery specification")


@dataclass(frozen=True)
class Draw:
    numbers: tuple[int, ...]
    draw_date: str | None = None
    bonus: int | None = None

    @classmethod
    def from_numbers(cls, numbers: Iterable[int], draw_date=None, bonus=None) -> "Draw":
        return cls(
            tuple(sorted(map(int, numbers))),
            None if draw_date is None else str(draw_date),
            None if bonus is None else int(bonus),
        )


@dataclass(frozen=True)
class NullResult:
    statistic: float
    null_mean: float
    null_std: float
    empirical_p_value: float
    trials: int
    alternative: str
    seed: int

    def summary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BacktestResult:
    model: str
    window: int
    evaluated_draws: int
    total_hits: int
    mean_hits: float
    chance_mean_hits: float
    empirical_p_value: float
    adjusted_p_value_bonferroni: float
    trials: int
    seed: int

    def summary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateScore:
    numbers: tuple[int, ...]
    anti_crowd_score: float
    measured_popularity_penalty: float
    historical_neutrality_score: float
    combined_score: float
    features: Mapping[str, float]

    def summary(self) -> dict[str, object]:
        data = asdict(self)
        data["numbers"] = list(self.numbers)
        data["features"] = dict(self.features)
        return data


def validate_draws(draws: Sequence[Draw], spec: LotterySpec) -> tuple[Draw, ...]:
    spec.validate()
    if len(draws) < 3:
        raise ValueError("at least three draws are required")
    out: list[Draw] = []
    seen_dates: set[str] = set()
    for index, draw in enumerate(draws):
        numbers = tuple(sorted(map(int, draw.numbers)))
        if len(numbers) != spec.pick_count or len(set(numbers)) != len(numbers):
            raise ValueError(f"draw {index} has invalid number count/duplicates")
        if numbers[0] < 1 or numbers[-1] > spec.pool_size:
            raise ValueError(f"draw {index} outside valid range")
        if draw.bonus is not None and (
            not 1 <= int(draw.bonus) <= spec.pool_size or int(draw.bonus) in numbers
        ):
            raise ValueError(f"draw {index} has invalid bonus")
        if draw.draw_date:
            if draw.draw_date in seen_dates:
                raise ValueError(f"duplicate draw date: {draw.draw_date}")
            seen_dates.add(draw.draw_date)
        out.append(Draw(numbers, draw.draw_date, draw.bonus))
    return tuple(out)


def draws_digest(draws: Sequence[Draw], spec: LotterySpec) -> str:
    body = {
        "game": asdict(spec),
        "draws": [
            {"date": draw.draw_date, "numbers": list(draw.numbers), "bonus": draw.bonus}
            for draw in draws
        ],
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(canonical.encode()).hexdigest()


def encode_draws(draws: Sequence[Draw], spec: LotterySpec) -> np.ndarray:
    draws = validate_draws(draws, spec)
    encoded = np.zeros((len(draws), spec.pool_size), dtype=float)
    for row, draw in enumerate(draws):
        encoded[row, np.asarray(draw.numbers) - 1] = 1.0
    return encoded


def fibonacci_numbers(limit: int) -> tuple[int, ...]:
    if limit < 1:
        return ()
    values = [1, 2]
    while values[-1] + values[-2] <= limit:
        values.append(values[-1] + values[-2])
    return tuple(value for value in values if value <= limit)


def number_frequency_records(draws: Sequence[Draw], spec: LotterySpec) -> list[dict[str, float | int]]:
    counts = encode_draws(draws, spec).sum(0)
    p = spec.pick_count / spec.pool_size
    expected = len(draws) * p
    std = math.sqrt(len(draws) * p * (1 - p)) or 1.0
    return [
        {"number": i + 1, "count": int(count), "expected": float(expected), "z_score": float((count - expected) / std)}
        for i, count in enumerate(counts)
    ]


def _random_draw(rng: random.Random, spec: LotterySpec) -> tuple[int, ...]:
    return tuple(sorted(rng.sample(range(1, spec.pool_size + 1), spec.pick_count)))


def subset_occurrence_test(draws, subset, spec, *, trials=5000, seed=0) -> NullResult:
    draws = validate_draws(draws, spec)
    subset = frozenset(map(int, subset))
    if not subset or trials < 1 or any(n < 1 or n > spec.pool_size for n in subset):
        raise ValueError("invalid subset/trials")
    observed = sum(len(subset.intersection(draw.numbers)) for draw in draws)
    rng = random.Random(seed)
    null = np.asarray([
        sum(len(subset.intersection(_random_draw(rng, spec))) for _ in draws)
        for _ in range(trials)
    ], dtype=float)
    mean = float(null.mean())
    distance = abs(observed - mean)
    extreme = int(np.count_nonzero(np.abs(null - mean) >= distance - 1e-12))
    return NullResult(float(observed), mean, float(null.std(ddof=1)) if trials > 1 else 0.0, (extreme + 1) / (trials + 1), trials, "two-sided", seed)


def _binomial_upper(n: int, p: float, k0: int) -> float:
    return min(1.0, math.fsum(math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(max(0, k0), n + 1)))


def _bh(p_values: Sequence[float]) -> list[float]:
    count = len(p_values)
    order = sorted(range(count), key=lambda i: p_values[i])
    q = [1.0] * count
    running = 1.0
    for reverse_rank in range(count - 1, -1, -1):
        index = order[reverse_rank]
        running = min(running, p_values[index] * count / (reverse_rank + 1), 1.0)
        q[index] = running
    return q


def pair_anomalies(draws, spec, *, top_n=20) -> list[dict[str, object]]:
    draws = validate_draws(draws, spec)
    pairs = list(combinations(range(1, spec.pool_size + 1), 2))
    counts = {pair: 0 for pair in pairs}
    for draw in draws:
        for pair in combinations(draw.numbers, 2):
            counts[pair] += 1
    p_pair = spec.pick_count * (spec.pick_count - 1) / (spec.pool_size * (spec.pool_size - 1))
    p_values = [_binomial_upper(len(draws), p_pair, counts[pair]) for pair in pairs]
    q_values = _bh(p_values)
    rows = [
        {"pair": list(pair), "count": counts[pair], "expected": len(draws) * p_pair, "p_value_upper": p_values[i], "q_value_bh": q_values[i]}
        for i, pair in enumerate(pairs)
    ]
    rows.sort(key=lambda row: (row["q_value_bh"], row["p_value_upper"], -row["count"], row["pair"]))
    return rows[: max(1, top_n)]


def _lag1_max(encoded: np.ndarray) -> float:
    values = []
    for column in range(encoded.shape[1]):
        before, after = encoded[:-1, column], encoded[1:, column]
        values.append(0.0 if np.std(before) == 0 or np.std(after) == 0 else abs(float(np.corrcoef(before, after)[0, 1])))
    return max(values, default=0.0)


def temporal_order_test(draws, spec, *, trials=2000, seed=0) -> NullResult:
    encoded = encode_draws(draws, spec)
    if trials < 1:
        raise ValueError("trials must be positive")
    observed = _lag1_max(encoded)
    rng = np.random.default_rng(seed)
    null = np.asarray([_lag1_max(encoded[rng.permutation(len(encoded))]) for _ in range(trials)], dtype=float)
    p_value = (int(np.count_nonzero(null >= observed - 1e-12)) + 1) / (trials + 1)
    return NullResult(observed, float(null.mean()), float(null.std(ddof=1)) if trials > 1 else 0.0, p_value, trials, "greater", seed)


def dmd_temporal_order_test(draws, spec, *, trials=128, seed=0, rank=12) -> dict[str, object]:
    from gaugegap.koopman import dominant_modes, exact_dmd

    encoded = encode_draws(draws, spec)
    if trials < 1:
        raise ValueError("trials must be positive")
    rank = max(1, min(rank, len(encoded) - 1, encoded.shape[1]))
    observed = exact_dmd(encoded, dt=1.0, rank=rank)
    rng = np.random.default_rng(seed)
    null = np.asarray([
        exact_dmd(encoded[rng.permutation(len(encoded))], dt=1.0, rank=rank).reconstruction_error
        for _ in range(trials)
    ], dtype=float)
    p_value = (int(np.count_nonzero(null <= observed.reconstruction_error + 1e-12)) + 1) / (trials + 1)
    return {
        "rank": rank,
        "observed_reconstruction_error": float(observed.reconstruction_error),
        "observed_spectral_radius": float(observed.spectral_radius),
        "dominant_modes": dominant_modes(observed, count=min(8, rank)),
        "null_mean_reconstruction_error": float(null.mean()),
        "null_std_reconstruction_error": float(null.std(ddof=1)) if trials > 1 else 0.0,
        "empirical_p_value_lower_error": p_value,
        "trials": trials,
        "seed": seed,
        "claim_boundary": "Finite sampled DMD diagnostic only; lower error than shuffled order is exploratory structure, not prospective prediction.",
    }


def _predict(history, spec, model) -> tuple[int, ...]:
    encoded = encode_draws(history, spec)
    counts = encoded.sum(0)
    if model == "frequency":
        score = counts
    elif model == "cold-frequency":
        score = -counts
    else:
        gaps = np.zeros(spec.pool_size)
        for column in range(spec.pool_size):
            hits = np.flatnonzero(encoded[:, column])
            gaps[column] = len(history) if not hits.size else len(history) - 1 - int(hits[-1])
        if model == "recency":
            score = gaps
        elif model == "hybrid":
            score = (counts - counts.mean()) / max(float(counts.std()), 1e-12) + 0.25 * (gaps - gaps.mean()) / max(float(gaps.std()), 1e-12)
        else:
            raise ValueError(f"unknown model: {model}")
    order = sorted(range(spec.pool_size), key=lambda i: (-float(score[i]), i + 1))
    return tuple(sorted(i + 1 for i in order[: spec.pick_count]))


def rolling_backtest(draws, spec, *, model, window=52, trials=5000, seed=0, family_size=1) -> BacktestResult:
    draws = validate_draws(draws, spec)
    if window < 3 or window >= len(draws) or trials < 1 or family_size < 1:
        raise ValueError("invalid backtest settings")
    hits = [
        len(set(_predict(draws[i - window : i], spec, model)).intersection(draws[i].numbers))
        for i in range(window, len(draws))
    ]
    observed = sum(hits)
    actual = [set(draw.numbers) for draw in draws[window:]]
    rng = random.Random(seed)
    null = [
        sum(len(set(_random_draw(rng, spec)).intersection(target)) for target in actual)
        for _ in range(trials)
    ]
    raw_p = (sum(value >= observed for value in null) + 1) / (trials + 1)
    return BacktestResult(
        model, window, len(hits), observed, float(np.mean(hits)), spec.pick_count**2 / spec.pool_size,
        raw_p, min(1.0, raw_p * family_size), trials, seed,
    )


def _progressions(numbers: Sequence[int]) -> int:
    chosen = set(numbers)
    return sum(1 for a, b in combinations(sorted(numbers), 2) if 2 * b - a in chosen and 2 * b - a > b)


def combination_features(numbers, spec) -> dict[str, float]:
    values = tuple(sorted(map(int, numbers)))
    if len(values) != spec.pick_count or len(set(values)) != len(values) or values[0] < 1 or values[-1] > spec.pool_size:
        raise ValueError("invalid combination")
    chosen = set(values)
    fibonacci = set(fibonacci_numbers(spec.pool_size))
    return {
        "birthday_count": float(sum(value <= 31 for value in values)),
        "fibonacci_count": float(sum(value in fibonacci for value in values)),
        "lucky_count": float(sum(value in {7, 11, 13} for value in values)),
        "round_count": float(sum(value % 5 == 0 for value in values)),
        "consecutive_pairs": float(sum(value + 1 in chosen for value in values)),
        "three_term_progressions": float(_progressions(values)),
        "same_last_digit_pairs": float(sum(a % 10 == b % 10 for a, b in combinations(values, 2))),
        "all_above_31": float(all(value > 31 for value in values)),
        "sum": float(sum(values)),
        "odd_count": float(sum(value % 2 for value in values)),
        "range": float(values[-1] - values[0]),
    }


def anti_crowd_proxy(numbers, spec) -> tuple[float, dict[str, float]]:
    features = combination_features(numbers, spec)
    penalty = (
        0.55 * features["birthday_count"] + 0.80 * features["fibonacci_count"]
        + 0.50 * features["lucky_count"] + 0.15 * features["round_count"]
        + 0.75 * features["three_term_progressions"] + 0.20 * features["same_last_digit_pairs"]
        + 0.80 * features["all_above_31"] - 0.10 * min(features["consecutive_pairs"], 1.0)
    )
    return -float(penalty), features


def historical_neutrality_score(numbers, frequency_records) -> float:
    z = {int(row["number"]): float(row["z_score"]) for row in frequency_records}
    return -float(np.mean([abs(z[int(number)]) for number in numbers]))


def measured_popularity_penalty(numbers, popular_combinations, spec) -> float:
    if not popular_combinations:
        return 0.0
    chosen = set(numbers)
    return max(
        math.log1p(max(0, int(plays))) * (len(chosen.intersection(combo)) / spec.pick_count) ** 4
        for combo, plays in popular_combinations.items()
    )


def score_candidate(numbers, spec, frequency_records, *, neutrality_weight=0.0, popular_combinations=None, popularity_weight=0.35) -> CandidateScore:
    combo = tuple(sorted(map(int, numbers)))
    anti, features = anti_crowd_proxy(combo, spec)
    neutrality = historical_neutrality_score(combo, frequency_records)
    measured = measured_popularity_penalty(combo, popular_combinations, spec)
    return CandidateScore(combo, anti, measured, neutrality, anti + neutrality_weight * neutrality - popularity_weight * measured, features)


def search_candidates(draws, spec, *, top_k=10, samples=200000, seed=0, exhaustive=False, neutrality_weight=0.0, popular_combinations=None, popularity_weight=0.35) -> list[CandidateScore]:
    draws = validate_draws(draws, spec)
    if top_k < 1 or samples < 1:
        raise ValueError("top_k/samples must be positive")
    records = number_frequency_records(draws, spec)
    heap = []
    if exhaustive:
        iterator = combinations(range(1, spec.pool_size + 1), spec.pick_count)
    else:
        rng = random.Random(seed)
        seen = set()
        target = min(samples, math.comb(spec.pool_size, spec.pick_count))

        def sampled():
            while len(seen) < target:
                combo = _random_draw(rng, spec)
                if combo not in seen:
                    seen.add(combo)
                    yield combo

        iterator = sampled()
    for combo in iterator:
        result = score_candidate(combo, spec, records, neutrality_weight=neutrality_weight, popular_combinations=popular_combinations, popularity_weight=popularity_weight)
        entry = (result.combined_score, tuple(-number for number in result.numbers), result)
        if len(heap) < top_k:
            heapq.heappush(heap, entry)
        elif entry[:2] > heap[0][:2]:
            heapq.heapreplace(heap, entry)
    return [entry[2] for entry in sorted(heap, key=lambda item: (item[0], item[1]), reverse=True)]


def generate_synthetic_draws(spec, *, count=220, seed=649) -> tuple[Draw, ...]:
    if count < 3:
        raise ValueError("count must be at least three")
    rng = random.Random(seed)
    return tuple(Draw(_random_draw(rng, spec)) for _ in range(count))


def analyse(
    draws, spec, *, null_trials=2000, candidate_samples=100000, candidate_top_k=10, seed=649,
    backtest_windows=(26, 52, 104), dmd_trials=None, popular_combinations=None,
    candidate_exhaustive=False, neutrality_weight=0.0, popularity_weight=0.35,
    reference_combinations=(),
) -> dict[str, object]:
    draws = validate_draws(draws, spec)
    frequencies = number_frequency_records(draws, spec)
    fibonacci = fibonacci_numbers(spec.pool_size)
    fib_test = subset_occurrence_test(draws, fibonacci, spec, trials=null_trials, seed=seed)
    temporal = temporal_order_test(draws, spec, trials=null_trials, seed=seed + 1)
    dmd = dmd_temporal_order_test(draws, spec, trials=min(128, null_trials) if dmd_trials is None else dmd_trials, seed=seed + 3)
    pairs = pair_anomalies(draws, spec)
    models = ("frequency", "cold-frequency", "recency", "hybrid")
    windows = tuple(window for window in backtest_windows if window < len(draws))
    family_size = max(1, len(models) * len(windows))
    backtests = [
        rolling_backtest(draws, spec, model=model, window=window, trials=null_trials, seed=seed + 10000 + window * 10 + model_index, family_size=family_size).summary()
        for window in windows for model_index, model in enumerate(models)
    ]
    candidates = search_candidates(
        draws, spec, top_k=candidate_top_k, samples=candidate_samples, seed=seed + 2,
        exhaustive=candidate_exhaustive, neutrality_weight=neutrality_weight,
        popular_combinations=popular_combinations, popularity_weight=popularity_weight,
    )
    references = [
        score_candidate(combo, spec, frequencies, neutrality_weight=neutrality_weight, popular_combinations=popular_combinations, popularity_weight=popularity_weight).summary()
        for combo in reference_combinations
    ]
    gate = any(row["adjusted_p_value_bonferroni"] < 0.01 and row["mean_hits"] > row["chance_mean_hits"] for row in backtests)
    return {
        "schema": "gaugegap.lottery_forge.analysis.v2",
        "game": asdict(spec), "draw_count": len(draws), "draws_sha256": draws_digest(draws, spec),
        "claim_boundary": CLAIM_BOUNDARY, "frequency_records": frequencies,
        "fibonacci": {"numbers": list(fibonacci), "null_test": fib_test.summary(), "interpretation": "Exploratory historical statistic only. It is not a prediction rule."},
        "pair_anomalies": pairs, "pairs_surviving_bh_0_05": [row for row in pairs if row["q_value_bh"] < 0.05],
        "temporal_order": temporal.summary(), "dmd_temporal_order": dmd,
        "rolling_backtests": backtests,
        "predictive_evidence_gate": {"threshold": "Bonferroni-adjusted empirical p < 0.01 and mean hits > exact chance mean on strict later-draw holdouts", "family_size": family_size, "passed": bool(gate)},
        "candidate_search": {
            "objective": "anti-crowd behavioural proxy plus optional measured OLG top-combination overlap; historical neutrality weight defaults to zero; NOT draw probability",
            "measured_popular_combinations_count": len(popular_combinations or {}),
            "sample_count": math.comb(spec.pool_size, spec.pick_count) if candidate_exhaustive else min(candidate_samples, math.comb(spec.pool_size, spec.pick_count)),
            "exhaustive": bool(candidate_exhaustive), "neutrality_weight": float(neutrality_weight), "popularity_weight": float(popularity_weight),
            "top": [candidate.summary() for candidate in candidates], "references": references,
        },
    }


def make_proofpack(analysis: Mapping[str, object]) -> dict[str, object]:
    payload = dict(analysis)
    payload["proofpack_schema"] = "gaugegap.lottery_forge.proofpack.v2"
    payload["claim_boundary"] = CLAIM_BOUNDARY
    payload.pop("result_hash", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload["result_hash"] = sha256(canonical.encode()).hexdigest()
    return payload


def verify_proofpack(payload: Mapping[str, object]) -> bool:
    if payload.get("proofpack_schema") != "gaugegap.lottery_forge.proofpack.v2" or payload.get("claim_boundary") != CLAIM_BOUNDARY:
        return False
    expected = payload.get("result_hash")
    body = dict(payload)
    body.pop("result_hash", None)
    try:
        actual = sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError):
        return False
    return isinstance(expected, str) and expected == actual
