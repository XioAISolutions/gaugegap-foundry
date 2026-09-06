"""Every Lean DAG node's exact rational mirror, in one registry.

Each Lean track keeps its own mirror module; this composes them so the gate in
``scripts/run_lean_forge.py`` has a single registry to check the DAG against.
"""
from __future__ import annotations

from typing import Callable

from gaugegap import anomaly_theorem, no_hiding_theorem

MIRROR_MODULES = (anomaly_theorem, no_hiding_theorem)

NODE_CHECKS: dict[str, Callable[[], bool]] = {}
for _module in MIRROR_MODULES:
    _overlap = set(NODE_CHECKS) & set(_module.NODE_CHECKS)
    if _overlap:
        raise RuntimeError(f"duplicate mirror node IDs: {sorted(_overlap)}")
    NODE_CHECKS.update(_module.NODE_CHECKS)


def mirror_summary() -> dict[str, object]:
    results = {node_id: check() for node_id, check in sorted(NODE_CHECKS.items())}
    return {
        "schema": "gaugegap.lean_mirror.v1",
        "nodes": results,
        "all_hold": all(results.values()),
        "claim_boundary": (
            "finite exact rational check of the Lean statements; "
            "kernel verification requires lake build"
        ),
    }
