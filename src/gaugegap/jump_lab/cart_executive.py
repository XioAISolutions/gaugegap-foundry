"""Auditable abductive executive for the force-to-mass cart benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cart_axiom import compile_force_mass_ratio_axiom, verify_force_mass_ratio
from .cart_hypotheses import default_cart_hypotheses
from .contracts import Intervention, Observation, content_hash
from .executive import ExecutiveConfig
from .force_cart import ForceMassCartWorld
from .hypotheses import Hypothesis
from .salience import SalienceCandidate, SalienceController

KINEMATIC_KEYS = (
    "kinematic_acceleration_m_s2",
    "final_velocity_m_s",
    "position_m",
)
LOCAL_INVARIANCE_ACTIONS = {"change_duration", "scale_system"}


@dataclass(frozen=True)
class CartExperimentOutcome:
    action: Intervention
    observation_a: Observation
    observation_b: Observation
    local_match: bool
    latent_difference: bool
    discriminated_hypotheses: tuple[str, ...]
    salience_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "intervention": self.action.to_dict(),
            "observations": [self.observation_a.to_dict(), self.observation_b.to_dict()],
            "local_match": self.local_match,
            "latent_difference": self.latent_difference,
            "external_difference": self.latent_difference,
            "discriminated_hypotheses": list(self.discriminated_hypotheses),
            "salience_score": round(self.salience_score, 6),
        }


class CartAbductiveExecutive:
    def __init__(
        self,
        *,
        seed: int = 927451,
        tolerance: float = 1e-10,
        config: ExecutiveConfig | None = None,
        salience_memory: dict[str, Any] | None = None,
        parent_artifact_hashes: list[str] | None = None,
    ) -> None:
        self.seed = int(seed)
        self.tolerance = tolerance
        self.config = config or ExecutiveConfig()
        if self.config.max_interventions is not None and self.config.max_interventions < 1:
            raise ValueError("max_interventions must be positive")
        self._initial_salience_memory = salience_memory
        self.parent_artifact_hashes = list(parent_artifact_hashes or [])
        self.hypotheses = default_cart_hypotheses()
        self.salience = self._new_salience_controller()

    def _new_salience_controller(self) -> SalienceController:
        controller = SalienceController()
        if self._initial_salience_memory is not None:
            controller.load_snapshot(self._initial_salience_memory)
        return controller

    def _fresh_pair(self) -> tuple[ForceMassCartWorld, ForceMassCartWorld]:
        light = ForceMassCartWorld("light")
        heavy = ForceMassCartWorld("heavy")
        light.reset(self.seed)
        heavy.reset(self.seed)
        return light, heavy

    def _local_match(self, left: Observation, right: Observation) -> bool:
        for key in KINEMATIC_KEYS:
            left_value = left.sensor_readings[key]
            right_value = right.sensor_readings[key]
            if (
                left_value is None
                or right_value is None
                or abs(left_value - right_value) > self.tolerance
            ):
                return False
        return True

    def _candidate_plan(self) -> list[tuple[Intervention, SalienceCandidate]]:
        return [
            (
                Intervention("repeat_observation", rationale="test sensor stability"),
                SalienceCandidate(
                    "repeat_observation", 0.25, 0.62, 0.52, 1.0,
                    cost=0.03, association_key="repeat_probe",
                ),
            ),
            (
                Intervention("change_duration", {"duration_s": 3.0}),
                SalienceCandidate(
                    "change_duration", 0.52, 0.74, 0.70, 1.0,
                    cost=0.04, association_key="time_probe",
                ),
            ),
            (
                Intervention("scale_system", {"factor": 2.0}),
                SalienceCandidate(
                    "scale_system", 0.72, 0.84, 0.86, 1.0,
                    cost=0.06, association_key="parameter_probe",
                ),
            ),
            (
                Intervention("add_equal_payload", {"payload_kg": 2.0}),
                SalienceCandidate(
                    "add_equal_payload", 0.90, 0.95, 0.98, 1.0,
                    cost=0.08, association_key="parameter_probe",
                ),
            ),
            (
                Intervention(
                    "expose_force_sensor",
                    rationale="test whether latent causes differ",
                ),
                SalienceCandidate(
                    "expose_force_sensor", 0.95, 0.98, 0.99, 1.0,
                    cost=0.09, association_key="boundary_probe",
                ),
            ),
        ]

    def _rank_plan(
        self, plan: list[tuple[Intervention, SalienceCandidate]]
    ) -> list[tuple[str, float]]:
        if self.config.use_salience:
            return self.salience.rank(candidate for _, candidate in plan)
        return [
            (action.action_type, float(index + 1))
            for index, (action, _) in enumerate(plan)
        ]

    def _run_intervention(
        self, action: Intervention, salience_score: float
    ) -> CartExperimentOutcome:
        left, right = self._fresh_pair()
        left_observation = left.intervene(action).observation
        right_observation = right.intervene(action).observation
        local_match = self._local_match(left_observation, right_observation)

        latent_difference = False
        for key in ("force_sensor_n", "mass_sensor_kg"):
            left_value = left_observation.sensor_readings.get(key)
            right_value = right_observation.sensor_readings.get(key)
            if (
                left_value is not None
                and right_value is not None
                and abs(left_value - right_value) > self.tolerance
            ):
                latent_difference = True

        discrimination: dict[str, tuple[str, ...]] = {
            "repeat_observation": ("C1",),
            "change_duration": ("C3", "C4"),
            "scale_system": ("C3", "C4"),
            "add_equal_payload": ("C2", "C4"),
            "expose_force_sensor": ("C2", "C4"),
        }
        return CartExperimentOutcome(
            action=action,
            observation_a=left_observation,
            observation_b=right_observation,
            local_match=local_match,
            latent_difference=latent_difference,
            discriminated_hypotheses=discrimination.get(action.action_type, ()),
            salience_score=salience_score,
        )

    def _hypothesis(self, hypothesis_id: str) -> Hypothesis:
        return next(
            hypothesis
            for hypothesis in self.hypotheses
            if hypothesis.hypothesis_id == hypothesis_id
        )

    def _update_hypotheses(self, outcome: CartExperimentOutcome) -> None:
        action = outcome.action.action_type
        if action == "repeat_observation" and outcome.local_match:
            hypothesis = self._hypothesis("C1")
            hypothesis.score -= 0.22
            hypothesis.evidence_against.append("stable repeated kinematic readings")
        elif action == "change_duration" and outcome.local_match:
            controller = self._hypothesis("C3")
            controller.score -= 0.10
            controller.evidence_against.append("motion scaled with Newtonian duration")
            ratio = self._hypothesis("C4")
            ratio.score += 0.08
            ratio.evidence_for.append("kinematic match survived a duration change")
        elif action == "scale_system" and outcome.local_match:
            controller = self._hypothesis("C3")
            controller.score -= 0.18
            controller.evidence_against.append("proportional force and mass scaling preserved motion")
            ratio = self._hypothesis("C4")
            ratio.score += 0.15
            ratio.evidence_for.append("motion remained invariant when force and mass scaled together")
        elif action == "add_equal_payload" and not outcome.local_match:
            identical = self._hypothesis("C2")
            identical.score -= 0.30
            identical.evidence_against.append("an equal payload produced different accelerations")
            ratio = self._hypothesis("C4")
            ratio.score += 0.25
            ratio.evidence_for.append("equal payload broke the initially matched force-to-mass ratios")
        elif action == "expose_force_sensor" and outcome.latent_difference:
            identical = self._hypothesis("C2")
            identical.score -= 0.25
            identical.evidence_against.append("direct force readings differed")
            ratio = self._hypothesis("C4")
            ratio.score += 0.20
            ratio.evidence_for.append("different forces produced the same initial kinematics")

        for hypothesis in self.hypotheses:
            hypothesis.score = max(0.0, min(1.0, hypothesis.score))
            if hypothesis.score <= 0.18:
                hypothesis.status = "rejected"

    def _discovery_complete(
        self,
        *,
        local_invariance_tests: int,
        boundary_observed: bool,
    ) -> bool:
        winner = max(self.hypotheses, key=lambda item: item.score)
        return bool(
            winner.hypothesis_id == "C4"
            and winner.score >= self.config.confidence_threshold
            and local_invariance_tests >= self.config.minimum_local_invariance_tests
            and (boundary_observed or not self.config.require_scope_boundary)
        )

    def run(self) -> dict[str, Any]:
        self.hypotheses = default_cart_hypotheses()
        self.salience = self._new_salience_controller()
        memory_before = self.salience.snapshot()
        left, right = self._fresh_pair()
        initial_left, initial_right = left.observe(), right.observe()
        initial_match = self._local_match(initial_left, initial_right)

        plan = self._candidate_plan()
        ranking = self._rank_plan(plan)
        actions = {action.action_type: action for action, _ in plan}
        candidates = {candidate.name: candidate for _, candidate in plan}
        outcomes: list[CartExperimentOutcome] = []
        local_invariance_tests = 0
        boundary_observed = False
        stopped_early = False
        limit = self.config.max_interventions or len(ranking)

        for name, score in ranking[:limit]:
            outcome = self._run_intervention(actions[name], score)
            outcomes.append(outcome)
            self._update_hypotheses(outcome)
            if outcome.local_match and name in LOCAL_INVARIANCE_ACTIONS:
                local_invariance_tests += 1
            boundary_observed = boundary_observed or outcome.latent_difference
            useful = bool(outcome.discriminated_hypotheses) and (
                outcome.local_match
                or outcome.latent_difference
                or name == "add_equal_payload"
            )
            candidate = candidates[name]
            self.salience.reinforce(
                name,
                useful=useful,
                association_key=candidate.memory_key,
            )
            if self.config.early_stop and self._discovery_complete(
                local_invariance_tests=local_invariance_tests,
                boundary_observed=boundary_observed,
            ):
                stopped_early = len(outcomes) < len(ranking)
                break

        winner = max(self.hypotheses, key=lambda item: item.score)
        discovery_complete = self._discovery_complete(
            local_invariance_tests=local_invariance_tests,
            boundary_observed=boundary_observed,
        )
        axiom = (
            compile_force_mass_ratio_axiom()
            if winner.hypothesis_id == "C4" and discovery_complete
            else None
        )
        verification = verify_force_mass_ratio(tolerance=self.tolerance)
        if axiom is not None:
            axiom["status"] = verification.verdict

        artifact: dict[str, Any] = {
            "crumb_version": "1.5",
            "artifact_type": "eja_experiment",
            "experiment": {
                "id": f"force-cart-run-{self.seed}",
                "world": "force-mass-cart-v0.3",
                "deterministic_seed": self.seed,
                "agent_access": "observations_and_interventions_only",
                "search_policy": {
                    "allow_temporary_regression": True,
                    "regression_budget": 0.15,
                    "preserve_diverse_hypotheses": 4,
                    **self.config.to_dict(),
                },
            },
            "experience": {
                "initial_observations": [
                    initial_left.to_dict(),
                    initial_right.to_dict(),
                ],
                "initial_observational_match": initial_match,
            },
            "surprise": {
                "type": "latent_parameter_non_identifiability",
                "description": (
                    "Two carts generated matching kinematic trajectories despite "
                    "different hidden force and mass values."
                ),
                "magnitude": 0.91 if initial_match else 0.0,
            },
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "intervention_ranking": [
                {"action": name, "salience": round(score, 6)}
                for name, score in ranking
            ],
            "trajectories": [outcome.to_dict() for outcome in outcomes],
            "candidate_axiom": axiom,
            "deductions": [
                {
                    "id": "CD1",
                    "derived_from": axiom["id"] if axiom else None,
                    "prediction": (
                        "Scaling force and mass by the same positive factor preserves "
                        "the tested kinematic trajectory."
                    ),
                },
                {
                    "id": "CD2",
                    "derived_from": axiom["id"] if axiom else None,
                    "prediction": (
                        "Adding the same payload to systems with different hidden "
                        "masses generally breaks their initially equal ratios."
                    ),
                },
            ],
            "verification": verification.to_dict(),
            "metrics": {
                "discovery_complete": discovery_complete,
                "experiments_run": len(outcomes),
                "experiments_available": len(ranking),
                "stopped_early": stopped_early,
                "local_invariance_tests": local_invariance_tests,
                "scope_boundary_observed": boundary_observed,
                "winner": winner.hypothesis_id,
                "winner_score": round(winner.score, 6),
                "policy": (
                    "spiking_salience"
                    if self.config.use_salience
                    else "fixed_baseline"
                ),
            },
            "salience_memory": {
                "before": memory_before,
                "after": self.salience.snapshot(),
            },
            "provenance": {
                "generator": "gaugegap.jump_lab.CartAbductiveExecutive",
                "artifact_hash": "pending",
                "hidden_state_exposed_to_agent": False,
                "parent_artifact_hashes": list(self.parent_artifact_hashes),
            },
        }
        artifact["provenance"]["artifact_hash"] = content_hash(
            {
                **artifact,
                "provenance": {
                    **artifact["provenance"],
                    "artifact_hash": "pending",
                },
            }
        )
        return artifact
