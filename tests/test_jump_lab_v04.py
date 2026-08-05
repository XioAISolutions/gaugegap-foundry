from gaugegap.jump_lab import (
    ExecutiveConfig,
    Intervention,
    PendulumAbductiveExecutive,
    PendulumWorld,
    forbidden_term_hits,
    run_holdout_suite,
)
from gaugegap.jump_lab.pendulum_report import render_pendulum_html


def test_pendulum_world_hides_latent_parameters_and_exposes_controlled_sensors():
    world = PendulumWorld("earth_short")
    world.reset(7)
    visible = world.snapshot()
    hidden = world.snapshot(include_hidden=True)
    assert "hidden_length_m" not in visible
    assert hidden["hidden_length_m"] == 1.0
    observation = world.intervene(Intervention("expose_length_sensor")).observation
    assert observation.sensor_readings["length_sensor_m"] == 1.0


def test_equal_ratio_period_is_invariant_then_equal_length_breaks_pair_match():
    left = PendulumWorld("earth_short")
    right = PendulumWorld("strong_long")
    left.reset(11)
    right.reset(11)
    initial_delta = abs(
        left.observe().sensor_readings["period_s"]
        - right.observe().sensor_readings["period_s"]
    )
    assert initial_delta < 1e-12

    scaled_left = left.intervene(
        Intervention("scale_length_and_gravity", {"factor": 2.0})
    ).observation
    scaled_right = right.intervene(
        Intervention("scale_length_and_gravity", {"factor": 2.0})
    ).observation
    assert abs(
        scaled_left.sensor_readings["period_s"]
        - scaled_right.sensor_readings["period_s"]
    ) < 1e-12

    left.reset(11)
    right.reset(11)
    changed_left = left.intervene(
        Intervention("add_equal_length", {"length_m": 1.0})
    ).observation
    changed_right = right.intervene(
        Intervention("add_equal_length", {"length_m": 1.0})
    ).observation
    assert abs(
        changed_left.sensor_readings["period_s"]
        - changed_right.sensor_readings["period_s"]
    ) > 1e-3


def test_blind_prompt_contains_no_target_language_and_mapping_is_posthoc():
    artifact = PendulumAbductiveExecutive(seed=19).run()
    assert artifact["blind_protocol"]["leakage_hits"] == []
    assert artifact["blind_protocol"]["model_statements_visible_to_agent"] is False
    assert artifact["blind_protocol"]["open_ended_abduction"] is False
    assert forbidden_term_hits(
        {"instruction": "select an anonymous prediction model"},
        artifact["blind_protocol"]["target_terms_withheld"],
    ) == []


def test_blind_holdout_selects_ratio_model_and_compiles_only_after_evidence_gates():
    complete = PendulumAbductiveExecutive(seed=23).run()
    assert complete["metrics"]["blind_selection_correct"] is True
    assert complete["metrics"]["discovery_complete"] is True
    assert complete["candidate_axiom"] is not None
    assert complete["verification"]["verdict"] == "supported_within_scope"

    bounded = PendulumAbductiveExecutive(
        seed=23,
        config=ExecutiveConfig(
            use_salience=True,
            early_stop=True,
            max_interventions=2,
            confidence_threshold=0.70,
        ),
    ).run()
    assert bounded["metrics"]["discovery_complete"] is False
    assert bounded["candidate_axiom"] is None


def test_model_updates_reference_recorded_evidence_nodes():
    artifact = PendulumAbductiveExecutive(seed=29).run()
    evidence_refs = {item["evidence_ref"] for item in artifact["trajectories"]}
    for hypothesis in artifact["hypotheses"]:
        assert set(hypothesis["evidence_for"]).issubset(evidence_refs)
        assert set(hypothesis["evidence_against"]).issubset(evidence_refs)
    for deduction in artifact["deductions"]:
        assert set(deduction["evidence_refs"]).issubset(evidence_refs)


def test_holdout_suite_pairs_cold_warm_and_fixed_without_answer_transfer(tmp_path):
    report = run_holdout_suite([31, 32], output_dir=tmp_path)
    summary = report["summary"]
    assert summary["run_count"] == 2
    assert summary["cold_selection_accuracy"] == 1.0
    assert summary["warm_selection_accuracy"] == 1.0
    assert summary["fixed_selection_accuracy"] == 1.0
    assert summary["warm_leakage_free_rate"] == 1.0
    assert summary["warm_parent_link_rate"] == 1.0
    assert report["blind_protocol"]["open_ended_abduction"] is False


def test_pendulum_report_preserves_blind_claim_boundary():
    artifact = PendulumAbductiveExecutive(seed=37).run()
    html = render_pendulum_html(artifact)
    assert "Blinded pendulum holdout" in html
    assert "Semantic statements were withheld" in html
    assert "not open-ended hypothesis invention" in html
    assert artifact["provenance"]["artifact_hash"] in html
