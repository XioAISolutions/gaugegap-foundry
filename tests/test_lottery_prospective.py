import copy
from datetime import date, timedelta
import random

from gaugegap.lottery_forge import Draw, LotterySpec
from gaugegap.lottery_prospective import (
    PROTOCOL_SCHEMA,
    evaluate_scores,
    exact_total_hits_upper_tail,
    make_prediction,
    next_scheduled_draw_date,
    score_prediction,
    single_draw_hit_distribution,
    verify_prediction,
    verify_score,
)


def protocol():
    return {
        "schema": PROTOCOL_SCHEMA,
        "protocol_id": "test-protocol",
        "game": {"name": "lotto-6of49", "pool_size": 49, "pick_count": 6},
        "prediction_rule": {"model": "hybrid", "window": 20},
        "draw_weekdays": [2, 5],
        "decision_checkpoints": [2, 4, 6],
        "family_wise_alpha": 0.01,
    }


def dated_draws(count=30, seed=7):
    rng = random.Random(seed)
    start = date(2026, 1, 1)
    out = []
    for index in range(count):
        numbers = tuple(sorted(rng.sample(range(1, 50), 6)))
        out.append(Draw(numbers, (start + timedelta(days=index)).isoformat()))
    return tuple(out)


def test_next_draw_schedule():
    assert next_scheduled_draw_date("2026-08-15", [2, 5]) == "2026-08-19"
    assert next_scheduled_draw_date("2026-08-19", [2, 5]) == "2026-08-22"


def test_prediction_is_deterministic_and_tamper_evident():
    spec = LotterySpec()
    draws = dated_draws()
    prediction = make_prediction(
        draws, spec, protocol(), target_draw_date="2026-02-04", sealed_on_date="2026-01-31"
    )
    same = make_prediction(
        draws, spec, protocol(), target_draw_date="2026-02-04", sealed_on_date="2026-01-31"
    )
    assert prediction == same
    assert verify_prediction(prediction, protocol())
    tampered = copy.deepcopy(prediction)
    tampered["predicted_numbers"][0] = 49 if tampered["predicted_numbers"][0] != 49 else 48
    assert not verify_prediction(tampered, protocol())


def test_prediction_refuses_same_day_or_known_outcome():
    spec = LotterySpec()
    draws = dated_draws()
    latest = draws[-1].draw_date
    try:
        make_prediction(draws, spec, protocol(), target_draw_date=latest, sealed_on_date="2026-01-01")
        assert False, "expected known outcome rejection"
    except ValueError:
        pass
    try:
        make_prediction(draws, spec, protocol(), target_draw_date="2026-02-04", sealed_on_date="2026-02-04")
        assert False, "expected same-day seal rejection"
    except ValueError:
        pass


def test_score_and_verify():
    spec = LotterySpec()
    draws = dated_draws()
    prediction = make_prediction(draws, spec, protocol(), target_draw_date="2026-02-04", sealed_on_date="2026-01-31")
    bonus = next(value for value in range(1, 50) if value not in prediction["predicted_numbers"])
    actual = Draw.from_numbers(prediction["predicted_numbers"], draw_date="2026-02-04", bonus=bonus)
    score = score_prediction(prediction, actual, protocol())
    assert score["hits"] == 6
    assert verify_score(score, protocol())


def test_exact_null_distribution_and_checkpoint_evaluation():
    spec = LotterySpec()
    distribution = single_draw_hit_distribution(spec)
    assert abs(sum(distribution) - 1.0) < 1e-12
    assert exact_total_hits_upper_tail(0, 1, spec) == 1.0

    rows = []
    for target, seed in (("2026-02-04", 20), ("2026-02-07", 21)):
        pred = make_prediction(
            dated_draws(seed=seed), spec, protocol(),
            target_draw_date=target, sealed_on_date="2026-01-31",
        )
        bonus = next(value for value in range(1, 50) if value not in pred["predicted_numbers"])
        actual = Draw.from_numbers(pred["predicted_numbers"], draw_date=target, bonus=bonus)
        rows.append(score_prediction(pred, actual, protocol()))

    evaluation = evaluate_scores(rows, spec, protocol())
    assert evaluation["scored_draws"] == 2
    assert evaluation["decision_checkpoints"][0]["draw_count"] == 2
    assert evaluation["decision_checkpoints"][0]["passed"]
