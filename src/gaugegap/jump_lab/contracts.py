"""Core contracts for reproducible interactive discovery worlds.

The contract deliberately separates an agent-visible observation from the hidden
state used by a benchmark evaluator. An agent may act through interventions,
but it cannot read the world's causal label directly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Protocol

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


def canonical_json(value: Any) -> str:
    """Return stable JSON suitable for hashing and replay manifests."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(value: Any) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Intervention:
    action_type: str
    parameters: dict[str, JSONScalar] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Observation:
    observation_id: str
    state_id: str
    step: int
    values: dict[str, JSONScalar]
    sensor_readings: dict[str, float | None]
    invariant_results: dict[str, bool]
    metadata: dict[str, JSONScalar] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def hash(self) -> str:
        return content_hash(self.to_dict())


@dataclass(frozen=True)
class Transition:
    previous_state_id: str
    intervention: Intervention
    observation: Observation
    deterministic_seed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "previous_state_id": self.previous_state_id,
            "intervention": self.intervention.to_dict(),
            "observation": self.observation.to_dict(),
            "deterministic_seed": self.deterministic_seed,
        }


class ExperimentalWorld(Protocol):
    """Minimal world API used by the abductive executive."""

    def reset(self, seed: int = 0) -> Observation: ...

    def observe(self) -> Observation: ...

    def intervene(self, action: Intervention) -> Transition: ...

    def available_interventions(self) -> list[Intervention]: ...

    def check_invariants(self) -> dict[str, bool]: ...

    def snapshot(self, *, include_hidden: bool = False) -> dict[str, Any]: ...
