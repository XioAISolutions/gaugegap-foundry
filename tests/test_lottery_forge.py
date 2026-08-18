import copy

from gaugegap.lottery_forge import (
    LotterySpec,
    analyse,
    combination_features,
    fibonacci_numbers,
    generate_synthetic_draws,
    make_proofpack,
    number_frequency_records,
    rolling_backtest,
    score_candidate,
    validate_draws,
    verify_proofpack,
    Draw,
)


def test_fibonacci_6of49():
    assert fibonacci_numbers(49) == (1, 2, 3, 5, 8, 13, 21, 34)


def test_draw_validation_bonus_and_dates():
    spec = LotterySpec()
    draws = (
        Draw.from_numbers((1, 2, 3, 4, 5, 6), "2026-01-01", bonus=7),
        Draw.from_numbers((7, 8, 9, 10, 11, 12), "2026-01-03", bonus=13),
        Draw.from_numbers((13, 14, 15, 16, 17, 18), "2026-01-07", bonus=19),
    )
    normalized = validate_draws(draws, spec)
    assert len(normalized) == 3
    assert normalized[0].bonus == 7


def test_bonferroni_adjustment_never_smaller_than_raw():
    spec = LotterySpec()
    draws = generate_synthetic_draws(spec, count=90, seed=1)
    result = rolling_backtest(draws, spec, model="frequency", window=26, trials=200, seed=2, family_size=12)
    assert result.adjusted_p_value_bonferroni >= result.empirical_p_value
    assert result.adjusted_p_value_bonferroni <= 1.0


def test_default_candidate_score_does_not_use_historical_neutrality():
    spec = LotterySpec()
    draws_a = generate_synthetic_draws(spec, count=80, seed=11)
    draws_b = generate_synthetic_draws(spec, count=80, seed=12)
    combo = (6, 19, 28, 33, 42, 47)
    score_a = score_candidate(combo, spec, number_frequency_records(draws_a, spec))
    score_b = score_candidate(combo, spec, number_frequency_records(draws_b, spec))
    assert score_a.combined_score == score_b.combined_score
    assert score_a.historical_neutrality_score != score_b.historical_neutrality_score


def test_candidate_features_are_auditable():
    features = combination_features((1, 2, 3, 5, 8, 13), LotterySpec())
    assert features["fibonacci_count"] == 6.0
    assert features["birthday_count"] == 6.0
    assert features["consecutive_pairs"] >= 2.0


def test_analysis_gate_uses_corrected_family():
    spec = LotterySpec()
    draws = generate_synthetic_draws(spec, count=150, seed=649)
    report = analyse(draws, spec, null_trials=200, dmd_trials=10, candidate_samples=100, backtest_windows=(26, 52), seed=649)
    assert report["predictive_evidence_gate"]["family_size"] == 8
    assert all("adjusted_p_value_bonferroni" in row for row in report["rolling_backtests"])


def test_reference_combination_is_scored_but_not_declared_predictive():
    spec = LotterySpec()
    draws = generate_synthetic_draws(spec, count=90, seed=3)
    report = analyse(
        draws, spec, null_trials=20, dmd_trials=4, candidate_samples=50,
        backtest_windows=(26,), reference_combinations=((32, 37, 41, 43, 47, 49),),
    )
    reference = report["candidate_search"]["references"][0]
    assert reference["numbers"] == [32, 37, 41, 43, 47, 49]
    assert "combined_score" in reference
    assert "NOT draw probability" in report["candidate_search"]["objective"]


def test_proofpack_detects_tampering():
    spec = LotterySpec()
    draws = generate_synthetic_draws(spec, count=80, seed=4)
    report = analyse(draws, spec, null_trials=20, dmd_trials=4, candidate_samples=50, backtest_windows=(26,))
    pack = make_proofpack(report)
    assert verify_proofpack(pack)
    tampered = copy.deepcopy(pack)
    tampered["draw_count"] += 1
    assert not verify_proofpack(tampered)


def test_synthetic_null_smoke_keeps_schema_and_boundary():
    spec = LotterySpec()
    draws = generate_synthetic_draws(spec, count=120, seed=20)
    report = analyse(draws, spec, null_trials=50, dmd_trials=5, candidate_samples=75, backtest_windows=(26,))
    assert report["schema"] == "gaugegap.lottery_forge.analysis.v2"
    assert report["candidate_search"]["neutrality_weight"] == 0.0
