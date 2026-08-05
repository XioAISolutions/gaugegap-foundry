"""Hypothesis records and deterministic prediction policies for Jump Lab."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hypothesis:
    hypothesis_id: str
    hypothesis_class: str
    statement: str
    assumptions: list[str]
    falsifiers: list[str]
    score: float = 0.5
    status: str = "active"
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.hypothesis_id,
            "class": self.hypothesis_class,
            "statement": self.statement,
            "assumptions": list(self.assumptions),
            "falsifiers": list(self.falsifiers),
            "score": round(self.score, 6),
            "status": self.status,
            "evidence_for": list(self.evidence_for),
            "evidence_against": list(self.evidence_against),
        }


def default_elevator_hypotheses() -> list[Hypothesis]:
    """Return diverse explanations, including ordinary error explanations."""
    return [
        Hypothesis(
            "H1",
            "measurement_error",
            "Matching readings are caused by unstable or faulty sensors.",
            ["sensor errors are repeat-dependent"],
            ["stable repeated readings across both boxes"],
            score=0.35,
        ),
        Hypothesis(
            "H2",
            "object_specific_force",
            "A hidden force depends on the test object's mass or composition.",
            ["force coupling is object-dependent"],
            ["mass-normalized acceleration and composition changes remain invariant"],
            score=0.40,
        ),
        Hypothesis(
            "H3",
            "hidden_uniform_force",
            "Both boxes contain the same hidden downward force.",
            ["the cabin itself is not accelerating relative to an external frame"],
            ["different external cabin accelerations with matching local mechanics"],
            score=0.45,
        ),
        Hypothesis(
            "H4",
            "reference_frame_equivalence",
            "Uniform upward frame acceleration and uniform downward gravity produce equivalent tested local mechanical observations.",
            [
                "local enclosed measurements",
                "uniform fields and acceleration",
                "non-relativistic mechanical tests",
            ],
            ["a tested local mechanical observable differs beyond tolerance when effective acceleration is matched"],
            score=0.50,
        ),
    ]
