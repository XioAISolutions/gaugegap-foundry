from __future__ import annotations

import copy

from gaugegap.jump_lab import (
    CASE_DECEPTIVE_NO_FIT,
    CASE_HYBRID_NO_FIT,
    CASE_RATIO_SUPPORTED,
    CalibratedPendulumChallengeExecutive,
    ExecutiveConfig,
    apply_frozen_threshold,
    choose_frozen_threshold,
    render_calibration_html,
    run_calibrated_challenge_suite,
    verify_calibration_commitment,
)


def _raw(case_kind: str, seed: int = 41):
    return CalibratedPendulumChallengeExecutive(
        case_kind=case_kind,
        seed=seed,
        config=ExecutiveConfig(
            use_salience=True,
            early_stop=True,
            confidence_threshold=0.70,
        ),
        minimum_selection_score=0.0,
        minimum_selection_margin=-1.0,
    ).run()


def test_deceptive_no_fit_crosses_legacy_gate_but_is_not_a_valid_positive():
    artifact = _raw(CASE_DECEPTIVE_NO_FIT)
    submission = artifact["challenge_evaluation"]["submission_payload"]
    assert artifact["metrics"]["discovery_complete"] is True
    assert submission["top_score"] >= 0.70
    assert artifact["challenge_evaluation"]["answer_payload"]["expected_outcome"] == "abstain"
    assert artifact["challenge_evaluation"]["false_discovery"] is True


def test_threshold_calibration_rejects_deceptive_case_and_keeps_positive():
    records = []
    for case_kind in (
        CASE_RATIO_SUPPORTED,
        CASE_DECEPTIVE_NO_FIT,
        CASE_HYBRID_NO_FIT,
    ):
        artifact = _raw(case_kind, seed=53)
        submission = artifact["challenge_evaluation"]["submission_payload"]
        answer = artifact["challenge_evaluation"]["answer_payload"]
        records.append(
            {
                "case_kind": case_kind,
                "expected_outcome": answer["expected_outcome"],
                "top_semantic_key": artifact["metrics"]["evaluator_selected_semantic_key"],
                "top_score": submission["top_score"],
                "selection_margin": submission["selection_margin"],
                "base_discovery_complete": artifact["metrics"]["discovery_complete"],
            }
        )
    threshold, scorecards = choose_frozen_threshold(records)
    assert scorecards
    positive = apply_frozen_threshold(records[0], threshold)
    deceptive = apply_frozen_threshold(records[1], threshold)
    assert positive["selected_outcome"] == "length_gravity_ratio"
    assert positive["correct"] is True
    assert deceptive["selected_outcome"] == "abstain"
    assert deceptive["false_discovery"] is False


def test_calibration_and_test_splits_are_disjoint_and_committed(tmp_path):
    report = run_calibrated_challenge_suite(
        [61, 62],
        [71, 72],
        output_dir=tmp_path,
    )
    assert report["summary"]["split_disjoint"] is True
    assert report["summary"]["threshold_commitment_valid"] is True
    assert verify_calibration_commitment(report) is True
    assert report["summary"]["cold"]["frozen_decision_match_rate"] == 1.0
    assert report["summary"]["warm"]["frozen_decision_match_rate"] == 1.0
    assert report["summary"]["fixed"]["frozen_decision_match_rate"] == 1.0


def test_test_artifacts_use_one_frozen_threshold_and_block_false_axioms(tmp_path):
    report = run_calibrated_challenge_suite([81], [91], output_dir=tmp_path)
    threshold = report["calibration"]["chosen_threshold"]
    commitment = report["calibration"]["threshold_commitment_hash"]
    for entry in report["artifact_index"]:
        if entry["split"] != "test":
            continue
        path = tmp_path / entry["relative_path"]
        artifact = __import__("json").loads(path.read_text())
        protocol = artifact["calibration_protocol"]
        assert protocol["frozen_threshold"] == threshold
        assert protocol["threshold_commitment_hash"] == commitment
        if entry["case_kind"] in {CASE_DECEPTIVE_NO_FIT, CASE_HYBRID_NO_FIT}:
            assert artifact["challenge_evaluation"]["selected_outcome"] == "abstain"
            assert artifact["candidate_axiom"] is None
            assert artifact["verification"]["verdict"] == "not_evaluated_due_to_abstention"


def test_threshold_commitment_detects_tampering(tmp_path):
    report = run_calibrated_challenge_suite([101], [111], output_dir=tmp_path)
    tampered = copy.deepcopy(report)
    tampered["calibration"]["chosen_threshold"]["minimum_score"] += 0.01
    assert verify_calibration_commitment(tampered) is False


def test_calibration_report_preserves_claim_boundary(tmp_path):
    report = run_calibrated_challenge_suite([121], [131], output_dir=tmp_path)
    html = render_calibration_html(report)
    assert "Frozen threshold calibration" in html
    assert "unseen deterministic seeds" in html
    assert "does not establish real-world calibration" in html
    assert report["calibration"]["threshold_commitment_hash"] in html
