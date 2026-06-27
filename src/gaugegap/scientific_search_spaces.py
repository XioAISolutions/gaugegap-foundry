"""Finite scientific search spaces layered on the Search Forge core."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from .anomaly_audit import Hypercharges, audit
from .search_forge import SearchResult, WeightedGraph, astar, dijkstra


@dataclass(frozen=True)
class HyperchargeState:
    y_q: Fraction
    y_u: Fraction
    y_d: Fraction
    y_l: Fraction
    y_e: Fraction
    colors: int = 3
    generations: int = 3

    def assignment(self) -> Hypercharges:
        return Hypercharges(
            colors=self.colors,
            generations=self.generations,
            y_q=self.y_q,
            y_u=self.y_u,
            y_d=self.y_d,
            y_l=self.y_l,
            y_e=self.y_e,
        )

    def anomaly_norm(self) -> Fraction:
        result = audit(self.assignment())
        return sum(
            abs(value)
            for value in (
                result.su3_u1,
                result.su2_u1,
                result.u1_cubed,
                result.gravity_u1,
            )
        )

    @property
    def anomaly_free(self) -> bool:
        return audit(self.assignment()).passes


def hypercharge_line_graph(
    start: HyperchargeState,
    *,
    field: str,
    values: Iterable[Fraction],
) -> tuple[WeightedGraph, dict[Fraction, HyperchargeState]]:
    """Create a one-dimensional exact repair space for one hypercharge."""

    if field not in {"y_q", "y_u", "y_d", "y_l", "y_e"}:
        raise ValueError(f"unsupported hypercharge field: {field}")
    ordered = sorted(set(Fraction(value) for value in values))
    if not ordered:
        raise ValueError("at least one candidate value is required")

    states: dict[Fraction, HyperchargeState] = {}
    for value in ordered:
        payload = {
            "y_q": start.y_q,
            "y_u": start.y_u,
            "y_d": start.y_d,
            "y_l": start.y_l,
            "y_e": start.y_e,
            "colors": start.colors,
            "generations": start.generations,
        }
        payload[field] = value
        states[value] = HyperchargeState(**payload)

    graph = WeightedGraph()
    for state in states.values():
        graph.add_node(state)
    for left, right in zip(ordered, ordered[1:]):
        cost = float(abs(right - left))
        graph.add_edge(states[left], states[right], cost, bidirectional=True)
    return graph, states


def repair_hypercharge(
    start: HyperchargeState,
    target: HyperchargeState,
    *,
    field: str = "y_u",
    step: Fraction = Fraction(1, 30),
    use_astar: bool = False,
) -> SearchResult:
    """Find the least-change path between two declared rational assignments."""

    if step <= 0:
        raise ValueError("step must be positive")
    start_value = getattr(start, field)
    target_value = getattr(target, field)
    lo, hi = sorted((start_value, target_value))
    count = int((hi - lo) / step)
    values = [lo + index * step for index in range(count + 1)]
    if values[-1] != hi:
        values.append(hi)
    graph, states = hypercharge_line_graph(start, field=field, values=values)
    source = states[start_value]
    goal = states[target_value]
    if not use_astar:
        return dijkstra(graph, source, goal)

    def exact_line_distance(node: HyperchargeState) -> float:
        return float(abs(getattr(node, field) - target_value))

    return astar(
        graph,
        source,
        goal,
        exact_line_distance,
        heuristic_name=f"exact-{field}-distance",
        admissible_declared=True,
    )


RESEARCH_STAGES = (
    "idea",
    "toy-model",
    "known-answer-test",
    "validated-numerics",
    "formal-certificate",
    "cross-validation",
    "reviewer-packet",
)


def research_maturity_graph() -> WeightedGraph:
    """A small declared roadmap graph with explicit maturity costs."""

    graph = WeightedGraph()
    costs = {
        ("idea", "toy-model"): 1.0,
        ("toy-model", "known-answer-test"): 2.0,
        ("known-answer-test", "validated-numerics"): 3.0,
        ("validated-numerics", "formal-certificate"): 5.0,
        ("validated-numerics", "cross-validation"): 3.0,
        ("formal-certificate", "cross-validation"): 2.0,
        ("cross-validation", "reviewer-packet"): 2.0,
        ("known-answer-test", "reviewer-packet"): 12.0,
    }
    for stage in RESEARCH_STAGES:
        graph.add_node(stage)
    for (source, target), cost in costs.items():
        graph.add_edge(source, target, cost)
    return graph
