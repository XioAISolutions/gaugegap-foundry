from gaugegap.plane_frontier_degree2 import (
    derive_degree2_exact_certificate,
)


def test_degree2_exact_left_null_certificate() -> None:
    certificate = derive_degree2_exact_certificate()
    assert certificate.verified
    assert certificate.support == ((0, 1), (1, 0), (3, 5))
    assert certificate.total_equations == 1250
    assert certificate.total_unknowns == 1485
    assert certificate.selected_rows == 875
    assert certificate.active_columns == 924
    assert certificate.exact_rank_before_contradiction == 874
    assert len(certificate.certificate_rows) == 102
    assert certificate.rhs_pairing == -621_160_607_786_489_971_200


def test_degree2_certificate_digest_is_deterministic() -> None:
    payload = derive_degree2_exact_certificate().to_dict()
    assert payload["certificate_digest"] == (
        "18f96fbd550b2d48f3b4e4e035b7f8dbf05553a9f782743c30fc214a7d9904ad"
    )
    assert payload["evidence_label"] == "DERIVED_EXACT"
    assert payload["novelty_status"] == "UNESTABLISHED"
    assert "does not" in payload["claim_boundary"].lower()
