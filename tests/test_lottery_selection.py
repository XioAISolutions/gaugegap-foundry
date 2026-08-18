from gaugegap.lottery_selection import (
    SelectionSpec,
    combination_features,
    measured_popularity_penalty,
    score_selection,
    search_selections,
    shape_guardrails,
)


def test_guardrails_block_all_high_optimizer_artifact():
    spec = SelectionSpec("649", 49, 6)
    assert not shape_guardrails((32, 37, 41, 43, 47, 49), spec)
    assert shape_guardrails((9, 32, 37, 39, 43, 47), spec)


def test_measured_popularity_penalty_prefers_less_overlap():
    popular = {(1, 2, 3, 4, 5, 6): 30000}
    exact = measured_popularity_penalty((1, 2, 3, 4, 5, 6), popular)
    partial = measured_popularity_penalty((1, 8, 17, 33, 41, 49), popular)
    assert exact > partial


def test_long_run_penalty_only_starts_at_three():
    spec = SelectionSpec("649", 49, 6)
    pair = score_selection((9, 32, 33, 38, 41, 47), spec)
    run = score_selection((9, 32, 33, 34, 41, 47), spec)
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
    features = combination_features((4, 32, 33, 37, 49), spec)
    assert features["birthday_count"] == 1
    assert features["longest_consecutive_run"] == 2
    assert features["quartiles_occupied"] >= 3
