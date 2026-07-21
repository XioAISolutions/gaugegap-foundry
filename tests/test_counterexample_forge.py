from fractions import Fraction

import pytest

from gaugegap.counterexample_forge import (
    Polynomial,
    PolynomialMap,
    build_counterexample_proofpack,
    canonical_json,
    jacobian_benchmark_map,
    jacobian_benchmark_witnesses,
    verify_polynomial_counterexample,
)


def test_public_jacobian_benchmark_has_exact_constant_determinant() -> None:
    candidate = jacobian_benchmark_map()
    determinant = candidate.jacobian_determinant()
    assert determinant.is_constant
    assert determinant.constant_value == Fraction(-2)


def test_public_jacobian_benchmark_has_exact_collision() -> None:
    candidate = jacobian_benchmark_map()
    images = tuple(candidate.evaluate(point) for point in jacobian_benchmark_witnesses())
    assert len(set(images)) == 1
    assert images[0] == (Fraction(-1, 4), Fraction(0), Fraction(0))


def test_benchmark_verification_passes_all_gates() -> None:
    result = verify_polynomial_counterexample(
        jacobian_benchmark_map(),
        jacobian_benchmark_witnesses(),
        expected_determinant=-2,
    )
    assert result.passed
    assert all(gate.passed for gate in result.gates)
    assert result.determinant == Fraction(-2)
    assert result.common_image == (Fraction(-1, 4), Fraction(0), Fraction(0))


def test_tampered_witness_fails_closed() -> None:
    witnesses = list(jacobian_benchmark_witnesses())
    witnesses[-1] = (Fraction(-1), Fraction(3, 2), Fraction(6))
    result = verify_polynomial_counterexample(
        jacobian_benchmark_map(),
        witnesses,
        expected_determinant=-2,
    )
    assert not result.passed
    exact_collision = next(gate for gate in result.gates if gate.name == "exact_collision")
    assert not exact_collision.passed


def test_duplicate_witness_fails_closed() -> None:
    witness = jacobian_benchmark_witnesses()[0]
    result = verify_polynomial_counterexample(
        jacobian_benchmark_map(),
        (witness, witness),
        expected_determinant=-2,
    )
    assert not result.passed
    distinct = next(gate for gate in result.gates if gate.name == "distinct_witnesses")
    assert not distinct.passed


def test_wrong_expected_determinant_fails_closed() -> None:
    result = verify_polynomial_counterexample(
        jacobian_benchmark_map(),
        jacobian_benchmark_witnesses(),
        expected_determinant=1,
    )
    assert not result.passed
    expected = next(gate for gate in result.gates if gate.name == "expected_determinant")
    assert not expected.passed


def test_float_inputs_are_rejected() -> None:
    variables = ("x", "y", "z")
    with pytest.raises(TypeError):
        Polynomial.constant(variables, 0.5)  # type: ignore[arg-type]


def test_candidate_and_proofpack_hashes_are_deterministic() -> None:
    candidate_a = jacobian_benchmark_map()
    candidate_b = jacobian_benchmark_map()
    assert candidate_a.digest() == candidate_b.digest()

    witnesses = jacobian_benchmark_witnesses()
    verification = verify_polynomial_counterexample(candidate_a, witnesses, expected_determinant=-2)
    proofpack_a = build_counterexample_proofpack(candidate_a, witnesses, verification)
    proofpack_b = build_counterexample_proofpack(candidate_b, witnesses, verification)
    assert proofpack_a["proofpack_digest"] == proofpack_b["proofpack_digest"]
    assert canonical_json(proofpack_a) == canonical_json(proofpack_b)


def test_nonconstant_jacobian_does_not_certify() -> None:
    variables = ("x", "y", "z")
    x = Polynomial.variable(variables, 0)
    y = Polynomial.variable(variables, 1)
    z = Polynomial.variable(variables, 2)
    candidate = PolynomialMap(variables, (x**2, y, z), name="nonconstant-control")
    result = verify_polynomial_counterexample(
        candidate,
        ((0, 0, 0), (0, 1, 0)),
    )
    assert not result.passed
    jacobian_gate = next(gate for gate in result.gates if gate.name == "constant_nonzero_jacobian")
    assert not jacobian_gate.passed
