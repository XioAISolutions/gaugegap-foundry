from gaugegap.lottery_selection import (
    SelectionSpec,
    combination_features,
    measured_popularity_penalty,
    score_selection,
    search_selections,
    shape_guardrails,
)


def test_guardrails_block_high_tail_optimizer_artifact():
    spec = SelectionSpec("649", 49, 6)
    assert not shape_guardrails((32, 37, 41, 43, 47, 49), spec)
    assert not shape_guardrails((9, 32, 37, 39, 43, 47), spec)
    assert shape_guardrails((9, 27, 33, 38, 43, 47), spec)


def test_daily_grand_caps_unsupported_high_tail_concentration():
    spec = SelectionSpec("daily-grand", 49, 5)
    assert not shape_guardrails((4, 32, 33, 38, 47), spec)
    assert shape_guardrails((4, 26, 33, 38, 47), spec)


def test_measured_popularity_penalty_prefers_less_overlap():
    popular = {(1, 2, 3, 4, 5, 6): 30000}
    exact = measured_popularity_penalty((1, 2, 3, 4, 5, 6), popular)
    partial = measured_popularity_penalty((1, 8, 17, 33, 41, 49), popular)
    assert exact > partial


def test_birthday_penalty_saturates_near_fair_draw_expectation():
    spec = SelectionSpec("daily-grand", 49, 5)
    three_birthdays = score_selection((4, 19, 26, 38, 47), spec)
    four_birthdays = score_selection((4, 19, 26, 29, 47), spec)
    assert three_birthdays.components["birthday"] == 0
    assert four_birthdays.components["birthday"] > 0


def test_long_run_penalty_only_starts_at_three():
    spec = SelectionSpec("649", 49, 6)
    pair = score_selection((9, 27, 32, 33, 41, 47), spec)
    run = score_selection((9, 27, 32, 33, 34, 47), spec)
    assert pair.components["long_run"] == 0
    assert run.components["long_run"] > 0


def test_search_is_deterministic_and_robust():
    spec = SelectionSpec("max", 52, 7)
    popular = {(1, 2, 3, 4, 5, 6, 7): 44112}
    first = search_selections(spec, popular_combinations=popular, samples=5000, top_k=5, seed=42)
    second = search_selections(spec, popular_combinations=popular, samples=5000, top_k=5, seed=42)
    assert [row.numbers for row in first] == [row.numbers for row in second]
    assert all(row.guardrails_passed for row in first)


def test_features_expose_shape_not_prediction():
    spec = SelectionSpec("daily-grand", 49, 5)
    features = combination_features((4, 26, 33, 38, 47), spec)
    assert features["birthday_count"] == 2
    assert features["above_birthday_count"] == 3
    assert features["quartiles_occupied"] >= 3
