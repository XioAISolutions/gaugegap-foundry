from fractions import Fraction

from gaugegap.jacobian_aftershock import (
    aftershock_json,
    bounded_cubic_seed_search,
    compact_collision_image,
    compact_collision_witnesses,
    compact_four_point_image,
    compact_four_point_witnesses,
    compact_four_sheet_map,
    cubic_seed_endpoint_audit,
    cubic_seed_term_count,
    exact_cubic_seed_minimum,
    factor_cancellation_ledger,
    run_aftershock_audit,
)
from gaugegap.counterexample_forge import verify_polynomial_counterexample


def test_compact_map_has_constant_jacobian_two() -> None:
    candidate = compact_four_sheet_map()
    determinant = candidate.jacobian_determinant()
    assert determinant.is_constant
    assert determinant.constant_value == Fraction(2)


def test_short_collision_is_exact() -> None:
    candidate = compact_four_sheet_map()
    witnesses = compact_collision_witnesses()
    images = tuple(candidate.evaluate(point) for point in witnesses)
    assert len(set(images)) == 1
    assert images[0] == compact_collision_image()


def test_four_point_fiber_is_exact_and_distinct() -> None:
    candidate = compact_four_sheet_map()
    witnesses = compact_four_point_witnesses()
    assert len(set(witnesses)) == 4
    images = tuple(candidate.evaluate(point) for point in witnesses)
    assert len(set(images)) == 1
    assert images[0] == compact_four_point_image()


def test_compact_map_complexity_is_25_monomials() -> None:
    candidate = compact_four_sheet_map()
    assert tuple(len(poly.terms) for poly in candidate.coordinates) == (13, 10, 2)
    assert tuple(poly.total_degree for poly in candidate.coordinates) == (12, 11, 4)
    assert candidate.complexity()["terms"] == 25


def test_seed_g_six_satisfies_weighted_lift_conditions() -> None:
    audit = cubic_seed_endpoint_audit(6)
    assert audit["p(0)"] == 0
    assert audit["p(1)"] == -1
    assert audit["integral_0_1"] == 0
    assert audit["p_prime(1)"] == -1


def test_factor_ledger_certifies_unique_valid_global_minimum() -> None:
    ledger = dict(factor_cancellation_ledger())
    assert ledger[(0, 1)] == 17  # g=0, but the seed drops to degree two
    assert ledger[(-6, 1)] == 8
    assert all(
        occurrences == 1
        for factor, occurrences in ledger.items()
        if factor not in {(0, 1), (-6, 1)}
    )

    certificate = exact_cubic_seed_minimum()
    assert certificate.generic_term_count == 33
    assert certificate.minimum_term_count == 25
    assert certificate.unique_parameter == 6
    assert cubic_seed_term_count(6) == 25


def test_redundant_bounded_search_finds_only_g_six() -> None:
    assert bounded_cubic_seed_search(max_numerator=64, max_denominator=64) == (Fraction(6),)


def test_tampered_short_collision_fails_closed() -> None:
    witnesses = list(compact_collision_witnesses())
    x, y, z = witnesses[-1]
    witnesses[-1] = (x, y, z + 1)
    result = verify_polynomial_counterexample(
        compact_four_sheet_map(),
        witnesses,
        expected_determinant=2,
    )
    assert not result.passed


def test_aftershock_result_is_deterministic() -> None:
    first = run_aftershock_audit()
    second = run_aftershock_audit()
    assert aftershock_json(first) == aftershock_json(second)
    assert first.to_dict()["result_digest"] == second.to_dict()["result_digest"]
