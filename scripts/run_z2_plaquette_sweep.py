#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from xml.sax.saxutils import escape

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl
from gaugegap.models.z2_plaquette import (
    CLAIM_BOUNDARY,
    ground_state_observables,
    hamiltonian_dense,
    model_metadata,
    pauli_terms,
)
from gaugegap.quantum.pauli_export import pauli_terms_to_dense
from gaugegap.solvers.exact_gap import exact_gap


def parse_int_list(value: str) -> list[int]:
    try:
        items = [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated integers") from exc
    if not items or any(item < 1 for item in items):
        raise argparse.ArgumentTypeError("values must be positive integers")
    return items


def parse_float_list(value: str) -> list[float]:
    try:
        items = [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated numbers") from exc
    if not items or any(not math.isfinite(item) for item in items):
        raise argparse.ArgumentTypeError("values must be finite numbers")
    return items


def linspace(start: float, stop: float, points: int) -> list[float]:
    if not (math.isfinite(start) and math.isfinite(stop)):
        raise ValueError("field range must be finite")
    if points < 1:
        raise ValueError("field points must be positive")
    if points == 1:
        return [start]
    step = (stop - start) / (points - 1)
    return [start + i * step for i in range(points)]


def build_records(
    *,
    hypothesis_id: str,
    n_plaquettes: list[int],
    plaquette_coupling: float,
    transverse_fields: list[float],
    run_id: str,
) -> list[dict[str, object]]:
    git = git_state(ROOT)
    records: list[dict[str, object]] = []
    for count in n_plaquettes:
        for field in transverse_fields:
            metadata = model_metadata(count, plaquette_coupling, field)
            exact_matrix = hamiltonian_dense(count, plaquette_coupling, field)
            exact_result = exact_gap(exact_matrix)

            replica_matrix = pauli_terms_to_dense(pauli_terms(count, plaquette_coupling, field))
            replica_result = exact_gap(replica_matrix)
            matrix_delta = float(np.linalg.norm(exact_matrix - replica_matrix))
            gap_delta = abs(exact_result.gap - replica_result.gap)
            replica_status = "pass" if matrix_delta <= 1e-9 and gap_delta <= 1e-9 else "fail"
            status = exact_result.status if replica_status == "pass" else "fail_pauli_replica_mismatch"
            observables = ground_state_observables(count, plaquette_coupling, field)

            records.append(
                {
                    "run_id": run_id,
                    "hypothesis_id": hypothesis_id,
                    "track": "GaugeGap",
                    "model": metadata["model"],
                    "observable": "mass_gap_and_ground_state_observables",
                    "params": metadata,
                    "hamiltonian_hash": object_hash(metadata),
                    "value": exact_result.gap,
                    "ground_energy": exact_result.ground_energy,
                    "first_excited_energy": exact_result.first_excited_energy,
                    "residual_norm": exact_result.residual_norm,
                    "pauli_replica": {
                        "gap": replica_result.gap,
                        "gap_delta": gap_delta,
                        "matrix_delta": matrix_delta,
                        "status": replica_status,
                    },
                    "observables": observables,
                    "method": "dense_exact_diagonalization_with_pauli_dense_replica",
                    "backend": {
                        "provider": "local",
                        "name": "numpy.linalg.eigh",
                        "mode": "exact_dense_plus_pauli_replica",
                        "shots": None,
                    },
                    "status": status,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "git": git,
                }
            )
    return records


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "run_id",
                "hypothesis_id",
                "n_plaquettes",
                "n_qubits",
                "plaquette_coupling",
                "transverse_field",
                "mass_gap",
                "ground_energy",
                "first_excited_energy",
                "residual_norm",
                "pauli_matrix_delta",
                "pauli_gap_delta",
                "mean_plaquette_z",
                "mean_link_x",
                "status",
                "hamiltonian_hash",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for record in records:
            params = record["params"]
            observables = record["observables"]
            replica = record["pauli_replica"]
            assert isinstance(params, dict)
            assert isinstance(observables, dict)
            assert isinstance(replica, dict)
            writer.writerow(
                {
                    "run_id": record["run_id"],
                    "hypothesis_id": record["hypothesis_id"],
                    "n_plaquettes": params["n_plaquettes"],
                    "n_qubits": params["n_qubits"],
                    "plaquette_coupling": f"{float(params['plaquette_coupling']):.12g}",
                    "transverse_field": f"{float(params['transverse_field']):.12g}",
                    "mass_gap": f"{float(record['value']):.12g}",
                    "ground_energy": f"{float(record['ground_energy']):.12g}",
                    "first_excited_energy": f"{float(record['first_excited_energy']):.12g}",
                    "residual_norm": f"{float(record['residual_norm']):.12g}",
                    "pauli_matrix_delta": f"{float(replica['matrix_delta']):.12g}",
                    "pauli_gap_delta": f"{float(replica['gap_delta']):.12g}",
                    "mean_plaquette_z": f"{float(observables['mean_plaquette_z']):.12g}",
                    "mean_link_x": f"{float(observables['mean_link_x']):.12g}",
                    "status": record["status"],
                    "hamiltonian_hash": record["hamiltonian_hash"],
                }
            )


def write_svg(path: Path, records: list[dict[str, object]]) -> None:
    grouped: dict[int, list[tuple[float, float]]] = {}
    for record in records:
        params = record["params"]
        assert isinstance(params, dict)
        grouped.setdefault(int(params["n_plaquettes"]), []).append(
            (float(params["transverse_field"]), float(record["value"]))
        )
    for points in grouped.values():
        points.sort()
    xs = [x for points in grouped.values() for x, _ in points]
    ys = [y for points in grouped.values() for _, y in points]
    if not xs or not ys:
        raise ValueError("cannot plot empty records")

    width, height = 920, 560
    left, right, top, bottom = 80, 30, 45, 75
    plot_w, plot_h = width - left - right, height - top - bottom
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = 0.0, max(ys)
    if x_min == x_max:
        x_max += 1.0
    if y_min == y_max:
        y_max += 1.0

    def sx(value: float) -> float:
        return left + ((value - x_min) / (x_max - x_min)) * plot_w

    def sy(value: float) -> float:
        return top + (1.0 - ((value - y_min) / (y_max - y_min))) * plot_h

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]
    lines: list[str] = []
    legend: list[str] = []
    for index, count in enumerate(sorted(grouped)):
        color = colors[index % len(colors)]
        polyline = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in grouped[count])
        lines.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2.5" />')
        for x, y in grouped[count]:
            lines.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3.5" fill="{color}" />')
        legend_y = top + 22 * index
        legend.append(
            f'<line x1="{width - 195}" y1="{legend_y}" x2="{width - 165}" y2="{legend_y}" '
            f'stroke="{color}" stroke-width="3" />'
        )
        legend.append(f'<text x="{width - 157}" y="{legend_y + 5}" font-size="14">plaquettes={count}</text>')

    grid = _grid_lines(left, top, plot_w, plot_h, x_min, x_max, y_min, y_max, sx, sy, height)
    title = escape("GaugeGap gaugegap-0002: finite Z2 plaquette gap sweep")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left}" y="28" font-size="20" font-family="Arial, sans-serif" font-weight="700">{title}</text>
  <g font-family="Arial, sans-serif" fill="#111827">
    {''.join(grid)}
    <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#111827" stroke-width="1.2" />
    {''.join(lines)}
    {''.join(legend)}
    <text x="{left + plot_w / 2:.2f}" y="{height - 12}" font-size="14" text-anchor="middle">transverse field h</text>
    <text x="22" y="{top + plot_h / 2:.2f}" font-size="14" text-anchor="middle" transform="rotate(-90 22 {top + plot_h / 2:.2f})">mass gap E1 - E0</text>
  </g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def _grid_lines(
    left: int,
    top: int,
    plot_w: int,
    plot_h: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    sx,
    sy,
    height: int,
) -> list[str]:
    grid: list[str] = []
    for x in _ticks(x_min, x_max, 6):
        px = sx(x)
        grid.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top + plot_h}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{px:.2f}" y="{height - 42}" font-size="12" text-anchor="middle">{x:.2g}</text>')
    for y in _ticks(y_min, y_max, 6):
        py = sy(y)
        grid.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left + plot_w}" y2="{py:.2f}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{left - 12}" y="{py + 4:.2f}" font-size="12" text-anchor="end">{y:.2g}</text>')
    return grid


def _ticks(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + index * step for index in range(count)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a finite Z2 plaquette exact/Pauli sweep for gaugegap-0002.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0002")
    parser.add_argument("--n-plaquettes", type=parse_int_list, default=parse_int_list("1,2"))
    parser.add_argument("--plaquette-coupling", type=float, default=1.0)
    parser.add_argument("--fields", type=parse_float_list)
    parser.add_argument("--field-start", type=float, default=0.1)
    parser.add_argument("--field-stop", type=float, default=1.0)
    parser.add_argument("--field-points", type=int, default=4)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "baselines")
    args = parser.parse_args()

    try:
        fields = args.fields or linspace(args.field_start, args.field_stop, args.field_points)
        records = build_records(
            hypothesis_id=args.hypothesis_id,
            n_plaquettes=args.n_plaquettes,
            plaquette_coupling=args.plaquette_coupling,
            transverse_fields=fields,
            run_id=args.run_id or utc_run_id(),
        )
    except ValueError as exc:
        parser.error(str(exc))

    stem = f"{args.hypothesis_id}-z2-plaquette-sweep"
    jsonl_path = args.output_dir / f"{stem}.jsonl"
    csv_path = args.output_dir / f"{stem}.csv"
    svg_path = args.output_dir / f"{stem}.svg"
    write_jsonl(jsonl_path, records)
    write_csv(csv_path, records)
    write_svg(svg_path, records)

    status = "pass" if all(record["status"] == "finite_system_verified" for record in records) else "warning"
    print(
        json.dumps(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "csv": str(csv_path),
                "jsonl": str(jsonl_path),
                "records": len(records),
                "status": status,
                "svg": str(svg_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
