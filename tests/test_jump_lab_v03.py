from __future__ import annotations

from gaugegap.jump_lab import (
    CartAbductiveExecutive,
    ExecutiveConfig,
    ForceMassCartWorld,
    Intervention,
    SalienceController,
    render_discovery_html,
    render_suite_html,
    run_suite,
    verify_force_mass_ratio,
)


def test_cart_hidden_parameters_are_not_agent_visible():
    world = ForceMassCartWorld("light")
    world.reset(1)
    assert "hidden_force_n" not in world.snapshot()
    assert "hidden_mass_kg" not in world.snapshot()
    assert world.snapshot(include_hidden=True)["hidden_force_n"] == 10.0


def test_cart_initial_kinematics_match_but_force_boundary_differs():
    light = ForceMassCartWorld("light")
    heavy = ForceMassCartWorld("heavy")
    light.reset(2)
    heavy.reset(2)
    for key in (
        "kinematic_acceleration_m_s2",
        "final_velocity_m_s",
        "position_m",
    ):
        assert light.observe().sensor_readings[key] == heavy.observe().sensor_readings[key]

    light_force = light.intervene(Intervention("expose_force_sensor")).observation
    heavy_force = heavy.intervene(Intervention("expose_force_sensor")).observation
    assert light_force.sensor_readings["force_sensor_n"] != heavy_force.sensor_readings[
        "force_sensor_n"
    ]


def test_equal_payload_breaks_initial_force_mass_ratio_match():
    light = ForceMassCartWorld("light")
    heavy = ForceMassCartWorld("heavy")
    light.reset(3)
    heavy.reset(3)
    action = Intervention("add_equal_payload", {"payload_kg": 2.0})
    left = light.intervene(action).observation
    right = heavy.intervene(action).observation
    assert (
        left.sensor_readings["kinematic_acceleration_m_s2"]
        != right.sensor_readings["kinematic_acceleration_m_s2"]
    )


def test_cart_executive_compiles_only_scoped_ratio_axiom():
    artifact = CartAbductiveExecutive(seed=7).run()
    assert artifact["metrics"]["winner"] == "C4"
    assert artifact["metrics"]["discovery_complete"] is True
    assert artifact["metrics"]["experiments_run"] < artifact["metrics"][
        "experiments_available"
    ]
    assert artifact["candidate_axiom"]["id"] == "newtonian-force-mass-ratio-001"
    assert artifact["verification"]["verdict"] == "supported_within_scope"
    assert "friction" in " ".join(artifact["candidate_axiom"]["excluded_claims"])


def test_cart_bounded_run_refuses_premature_axiom():
    artifact = CartAbductiveExecutive(
        seed=8,
        config=ExecutiveConfig(max_interventions=1),
    ).run()
    assert artifact["metrics"]["discovery_complete"] is False
    assert artifact["candidate_axiom"] is None


def test_force_mass_verifier_has_local_cases_and_boundary_checks():
    result = verify_force_mass_ratio()
    assert result.verdict == "supported_within_scope"
    assert result.local_cases == 12
    assert result.local_failures == 0
    assert result.boundary_differences_detected == 2


def test_salience_memory_snapshot_round_trip_is_bounded():
    controller = SalienceController()
    controller.reinforce("force", useful=True, association_key="boundary_probe")
    snapshot = controller.snapshot()
    restored = SalienceController()
    restored.load_snapshot(snapshot)
    assert restored.associations == {"boundary_probe": 0.05}
    assert "does not" in snapshot["claim_boundary"]


def test_multiworld_suite_links_warm_cart_to_elevator(tmp_path):
    report = run_suite([11, 12], output_dir=tmp_path)
    assert report["summary"]["world_count"] == 2
    assert report["summary"]["cart_same_winner_rate"] == 1.0
    assert report["summary"]["cart_same_verdict_rate"] == 1.0
    assert report["summary"]["warm_parent_link_rate"] == 1.0
    assert report["summary"]["warm_vs_baseline_mean_experiments_saved"] > 0
    assert len(report["artifact_index"]) == 8
    assert all((tmp_path / f"seed-{seed}").exists() for seed in (11, 12))


def test_cart_and_suite_reports_keep_claim_boundaries_visible():
    artifact = CartAbductiveExecutive(seed=13).run()
    discovery_html = render_discovery_html(artifact)
    suite_html = render_suite_html(run_suite([13]))
    assert "1 · Synthetic force/mass cart world" in discovery_html
    assert "5 · Candidate axiom and deterministic verdict" in discovery_html
    assert "Claim boundary" in discovery_html
    assert "Multi-world suite" in suite_html
    assert "does not establish" in suite_html
