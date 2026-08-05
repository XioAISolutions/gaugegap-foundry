"""Auditable abductive executive for the elevator benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .axiom import compile_local_equivalence_axiom, verify_local_equivalence
from .contracts import Intervention, Observation, content_hash
from .elevator import EinsteinElevatorWorld
from .hypotheses import Hypothesis, default_elevator_hypotheses
from .salience import SalienceCandidate, SalienceController

LOCAL_KEYS = (
    "apparent_weight_n",
    "relative_drop_acceleration_m_s2",
    "floor_reaction_force_n",
)
LOCAL_INVARIANCE_ACTIONS = {
    "change_object_mass",
    "change_object_composition",
    "cut_cable",
}


@dataclass(frozen=True)
class ExecutiveConfig:
    """Controls search policy without changing the physical benchmark."""

    use_salience: bool = True
    early_stop: bool = True
    max_interventions: int | None = None
    confidence_threshold: float = 0.75
    minimum_local_invariance_tests: int = 1
    require_scope_boundary: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "use_salience": self.use_salience,
            "early_stop": self.early_stop,
            "max_interventions": self.max_interventions,
            "confidence_threshold": self.confidence_threshold,
            "minimum_local_invariance_tests": self.minimum_local_invariance_tests,
            "require_scope_boundary": self.require_scope_boundary,
        }


@dataclass(frozen=True)
class ExperimentOutcome:
    action: Intervention
    observation_a: Observation
    observation_b: Observation
    local_match: bool
    external_difference: bool
    discriminated_hypotheses: tuple[str, ...]
    salience_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "intervention": self.action.to_dict(),
            "observations": [self.observation_a.to_dict(), self.observation_b.to_dict()],
            "local_match": self.local_match,
            "external_difference": self.external_difference,
            "discriminated_hypotheses": list(self.discriminated_hypotheses),
            "salience_score": round(self.salience_score, 6),
        }


class AbductiveExecutive:
    def __init__(
        self,
        *,
        seed: int = 927451,
        tolerance: float = 1e-10,
        config: ExecutiveConfig | None = None,
        use_salience: bool | None = None,
        early_stop: bool | None = None,
        max_interventions: int | None = None,
    ) -> None:
        self.seed = seed
        self.tolerance = tolerance
        resolved = config or ExecutiveConfig()
        if use_salience is not None or early_stop is not None or max_interventions is not None:
            resolved = ExecutiveConfig(
                use_salience=(resolved.use_salience if use_salience is None else use_salience),
                early_stop=(resolved.early_stop if early_stop is None else early_stop),
                max_interventions=(
                    resolved.max_interventions
                    if max_interventions is None
                    else max_interventions
                ),
                confidence_threshold=resolved.confidence_threshold,
                minimum_local_invariance_tests=resolved.minimum_local_invariance_tests,
                require_scope_boundary=resolved.require_scope_boundary,
            )
        if resolved.max_interventions is not None and resolved.max_interventions < 1:
            raise ValueError("max_interventions must be positive")
        self.config = resolved
        self.hypotheses = default_elevator_hypotheses()
        self.salience = SalienceController()

    def _fresh_pair(self) -> tuple[EinsteinElevatorWorld, EinsteinElevatorWorld]:
        a = EinsteinElevatorWorld("gravity")
        b = EinsteinElevatorWorld("acceleration")
        a.reset(self.seed)
        b.reset(self.seed)
        return a, b

    def _local_match(self, a: Observation, b: Observation) -> bool:
        for key in LOCAL_KEYS:
            av, bv = a.sensor_readings[key], b.sensor_readings[key]
            if av is None or bv is None or abs(av - bv) > self.tolerance:
                return False
        return True

    def _candidate_plan(self) -> list[tuple[Intervention, SalienceCandidate]]:
        return [
            (
                Intervention("repeat_observation", rationale="test sensor stability"),
                SalienceCandidate("repeat_observation", 0.25, 0.65, 0.55, 1.0, cost=0.03),
            ),
            (
                Intervention("change_object_mass", {"mass_kg": 35.0}),
                SalienceCandidate("change_object_mass", 0.55, 0.82, 0.76, 1.0, cost=0.05),
            ),
            (
                Intervention("change_object_composition", {"composition": "aluminium"}),
                SalienceCandidate("change_object_composition", 0.52, 0.78, 0.72, 1.0, cost=0.05),
            ),
            (
                Intervention("cut_cable", rationale="enter free-fall state"),
                SalienceCandidate("cut_cable", 0.85, 0.88, 0.84, 1.0, cost=0.12),
            ),
            (
                Intervention(
                    "open_external_reference",
                    rationale="test local versus external-frame scope",
                ),
                SalienceCandidate(
                    "open_external_reference", 0.95, 0.98, 0.99, 1.0, cost=0.10
                ),
            ),
        ]

    def _rank_plan(
        self, plan: list[tuple[Intervention, SalienceCandidate]]
    ) -> list[tuple[str, float]]:
        if self.config.use_salience:
            return self.salience.rank(candidate for _, candidate in plan)
        return [(action.action_type, float(index + 1)) for index, (action, _) in enumerate(plan)]

    def _run_intervention(self, action: Intervention, salience_score: float) -> ExperimentOutcome:
        a, b = self._fresh_pair()
        oa = a.intervene(action).observation
        ob = b.intervene(action).observation
        local_match = self._local_match(oa, ob)
        ea = oa.sensor_readings.get("external_cabin_acceleration_up_m_s2")
        eb = ob.sensor_readings.get("external_cabin_acceleration_up_m_s2")
        external_difference = bool(
            ea is not None and eb is not None and abs(ea - eb) > self.tolerance
        )
        discrimination: dict[str, tuple[str, ...]] = {
            "repeat_observation": ("H1",),
            "change_object_mass": ("H2",),
            "change_object_composition": ("H2",),
            "cut_cable": ("H3", "H4"),
            "open_external_reference": ("H3", "H4"),
        }
        return ExperimentOutcome(
            action,
            oa,
            ob,
            local_match,
            external_difference,
            discrimination.get(action.action_type, ()),
            salience_score,
        )

    def _hypothesis(self, hypothesis_id: str) -> Hypothesis:
        return next(h for h in self.hypotheses if h.hypothesis_id == hypothesis_id)

    def _update_hypotheses(self, outcome: ExperimentOutcome) -> None:
        action = outcome.action.action_type
        if action == "repeat_observation" and outcome.local_match:
            h = self._hypothesis("H1")
            h.score -= 0.22
            h.evidence_against.append("stable repeated local readings")
        elif action in {"change_object_mass", "change_object_composition"} and outcome.local_match:
            h = self._hypothesis("H2")
            h.score -= 0.18
            h.evidence_against.append(f"local match survived {action}")
            h4 = self._hypothesis("H4")
            h4.score += 0.08
            h4.evidence_for.append(f"equivalence survived {action}")
        elif action == "cut_cable" and outcome.local_match:
            h4 = self._hypothesis("H4")
            h4.score += 0.15
            h4.evidence_for.append("both black boxes became locally weightless")
        elif action == "open_external_reference" and outcome.external_difference:
            h3 = self._hypothesis("H3")
            h3.score -= 0.30
            h3.evidence_against.append(
                "external reference revealed different cabin accelerations"
            )
            h4 = self._hypothesis("H4")
            h4.score += 0.25
            h4.evidence_for.append(
                "local mechanics matched while external acceleration differed"
            )

        for hypothesis in self.hypotheses:
            hypothesis.score = max(0.0, min(1.0, hypothesis.score))
            if hypothesis.score <= 0.18:
                hypothesis.status = "rejected"

    def _stopping_condition(
        self,
        *,
        local_invariance_tests: int,
        boundary_observed: bool,
    ) -> bool:
        if not self.config.early_stop:
            return False
        winner = max(self.hypotheses, key=lambda hypothesis: hypothesis.score)
        if winner.hypothesis_id != "H4":
            return False
        if winner.score < self.config.confidence_threshold:
            return False
        if local_invariance_tests < self.config.minimum_local_invariance_tests:
            return False
        if self.config.require_scope_boundary and not boundary_observed:
            return False
        return True

    def run(self) -> dict[str, Any]:
        self.hypotheses = default_elevator_hypotheses()
        self.salience = SalienceController()
        initial_a, initial_b = self._fresh_pair()
        obs_a, obs_b = initial_a.observe(), initial_b.observe()
        initial_match = self._local_match(obs_a, obs_b)

        plan = self._candidate_plan()
        ranking = self._rank_plan(plan)
        actions_by_name = {action.action_type: action for action, _ in plan}
        outcomes: list[ExperimentOutcome] = []
        local_invariance_tests = 0
        boundary_observed = False
        stopped_early = False
        limit = self.config.max_interventions or len(ranking)

        for name, score in ranking[:limit]:
            outcome = self._run_intervention(actions_by_name[name], score)
            outcomes.append(outcome)
            self._update_hypotheses(outcome)
            if outcome.local_match and name in LOCAL_INVARIANCE_ACTIONS:
                local_invariance_tests += 1
            boundary_observed = boundary_observed or outcome.external_difference
            useful = bool(outcome.discriminated_hypotheses) and (
                outcome.local_match or outcome.external_difference
            )
            self.salience.reinforce(name, useful=useful)
            if self._stopping_condition(
                local_invariance_tests=local_invariance_tests,
                boundary_observed=boundary_observed,
            ):
                stopped_early = len(outcomes) < len(ranking)
                break

        winner = max(self.hypotheses, key=lambda hypothesis: hypothesis.score)
        discovery_complete = self._stopping_condition(
            local_invariance_tests=local_invariance_tests,
            boundary_observed=boundary_observed,
        ) or (
            winner.hypothesis_id == "H4"
            and winner.score >= self.config.confidence_threshold
            and local_invariance_tests >= self.config.minimum_local_invariance_tests
            and (boundary_observed or not self.config.require_scope_boundary)
        )
        axiom = (
            compile_local_equivalence_axiom()
            if winner.hypothesis_id == "H4" and discovery_complete
            else None
        )
        verification = verify_local_equivalence(tolerance=self.tolerance)
        if axiom is not None:
            axiom["status"] = (
                "supported_within_scope"
                if verification.verdict == "supported_within_scope"
                else "rejected"
            )

        artifact: dict[str, Any] = {
            "crumb_version": "1.5",
            "artifact_type": "eja_experiment",
            "experiment": {
                "id": f"elevator-run-{self.seed}",
                "world": "einstein-elevator-v0.2",
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
                "initial_observations": [obs_a.to_dict(), obs_b.to_dict()],
                "initial_observational_match": initial_match,
            },
            "surprise": {
                "type": "observational_equivalence",
                "description": (
                    "Two causally different benchmark boxes generated matching "
                    "local mechanical sensor readings."
                ),
                "magnitude": 0.94 if initial_match else 0.0,
            },
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "intervention_ranking": [
                {"action": name, "salience": round(score, 6)} for name, score in ranking
            ],
            "trajectories": [outcome.to_dict() for outcome in outcomes],
            "candidate_axiom": axiom,
            "deductions": [
                {
                    "id": "D1",
                    "derived_from": axiom["id"] if axiom else None,
                    "prediction": (
                        "Changing object mass or composition preserves equal "
                        "mass-normalized local drop acceleration across the boxes."
                    ),
                },
                {
                    "id": "D2",
                    "derived_from": axiom["id"] if axiom else None,
                    "prediction": (
                        "An external inertial reference may distinguish the causes, "
                        "so the claim must remain local and scoped."
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
                "policy": "spiking_salience" if self.config.use_salience else "fixed_baseline",
            },
            "provenance": {
                "generator": "gaugegap.jump_lab.AbductiveExecutive",
                "artifact_hash": "pending",
                "hidden_state_exposed_to_agent": False,
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
