import json

import pytest

from gaugegap.hadamard_forge import (
    HadamardForgeError,
    HadamardWitness,
    build_hadamard_proofpack,
    canonical_json,
    construct_witness,
    constructible_orders,
    kronecker_witness,
    load_witness,
    orders_awaiting_witness,
    paley_type_i_witness,
    paley_type_ii_witness,
    sylvester_witness,
    verify_hadamard,
    write_witness,
)


def test_sylvester_order_eight_passes_every_gate() -> None:
    verification = verify_hadamard(sylvester_witness(3), expected_order=8)
    assert verification.passed
    assert all(gate.passed for gate in verification.gates)
    assert verification.gram_diagonal == 8
    assert verification.gram_offdiagonal_max_abs == 0


def test_paley_constructions_are_orthogonal() -> None:
    paley_i = paley_type_i_witness(11)
    paley_ii = paley_type_ii_witness(13)
    assert paley_i.order == 12
    assert paley_ii.order == 28
    assert verify_hadamard(paley_i).passed
    assert verify_hadamard(paley_ii).passed


def test_paley_rejects_wrong_residue_class() -> None:
    with pytest.raises(HadamardForgeError):
        paley_type_i_witness(13)  # 13 = 1 (mod 4)
    with pytest.raises(HadamardForgeError):
        paley_type_ii_witness(11)  # 11 = 3 (mod 4)
    with pytest.raises(HadamardForgeError):
        paley_type_i_witness(15)  # not prime


def test_kronecker_product_multiplies_orders() -> None:
    product = kronecker_witness(sylvester_witness(1), paley_type_i_witness(11))
    assert product.order == 24
    assert verify_hadamard(product, expected_order=24).passed


@pytest.mark.parametrize("order", [1, 2, 4, 8, 12, 20, 24, 28, 36, 40, 44, 48, 60, 68, 84])
def test_dispatcher_builds_and_verifies_supported_orders(order: int) -> None:
    witness = construct_witness(order)
    assert witness.order == order
    assert verify_hadamard(witness, expected_order=order).passed


def test_dispatcher_rejects_inadmissible_order() -> None:
    with pytest.raises(HadamardForgeError):
        construct_witness(6)


def test_dispatcher_reports_uncovered_order_without_claiming_it_is_open() -> None:
    # 92 is constructible in the literature (Williamson); this module's
    # constructor set does not cover it, and the survey says exactly that.
    with pytest.raises(HadamardForgeError):
        construct_witness(92)
    assert 92 in orders_awaiting_witness(200)
    assert 92 not in constructible_orders(200)
    assert set(constructible_orders(200)).isdisjoint(orders_awaiting_witness(200))


def test_survey_agrees_with_the_dispatcher() -> None:
    # The survey uses a structural coverage test; if it ever disagreed with the
    # dispatcher, the published order list would describe a constructor set the
    # repository does not actually have.
    for order in constructible_orders(132):
        witness = construct_witness(order)
        assert verify_hadamard(witness, expected_order=order).passed
    for order in orders_awaiting_witness(132):
        with pytest.raises(HadamardForgeError):
            construct_witness(order)


def test_inner_products_are_exact_integers() -> None:
    witness = construct_witness(12)
    assert witness.row_inner_product(0, 0) == 12
    assert all(
        witness.row_inner_product(i, j) == 0
        for i in range(12)
        for j in range(12)
        if i != j
    )
    assert all(isinstance(value, int) for value in (witness.row_inner_product(0, 1),))


def test_transpose_is_also_hadamard() -> None:
    witness = construct_witness(20)
    assert verify_hadamard(witness.transpose(), expected_order=20).passed
    assert witness.transpose().transpose().rows == witness.rows


def test_single_flipped_sign_fails_closed() -> None:
    witness = construct_witness(20)
    rows = list(witness.rows)
    rows[3] ^= 1
    tampered = HadamardWitness(20, tuple(rows), "tampered", "test")
    verification = verify_hadamard(tampered)
    assert not verification.passed
    assert "row_orthogonality" in verification.failed_gates()
    assert verification.gram_offdiagonal_max_abs == 2


def test_non_pm1_entry_is_rejected_at_ingestion() -> None:
    with pytest.raises(HadamardForgeError):
        HadamardWitness.from_signs([[1, 0], [1, -1]], name="x", provenance="test")


def test_float_entry_is_rejected_at_ingestion() -> None:
    with pytest.raises(HadamardForgeError):
        HadamardWitness.from_signs([[1.0, 1.0], [1.0, -1.0]], name="x", provenance="test")


def test_non_square_witness_is_rejected() -> None:
    with pytest.raises(HadamardForgeError):
        HadamardWitness.from_signs([[1, 1, 1], [1, -1, 1]], name="x", provenance="test")


def test_inadmissible_order_fails_the_order_gate() -> None:
    witness = HadamardWitness.from_signs(
        [[1] * 6 for _ in range(6)], name="all-ones-6", provenance="test"
    )
    verification = verify_hadamard(witness)
    assert not verification.passed
    assert "admissible_order" in verification.failed_gates()


def test_expected_order_gate_fails_on_mismatch() -> None:
    verification = verify_hadamard(construct_witness(8), expected_order=12)
    assert not verification.passed
    assert "expected_order" in verification.failed_gates()


def test_expected_rows_digest_gate_fails_on_mismatch() -> None:
    verification = verify_hadamard(construct_witness(8), expected_rows_digest="0" * 64)
    assert not verification.passed
    assert "expected_rows_digest" in verification.failed_gates()


def test_packed_round_trip_is_lossless() -> None:
    witness = construct_witness(28)
    decoded = HadamardWitness.from_packed_hex(
        witness.order, witness.packed_hex(), name=witness.name, provenance=witness.provenance
    )
    assert decoded.rows == witness.rows
    assert decoded.signs() == witness.signs()
    assert decoded.digest() == witness.digest()


def test_rows_digest_is_stable_across_provenance() -> None:
    witness = construct_witness(12)
    relabelled = HadamardWitness(witness.order, witness.rows, "other-name", "other-provenance")
    assert relabelled.rows_digest() == witness.rows_digest()
    assert relabelled.digest() != witness.digest()


def test_witness_file_round_trip(tmp_path) -> None:
    witness = construct_witness(20)
    path = write_witness(witness, tmp_path / "witness.json")
    reloaded = load_witness(path)
    assert reloaded.rows == witness.rows
    assert reloaded.rows_digest() == witness.rows_digest()
    assert verify_hadamard(reloaded, expected_order=20).passed


def test_sign_text_witness_is_accepted(tmp_path) -> None:
    path = tmp_path / "witness.txt"
    path.write_text("# order 4\n++++\n+-+-\n++--\n+--+\n", encoding="utf-8")
    witness = load_witness(path)
    assert witness.order == 4
    assert verify_hadamard(witness, expected_order=4).passed


def test_sign_text_rejects_unknown_token(tmp_path) -> None:
    path = tmp_path / "witness.txt"
    path.write_text("++x+\n", encoding="utf-8")
    with pytest.raises(HadamardForgeError):
        load_witness(path)


def test_signs_json_witness_is_accepted(tmp_path) -> None:
    path = tmp_path / "witness.json"
    path.write_text(
        json.dumps({"signs": [[1, 1], [1, -1]], "name": "order-two"}), encoding="utf-8"
    )
    witness = load_witness(path)
    assert witness.order == 2
    assert verify_hadamard(witness, expected_order=2).passed


def test_proofpack_hashes_are_deterministic() -> None:
    witness_a = construct_witness(12)
    witness_b = construct_witness(12)
    assert witness_a.digest() == witness_b.digest()
    pack_a = build_hadamard_proofpack(
        witness_a, verify_hadamard(witness_a), problem_id="hadamard-forge-0012"
    )
    pack_b = build_hadamard_proofpack(
        witness_b, verify_hadamard(witness_b), problem_id="hadamard-forge-0012"
    )
    assert pack_a["proofpack_digest"] == pack_b["proofpack_digest"]
    assert canonical_json(pack_a) == canonical_json(pack_b)


def test_proofpack_rejects_unknown_release_label() -> None:
    witness = construct_witness(8)
    with pytest.raises(ValueError):
        build_hadamard_proofpack(
            witness,
            verify_hadamard(witness),
            release_label="PROVEN",
            problem_id="hadamard-forge-0008",
        )


def test_large_order_witness_references_rows_by_hash() -> None:
    witness = construct_witness(128)
    pack = build_hadamard_proofpack(
        witness, verify_hadamard(witness), problem_id="hadamard-forge-0128"
    )
    assert "rows_hex" not in pack["witness"]
    assert pack["rows_sha256"] == witness.rows_digest()
