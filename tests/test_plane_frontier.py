from gaugegap.plane_frontier import (
    DEGREE1_CERTIFICATE,
    LOWER_OPERATORS,
    P_POINTS,
    Q_POINTS,
    build_exact_context,
    run_plane_frontier_audit,
    verify_degree1_certificate,
)


def test_gghv_polygon_transcription_counts() -> None:
    assert len(P_POINTS) == 61
    assert len(Q_POINTS) == 125
    assert len(LOWER_OPERATORS) == 51


def test_exact_base_system_invariants() -> None:
    context = build_exact_context()
    assert context.rank == 124
    assert len(context.kernel) == 165
    assert len(context.operators) == 51


def test_degree1_certificate_is_exact_and_nonzero() -> None:
    result = verify_degree1_certificate(build_exact_context())
    assert result.verified
    assert result.annihilates_kernel_image
    assert result.nonzero_rows == 10
    assert result.rhs_pairing == -126_023_040


def test_tampered_degree1_certificate_fails_closed(monkeypatch) -> None:
    monkeypatch.setitem(
        DEGREE1_CERTIFICATE,
        (0, 8),
        DEGREE1_CERTIFICATE[(0, 8)] + 1,
    )
    result = verify_degree1_certificate(build_exact_context())
    assert not result.verified


def test_full_audit_is_deterministic_and_claim_limited() -> None:
    audit = run_plane_frontier_audit()
    payload = audit.to_dict()
    assert audit.passed
    assert payload["audit_digest"] == (
        "e38d4168a6b14aed9d2533c0456eb13769127af4ad2e9f2bb5ef77ea3f55fe5e"
    )
    assert all(item.infeasible for item in audit.degree2)
    assert all(
        item.to_dict()["proof_status"]
        == "FINITE_FIELD_EVIDENCE_NOT_Q_CERTIFICATE"
        for item in audit.degree2
    )
    boundary = audit.claim_boundary.lower()
    assert "do not cover" in boundary
    assert "solve jc(2)" in boundary
