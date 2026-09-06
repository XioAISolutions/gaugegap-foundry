#!/usr/bin/env python3
"""Render the Lean statement DAG as a deterministic SVG.

Node colour encodes the *verification status recorded by ``lake build``*, read
from ``results/lean-forge/lean_forge_report.json`` when present.  Without a
report every node is drawn as unchecked -- the figure never shows a proved node
that Lean has not accepted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAG_PATH = ROOT / "formal" / "lean" / "dag.json"
REPORT_PATH = ROOT / "results" / "lean-forge" / "lean_forge_report.json"

PALETTE = {
    "verified": "#7ee787",
    "failed": "#ff6b6b",
    "toolchain_missing": "#8b949e",
    "skipped": "#8b949e",
    "unchecked": "#8b949e",
}


def _depths(nodes: list[dict]) -> dict[str, int]:
    by_id = {node["id"]: node for node in nodes}
    depth: dict[str, int] = {}

    def resolve(node_id: str, seen: frozenset[str]) -> int:
        if node_id in depth:
            return depth[node_id]
        if node_id in seen:
            raise ValueError(f"cycle in DAG at {node_id}")
        parents = by_id[node_id]["depends_on"]
        value = 0 if not parents else 1 + max(
            resolve(parent, seen | {node_id}) for parent in parents
        )
        depth[node_id] = value
        return value

    for node in nodes:
        resolve(node["id"], frozenset())
    return depth


def render(dag: dict, statuses: dict[str, str]) -> str:
    nodes = dag["nodes"]
    depth = _depths(nodes)
    layers: dict[int, list[dict]] = {}
    for node in nodes:
        layers.setdefault(depth[node["id"]], []).append(node)

    width, top, row_height, radius = 960, 132, 118, 26
    height = top + row_height * len(layers) + 96
    centres: dict[str, tuple[int, int]] = {}
    for level in sorted(layers):
        row = layers[level]
        y = top + row_height * level
        for index, node in enumerate(row):
            x = int(width * (index + 1) / (len(row) + 1))
            centres[node["id"]] = (x, y)

    edges = "".join(
        f'<line x1="{centres[parent][0]}" y1="{centres[parent][1] + radius}" '
        f'x2="{centres[node["id"]][0]}" y2="{centres[node["id"]][1] - radius}" '
        f'stroke="#30363d" stroke-width="2"/>'
        for node in nodes
        for parent in node["depends_on"]
    )
    circles = "".join(
        f'<circle cx="{centres[node["id"]][0]}" cy="{centres[node["id"]][1]}" r="{radius}" '
        f'fill="#0d1117" stroke="{PALETTE.get(statuses.get(node["id"], "unchecked"), "#8b949e")}" '
        f'stroke-width="3"/>'
        f'<text x="{centres[node["id"]][0]}" y="{centres[node["id"]][1] + 6}" '
        f'fill="#e6edf3" text-anchor="middle" font-family="ui-monospace,monospace" '
        f'font-size="16">{node["id"]}</text>'
        for node in nodes
    )
    legend = " · ".join(
        f"{name}: {sum(1 for value in statuses.values() if value == name)}"
        for name in ("verified", "failed")
    )
    unchecked = sum(
        1 for node in nodes if statuses.get(node["id"], "unchecked") not in {"verified", "failed"}
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="{width}" height="{height}" rx="20" fill="#0b0e14"/>
<text x="44" y="54" fill="#e6edf3" font-family="system-ui" font-size="26" font-weight="700">Anomaly Forge statement DAG</text>
<text x="44" y="84" fill="#8b949e" font-family="system-ui" font-size="15">{len(nodes)} statements · {legend} · unchecked: {unchecked}</text>
{edges}{circles}
<text x="{width // 2}" y="{height - 34}" fill="#6e7681" text-anchor="middle" font-family="monospace" font-size="11">colour reflects lake build only · exact rational identities for a declared finite inventory</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dag", type=Path, default=DAG_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "figures" / "anomaly-forge" / "lean-dag.svg"
    )
    args = parser.parse_args()

    dag = json.loads(args.dag.read_text(encoding="utf-8"))
    statuses: dict[str, str] = {}
    if args.report.exists():
        report = json.loads(args.report.read_text(encoding="utf-8"))
        statuses = {node["id"]: node["lean_status"] for node in report["nodes"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(dag, statuses), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
