"""Deterministic simple-pendulum holdout world.

Two hidden systems use different length and gravity values but the same L/g ratio,
so their periods initially match. Interventions can preserve the ratio, break it,
expose latent parameters, or leave the small-angle scope. This is an idealized
Newtonian toy model, not a laboratory-grade pendulum simulator.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite, pi, sqrt
from typing import Any

from .contracts import Intervention, Observation, Transition, content_hash


@dataclass(frozen=True)
class PendulumState:
    scenario_id: str
    hidden_length_m: float
    hidden_gravity_m_s2: float
    amplitude_rad: float = 0.12
    length_sensor_visible: bool = False
    gravity_sensor_visible: bool = False
    step: int = 0

    @property
    def ratio(self) -> float:
        return self.hidden_length_m / self.hidden_gravity_m_s2

    @property
    def small_angle_period_s(self) -> float:
        return 2.0 * pi * sqrt(self.ratio)

    @property
    def corrected_period_s(self) -> float:
        theta = self.amplitude_rad
        correction = 1.0 + theta**2 / 16.0 + 11.0 * theta**4 / 3072.0
        return self.small_angle_period_s * correction


class PendulumWorld:
    VALID_SCENARIOS = {"earth_short", "strong_long"}

    def __init__(self, scenario: str = "earth_short") -> None:
        if scenario not in self.VALID_SCENARIOS:
            raise ValueError(f"unknown scenario: {scenario}")
        self._scenario = scenario
        self._seed = 0
        self._state = self._initial_state()

    def _initial_state(self) -> PendulumState:
        if self._scenario == "earth_short":
            return PendulumState("pendulum-box-A", 1.0, 9.81)
        return PendulumState("pendulum-box-B", 4.0, 39.24)

    def reset(self, seed: int = 0) -> Observation:
        self._seed = int(seed)
        self._state = self._initial_state()
        return self.observe()

    def _state_id(self) -> str:
        return content_hash(self.snapshot(include_hidden=True))

    def observe(self) -> Observation:
        state = self._state
        small = state.small_angle_period_s
        corrected = state.corrected_period_s
        readings: dict[str, float | None] = {
            "period_s": corrected,
            "small_angle_period_s": small,
            "amplitude_correction_s": corrected - small,
            "length_sensor_m": state.hidden_length_m if state.length_sensor_visible else None,
            "gravity_sensor_m_s2": (
                state.hidden_gravity_m_s2 if state.gravity_sensor_visible else None
            ),
        }
        return Observation(
            observation_id=f"{state.scenario_id}-obs-{state.step:03d}",
            state_id=self._state_id(),
            step=state.step,
            values={
                "scenario_id": state.scenario_id,
                "amplitude_rad": state.amplitude_rad,
                "length_sensor_visible": state.length_sensor_visible,
                "gravity_sensor_visible": state.gravity_sensor_visible,
            },
            sensor_readings=readings,
            invariant_results=self.check_invariants(),
            metadata={
                "model": "ideal-simple-pendulum-v0.4",
                "cause_hidden_from_agent": True,
                "deterministic_seed": self._seed,
            },
        )

    def available_interventions(self) -> list[Intervention]:
        return [
            Intervention("repeat_observation", rationale="test period stability"),
            Intervention("scale_length_and_gravity", {"factor": 2.0}),
            Intervention("add_equal_length", {"length_m": 1.0}),
            Intervention("increase_amplitude", {"amplitude_rad": 1.0}),
            Intervention("expose_length_sensor", rationale="probe a latent parameter"),
            Intervention("expose_gravity_sensor", rationale="probe a second latent parameter"),
        ]

    def intervene(self, action: Intervention) -> Transition:
        previous = self._state_id()
        state = self._state
        parameters = action.parameters
        if action.action_type == "repeat_observation":
            next_state = replace(state, step=state.step + 1)
        elif action.action_type == "scale_length_and_gravity":
            factor = float(parameters.get("factor", 2.0))
            if factor <= 0:
                raise ValueError("factor must be positive")
            next_state = replace(
                state,
                hidden_length_m=state.hidden_length_m * factor,
                hidden_gravity_m_s2=state.hidden_gravity_m_s2 * factor,
                step=state.step + 1,
            )
        elif action.action_type == "add_equal_length":
            length = float(parameters.get("length_m", 1.0))
            if length <= 0:
                raise ValueError("length_m must be positive")
            next_state = replace(
                state,
                hidden_length_m=state.hidden_length_m + length,
                step=state.step + 1,
            )
        elif action.action_type == "increase_amplitude":
            amplitude = float(parameters.get("amplitude_rad", 1.0))
            if amplitude <= 0 or amplitude >= 1.4:
                raise ValueError("amplitude_rad must be in (0, 1.4)")
            next_state = replace(state, amplitude_rad=amplitude, step=state.step + 1)
        elif action.action_type == "expose_length_sensor":
            next_state = replace(state, length_sensor_visible=True, step=state.step + 1)
        elif action.action_type == "expose_gravity_sensor":
            next_state = replace(state, gravity_sensor_visible=True, step=state.step + 1)
        else:
            raise ValueError(f"unsupported intervention: {action.action_type}")
        self._state = next_state
        return Transition(previous, action, self.observe(), self._seed)

    def check_invariants(self) -> dict[str, bool]:
        state = self._state
        values = (
            state.hidden_length_m,
            state.hidden_gravity_m_s2,
            state.amplitude_rad,
        )
        return {
            "finite_state": all(isfinite(value) for value in values),
            "positive_length": state.hidden_length_m > 0,
            "positive_gravity": state.hidden_gravity_m_s2 > 0,
            "supported_amplitude": 0 < state.amplitude_rad < 1.4,
        }

    def snapshot(self, *, include_hidden: bool = False) -> dict[str, Any]:
        state = self._state
        visible: dict[str, Any] = {
            "scenario_id": state.scenario_id,
            "amplitude_rad": state.amplitude_rad,
            "length_sensor_visible": state.length_sensor_visible,
            "gravity_sensor_visible": state.gravity_sensor_visible,
            "step": state.step,
            "seed": self._seed,
        }
        if include_hidden:
            visible.update(
                {
                    "hidden_length_m": state.hidden_length_m,
                    "hidden_gravity_m_s2": state.hidden_gravity_m_s2,
                    "length_gravity_ratio": state.ratio,
                }
            )
        return visible
