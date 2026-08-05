"""Deterministic force-to-mass cart world for multi-world abduction tests.

Two black boxes begin with different hidden force and mass values but the same
force-to-mass ratio. Their kinematic observations therefore match until an
intervention changes the ratio or exposes a latent parameter. The environment is
a frictionless Newtonian toy model, not a high-fidelity mechanics simulator.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Any

from .contracts import Intervention, Observation, Transition, content_hash


@dataclass(frozen=True)
class CartState:
    scenario_id: str
    hidden_force_n: float
    hidden_mass_kg: float
    duration_s: float = 2.0
    initial_velocity_m_s: float = 0.0
    force_sensor_visible: bool = False
    mass_sensor_visible: bool = False
    step: int = 0

    @property
    def acceleration_m_s2(self) -> float:
        return self.hidden_force_n / self.hidden_mass_kg


class ForceMassCartWorld:
    """Black-box constant-force cart with hidden force and mass."""

    VALID_SCENARIOS = {"light", "heavy"}

    def __init__(self, scenario: str = "light") -> None:
        if scenario not in self.VALID_SCENARIOS:
            raise ValueError(f"unknown scenario: {scenario}")
        self._scenario = scenario
        self._seed = 0
        self._state = self._initial_state()

    def _initial_state(self) -> CartState:
        if self._scenario == "light":
            return CartState("cart-box-A", hidden_force_n=10.0, hidden_mass_kg=2.0)
        return CartState("cart-box-B", hidden_force_n=20.0, hidden_mass_kg=4.0)

    def reset(self, seed: int = 0) -> Observation:
        self._seed = int(seed)
        self._state = self._initial_state()
        return self.observe()

    def _state_id(self) -> str:
        return content_hash(self.snapshot(include_hidden=True))

    def observe(self) -> Observation:
        state = self._state
        acceleration = state.acceleration_m_s2
        velocity = state.initial_velocity_m_s + acceleration * state.duration_s
        position = (
            state.initial_velocity_m_s * state.duration_s
            + 0.5 * acceleration * state.duration_s**2
        )
        readings: dict[str, float | None] = {
            "kinematic_acceleration_m_s2": acceleration,
            "final_velocity_m_s": velocity,
            "position_m": position,
            "force_sensor_n": (
                state.hidden_force_n if state.force_sensor_visible else None
            ),
            "mass_sensor_kg": (
                state.hidden_mass_kg if state.mass_sensor_visible else None
            ),
        }
        return Observation(
            observation_id=f"{state.scenario_id}-obs-{state.step:03d}",
            state_id=self._state_id(),
            step=state.step,
            values={
                "scenario_id": state.scenario_id,
                "duration_s": state.duration_s,
                "initial_velocity_m_s": state.initial_velocity_m_s,
                "force_sensor_visible": state.force_sensor_visible,
                "mass_sensor_visible": state.mass_sensor_visible,
            },
            sensor_readings=readings,
            invariant_results=self.check_invariants(),
            metadata={
                "model": "newtonian-force-mass-cart-v0.3",
                "cause_hidden_from_agent": True,
                "deterministic_seed": self._seed,
            },
        )

    def available_interventions(self) -> list[Intervention]:
        return [
            Intervention("repeat_observation", rationale="test sensor stability"),
            Intervention("change_duration", {"duration_s": 3.0}),
            Intervention("scale_system", {"factor": 2.0}),
            Intervention("add_equal_payload", {"payload_kg": 2.0}),
            Intervention("expose_force_sensor", rationale="probe a latent parameter"),
            Intervention("expose_mass_sensor", rationale="probe a second latent parameter"),
        ]

    def intervene(self, action: Intervention) -> Transition:
        previous = self._state_id()
        state = self._state
        parameters = action.parameters
        if action.action_type == "repeat_observation":
            next_state = replace(state, step=state.step + 1)
        elif action.action_type == "change_duration":
            duration = float(parameters.get("duration_s", 3.0))
            if duration <= 0:
                raise ValueError("duration_s must be positive")
            next_state = replace(state, duration_s=duration, step=state.step + 1)
        elif action.action_type == "scale_system":
            factor = float(parameters.get("factor", 2.0))
            if factor <= 0:
                raise ValueError("factor must be positive")
            next_state = replace(
                state,
                hidden_force_n=state.hidden_force_n * factor,
                hidden_mass_kg=state.hidden_mass_kg * factor,
                step=state.step + 1,
            )
        elif action.action_type == "add_equal_payload":
            payload = float(parameters.get("payload_kg", 2.0))
            if payload <= 0:
                raise ValueError("payload_kg must be positive")
            next_state = replace(
                state,
                hidden_mass_kg=state.hidden_mass_kg + payload,
                step=state.step + 1,
            )
        elif action.action_type == "expose_force_sensor":
            next_state = replace(state, force_sensor_visible=True, step=state.step + 1)
        elif action.action_type == "expose_mass_sensor":
            next_state = replace(state, mass_sensor_visible=True, step=state.step + 1)
        else:
            raise ValueError(f"unsupported intervention: {action.action_type}")
        self._state = next_state
        return Transition(previous, action, self.observe(), self._seed)

    def check_invariants(self) -> dict[str, bool]:
        state = self._state
        values = (
            state.hidden_force_n,
            state.hidden_mass_kg,
            state.duration_s,
            state.initial_velocity_m_s,
        )
        return {
            "finite_state": all(isfinite(value) for value in values),
            "positive_mass": state.hidden_mass_kg > 0,
            "positive_duration": state.duration_s > 0,
            "nonzero_force": state.hidden_force_n != 0,
        }

    def snapshot(self, *, include_hidden: bool = False) -> dict[str, Any]:
        state = self._state
        visible: dict[str, Any] = {
            "scenario_id": state.scenario_id,
            "duration_s": state.duration_s,
            "initial_velocity_m_s": state.initial_velocity_m_s,
            "force_sensor_visible": state.force_sensor_visible,
            "mass_sensor_visible": state.mass_sensor_visible,
            "step": state.step,
            "seed": self._seed,
        }
        if include_hidden:
            visible.update(
                {
                    "hidden_force_n": state.hidden_force_n,
                    "hidden_mass_kg": state.hidden_mass_kg,
                    "force_mass_ratio": state.acceleration_m_s2,
                }
            )
        return visible
