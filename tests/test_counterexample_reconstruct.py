from fractions import Fraction

import pytest

from gaugegap.counterexample_forge import jacobian_benchmark_map
from gaugegap.counterexample_reconstruct import (
    candidate_from_parameter,
    coefficients_from_parameter,
    reconstruct_jacobian_benchmark,
    reconstruction_json,
)


def test_reduced_family_preserves_constant_jacobian() -> None:
    for parameter in (-7, -3, -1, 1, 3, 7):
        candidate = candidate_from_parameter(parameter)
        determinant = candidate.jacobian_determinant()
        assert determinant.is_constant
        assert determinant.constant_value == Fraction(2 * parameter, 3)
        assert determinant.constant_value != 0


def test_structured_search_recovers_one_exact_solution() -> None:
    result = reconstruct_jacobian_benchmark(range(-8, 9))
    assert result.attempted == 16
    assert len(result.solutions) == 1
    assert len(result.verifications) == 1
    assert result.verifications[0].passed

    solution = result.unique_solution
    assert solution is not None
    assert solution.digest() == jacobian_benchmark_map().digest()


def test_recovered_coefficients_are_not_supplied_as_search_input() -> None:
    result = reconstruct_jacobian_benchmark((-5, -4, -3, -2, -1, 1, 2, 3, 4, 5))
    passed_trials = [trial for trial in result.trials if trial.verified]
    assert len(passed_trials) == 1
    recovered = passed_trials[0].coefficients
    assert recovered.a == Fraction(4)
    assert recovered.b == Fraction(3)
    assert recovered.c == Fraction(3)
    assert recovered.d == Fraction(2)
    assert recovered.e == Fraction(-3)
    assert passed_trials[0].determinant == Fraction(-2)


def test_parameter_window_without_solution_records_honest_negative_result() -> None:
    result = reconstruct_jacobian_benchmark((1, 2, 3, 4))
    assert result.unique_solution is None
    assert not result.solutions
    assert all(not trial.verified for trial in result.trials)


def test_reconstruction_is_deterministic() -> None:
    first = reconstruct_jacobian_benchmark(range(-8, 9))
    second = reconstruct_jacobian_benchmark(reversed(range(-8, 9)))
    assert reconstruction_json(first) == reconstruction_json(second)
    assert first.to_dict()["reconstruction_digest"] == second.to_dict()["reconstruction_digest"]


def test_zero_parameter_is_rejected_by_direct_instantiation() -> None:
    with pytest.raises(ValueError):
        coefficients_from_parameter(0)


def test_tampered_collision_constraints_produce_no_solution() -> None:
    witnesses = (
        (Fraction(0), Fraction(0), Fraction(-1, 4)),
        (Fraction(1), Fraction(-3, 2), Fraction(13, 2)),
        (Fraction(-1), Fraction(3, 2), Fraction(6)),
    )
    result = reconstruct_jacobian_benchmark(range(-8, 9), witnesses=witnesses)
    assert result.unique_solution is None
