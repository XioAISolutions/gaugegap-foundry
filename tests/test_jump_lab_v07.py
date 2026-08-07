from __future__ import annotations

import copy
import json

from gaugegap.jump_lab import (
    choose_synthesis_threshold,
    grammar_commitment_hash,
    render_synthesis_html,
    run_symbolic_synthesis_suite,
    run_synthesis_case,
    synthesize_candidates,
    verify_synthesis_commitment,
)
from gaugegap.jump_lab.synthesis import (
    CASE_CALIBRATION_NO_FIT,
    CASE_LINEAR_RATIO,
    CASE_SQRT_RATIO_HOLDOUT,
    _measurements,
    _record_from_run,
)


def test_heldout_sqrt_ratio_is_generated_from_grammar_not_registered_deck():
    measurements = _measurements(CASE_SQRT_RATIO_HOLDOUT, 401)
    candidates = synthesize_candidates(measurements)
    assert candidates[0]["exponents"] == [0.5, -0.5]
    artifact = run_synthesis_case(
        CASE_SQRT_RATIO_HOLDOUT,
        401,
        split="test",
        threshold={"minimum_score": 0.95, "minimum_margin": 0.01},
    )
    protocol = artifact["synthesis_protocol"]
    assert protocol["target_visible_to_agent"] is False
    assert protocol["target_expression_pre_registered"] is False
    assert protocol["generated_candidate_count"] == 49
    assert protocol["grammar_commitment_hash"] == grammar_commitment_hash()
    assert artifact["synthesis_evaluation"]["exact_exponent_recovery"] is True
    assert artifact["verification"]["verdict"] == "supported_within_scope"


def test_calibration_separates_exact_law_from_no_fit_case():
    records = []
    for case_kind in (CASE_LINEAR_RATIO, CASE_CALIBRATION_NO_FIT):
        candidates = synthesize_candidates(_measurements(case_kind, 503))
        records.append(_record_from_run(case_kind, 503, candidates, split="calibration"))
    threshold, scorecards = choose_synthesis_threshold(records)
    assert scorecards
    assert threshold["minimum_score"] >= 0.90
    positive = run_synthesis_case(
        CASE_LINEAR_RATIO,
        503,
        split="calibration",
        threshold=threshold,
    )
    no_fit = run_synthesis_case(
        CASE_CALIBRATION_NO_FIT,
        503,
        split="calibration",
        threshold=threshold,
    )
    assert positive["synthesis_evaluation"]["correct"] is True
    assert positive["candidate_axiom"] is not None
    assert no_fit["synthesis_evaluation"]["selected_outcome"] == "abstain"
    assert no_fit["candidate_axiom"] is None
    assert no_fit["verification"]["verdict"] == "not_evaluated_due_to_abstention"


def test_suite_freezes_threshold_and_recovers_disjoint_holdout_pairs(tmp_path):
    report = run_symbolic_synthesis_suite([601, 602], [701, 702], output_dir=tmp_path)
    summary = report["summary"]
    assert summary["split_disjoint"] is True
    assert summary["threshold_commitment_valid"] is True
    assert summary["grammar_commitment_valid"] is True
    assert summary["holdout_target_pairs_disjoint"] is True
    assert summary["exact_exponent_recovery_rate"] == 1.0
    assert summary["no_fit_abstention_accuracy"] == 1.0
    assert summary["false_discovery_rate"] == 0.0
    assert verify_synthesis_commitment(report) is True

    for entry in report["artifact_index"]:
        if entry["split"] != "test":
            continue
        artifact = json.loads((tmp_path / entry["relative_path"]).read_text())
        protocol = artifact["synthesis_protocol"]
        assert protocol["threshold_commitment_hash"] == report["calibration"]["threshold_commitment_hash"]
        assert protocol["test_answers_used_for_calibration"] is False
        assert protocol["target_expression_pre_registered"] is False


def test_synthesis_commitment_detects_threshold_tampering(tmp_path):
    report = run_symbolic_synthesis_suite([801], [901], output_dir=tmp_path)
    tampered = copy.deepcopy(report)
    tampered["calibration"]["chosen_threshold"]["minimum_score"] += 0.001
    assert verify_synthesis_commitment(tampered) is False


def test_synthesis_html_preserves_bounded_claim_boundary(tmp_path):
    report = run_symbolic_synthesis_suite([1001], [1101], output_dir=tmp_path)
    html = render_synthesis_html(report)
    assert "Finite-grammar symbolic synthesis" in html
    assert "Holdout pair disjoint" in html
    assert "not open-ended scientific invention" in html
