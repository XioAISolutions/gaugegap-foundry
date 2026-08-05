from gaugegap.jump_lab import (
    AbductiveExecutive,
    EinsteinElevatorWorld,
    Intervention,
    SalienceCandidate,
    SalienceController,
    verify_local_equivalence,
)


def test_same_seed_and_interventions_replay_identically():
    action = Intervention("change_object_mass", {"mass_kg": 35.0})
    first = EinsteinElevatorWorld("gravity")
    second = EinsteinElevatorWorld("gravity")
    first.reset(101)
    second.reset(101)
    assert first.intervene(action).to_dict() == second.intervene(action).to_dict()


def test_hidden_cause_is_not_in_agent_snapshot():
    world = EinsteinElevatorWorld("gravity")
    world.reset(0)
    assert "hidden_cause" not in world.snapshot()
    assert "hidden_cause" in world.snapshot(include_hidden=True)


def test_local_mechanics_match_but_external_reference_differs():
    gravity = EinsteinElevatorWorld("gravity")
    acceleration = EinsteinElevatorWorld("acceleration")
    gravity.reset(5)
    acceleration.reset(5)
    for key in (
        "apparent_weight_n",
        "relative_drop_acceleration_m_s2",
        "floor_reaction_force_n",
    ):
        assert gravity.observe().sensor_readings[key] == acceleration.observe().sensor_readings[key]

    og = gravity.intervene(Intervention("open_external_reference")).observation
    oa = acceleration.intervene(Intervention("open_external_reference")).observation
    assert (
        og.sensor_readings["external_cabin_acceleration_up_m_s2"]
        != oa.sensor_readings["external_cabin_acceleration_up_m_s2"]
    )


def test_verifier_supports_only_scoped_claim():
    result = verify_local_equivalence()
    assert result.verdict == "supported_within_scope"
    assert result.local_failures == 0
    assert result.boundary_differences_detected == 1


def test_salience_ranking_is_deterministic_and_not_truth_decision():
    controller = SalienceController()
    ranked = controller.rank(
        [
            SalienceCandidate("cheap-repeat", 0.2, 0.4, 0.3, 1.0, cost=0.01),
            SalienceCandidate("external-reference", 0.9, 0.9, 0.95, 1.0, cost=0.1),
        ]
    )
    assert ranked[0][0] == "external-reference"
    assert 0.0 <= ranked[0][1] <= 1.0


def test_end_to_end_executive_promotes_h4_with_auditable_scope():
    artifact = AbductiveExecutive(seed=927451).run()
    winner = max(artifact["hypotheses"], key=lambda h: h["score"])
    assert winner["id"] == "H4"
    assert artifact["verification"]["verdict"] == "supported_within_scope"
    assert artifact["candidate_axiom"]["status"] == "supported_within_scope"
    assert "global equivalence" in artifact["candidate_axiom"]["excluded_claims"]
    assert artifact["provenance"]["hidden_state_exposed_to_agent"] is False
    assert artifact["provenance"]["artifact_hash"].startswith("sha256:")
