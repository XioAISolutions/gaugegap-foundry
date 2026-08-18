import numpy as np
import pytest

from gaugegap.hadamard_forge import HadamardForgeError, verify_hadamard
from gaugegap.hadamard_williamson import (
    OUTCOME_BUDGET,
    OUTCOME_FOUND,
    exact_autocorrelation,
    periodic_autocorrelations,
    quadruple_is_valid,
    row_sum_partitions,
    search_williamson_quadruple,
    symmetric_rows,
    williamson_search_orders,
    williamson_witness,
)


def test_symmetric_rows_are_symmetric_and_complete() -> None:
    rows = symmetric_rows(7)
    assert rows.shape == (1 << 3, 7)
    assert {tuple(row) for row in rows}.__len__() == 1 << 3
    for row in rows:
        assert row[0] == 1
        assert all(row[j] == row[7 - j] for j in range(1, 7))


def test_even_length_rows_are_rejected() -> None:
    with pytest.raises(HadamardForgeError):
        symmetric_rows(8)


def test_vectorized_autocorrelation_matches_the_exact_one() -> None:
    rows = symmetric_rows(11)
    fast = periodic_autocorrelations(rows)
    for index in (0, 3, 17, len(rows) - 1):
        row = [int(value) for value in rows[index]]
        assert tuple(int(value) for value in fast[index]) == exact_autocorrelation(row)


def test_autocorrelation_stays_in_integer_arithmetic() -> None:
    assert periodic_autocorrelations(symmetric_rows(9)).dtype == np.int64


def test_row_sum_partitions_satisfy_the_frequency_zero_identity() -> None:
    for n in (3, 13, 23, 29):
        partitions = row_sum_partitions(n)
        assert partitions
        for partition in partitions:
            assert sum(value * value for value in partition) == 4 * n
            assert all(value % 2 == 1 for value in partition)


@pytest.mark.parametrize("n", [1, 3, 5, 7, 9, 11, 13])
def test_search_finds_a_quadruple_that_verifies(n: int) -> None:
    search = search_williamson_quadruple(n)
    assert search.outcome == OUTCOME_FOUND
    assert search.quadruple is not None
    assert quadruple_is_valid(search.quadruple)

    witness = williamson_witness(search.quadruple)
    assert witness.order == 4 * n
    verification = verify_hadamard(witness, expected_order=4 * n)
    assert verification.passed
    assert verification.gram_offdiagonal_max_abs == 0


def test_search_record_reports_what_was_examined() -> None:
    payload = search_williamson_quadruple(11).to_dict()
    space = payload["search_space"]
    assert payload["order"] == 44
    assert space["symmetric_rows_with_leading_plus_one"] == 1 << 5
    assert space["rows_enumerated"] == 1 << 5
    assert space["rows_surviving_psd_bound"] <= space["rows_enumerated"]
    assert space["admissible_row_sum_partitions"]
    assert "Hadamard conjecture" in payload["claim_boundary"]


def test_budget_stop_is_reported_rather_than_guessed() -> None:
    search = search_williamson_quadruple(23, candidate_budget=16)
    assert search.outcome == OUTCOME_BUDGET
    assert search.quadruple is None
    assert search.enumerated == 0
    assert search.space_size == 1 << 11


def test_exhausted_family_is_reported_as_a_result(monkeypatch) -> None:
    # Force every candidate out of the search space; the run must report an
    # exhausted family rather than an error or a silent empty output.
    import gaugegap.hadamard_williamson as module

    monkeypatch.setattr(
        module, "_psd_admissible", lambda rows, n: np.zeros(len(rows), dtype=bool)
    )
    search = module.search_williamson_quadruple(7)
    assert search.outcome == module.OUTCOME_EXHAUSTED
    assert search.quadruple is None
    assert search.psd_survivors == 0
    payload = search.to_dict()
    assert payload["outcome"] == module.OUTCOME_EXHAUSTED
    assert "no quadruple" in payload["claim_boundary"] or "exhausted" in payload[
        "claim_boundary"
    ]


def test_pair_budget_stop_is_not_reported_as_exhaustion() -> None:
    # A split too large to index leaves part of the space unexamined, so the
    # outcome must not claim the family is empty.
    search = search_williamson_quadruple(23, pair_budget=4)
    assert search.outcome == OUTCOME_BUDGET
    assert search.quadruple is None


def test_quadruple_validation_is_fail_closed() -> None:
    search = search_williamson_quadruple(7)
    assert search.quadruple is not None
    rows = [list(row) for row in search.quadruple]

    tampered = [list(row) for row in rows]
    tampered[0][1] = -tampered[0][1]  # breaks symmetry and the identity
    assert not quadruple_is_valid(tampered)
    with pytest.raises(HadamardForgeError):
        williamson_witness(tampered)

    off_alphabet = [list(row) for row in rows]
    off_alphabet[2][0] = 0
    assert not quadruple_is_valid(off_alphabet)

    assert not quadruple_is_valid(rows[:3])


def test_witness_provenance_records_the_search() -> None:
    search = search_williamson_quadruple(5)
    assert search.quadruple is not None
    witness = williamson_witness(search.quadruple)
    assert witness.provenance == "search:williamson(n=5)"
    assert witness.name == "williamson-20"


def test_search_reaches_orders_the_constructor_set_misses() -> None:
    # Order 52 is not covered by this repository's closed-form constructors; the
    # search settles it, which is the point of having a search lane at all.
    from gaugegap.hadamard_forge import orders_awaiting_witness

    assert 52 in orders_awaiting_witness(60)
    search = search_williamson_quadruple(13)
    assert search.outcome == OUTCOME_FOUND
    assert verify_hadamard(
        williamson_witness(search.quadruple), expected_order=52
    ).passed


def test_search_order_listing_respects_the_budget() -> None:
    orders = williamson_search_orders(200, candidate_budget=1 << 12)
    assert 52 in orders and 92 in orders
    # n = 47 needs 2 ** 23 rows, far beyond this budget.
    assert 188 not in orders
    assert all(order % 4 == 0 and (order // 4) % 2 == 1 for order in orders)
