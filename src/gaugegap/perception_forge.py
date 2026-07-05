"""Finite fitness-vs-truth perception simulations.

This is an auditable toy model inspired by Hoffman's interface theory of
perception and fitness-beats-truth work.  It tests a narrow claim: under a fixed
finite percept budget and non-monotone payoffs, an interface strategy that groups
states by action-relevant fitness can outcompete a truth-coded strategy that
groups states by objective order.  It does not settle the metaphysics of space,
time, objects, or consciousness.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import numpy as np

CLAIM_BOUNDARY = (
    "finite evolutionary-game toy model only; not a proof that perception is "
    "false, not a neuroscience result, and not evidence for or against conscious "
    "realism, quantum interpretations, or spirituality"
)


@dataclass(frozen=True)
class StrategyAudit:
    name: str
    expected_payoff: float
    initial_share: float
    final_share: float
    extinct: bool
    percept_count: int
    coding_rule: str

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PerceptionWorldAudit:
    world_id: str
    state_count: int
    action_count: int
    percept_count: int
    payoff_period: int
    truth_payoff: float
    interface_payoff: float
    payoff_advantage: float
    truth_extinct: bool
    interface_dominates: bool
    strategies: tuple[StrategyAudit, ...]

    def summary(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["strategies"] = [strategy.summary() for strategy in self.strategies]
        return payload


@dataclass(frozen=True)
class PerceptionForgeReport:
    schema: str
    benchmark_id: str
    world_count: int
    truth_extinction_fraction: float
    interface_win_fraction: float
    minimum_payoff_advantage: float
    passed: bool
    worlds: tuple[PerceptionWorldAudit, ...]
    controls: dict[str, Any]
    claim_level: str
    claim_boundary: str
    exclusions: tuple[str, ...]

    def summary(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "benchmark_id": self.benchmark_id,
            "world_count": self.world_count,
            "truth_extinction_fraction": self.truth_extinction_fraction,
            "interface_win_fraction": self.interface_win_fraction,
            "minimum_payoff_advantage": self.minimum_payoff_advantage,
            "passed": self.passed,
            "worlds": [world.summary() for world in self.worlds],
            "controls": self.controls,
            "claim_level": self.claim_level,
            "claim_boundary": self.claim_boundary,
            "exclusions": list(self.exclusions),
        }


def _target_actions(
    *,
    state_count: int,
    action_count: int,
    payoff_period: int,
    phase: int,
) -> np.ndarray:
    states = np.arange(state_count)
    # Non-monotone objective-to-fitness relation: the best action cycles as the
    # hidden state increases, so equal-width truth bins alias distinct payoffs.
    return ((states * payoff_period + phase) % action_count).astype(int)


def payoff_matrix(
    *,
    state_count: int,
    action_count: int,
    payoff_period: int,
    phase: int = 0,
    miss_payoff: float = 0.05,
) -> np.ndarray:
    if state_count <= 1 or action_count <= 1:
        raise ValueError("state_count and action_count must exceed one")
    if payoff_period <= 0:
        raise ValueError("payoff_period must be positive")
    if not 0.0 <= miss_payoff < 1.0:
        raise ValueError("miss_payoff must be in [0, 1)")
    targets = _target_actions(
        state_count=state_count,
        action_count=action_count,
        payoff_period=payoff_period,
        phase=phase,
    )
    payoff = np.full((state_count, action_count), miss_payoff, dtype=float)
    payoff[np.arange(state_count), targets] = 1.0
    return payoff


def _truth_percepts(state_count: int, percept_count: int) -> np.ndarray:
    edges = np.linspace(0, state_count, percept_count + 1)
    percepts = np.zeros(state_count, dtype=int)
    for index in range(percept_count):
        lo = int(round(edges[index]))
        hi = int(round(edges[index + 1]))
        percepts[lo:hi] = index
    return percepts


def _interface_percepts(payoff: np.ndarray, percept_count: int) -> np.ndarray:
    target = np.argmax(payoff, axis=1)
    if percept_count < payoff.shape[1]:
        return target % percept_count
    return target


def _expected_payoff(payoff: np.ndarray, percepts: np.ndarray) -> float:
    state_count = payoff.shape[0]
    total = 0.0
    for percept in sorted(set(int(value) for value in percepts)):
        states = np.flatnonzero(percepts == percept)
        average = payoff[states].mean(axis=0)
        action = int(np.argmax(average))
        total += float(payoff[states, action].sum())
    return total / state_count


def _replicator(
    payoffs: np.ndarray,
    *,
    generations: int,
    initial: tuple[float, float] = (0.5, 0.5),
) -> np.ndarray:
    shares = np.asarray(initial, dtype=float)
    shares = shares / shares.sum()
    for _ in range(generations):
        weighted = shares * payoffs
        total = float(weighted.sum())
        if total <= 0.0 or not math.isfinite(total):
            raise ValueError("invalid total fitness")
        shares = weighted / total
    return shares


def audit_world(
    *,
    world_id: str = "world-000",
    state_count: int = 64,
    action_count: int = 4,
    percept_count: int = 4,
    payoff_period: int = 3,
    phase: int = 0,
    generations: int = 80,
    extinction_threshold: float = 1e-6,
) -> PerceptionWorldAudit:
    payoff = payoff_matrix(
        state_count=state_count,
        action_count=action_count,
        payoff_period=payoff_period,
        phase=phase,
    )
    truth_percepts = _truth_percepts(state_count, percept_count)
    interface_percepts = _interface_percepts(payoff, percept_count)
    truth_payoff = _expected_payoff(payoff, truth_percepts)
    interface_payoff = _expected_payoff(payoff, interface_percepts)
    shares = _replicator(np.asarray([truth_payoff, interface_payoff]), generations=generations)
    truth_extinct = bool(shares[0] < extinction_threshold)
    strategies = (
        StrategyAudit(
            name="truth-coded",
            expected_payoff=float(truth_payoff),
            initial_share=0.5,
            final_share=float(shares[0]),
            extinct=truth_extinct,
            percept_count=percept_count,
            coding_rule="equal-width bins over objective hidden state",
        ),
        StrategyAudit(
            name="fitness-interface",
            expected_payoff=float(interface_payoff),
            initial_share=0.5,
            final_share=float(shares[1]),
            extinct=bool(shares[1] < extinction_threshold),
            percept_count=percept_count,
            coding_rule="bins keyed to action-relevant fitness payoff",
        ),
    )
    return PerceptionWorldAudit(
        world_id=world_id,
        state_count=state_count,
        action_count=action_count,
        percept_count=percept_count,
        payoff_period=payoff_period,
        truth_payoff=float(truth_payoff),
        interface_payoff=float(interface_payoff),
        payoff_advantage=float(interface_payoff - truth_payoff),
        truth_extinct=truth_extinct,
        interface_dominates=interface_payoff > truth_payoff,
        strategies=strategies,
    )


def run_perception_forge(
    *,
    world_count: int = 12,
    state_count: int = 64,
    action_count: int = 4,
    percept_count: int = 4,
    generations: int = 80,
) -> PerceptionForgeReport:
    if world_count <= 0:
        raise ValueError("world_count must be positive")
    payoff_periods = (3, 5, 6, 7, 9)
    worlds = tuple(
        audit_world(
            world_id=f"world-{index:03d}",
            state_count=state_count,
            action_count=action_count,
            percept_count=percept_count,
            payoff_period=payoff_periods[index % len(payoff_periods)],
            phase=index % action_count,
            generations=generations,
        )
        for index in range(world_count)
    )
    truth_extinctions = sum(world.truth_extinct for world in worlds)
    interface_wins = sum(world.interface_dominates for world in worlds)
    minimum_advantage = min(world.payoff_advantage for world in worlds)
    control_payoff = payoff_matrix(
        state_count=state_count,
        action_count=action_count,
        payoff_period=3,
        phase=0,
    )
    rich_truth = _expected_payoff(control_payoff, np.arange(state_count))
    rich_interface = _expected_payoff(control_payoff, _interface_percepts(control_payoff, state_count))
    return PerceptionForgeReport(
        schema="gaugegap.perception_forge.v1",
        benchmark_id="perception-0001-fitness-interface",
        world_count=world_count,
        truth_extinction_fraction=truth_extinctions / world_count,
        interface_win_fraction=interface_wins / world_count,
        minimum_payoff_advantage=float(minimum_advantage),
        passed=truth_extinctions == world_count and interface_wins == world_count,
        worlds=worlds,
        controls={
            "same_percept_budget": percept_count,
            "rich_truth_control_payoff": float(rich_truth),
            "rich_interface_control_payoff": float(rich_interface),
            "rich_truth_control_note": (
                "With one percept per state and an action payoff oracle, truth-coded "
                "perception is no longer resource-limited in this toy setup."
            ),
        },
        claim_level="reproducible_finite_result",
        claim_boundary=CLAIM_BOUNDARY,
        exclusions=(
            "does not show that human perception is globally false",
            "does not establish that space-time is non-fundamental",
            "does not model real nervous systems or ecological learning",
            "does not adjudicate conscious realism or quantum-foundation claims",
        ),
    )
