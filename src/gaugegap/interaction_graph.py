"""Deterministic interaction-hypergraph helpers."""
from __future__ import annotations

from collections import Counter
import math
from typing import Any

from gaugegap.standard_model_catalog import StandardModelCatalog

_KIND_ORDER = {"gauge": 0, "scalar": 1, "fermion": 2, "ghost": 3}
_KIND_RADIUS = {"gauge": 0.42, "scalar": 0.62, "fermion": 0.86, "ghost": 1.02}
_KIND_PHASE = {"gauge": -2.7, "scalar": -0.5, "fermion": 0.6, "ghost": 2.7}
_KIND_SWEEP = {"gauge": 1.6, "scalar": 1.0, "fermion": 3.5, "ghost": 1.0}


def build_interaction_graph(catalog: StandardModelCatalog) -> dict[str, Any]:
    """Return stable nodes, hyperedges, and drawable centroid segments."""
    degree = Counter(fid for interaction in catalog.interactions for fid in interaction.fields)
    grouped: dict[str, list[object]] = {}
    for field in sorted(catalog.fields, key=lambda f: (_KIND_ORDER.get(f.kind, 99), f.field_id)):
        grouped.setdefault(field.kind, []).append(field)

    nodes: list[dict[str, Any]] = []
    index_by_id: dict[str, int] = {}
    for kind in sorted(grouped, key=lambda key: _KIND_ORDER.get(key, 99)):
        group = grouped[kind]
        for offset, field in enumerate(group):
            fraction = 0.5 if len(group) == 1 else offset / (len(group) - 1)
            angle = _KIND_PHASE.get(kind, 0.0) + _KIND_SWEEP.get(kind, math.pi) * fraction
            radius = _KIND_RADIUS.get(kind, 0.9)
            index_by_id[field.field_id] = len(nodes)
            nodes.append({
                "id": field.field_id,
                "label": field.label,
                "kind": field.kind,
                "x": round(radius * math.cos(angle), 7),
                "y": round(radius * math.sin(angle), 7),
                "electric_charge": field.electric_charge,
                "charge_thirds": field.charge_thirds,
                "degree": int(degree[field.field_id]),
                "multiplicity": field.multiplicity,
            })

    field_map = catalog.field_map()
    hyperedges: list[dict[str, Any]] = []
    segments: list[list[int]] = []
    sector_counts: Counter[str] = Counter()
    coupling_counts: Counter[str] = Counter()
    for interaction in sorted(catalog.interactions, key=lambda item: item.interaction_id):
        node_indices = [index_by_id[field_id] for field_id in interaction.fields]
        centroid = [
            round(sum(nodes[index][axis] for index in node_indices) / len(node_indices), 7)
            for axis in ("x", "y")
        ]
        edge_index = len(hyperedges)
        hyperedges.append({
            "id": interaction.interaction_id,
            "label": interaction.label,
            "sector": interaction.sector_id,
            "coupling": interaction.coupling,
            "fields": list(interaction.fields),
            "node_indices": node_indices,
            "centroid": centroid,
            "operator_dimension": interaction.operator_dimension,
            "parent_term": interaction.parent_term,
            "charge_sum_thirds": sum(field_map[field_id].charge_thirds for field_id in interaction.fields),
        })
        segments.extend([edge_index, node_index] for node_index in sorted(set(node_indices)))
        sector_counts[interaction.sector_id] += 1
        coupling_counts[interaction.coupling] += 1

    return {
        "nodes": nodes,
        "hyperedges": hyperedges,
        "segments": segments,
        "summary": {
            "field_nodes": len(nodes),
            "interaction_hyperedges": len(hyperedges),
            "drawable_segments": len(segments),
            "sector_counts": dict(sorted(sector_counts.items())),
            "coupling_counts": dict(sorted(coupling_counts.items())),
            "maximum_degree": max((node["degree"] for node in nodes), default=0),
        },
    }
