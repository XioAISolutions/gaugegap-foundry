"""A small deterministic spiking salience controller.

The controller ranks attention; it never determines scientific truth. It uses a
leaky-integrate-and-fire style accumulator and a simple STDP-like association
matrix that can be updated after useful interventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from typing import Iterable


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


@dataclass
class SalienceController:
    threshold: float = 0.55
    leak: float = 0.72
    membrane: dict[str, float] = field(default_factory=dict)
    associations: dict[str, float] = field(default_factory=dict)

    def _input_current(self, candidate: SalienceCandidate) -> float:
        learned = self.associations.get(candidate.name, 0.0)
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

    def reinforce(self, name: str, *, useful: bool, learning_rate: float = 0.05) -> None:
        delta = learning_rate if useful else -learning_rate
        self.associations[name] = max(
            -0.25,
            min(0.25, self.associations.get(name, 0.0) + delta),
        )
