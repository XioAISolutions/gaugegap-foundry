from __future__ import annotations

import copy

from gaugegap.jump_lab import (
    CASE_HYBRID_NO_FIT,
    CASE_RATIO_SUPPORTED,
    SealedPendulumChallengeExecutive,
    run_challenge_suite,
    verify_challenge_commitments,
)


def test_answerable_case_selects_registered_ratio_model():
    artifact = SealedPendulumChallengeExecutive(
        case_kind=CASE_RATIO_SUPPORTED,
        seed=71,
    ).run()
    assert artifact["metrics"]["abstained"] is False
    assert artifact["metrics"]["selected_outcome"] == "length_gravity_ratio"
    assert artifact["metrics"]["challenge_correct"] is True
    assert artifact["candidate_axiom"] is not None
    assert artifact["verification"]["verdict"] == "supported_within_scope"


def test_none_of_the_above_case_abstains_instead_of_compiling_false_axiom():
    artifact = SealedPendulumChallengeExecutive(
        case_kind=CASE_HYBRID_NO_FIT,
        seed=73,
    ).run()
    assert artifact["metrics"]["abstained"] is True
    assert artifact["metrics"]["selected_outcome"] == "abstain"
    assert artifact["metrics"]["challenge_correct"] is True
    assert artifact["metrics"]["false_discovery"] is False
    assert artifact["candidate_axiom"] is None
    assert artifact["verification"]["verdict"] == "not_evaluated_due_to_abstention"
    assert artifact["deductions"] == []


def test_challenge_commitments_recompute_after_postrun_reveal():
    artifact = SealedPendulumChallengeExecutive(seed=79).run()
    checks = verify_challenge_commitments(artifact)
    assert all(checks.values())
    assert artifact["challenge_protocol"]["answer_visible_to_agent"] is False
    assert artifact["challenge_protocol"]["case_spec_visible_to_agent"] is False


def test_commitment_verifier_detects_tampered_answer():
    artifact = SealedPendulumChallengeExecutive(seed=83).run()
    tampered = copy.deepcopy(artifact)
    tampered["challenge_evaluation"]["answer_payload"]["expected_outcome"] = "abstain"
    checks = verify_challenge_commitments(tampered)
    assert checks["case_commitment_valid"] is True
    assert checks["answer_commitment_valid"] is False


def test_hybrid_case_records_real_conflicting_intervention_evidence():
    artifact = SealedPendulumChallengeExecutive(
        case_kind=CASE_HYBRID_NO_FIT,
        seed=89,
    ).run()
    by_action = {
        item["intervention"]["action_type"]: item
        for item in artifact["trajectories"]
    }
    scaled = by_action["scale_length_and_gravity"]
    assert scaled["observed_signature"] == "pair_diverges"
    periods = [obs["sensor_readings"]["period_s"] for obs in scaled["observations"]]
    assert periods[0] != periods[1]


def test_challenge_suite_scores_answerable_and_abstention_cases(tmp_path):
    report = run_challenge_suite([91, 92], output_dir=tmp_path)
    summary = report["summary"]
    assert summary["seed_count"] == 2
    assert summary["case_count"] == 4
    assert summary["answerable_case_count"] == 2
    assert summary["no_fit_case_count"] == 2
    assert summary["cold_overall_accuracy"] == 1.0
    assert summary["warm_overall_accuracy"] == 1.0
    assert summary["fixed_overall_accuracy"] == 1.0
    assert summary["warm_false_discovery_rate"] == 0.0
    assert summary["warm_commitment_valid_rate"] == 1.0
    assert summary["warm_parent_link_rate"] == 1.0
    assert len(report["artifact_index"]) == 12


def test_challenge_claim_boundary_does_not_overstate_discovery():
    report = run_challenge_suite([97])
    boundary = report["claim_boundary"].lower()
    assert "hand-authored" in boundary
    assert "does not demonstrate" in boundary
    assert report["challenge_protocol"]["open_ended_abduction"] is False
