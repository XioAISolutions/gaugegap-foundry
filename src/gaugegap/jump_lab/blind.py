"""Blinded model-selection helpers for holdout discovery benchmarks.

This module deliberately narrows the claim: the executive selects among a
pre-registered prediction deck whose semantic labels are withheld until after
selection. That is auditable model selection, not open-ended hypothesis invention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import random
from typing import Any, Iterable


@dataclass(frozen=True)
class BlindModelSpec:
    key: str
    hypothesis_class: str
    statement: str
    assumptions: tuple[str, ...]
    falsifiers: tuple[str, ...]
    predictions: dict[str, str]
    initial_score: float = 0.25


@dataclass
class BlindModelState:
    blind_id: str
    key: str
    score: float
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)


class BlindModelDeck:
    """Randomize model identifiers and update them from outcome signatures."""

    def __init__(self, specs: Iterable[BlindModelSpec], *, seed: int) -> None:
        self._specs = {spec.key: spec for spec in specs}
        if len(self._specs) < 2:
            raise ValueError("a blind deck requires at least two models")
        keys = sorted(self._specs)
        rng = random.Random(int(seed))
        ids = [f"B{index + 1}" for index in range(len(keys))]
        rng.shuffle(ids)
        self._states = {
            key: BlindModelState(ids[index], key, self._specs[key].initial_score)
            for index, key in enumerate(keys)
        }

    def agent_deck(self) -> list[dict[str, Any]]:
        """Return only anonymous prediction fingerprints, not semantic statements."""
        rows = []
        for key, state in sorted(self._states.items(), key=lambda item: item[1].blind_id):
            spec = self._specs[key]
            rows.append(
                {
                    "id": state.blind_id,
                    "prediction_fingerprint": dict(sorted(spec.predictions.items())),
                    "statement_visible": False,
                }
            )
        return rows

    def update(self, action: str, observed_signature: str, *, evidence_ref: str) -> None:
        for key, state in self._states.items():
            predicted = self._specs[key].predictions.get(action, "unspecified")
            if predicted == "unspecified":
                continue
            if predicted == observed_signature:
                state.score += 0.18
                state.evidence_for.append(evidence_ref)
            else:
                state.score -= 0.24
                state.evidence_against.append(evidence_ref)
            state.score = max(0.0, min(1.0, state.score))

    def winner(self) -> BlindModelState:
        return max(self._states.values(), key=lambda item: (item.score, item.blind_id))

    def revealed_hypotheses(self) -> list[dict[str, Any]]:
        rows = []
        for key, state in sorted(self._states.items(), key=lambda item: item[1].blind_id):
            spec = self._specs[key]
            rows.append(
                {
                    "id": state.blind_id,
                    "class": spec.hypothesis_class,
                    "statement": spec.statement,
                    "assumptions": list(spec.assumptions),
                    "falsifiers": list(spec.falsifiers),
                    "score": round(state.score, 6),
                    "status": "rejected" if state.score <= 0.18 else "active",
                    "evidence_for": list(state.evidence_for),
                    "evidence_against": list(state.evidence_against),
                    "semantic_key": key,
                    "statement_visible_to_agent": False,
                }
            )
        return rows

    def mapping_hash(self) -> str:
        payload = {
            state.blind_id: key
            for key, state in sorted(self._states.items(), key=lambda item: item[1].blind_id)
        }
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "sha256:" + sha256(text.encode("utf-8")).hexdigest()

    def selected_key(self) -> str:
        return self.winner().key


def forbidden_term_hits(value: Any, forbidden_terms: Iterable[str]) -> list[str]:
    """Find target-language leakage in an agent-visible JSON-like payload."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
    return sorted(
        {
            term.strip().lower()
            for term in forbidden_terms
            if term.strip() and term.strip().lower() in text
        }
    )
