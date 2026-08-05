"""Blinded model-selection executive for the pendulum holdout benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .blind import BlindModelDeck, forbidden_term_hits
from .contracts import Intervention, Observation, content_hash
from .executive import ExecutiveConfig
from .pendulum import PendulumWorld
from .pendulum_axiom import compile_pendulum_ratio_axiom, verify_pendulum_ratio
from .pendulum_models import pendulum_model_specs
from .salience import SalienceCandidate, SalienceController


@dataclass(frozen=True)
class PendulumOutcome:
    evidence_ref: str
    action: Intervention
    observation_a: Observation
    observation_b: Observation
    pair_match: bool
    latent_difference: bool
    scope_boundary: bool
    observed_signature: str
    salience_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ref": self.evidence_ref,
            "intervention": self.action.to_dict(),
            "observations": [self.observation_a.to_dict(), self.observation_b.to_dict()],
            "local_match": self.pair_match,
            "external_difference": self.latent_difference,
            "scope_boundary": self.scope_boundary,
            "observed_signature": self.observed_signature,
            "salience_score": round(self.salience_score, 6),
        }


class PendulumAbductiveExecutive:
    """Select an anonymous prediction model, then reveal and compile it."""

    TARGET_KEY = "length_gravity_ratio"
    FORBIDDEN_TARGET_TERMS = (
        "length-to-gravity ratio",
        "l/g",
        "2*pi*sqrt",
        "simple-pendulum-length-gravity-ratio",
    )

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
        self.tolerance = float(tolerance)
        self.config = config or ExecutiveConfig(confidence_threshold=0.70)
        if self.config.max_interventions is not None and self.config.max_interventions < 1:
            raise ValueError("max_interventions must be positive")
        self._initial_memory = salience_memory
        self.parent_artifact_hashes = list(parent_artifact_hashes or [])
        self.salience = self._new_salience()
        self.deck = BlindModelDeck(pendulum_model_specs(), seed=self.seed)

    def _new_salience(self) -> SalienceController:
        controller = SalienceController()
        if self._initial_memory is not None:
            controller.load_snapshot(self._initial_memory)
        return controller

    def _fresh_pair(self) -> tuple[PendulumWorld, PendulumWorld]:
        left = PendulumWorld("earth_short")
        right = PendulumWorld("strong_long")
        left.reset(self.seed)
        right.reset(self.seed)
        return left, right

    def _period_match(self, left: Observation, right: Observation) -> bool:
        a = left.sensor_readings["period_s"]
        b = right.sensor_readings["period_s"]
        return bool(a is not None and b is not None and abs(a - b) <= self.tolerance)

    def _candidate_plan(self) -> list[tuple[Intervention, SalienceCandidate]]:
        return [
            (
                Intervention("repeat_observation", rationale="test period stability"),
                SalienceCandidate(
                    "repeat_observation", 0.25, 0.60, 0.50, 1.0,
                    cost=0.03, association_key="repeat_probe",
                ),
            ),
            (
                Intervention("scale_length_and_gravity", {"factor": 2.0}),
                SalienceCandidate(
                    "scale_length_and_gravity", 0.78, 0.94, 0.96, 1.0,
                    cost=0.06, association_key="ratio_probe",
                ),
            ),
            (
                Intervention("add_equal_length", {"length_m": 1.0}),
                SalienceCandidate(
                    "add_equal_length", 0.88, 0.96, 0.98, 1.0,
                    cost=0.07, association_key="parameter_probe",
                ),
            ),
            (
                Intervention("increase_amplitude", {"amplitude_rad": 1.0}),
                SalienceCandidate(
                    "increase_amplitude", 0.90, 0.90, 0.91, 1.0,
                    cost=0.08, association_key="boundary_probe",
                ),
            ),
            (
                Intervention("expose_length_sensor", rationale="probe a latent parameter"),
                SalienceCandidate(
                    "expose_length_sensor", 0.84, 0.88, 0.89, 1.0,
                    cost=0.09, association_key="parameter_probe",
                ),
            ),
        ]

    def _rank_plan(self, plan: list[tuple[Intervention, SalienceCandidate]]) -> list[tuple[str, float]]:
        if self.config.use_salience:
            return self.salience.rank(candidate for _, candidate in plan)
        return [(action.action_type, float(index + 1)) for index, (action, _) in enumerate(plan)]

    def _run_intervention(self, action: Intervention, salience_score: float, index: int) -> PendulumOutcome:
        left, right = self._fresh_pair()
        observation_a = left.intervene(action).observation
        observation_b = right.intervene(action).observation
        pair_match = self._period_match(observation_a, observation_b)
        length_a = observation_a.sensor_readings.get("length_sensor_m")
        length_b = observation_b.sensor_readings.get("length_sensor_m")
        latent_difference = bool(
            length_a is not None
            and length_b is not None
            and abs(length_a - length_b) > self.tolerance
        )
        correction_a = observation_a.sensor_readings.get("amplitude_correction_s") or 0.0
        correction_b = observation_b.sensor_readings.get("amplitude_correction_s") or 0.0
        scope_boundary = bool(
            action.action_type == "increase_amplitude"
            and max(abs(correction_a), abs(correction_b)) > 0.01
        )
        if action.action_type == "repeat_observation":
            signature = "stable_repeat" if pair_match else "unstable_repeat"
        elif latent_difference:
            signature = "latent_difference"
        elif scope_boundary:
            signature = "scope_boundary"
        else:
            signature = "pair_matches" if pair_match else "pair_diverges"
        return PendulumOutcome(
            evidence_ref=f"pendulum-evidence-{index:03d}",
            action=action,
            observation_a=observation_a,
            observation_b=observation_b,
            pair_match=pair_match,
            latent_difference=latent_difference,
            scope_boundary=scope_boundary,
            observed_signature=signature,
            salience_score=salience_score,
        )

    def _complete(
        self,
        *,
        invariance_tests: int,
        discriminating_tests: int,
        scope_boundary: bool,
        latent_difference: bool,
    ) -> bool:
        winner = self.deck.winner()
        return bool(
            winner.key == self.TARGET_KEY
            and winner.score >= self.config.confidence_threshold
            and invariance_tests >= 1
            and discriminating_tests >= 1
            and scope_boundary
            and latent_difference
        )

    def run(self) -> dict[str, Any]:
        self.salience = self._new_salience()
        self.deck = BlindModelDeck(pendulum_model_specs(), seed=self.seed)
        memory_before = self.salience.snapshot()
        left, right = self._fresh_pair()
        initial_a, initial_b = left.observe(), right.observe()
        initial_match = self._period_match(initial_a, initial_b)

        agent_prompt = {
            "instruction": (
                "Select the anonymous prediction model best supported by controlled "
                "interventions. Model meanings remain withheld until selection ends."
            ),
            "initial_observations": [initial_a.to_dict(), initial_b.to_dict()],
            "model_deck": self.deck.agent_deck(),
        }
        leakage_hits = forbidden_term_hits(agent_prompt, self.FORBIDDEN_TARGET_TERMS)

        plan = self._candidate_plan()
        ranking = self._rank_plan(plan)
        actions = {action.action_type: action for action, _ in plan}
        candidates = {candidate.name: candidate for _, candidate in plan}
        outcomes: list[PendulumOutcome] = []
        invariance_tests = 0
        discriminating_tests = 0
        boundary_observed = False
        latent_observed = False
        stopped_early = False
        limit = self.config.max_interventions or len(ranking)

        for index, (name, score) in enumerate(ranking[:limit], start=1):
            outcome = self._run_intervention(actions[name], score, index)
            outcomes.append(outcome)
            self.deck.update(name, outcome.observed_signature, evidence_ref=outcome.evidence_ref)
            if name == "scale_length_and_gravity" and outcome.pair_match:
                invariance_tests += 1
            if name == "add_equal_length" and not outcome.pair_match:
                discriminating_tests += 1
            boundary_observed = boundary_observed or outcome.scope_boundary
            latent_observed = latent_observed or outcome.latent_difference
            candidate = candidates[name]
            self.salience.reinforce(
                name,
                useful=(outcome.observed_signature != "unspecified"),
                association_key=candidate.memory_key,
            )
            if self.config.early_stop and self._complete(
                invariance_tests=invariance_tests,
                discriminating_tests=discriminating_tests,
                scope_boundary=boundary_observed,
                latent_difference=latent_observed,
            ):
                stopped_early = len(outcomes) < len(ranking)
                break

        winner = self.deck.winner()
        discovery_complete = self._complete(
            invariance_tests=invariance_tests,
            discriminating_tests=discriminating_tests,
            scope_boundary=boundary_observed,
            latent_difference=latent_observed,
        )
        verification = verify_pendulum_ratio(tolerance=self.tolerance)
        axiom = (
            compile_pendulum_ratio_axiom()
            if discovery_complete and winner.key == self.TARGET_KEY
            else None
        )
        if axiom is not None:
            axiom["status"] = verification.verdict

        artifact: dict[str, Any] = {
            "crumb_version": "1.5",
            "artifact_type": "eja_experiment",
            "experiment": {
                "id": f"pendulum-holdout-{self.seed}",
                "world": "simple-pendulum-holdout-v0.4",
                "deterministic_seed": self.seed,
                "agent_access": "observations_interventions_and_anonymous_prediction_deck",
                "search_policy": {
                    "allow_temporary_regression": True,
                    "regression_budget": 0.15,
                    "preserve_diverse_hypotheses": 4,
                    **self.config.to_dict(),
                },
            },
            "blind_protocol": {
                "protocol": "pre_registered_anonymous_model_selection_v1",
                "open_ended_abduction": False,
                "model_statements_visible_to_agent": False,
                "target_terms_withheld": list(self.FORBIDDEN_TARGET_TERMS),
                "leakage_hits": leakage_hits,
                "mapping_hash": self.deck.mapping_hash(),
                "agent_prompt_hash": content_hash(agent_prompt),
                "reveal_policy": "semantic statements revealed only after selection",
            },
            "experience": {
                "initial_observations": [initial_a.to_dict(), initial_b.to_dict()],
                "initial_observational_match": initial_match,
            },
            "surprise": {
                "type": "latent_ratio_non_identifiability",
                "description": (
                    "Two pendulum boxes produced matching periods despite different "
                    "hidden physical parameters."
                ),
                "magnitude": 0.92 if initial_match else 0.0,
            },
            "hypotheses": self.deck.revealed_hypotheses(),
            "intervention_ranking": [
                {"action": name, "salience": round(score, 6)} for name, score in ranking
            ],
            "trajectories": [outcome.to_dict() for outcome in outcomes],
            "candidate_axiom": axiom,
            "deductions": [
                {
                    "id": "PD1",
                    "derived_from": axiom["id"] if axiom else None,
                    "prediction": "Scaling length and gravity together preserves the tested period.",
                    "evidence_refs": [
                        outcome.evidence_ref
                        for outcome in outcomes
                        if outcome.action.action_type == "scale_length_and_gravity"
                    ],
                },
                {
                    "id": "PD2",
                    "derived_from": axiom["id"] if axiom else None,
                    "prediction": "Large amplitude creates a measurable boundary to the small-angle approximation.",
                    "evidence_refs": [
                        outcome.evidence_ref
                        for outcome in outcomes
                        if outcome.action.action_type == "increase_amplitude"
                    ],
                },
            ],
            "verification": verification.to_dict(),
            "metrics": {
                "discovery_complete": discovery_complete,
                "experiments_run": len(outcomes),
                "experiments_available": len(ranking),
                "stopped_early": stopped_early,
                "local_invariance_tests": invariance_tests,
                "discriminating_tests": discriminating_tests,
                "scope_boundary_observed": boundary_observed,
                "latent_difference_observed": latent_observed,
                "winner": winner.blind_id,
                "winner_score": round(winner.score, 6),
                "blind_selection_correct": winner.key == self.TARGET_KEY,
                "evaluator_selected_semantic_key": winner.key,
                "policy": "spiking_salience" if self.config.use_salience else "fixed_baseline",
            },
            "salience_memory": {
                "before": memory_before,
                "after": self.salience.snapshot(),
            },
            "provenance": {
                "generator": "gaugegap.jump_lab.PendulumAbductiveExecutive",
                "artifact_hash": "pending",
                "hidden_state_exposed_to_agent": False,
                "hypothesis_origin": "pre_registered_anonymous_prediction_deck",
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
