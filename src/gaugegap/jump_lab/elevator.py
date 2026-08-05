"""A deterministic local elevator world for E-J-A discovery experiments.

This is intentionally a scoped Newtonian toy world, not a general-relativity
simulator. It tests whether an agent can distinguish local mechanical
equivalence from a universal claim.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Any

from .contracts import Intervention, Observation, Transition, content_hash

G0 = 9.81


@dataclass(frozen=True)
class ElevatorState:
    scenario_id: str
    hidden_cause: str
    gravity_m_s2: float
    cabin_acceleration_up_m_s2: float
    gravity_gradient_s2: float = 0.0
    object_mass_kg: float = 70.0
    object_composition: str = "steel"
    cabin_height_m: float = 2.5
    cable_attached: bool = True
    external_reference_visible: bool = False
    step: int = 0

    @property
    def effective_downward_acceleration(self) -> float:
        return self.gravity_m_s2 + self.cabin_acceleration_up_m_s2


class EinsteinElevatorWorld:
    """Black-box elevator world with hidden gravity or acceleration cause."""

    VALID_SCENARIOS = {"gravity", "acceleration"}

    def __init__(self, scenario: str = "gravity") -> None:
        if scenario not in self.VALID_SCENARIOS:
            raise ValueError(f"unknown scenario: {scenario}")
        self._scenario = scenario
        self._seed = 0
        self._state = self._initial_state()

    def _initial_state(self) -> ElevatorState:
        if self._scenario == "gravity":
            return ElevatorState(
                scenario_id="black-box-A",
                hidden_cause="uniform_gravity",
                gravity_m_s2=G0,
                cabin_acceleration_up_m_s2=0.0,
            )
        return ElevatorState(
            scenario_id="black-box-B",
            hidden_cause="uniform_acceleration",
            gravity_m_s2=0.0,
            cabin_acceleration_up_m_s2=G0,
        )

    def reset(self, seed: int = 0) -> Observation:
        self._seed = int(seed)
        self._state = self._initial_state()
        return self.observe()

    def _state_id(self) -> str:
        return content_hash(self.snapshot(include_hidden=True))

    def observe(self) -> Observation:
        s = self._state
        effective = s.effective_downward_acceleration
        weight = s.object_mass_kg * effective
        external_accel = (
            s.cabin_acceleration_up_m_s2 if s.external_reference_visible else None
        )
        readings: dict[str, float | None] = {
            "apparent_weight_n": weight,
            "relative_drop_acceleration_m_s2": effective,
            "floor_reaction_force_n": weight,
            "tidal_acceleration_delta_m_s2": s.gravity_gradient_s2 * s.cabin_height_m,
            "external_cabin_acceleration_up_m_s2": external_accel,
        }
        state_id = self._state_id()
        return Observation(
            observation_id=f"{s.scenario_id}-obs-{s.step:03d}",
            state_id=state_id,
            step=s.step,
            values={
                "scenario_id": s.scenario_id,
                "object_mass_kg": s.object_mass_kg,
                "object_composition": s.object_composition,
                "cabin_height_m": s.cabin_height_m,
                "cable_attached": s.cable_attached,
                "external_reference_visible": s.external_reference_visible,
            },
            sensor_readings=readings,
            invariant_results=self.check_invariants(),
            metadata={
                "model": "newtonian-local-elevator-v0.1",
                "cause_hidden_from_agent": True,
                "deterministic_seed": self._seed,
            },
        )

    def check_invariants(self) -> dict[str, bool]:
        s = self._state
        values = [
            s.gravity_m_s2,
            s.cabin_acceleration_up_m_s2,
            s.gravity_gradient_s2,
            s.object_mass_kg,
            s.cabin_height_m,
        ]
        return {
            "finite_state": all(isfinite(v) for v in values),
            "positive_mass": s.object_mass_kg > 0,
            "positive_cabin_height": s.cabin_height_m > 0,
            "known_composition": bool(s.object_composition),
        }

    def available_interventions(self) -> list[Intervention]:
        return [
            Intervention("repeat_observation", rationale="test sensor stability"),
            Intervention("change_object_mass", {"mass_kg": 35.0}),
            Intervention("change_object_composition", {"composition": "aluminium"}),
            Intervention("cut_cable", rationale="test transition to free fall"),
            Intervention("open_external_reference", rationale="test local versus global scope"),
            Intervention("set_cabin_height", {"height_m": 20.0}),
        ]

    def intervene(self, action: Intervention) -> Transition:
        previous = self._state_id()
        s = self._state
        p = action.parameters
        if action.action_type == "repeat_observation":
            new_state = replace(s, step=s.step + 1)
        elif action.action_type == "change_object_mass":
            mass = float(p.get("mass_kg", 35.0))
            if mass <= 0:
                raise ValueError("mass_kg must be positive")
            new_state = replace(s, object_mass_kg=mass, step=s.step + 1)
        elif action.action_type == "change_object_composition":
            composition = str(p.get("composition", "aluminium"))
            if not composition:
                raise ValueError("composition must be non-empty")
            new_state = replace(s, object_composition=composition, step=s.step + 1)
        elif action.action_type == "cut_cable":
            new_acceleration = -s.gravity_m_s2 if s.hidden_cause == "uniform_gravity" else 0.0
            new_state = replace(
                s,
                cabin_acceleration_up_m_s2=new_acceleration,
                cable_attached=False,
                step=s.step + 1,
            )
        elif action.action_type == "open_external_reference":
            new_state = replace(s, external_reference_visible=True, step=s.step + 1)
        elif action.action_type == "set_cabin_height":
            height = float(p.get("height_m", 20.0))
            if height <= 0:
                raise ValueError("height_m must be positive")
            new_state = replace(s, cabin_height_m=height, step=s.step + 1)
        else:
            raise ValueError(f"unsupported intervention: {action.action_type}")

        self._state = new_state
        return Transition(previous, action, self.observe(), self._seed)

    def snapshot(self, *, include_hidden: bool = False) -> dict[str, Any]:
        s = self._state
        visible = {
            "scenario_id": s.scenario_id,
            "object_mass_kg": s.object_mass_kg,
            "object_composition": s.object_composition,
            "cabin_height_m": s.cabin_height_m,
            "cable_attached": s.cable_attached,
            "external_reference_visible": s.external_reference_visible,
            "step": s.step,
            "seed": self._seed,
        }
        if include_hidden:
            visible.update(
                {
                    "hidden_cause": s.hidden_cause,
                    "gravity_m_s2": s.gravity_m_s2,
                    "cabin_acceleration_up_m_s2": s.cabin_acceleration_up_m_s2,
                    "gravity_gradient_s2": s.gravity_gradient_s2,
                }
            )
        return visible
