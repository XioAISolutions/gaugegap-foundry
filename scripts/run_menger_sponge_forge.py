#!/usr/bin/env python3
"""Run the finite Menger sponge topology/fractal forge."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.fractal_topology_forge import run_menger_forge  # noqa: E402


def _render_svg(payload: dict[str, object]) -> str:
    stages = payload["stages"]
    width = 960
    height = 420
    max_surface = max(float(stage["surface_area"]) for stage in stages)
    points = []
    bars = []
    for index, stage in enumerate(stages):
        x = 90 + index * (760 / max(1, len(stages) - 1))
        volume_h = 260 * float(stage["volume"])
        surface_h = 260 * float(stage["surface_area"]) / max_surface
        y_surface = 330 - surface_h
        points.append(f"{x:.1f},{y_surface:.1f}")
        bars.append(
            f'<rect x="{x - 18:.1f}" y="{330 - volume_h:.1f}" width="16" '
            f'height="{volume_h:.1f}" fill="#58a6ff" opacity="0.75"/>'
        )
        bars.append(
            f'<rect x="{x + 3:.1f}" y="{y_surface:.1f}" width="16" '
            f'height="{surface_h:.1f}" fill="#f2cc60" opacity="0.85"/>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="420" viewBox="0 0 960 420">'
        '<rect width="960" height="420" fill="#030303"/>'
        '<text x="48" y="54" fill="#f0f6fc" font-size="28" font-family="system-ui">Menger Sponge Forge</text>'
        '<text x="48" y="84" fill="#8b949e" font-size="14" font-family="monospace">finite stages · volume collapse · surface growth · dimension boundary</text>'
        '<line x1="70" y1="330" x2="880" y2="330" stroke="#30363d"/>'
        f'{"".join(bars)}'
        f'<polyline points="{" ".join(points)}" fill="none" stroke="#f2cc60" stroke-width="3"/>'
        '<text x="48" y="382" fill="#58a6ff" font-size="13" font-family="monospace">blue: volume</text>'
        '<text x="210" y="382" fill="#f2cc60" font-size="13" font-family="monospace">yellow: surface area</text>'
        f'<text x="520" y="382" fill="#f0f6fc" font-size="13" font-family="monospace">dim_H≈{float(payload["hausdorff_dimension"]):.6f}</text>'
        '</svg>'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--voxel-sample-limit", type=int, default=512)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "menger-0001")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    report = run_menger_forge(
        iterations=args.iterations,
        voxel_sample_limit=args.voxel_sample_limit,
    )
    payload = report.summary()
    (args.output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "stages.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(payload["stages"][0].keys()))
        writer.writeheader()
        writer.writerows(payload["stages"])
    with (args.output_dir / "voxels.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["x", "y", "z"])
        writer.writeheader()
        writer.writerows(
            {"x": point[0], "y": point[1], "z": point[2]}
            for point in payload["voxel_sample"]
        )
    with (args.output_dir / "ledger.jsonl").open("w", encoding="utf-8") as handle:
        for stage in payload["stages"]:
            handle.write(json.dumps({"event": "menger_stage", **stage}, sort_keys=True) + "\n")
        handle.write(
            json.dumps(
                {
                    "event": "claim_boundary",
                    "claim_boundary": payload["claim_boundary"],
                    "topological_dimension_label": payload["topological_dimension_label"],
                },
                sort_keys=True,
            )
            + "\n"
        )
    (args.output_dir / "menger_sponge_forge.svg").write_text(_render_svg(payload), encoding="utf-8")
    print(json.dumps({"passed": report.passed, "output_dir": str(args.output_dir)}, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
