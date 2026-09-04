import math

from gaugegap.lottery_evaluation import (
    evaluate_ranked_lines,
    fixed_family_max_hit_null,
    overlap_probability,
    overlap_tail_probability,
)


def test_overlap_distribution_is_normalized_and_has_correct_mean():
    probabilities = [
        overlap_probability(pool_size=52, pick_count=7, hits=hits)
        for hits in range(8)
    ]
    assert math.isclose(sum(probabilities), 1.0, rel_tol=0, abs_tol=1e-12)
    mean = sum(hits * probability for hits, probability in enumerate(probabilities))
    assert math.isclose(mean, 49 / 52, rel_tol=0, abs_tol=1e-12)
    assert overlap_tail_probability(pool_size=52, pick_count=7, at_least_hits=3) > 0


def test_ranked_outcomes_score_frozen_lines_only():
    draw = (4, 13, 21, 26, 39, 43, 48)
    lines = [
        (12, 23, 26, 31, 44, 47, 48),
        (12, 26, 31, 39, 43, 44, 48),
    ]
    outcomes = evaluate_ranked_lines(lines, draw, pool_size=52, pick_count=7, bonus=5)
    assert outcomes[0].matching_numbers == (26, 48)
    assert outcomes[0].hit_count == 2
    assert outcomes[1].matching_numbers == (26, 39, 43, 48)
    assert outcomes[1].hit_count == 4
    assert not outcomes[0].bonus_hit


def test_family_null_is_deterministic_and_preserves_line_geometry():
    lines = [
        (12, 23, 26, 31, 44, 47, 48),
        (12, 26, 31, 39, 43, 44, 48),
        (14, 16, 17, 29, 48, 51, 52),
    ]
    first = fixed_family_max_hit_null(
        lines,
        pool_size=52,
        pick_count=7,
        observed_max_hits=4,
        trials=5000,
        seed=20260819,
    )
    second = fixed_family_max_hit_null(
        lines,
        pool_size=52,
        pick_count=7,
        observed_max_hits=4,
        trials=5000,
        seed=20260819,
    )
    assert first == second
    assert 0 < first.empirical_p_value < 1
    assert sum(first.null_max_hit_counts.values()) == 5000
