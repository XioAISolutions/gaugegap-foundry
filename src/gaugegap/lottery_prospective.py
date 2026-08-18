"""Prospective, pre-registered validation for Lottery Forge.

This module exists to prevent retrospective tuning from being mistaken for
prediction. A protocol fixes the rule and decision checkpoints before future
outcomes are observed. Prediction artifacts are content-hashed and are intended
to be committed to an append-only Git branch before the target draw.
"""
from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
import json
import math
from typing import Mapping, Sequence

from gaugegap.lottery_forge import Draw, LotterySpec, _predict, draws_digest, validate_draws

PROTOCOL_SCHEMA = "gaugegap.lottery_forge.prospective_protocol.v1"
PREDICTION_SCHEMA = "gaugegap.lottery_forge.prospective_prediction.v1"
SCORE_SCHEMA = "gaugegap.lottery_forge.prospective_score.v1"
EVALUATION_SCHEMA = "gaugegap.lottery_forge.prospective_evaluation.v1"

PROSPECTIVE_CLAIM_BOUNDARY = (
    "A prospective prediction is evidence only if it was sealed before the target draw, "
    "the protocol and model parameters were fixed in advance, and a pre-declared checkpoint "
    "passes its family-wise corrected threshold. Individual hits, near-misses, interim p-values, "
    "or anti-crowd rankings do not establish predictive power."
)


def _canonical(value: Mapping[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def object_digest(value: Mapping[str, object]) -> str:
    return sha256(_canonical(value).encode()).hexdigest()


def protocol_digest(protocol: Mapping[str, object]) -> str:
    validate_protocol(protocol)
    return object_digest(dict(protocol))


def validate_protocol(protocol: Mapping[str, object]) -> None:
    if protocol.get("schema") != PROTOCOL_SCHEMA:
        raise ValueError("unsupported prospective protocol schema")
    rule = protocol.get("prediction_rule")
    if not isinstance(rule, Mapping):
        raise ValueError("protocol prediction_rule is missing")
    if rule.get("model") not in {"frequency", "cold-frequency", "recency", "hybrid"}:
        raise ValueError("unsupported prospective model")
    window = int(rule.get("window", 0))
    if window < 3:
        raise ValueError("prospective window must be at least 3")
    checkpoints = protocol.get("decision_checkpoints")
    if not isinstance(checkpoints, Sequence) or isinstance(checkpoints, (str, bytes)):
        raise ValueError("decision_checkpoints must be a sequence")
    normalized = tuple(int(value) for value in checkpoints)
    if not normalized or normalized != tuple(sorted(set(normalized))) or normalized[0] < 1:
        raise ValueError("decision checkpoints must be positive, unique, and increasing")
    alpha = float(protocol.get("family_wise_alpha", 0.0))
    if not 0.0 < alpha < 1.0:
        raise ValueError("family_wise_alpha must be between 0 and 1")
    weekdays = tuple(int(value) for value in protocol.get("draw_weekdays", ()))
    if not weekdays or any(value < 0 or value > 6 for value in weekdays):
        raise ValueError("draw_weekdays must contain Python weekday integers")


def next_scheduled_draw_date(latest_draw_date: str, draw_weekdays: Sequence[int]) -> str:
    current = date.fromisoformat(latest_draw_date) + timedelta(days=1)
    allowed = set(int(value) for value in draw_weekdays)
    for _ in range(8):
        if current.weekday() in allowed:
            return current.isoformat()
        current += timedelta(days=1)
    raise ValueError("could not resolve next scheduled draw date")


def make_prediction(
    draws: Sequence[Draw],
    spec: LotterySpec,
    protocol: Mapping[str, object],
    *,
    target_draw_date: str | None = None,
    sealed_on_date: str,
    source_snapshot: Mapping[str, object] | None = None,
) -> dict[str, object]:
    validate_protocol(protocol)
    validated = validate_draws(draws, spec)
    if any(draw.draw_date is None for draw in validated):
        raise ValueError("prospective prediction requires dated training draws")
    ordered = tuple(sorted(validated, key=lambda draw: str(draw.draw_date)))
    latest = date.fromisoformat(str(ordered[-1].draw_date))
    seal_date = date.fromisoformat(sealed_on_date)
    rule = protocol["prediction_rule"]
    window = int(rule["window"])
    model = str(rule["model"])
    if len(ordered) < window:
        raise ValueError("not enough historical draws for the frozen prospective window")
    if target_draw_date is None:
        target_draw_date = next_scheduled_draw_date(latest.isoformat(), protocol["draw_weekdays"])
    target = date.fromisoformat(target_draw_date)
    if target <= latest:
        raise ValueError("target draw already exists in the training data")
    if target <= seal_date:
        raise ValueError("target draw must be after the local seal date")
    if target.weekday() not in set(int(value) for value in protocol["draw_weekdays"]):
        raise ValueError("target date is not a scheduled draw weekday under the protocol")

    training_window = ordered[-window:]
    predicted = _predict(training_window, spec, model)
    body: dict[str, object] = {
        "schema": PREDICTION_SCHEMA,
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": protocol_digest(protocol),
        "game": {"name": spec.name, "pool_size": spec.pool_size, "pick_count": spec.pick_count},
        "target_draw_date": target.isoformat(),
        "sealed_on_date": seal_date.isoformat(),
        "prediction_rule": {"model": model, "window": window},
        "predicted_numbers": list(predicted),
        "training": {
            "latest_draw_date": latest.isoformat(),
            "window_first_draw_date": training_window[0].draw_date,
            "window_draw_count": len(training_window),
            "window_draws_sha256": draws_digest(training_window, spec),
            "all_draw_count": len(ordered),
            "all_draws_sha256": draws_digest(ordered, spec),
        },
        "source_snapshot": dict(source_snapshot or {}),
        "claim_boundary": PROSPECTIVE_CLAIM_BOUNDARY,
    }
    body["prediction_hash"] = object_digest(body)
    return body


def verify_prediction(prediction: Mapping[str, object], protocol: Mapping[str, object]) -> bool:
    try:
        validate_protocol(protocol)
        if prediction.get("schema") != PREDICTION_SCHEMA:
            return False
        if prediction.get("protocol_id") != protocol.get("protocol_id"):
            return False
        if prediction.get("protocol_sha256") != protocol_digest(protocol):
            return False
        expected = prediction.get("prediction_hash")
        body = dict(prediction)
        body.pop("prediction_hash", None)
        if not isinstance(expected, str) or expected != object_digest(body):
            return False
        numbers = tuple(int(value) for value in prediction["predicted_numbers"])
        game = prediction["game"]
        spec = LotterySpec(str(game["name"]), int(game["pool_size"]), int(game["pick_count"]))
        if len(numbers) != spec.pick_count or len(set(numbers)) != spec.pick_count:
            return False
        if min(numbers) < 1 or max(numbers) > spec.pool_size:
            return False
        target = date.fromisoformat(str(prediction["target_draw_date"]))
        sealed = date.fromisoformat(str(prediction["sealed_on_date"]))
        latest = date.fromisoformat(str(prediction["training"]["latest_draw_date"]))
        return target > sealed and target > latest
    except (KeyError, TypeError, ValueError):
        return False


def score_prediction(
    prediction: Mapping[str, object],
    actual_draw: Draw,
    protocol: Mapping[str, object],
) -> dict[str, object]:
    if not verify_prediction(prediction, protocol):
        raise ValueError("invalid prospective prediction")
    if actual_draw.draw_date != prediction["target_draw_date"]:
        raise ValueError("actual draw date does not match prediction target")
    game = prediction["game"]
    spec = LotterySpec(str(game["name"]), int(game["pool_size"]), int(game["pick_count"]))
    actual_numbers = tuple(sorted(map(int, actual_draw.numbers)))
    if len(actual_numbers) != spec.pick_count or len(set(actual_numbers)) != spec.pick_count:
        raise ValueError("actual draw has invalid number count/duplicates")
    if actual_numbers[0] < 1 or actual_numbers[-1] > spec.pool_size:
        raise ValueError("actual draw outside valid range")
    if actual_draw.bonus is not None and (
        not 1 <= int(actual_draw.bonus) <= spec.pool_size or int(actual_draw.bonus) in actual_numbers
    ):
        raise ValueError("actual draw has invalid bonus")
    actual = Draw(actual_numbers, actual_draw.draw_date, actual_draw.bonus)
    predicted = set(int(value) for value in prediction["predicted_numbers"])
    hits = len(predicted.intersection(actual.numbers))
    body: dict[str, object] = {
        "schema": SCORE_SCHEMA,
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": protocol_digest(protocol),
        "prediction_hash": prediction["prediction_hash"],
        "target_draw_date": actual.draw_date,
        "predicted_numbers": list(prediction["predicted_numbers"]),
        "actual_numbers": list(actual.numbers),
        "bonus": actual.bonus,
        "hits": hits,
        "claim_boundary": PROSPECTIVE_CLAIM_BOUNDARY,
    }
    body["score_hash"] = object_digest(body)
    return body


def verify_score(score: Mapping[str, object], protocol: Mapping[str, object]) -> bool:
    try:
        if score.get("schema") != SCORE_SCHEMA:
            return False
        if score.get("protocol_id") != protocol.get("protocol_id") or score.get("protocol_sha256") != protocol_digest(protocol):
            return False
        expected = score.get("score_hash")
        body = dict(score)
        body.pop("score_hash", None)
        if not isinstance(expected, str) or expected != object_digest(body):
            return False
        predicted_values = tuple(int(value) for value in score["predicted_numbers"])
        actual_values = tuple(int(value) for value in score["actual_numbers"])
        game = protocol["game"]
        spec = LotterySpec(str(game["name"]), int(game["pool_size"]), int(game["pick_count"]))
        if len(predicted_values) != spec.pick_count or len(set(predicted_values)) != spec.pick_count:
            return False
        if len(actual_values) != spec.pick_count or len(set(actual_values)) != spec.pick_count:
            return False
        if min(predicted_values + actual_values) < 1 or max(predicted_values + actual_values) > spec.pool_size:
            return False
        predicted = set(predicted_values)
        actual = set(actual_values)
        return int(score["hits"]) == len(predicted.intersection(actual))
    except (KeyError, TypeError, ValueError):
        return False


def single_draw_hit_distribution(spec: LotterySpec) -> tuple[float, ...]:
    spec.validate()
    denominator = math.comb(spec.pool_size, spec.pick_count)
    values = []
    for hits in range(spec.pick_count + 1):
        if hits > spec.pick_count or spec.pick_count - hits > spec.pool_size - spec.pick_count:
            values.append(0.0)
        else:
            values.append(
                math.comb(spec.pick_count, hits)
                * math.comb(spec.pool_size - spec.pick_count, spec.pick_count - hits)
                / denominator
            )
    return tuple(values)


def exact_total_hits_upper_tail(total_hits: int, draw_count: int, spec: LotterySpec) -> float:
    if draw_count < 1 or total_hits < 0:
        raise ValueError("draw_count must be positive and total_hits non-negative")
    one = single_draw_hit_distribution(spec)
    distribution = [1.0]
    for _ in range(draw_count):
        updated = [0.0] * (len(distribution) + spec.pick_count)
        for left_index, left_probability in enumerate(distribution):
            for right_index, right_probability in enumerate(one):
                updated[left_index + right_index] += left_probability * right_probability
        distribution = updated
    if total_hits >= len(distribution):
        return 0.0
    return min(1.0, math.fsum(distribution[total_hits:]))


def evaluate_scores(
    scores: Sequence[Mapping[str, object]],
    spec: LotterySpec,
    protocol: Mapping[str, object],
) -> dict[str, object]:
    validate_protocol(protocol)
    valid_scores = []
    seen_dates: set[str] = set()
    for score in scores:
        if not verify_score(score, protocol):
            raise ValueError("invalid score record")
        target = str(score["target_draw_date"])
        if target in seen_dates:
            raise ValueError(f"duplicate scored target date: {target}")
        seen_dates.add(target)
        valid_scores.append(dict(score))
    valid_scores.sort(key=lambda row: str(row["target_draw_date"]))
    checkpoints = tuple(int(value) for value in protocol["decision_checkpoints"])
    family_size = len(checkpoints)
    alpha = float(protocol["family_wise_alpha"])
    checkpoint_rows = []
    for checkpoint in checkpoints:
        if len(valid_scores) < checkpoint:
            continue
        subset = valid_scores[:checkpoint]
        total_hits = sum(int(row["hits"]) for row in subset)
        raw_p = exact_total_hits_upper_tail(total_hits, checkpoint, spec)
        adjusted = min(1.0, raw_p * family_size)
        mean_hits = total_hits / checkpoint
        chance = spec.pick_count**2 / spec.pool_size
        checkpoint_rows.append({
            "draw_count": checkpoint,
            "total_hits": total_hits,
            "mean_hits": mean_hits,
            "chance_mean_hits": chance,
            "raw_exact_upper_tail_p": raw_p,
            "bonferroni_adjusted_p": adjusted,
            "passed": bool(adjusted < alpha and mean_hits > chance),
        })
    current_total_hits = sum(int(row["hits"]) for row in valid_scores)
    current_raw_p = (
        exact_total_hits_upper_tail(current_total_hits, len(valid_scores), spec)
        if valid_scores else None
    )
    next_checkpoint = next((value for value in checkpoints if value > len(valid_scores)), None)
    return {
        "schema": EVALUATION_SCHEMA,
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": protocol_digest(protocol),
        "scored_draws": len(valid_scores),
        "current_total_hits": current_total_hits,
        "current_mean_hits": (current_total_hits / len(valid_scores)) if valid_scores else None,
        "chance_mean_hits": spec.pick_count**2 / spec.pool_size,
        "current_exact_upper_tail_p_descriptive_only": current_raw_p,
        "decision_checkpoints": checkpoint_rows,
        "next_checkpoint": next_checkpoint,
        "predictive_evidence_gate_passed": any(row["passed"] for row in checkpoint_rows),
        "claim_boundary": PROSPECTIVE_CLAIM_BOUNDARY,
    }
