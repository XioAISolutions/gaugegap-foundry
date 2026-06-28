from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

import pytest

from gaugegap.scientific_search_spaces import HyperchargeState, repair_hypercharge, research_maturity_graph
from gaugegap.search_forge import WeightedGraph, astar, dijkstra, manhattan, rectangular_grid
from gaugegap.symbolic_search import evaluate, null_distance_test


def test_dijkstra_finds_known_minimum() -> None:
    graph = WeightedGraph()
    graph.add_edge("s", "a", 1)
    graph.add_edge("a", "g", 2)
    graph.add_edge("s", "g", 10)
    result = dijkstra(graph, "s", "g")
    assert result.path == ("s", "a", "g")
    assert result.path_cost == 3
    assert result.certificate()["result_hash"]


def test_negative_edge_is_rejected() -> None:
    graph = WeightedGraph()
    with pytest.raises(ValueError):
        graph.add_edge("a", "b", -1)


def test_astar_matches_dijkstra_with_consistent_manhattan_heuristic() -> None:
    graph = rectangular_grid(8, 6, blocked={(3, 1), (3, 2), (3, 3), (5, 4)})
    start, goal = (0, 0), (7, 5)
    baseline = dijkstra(graph, start, goal)
    guided = astar(
        graph,
        start,
        goal,
        manhattan(goal),
        heuristic_name="manhattan",
        admissible_declared=True,
    )
    assert guided.path_cost == baseline.path_cost
    assert guided.heuristic_consistent is True
    assert len(guided.expanded_order) <= len(baseline.expanded_order)


def test_hypercharge_repair_recovers_standard_assignment() -> None:
    start = HyperchargeState(
        Fraction(1, 6), Fraction(7, 10), Fraction(-1, 3), Fraction(-1, 2), Fraction(-1)
    )
    goal = HyperchargeState(
        Fraction(1, 6), Fraction(2, 3), Fraction(-1, 3), Fraction(-1, 2), Fraction(-1)
    )
    result = repair_hypercharge(start, goal, field="y_u", step=Fraction(1, 30), use_astar=True)
    assert result.found
    assert result.path[-1].anomaly_free
    assert result.heuristic_consistent is True


def test_research_graph_prefers_evidence_path() -> None:
    result = dijkstra(research_maturity_graph(), "idea", "reviewer-packet")
    assert result.path == (
        "idea",
        "toy-model",
        "known-answer-test",
        "validated-numerics",
        "cross-validation",
        "reviewer-packet",
    )
    assert result.path_cost == 11


def test_historical_hebrew_examples_are_exact() -> None:
    assert evaluate("חי", cipher_name="hebrew-standard").value == 18
    assert evaluate("משיח", cipher_name="hebrew-standard").value == 358
    assert evaluate("נחש", cipher_name="hebrew-standard").value == 358


def test_null_model_is_deterministic_and_bounded() -> None:
    first = null_distance_test("SEARCH FORGE", target=113, trials=100, seed=72)
    second = null_distance_test("SEARCH FORGE", target=113, trials=100, seed=72)
    assert first == second
    assert 0 < first.empirical_p_value <= 1
    assert first.trials == 100


def test_search_forge_generates_complete_offline_bundle(tmp_path: Path) -> None:
    output = tmp_path / "site"
    preview = tmp_path / "preview.svg"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_search_forge.py",
            "--output-dir",
            str(output),
            "--preview",
            str(preview),
        ],
        check=True,
    )
    payload = json.loads((output / "search-forge.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "gaugegap.search_forge.v1"
    assert payload["grid"]["dijkstra"]["path_cost"] == payload["grid"]["astar"]["path_cost"]
    boundary = payload["symbolic"]["claim_boundary"].lower()
    assert "symbolic association" in boundary
    assert "not evidence" in boundary
    assert (output / "index.html").stat().st_size > 5000
    assert preview.read_text(encoding="utf-8").startswith("<svg")
