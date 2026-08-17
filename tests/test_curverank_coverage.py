from fractions import Fraction

import pytest

from gaugegap.curverank_coverage import (
    VERDICT_BELOW,
    VERDICT_MEETS,
    VERDICT_UNDETERMINED,
    CurveRankCoverageError,
    certified_coverage,
    classify,
    screen_family,
)
from gaugegap.rigorous.interval_arithmetic import Interval


def _iv(lower: float, upper: float) -> Interval:
    return Interval.from_bounds(lower, upper)


def test_tight_enclosure_near_a_zero_is_certainly_covered() -> None:
    result = certified_coverage([_iv(14.1, 14.2)], [_iv(14.134, 14.135)], tolerance=0.5)
    assert result.covered == 1
    assert result.uncovered == 0
    assert result.undetermined == 0
    assert result.lower_fraction == Fraction(1, 1)
    assert result.upper_fraction == Fraction(1, 1)


def test_distant_enclosure_is_certainly_uncovered() -> None:
    result = certified_coverage([_iv(5.0, 5.1)], [_iv(14.134, 14.135)], tolerance=0.5)
    assert result.uncovered == 1
    assert result.lower_fraction == Fraction(0, 1)
    assert result.upper_fraction == Fraction(0, 1)


def test_wide_enclosure_is_undetermined_and_charged_to_the_upper_bound() -> None:
    # The enclosure overlaps the zero (so a match is possible) but is wider than
    # the tolerance (so a match is not certain): it must not raise the lower bound.
    result = certified_coverage([_iv(13.5, 14.8)], [_iv(14.134, 14.135)], tolerance=0.5)
    assert result.covered == 0
    assert result.uncovered == 0
    assert result.undetermined == 1
    assert result.lower_fraction == Fraction(0, 1)
    assert result.upper_fraction == Fraction(1, 1)


def test_zero_modes_cannot_cover_a_zero() -> None:
    # An enclosure containing 0 is a structural zero mode; after |.| it would sit
    # near the origin, so it must be filtered rather than matched against a zero.
    result = certified_coverage(
        [_iv(-0.1, 0.1)], [_iv(0.0, 0.0)], tolerance=0.5
    )
    assert result.covered == 0
    assert result.uncovered == 1


def test_negative_enclosures_are_compared_by_absolute_value() -> None:
    result = certified_coverage([_iv(-14.2, -14.1)], [_iv(14.134, 14.135)], tolerance=0.5)
    assert result.covered == 1


def test_mixed_population_counts_each_zero_once() -> None:
    eigs = [_iv(14.1, 14.2), _iv(100.0, 100.1)]
    zeros = [_iv(14.134, 14.135), _iv(21.02, 21.03), _iv(25.01, 25.02)]
    result = certified_coverage(eigs, zeros, tolerance=0.5)
    assert (result.covered, result.uncovered, result.undetermined) == (1, 2, 0)
    assert result.lower_fraction == Fraction(1, 3)


def test_non_positive_tolerance_is_rejected() -> None:
    with pytest.raises(CurveRankCoverageError):
        certified_coverage([_iv(1.0, 1.0)], [_iv(1.0, 1.0)], tolerance=0.0)


def test_empty_zero_set_is_rejected() -> None:
    with pytest.raises(CurveRankCoverageError):
        certified_coverage([_iv(1.0, 1.0)], [], tolerance=0.5)


def test_classify_distinguishes_the_three_verdicts() -> None:
    zeros = [_iv(float(t), float(t)) for t in (10.0, 20.0, 30.0, 40.0)]
    all_covered = certified_coverage(
        [_iv(t.lower, t.upper) for t in zeros], zeros, tolerance=0.5
    )
    assert classify(all_covered, Fraction(6725, 10000)) == VERDICT_MEETS

    none_covered = certified_coverage([_iv(1000.0, 1000.0)], zeros, tolerance=0.5)
    assert classify(none_covered, Fraction(6725, 10000)) == VERDICT_BELOW

    straddling = certified_coverage(
        [_iv(9.9, 10.1), _iv(19.0, 21.0), _iv(29.0, 31.0), _iv(39.0, 41.0)],
        zeros,
        tolerance=0.5,
    )
    assert straddling.covered == 1
    assert straddling.undetermined == 3
    assert classify(straddling, Fraction(6725, 10000)) == VERDICT_UNDETERMINED


def test_screen_family_emits_a_hashed_certificate() -> None:
    payload = screen_family(
        "xp", 12, 6, tolerance=0.5, threshold=Fraction(6725, 10000)
    )
    assert payload["schema"] == "gaugegap.curverank_coverage_certificate.v1"
    assert payload["verdict"] in (VERDICT_BELOW, VERDICT_MEETS, VERDICT_UNDETERMINED)
    assert len(payload["certificate_digest"]) == 64
    assert payload["coverage"]["k_zeros"] == 6
    assert payload["certified_mismatch"]["lower"] <= payload["certified_mismatch"]["upper"]
    assert "Riemann Hypothesis" in payload["claim_boundary"]


def test_screen_family_is_deterministic() -> None:
    first = screen_family("xp", 12, 6, tolerance=0.5, threshold=Fraction(6725, 10000))
    second = screen_family("xp", 12, 6, tolerance=0.5, threshold=Fraction(6725, 10000))
    assert first["certificate_digest"] == second["certificate_digest"]


def test_truncated_xp_stays_below_the_reference_threshold() -> None:
    # The finite screening result this track actually reports: the truncated
    # Berry-Keating operator does not match most of the first zeros at this
    # tolerance. This is a statement about the truncation, not about the zeros.
    payload = screen_family(
        "xp", 24, 12, tolerance=0.5, threshold=Fraction(6725, 10000)
    )
    assert payload["verdict"] == VERDICT_BELOW
    assert payload["coverage"]["coverage_upper_float"] < 0.6725


def test_unknown_family_is_rejected() -> None:
    with pytest.raises(CurveRankCoverageError):
        screen_family("hilbert_polya", 12, 6, tolerance=0.5, threshold=Fraction(1, 2))


def test_degenerate_parameters_are_rejected() -> None:
    with pytest.raises(CurveRankCoverageError):
        screen_family("xp", 1, 6, tolerance=0.5, threshold=Fraction(1, 2))
    with pytest.raises(CurveRankCoverageError):
        screen_family("xp", 12, 0, tolerance=0.5, threshold=Fraction(1, 2))
