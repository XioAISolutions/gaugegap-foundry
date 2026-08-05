"""A small deterministic spiking salience controller.

The controller ranks attention; it never determines scientific truth. It uses a
leaky-integrate-and-fire style accumulator and a simple STDP-like association
matrix that can be updated after useful interventions.

v0.3 adds semantic association keys and explicit memory snapshots. This allows a
controller to carry a bounded preference such as ``boundary_probe`` between toy
worlds without confusing action names or bypassing each world's verifier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, isfinite
from typing import Any, Iterable


@dataclass(frozen=True)
class SalienceCandidate:
    name: str
    novelty: float
    hypothesis_disagreement: float
    expected_information_gain: float
    reproducibility: float
    safety: float = 1.0
    cost: float = 0.1
    redundancy: float = 0.0
    association_key: str | None = None

    @property
    def memory_key(self) -> str:
        return self.association_key or self.name


@dataclass
class SalienceController:
    threshold: float = 0.55
    leak: float = 0.72
    membrane: dict[str, float] = field(default_factory=dict)
    associations: dict[str, float] = field(default_factory=dict)

    def _input_current(self, candidate: SalienceCandidate) -> float:
        learned = self.associations.get(candidate.memory_key, 0.0)
        excitation = (
            0.24 * candidate.novelty
            + 0.27 * candidate.hypothesis_disagreement
            + 0.30 * candidate.expected_information_gain
            + 0.12 * candidate.reproducibility
            + 0.07 * candidate.safety
            + learned
        )
        inhibition = 0.16 * candidate.cost + 0.25 * candidate.redundancy
        return excitation - inhibition

    def rank(self, candidates: Iterable[SalienceCandidate]) -> list[tuple[str, float]]:
        ranked: list[tuple[str, float]] = []
        for candidate in candidates:
            previous = self.membrane.get(candidate.name, 0.0)
            potential = self.leak * previous + self._input_current(candidate)
            spike = 1.0 / (1.0 + exp(-8.0 * (potential - self.threshold)))
            self.membrane[candidate.name] = 0.0 if spike >= 0.95 else potential
            ranked.append((candidate.name, spike))
        return sorted(ranked, key=lambda item: (-item[1], item[0]))

    def reinforce(
        self,
        name: str,
        *,
        useful: bool,
        learning_rate: float = 0.05,
        association_key: str | None = None,
    ) -> None:
        key = association_key or name
        delta = learning_rate if useful else -learning_rate
        self.associations[key] = max(
            -0.25,
            min(0.25, self.associations.get(key, 0.0) + delta),
        )

    def snapshot(self) -> dict[str, Any]:
        """Return portable learned associations, excluding transient membrane state."""
        return {
            "memory_type": "jump_lab_salience_v1",
            "threshold": self.threshold,
            "leak": self.leak,
            "associations": dict(sorted(self.associations.items())),
            "claim_boundary": (
                "This memory stores bounded attention preferences only. It does not "
                "store scientific verdicts or authorize candidate axioms."
            ),
        }

    def load_snapshot(self, snapshot: dict[str, Any]) -> None:
        if snapshot.get("memory_type") != "jump_lab_salience_v1":
            raise ValueError("unsupported salience memory snapshot")
        associations = snapshot.get("associations")
        if not isinstance(associations, dict):
            raise ValueError("salience associations must be an object")
        restored: dict[str, float] = {}
        for raw_key, raw_value in associations.items():
            key = str(raw_key)
            value = float(raw_value)
            if not key or not isfinite(value):
                raise ValueError("invalid salience association")
            restored[key] = max(-0.25, min(0.25, value))
        self.associations = restored
        self.membrane.clear()
