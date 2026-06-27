"""Deterministic finite graph search with auditable result certificates.

The module intentionally supports only non-negative edge costs.  Dijkstra is
therefore an exact finite-graph baseline.  A* can make the same optimality claim
only when its registered heuristic is admissible; consistency can be checked on
the declared finite graph.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import heapq
import json
import math
from typing import Callable, Hashable, Iterable, Mapping, TypeVar

Node = TypeVar("Node", bound=Hashable)
Heuristic = Callable[[Node], float]


@dataclass(frozen=True)
class Edge:
    source: Hashable
    target: Hashable
    cost: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.cost) or self.cost < 0:
            raise ValueError("edge costs must be finite and non-negative")


@dataclass
class WeightedGraph:
    """Small deterministic directed graph used by Search Forge."""

    _adjacency: dict[Hashable, list[tuple[Hashable, float]]] = field(default_factory=dict)

    def add_node(self, node: Hashable) -> None:
        self._adjacency.setdefault(node, [])

    def add_edge(self, source: Hashable, target: Hashable, cost: float, *, bidirectional: bool = False) -> None:
        edge = Edge(source, target, float(cost))
        self.add_node(edge.source)
        self.add_node(edge.target)
        self._adjacency[edge.source].append((edge.target, edge.cost))
        self._adjacency[edge.source].sort(key=lambda item: (repr(item[0]), item[1]))
        if bidirectional:
            self.add_edge(target, source, cost, bidirectional=False)

    def neighbors(self, node: Hashable) -> tuple[tuple[Hashable, float], ...]:
        return tuple(self._adjacency.get(node, ()))

    @property
    def nodes(self) -> tuple[Hashable, ...]:
        return tuple(sorted(self._adjacency, key=repr))

    @property
    def edges(self) -> tuple[Edge, ...]:
        return tuple(
            Edge(source, target, cost)
            for source in self.nodes
            for target, cost in self.neighbors(source)
        )

    def digest(self) -> str:
        serial = [
            {"source": repr(edge.source), "target": repr(edge.target), "cost": edge.cost}
            for edge in self.edges
        ]
        payload = json.dumps(serial, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SearchResult:
    algorithm: str
    start: Hashable
    goal: Hashable
    path: tuple[Hashable, ...]
    path_cost: float
    expanded_order: tuple[Hashable, ...]
    graph_hash: str
    heuristic_name: str | None = None
    heuristic_admissible: bool | None = None
    heuristic_consistent: bool | None = None
    claim_boundary: str = ""

    @property
    def found(self) -> bool:
        return bool(self.path)

    def certificate(self) -> dict[str, object]:
        body: dict[str, object] = {
            "schema": "gaugegap.search_certificate.v1",
            "algorithm": self.algorithm,
            "start": repr(self.start),
            "goal": repr(self.goal),
            "found": self.found,
            "path": [repr(node) for node in self.path],
            "path_cost": self.path_cost,
            "nodes_expanded": len(self.expanded_order),
            "expanded_order": [repr(node) for node in self.expanded_order],
            "graph_hash": self.graph_hash,
            "claim_boundary": self.claim_boundary,
        }
        if self.heuristic_name is not None:
            body["heuristic"] = {
                "name": self.heuristic_name,
                "admissible_declared": self.heuristic_admissible,
                "consistent_on_declared_graph": self.heuristic_consistent,
            }
        unsigned = json.dumps(body, sort_keys=True, separators=(",", ":"))
        body["result_hash"] = sha256(unsigned.encode("utf-8")).hexdigest()
        return body


def _reconstruct(came_from: Mapping[Node, Node], start: Node, goal: Node) -> tuple[Node, ...]:
    if goal != start and goal not in came_from:
        return ()
    cursor = goal
    path: list[Node] = [cursor]
    while cursor != start:
        cursor = came_from[cursor]
        path.append(cursor)
    path.reverse()
    return tuple(path)


def dijkstra(graph: WeightedGraph, start: Node, goal: Node) -> SearchResult:
    """Return the least-cost path on a finite graph with non-negative costs."""

    queue: list[tuple[float, str, Node]] = [(0.0, repr(start), start)]
    distance: dict[Node, float] = {start: 0.0}
    came_from: dict[Node, Node] = {}
    expanded: list[Node] = []
    settled: set[Node] = set()

    while queue:
        current_cost, _, current = heapq.heappop(queue)
        if current in settled:
            continue
        settled.add(current)
        expanded.append(current)
        if current == goal:
            break
        for neighbor, edge_cost in graph.neighbors(current):
            candidate = current_cost + edge_cost
            if candidate < distance.get(neighbor, math.inf):
                distance[neighbor] = candidate
                came_from[neighbor] = current
                heapq.heappush(queue, (candidate, repr(neighbor), neighbor))

    path = _reconstruct(came_from, start, goal)
    return SearchResult(
        algorithm="dijkstra",
        start=start,
        goal=goal,
        path=path,
        path_cost=distance.get(goal, math.inf),
        expanded_order=tuple(expanded),
        graph_hash=graph.digest(),
        claim_boundary=(
            "Optimal over the declared finite graph because all registered edge costs "
            "are finite and non-negative."
        ),
    )


def heuristic_is_consistent(graph: WeightedGraph, heuristic: Heuristic[Node], goal: Node, *, atol: float = 1e-12) -> bool:
    if abs(float(heuristic(goal))) > atol:
        return False
    return all(
        float(heuristic(edge.source)) <= edge.cost + float(heuristic(edge.target)) + atol
        for edge in graph.edges
    )


def astar(
    graph: WeightedGraph,
    start: Node,
    goal: Node,
    heuristic: Heuristic[Node],
    *,
    heuristic_name: str = "custom",
    admissible_declared: bool = False,
) -> SearchResult:
    """Run A* and attach the heuristic contract to the result certificate."""

    queue: list[tuple[float, float, str, Node]] = [
        (float(heuristic(start)), 0.0, repr(start), start)
    ]
    g_score: dict[Node, float] = {start: 0.0}
    came_from: dict[Node, Node] = {}
    expanded: list[Node] = []
    closed: set[Node] = set()

    while queue:
        _, current_cost, _, current = heapq.heappop(queue)
        if current in closed:
            continue
        closed.add(current)
        expanded.append(current)
        if current == goal:
            break
        for neighbor, edge_cost in graph.neighbors(current):
            candidate = current_cost + edge_cost
            if candidate < g_score.get(neighbor, math.inf):
                g_score[neighbor] = candidate
                came_from[neighbor] = current
                estimate = candidate + float(heuristic(neighbor))
                heapq.heappush(queue, (estimate, candidate, repr(neighbor), neighbor))

    consistent = heuristic_is_consistent(graph, heuristic, goal)
    path = _reconstruct(came_from, start, goal)
    return SearchResult(
        algorithm="astar",
        start=start,
        goal=goal,
        path=path,
        path_cost=g_score.get(goal, math.inf),
        expanded_order=tuple(expanded),
        graph_hash=graph.digest(),
        heuristic_name=heuristic_name,
        heuristic_admissible=admissible_declared,
        heuristic_consistent=consistent,
        claim_boundary=(
            "Optimal over the declared finite graph only when the registered heuristic "
            "is admissible; consistency was checked directly on every declared edge."
        ),
    )


def rectangular_grid(
    width: int,
    height: int,
    *,
    blocked: Iterable[tuple[int, int]] = (),
    diagonal: bool = False,
) -> WeightedGraph:
    """Build a deterministic unit-cost grid graph for visual comparison."""

    if width < 1 or height < 1:
        raise ValueError("grid dimensions must be positive")
    walls = set(blocked)
    graph = WeightedGraph()
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for y in range(height):
        for x in range(width):
            node = (x, y)
            if node in walls:
                continue
            graph.add_node(node)
            for dx, dy in steps:
                neighbor = (x + dx, y + dy)
                if 0 <= neighbor[0] < width and 0 <= neighbor[1] < height and neighbor not in walls:
                    graph.add_edge(node, neighbor, math.sqrt(2.0) if dx and dy else 1.0)
    return graph


def manhattan(goal: tuple[int, int]) -> Callable[[tuple[int, int]], float]:
    return lambda node: float(abs(node[0] - goal[0]) + abs(node[1] - goal[1]))
