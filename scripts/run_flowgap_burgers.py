#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl


def parse_sizes(value: str) -> list[int]:
    sizes = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not sizes or any(size < 4 for size in sizes):
        raise argparse.ArgumentTypeError("sizes must be comma-separated integers >= 4")
    return sizes


def linspace(start: float, stop: float, points: int) -> list[float]:
    if points <= 1:
        return [start]
    step = (stop - start) / (points - 1)
    return [start + i * step for i in range(points)]


def build_classical_records(
    hypothesis_id: str,
    grid_sizes: list[int],
    viscosities: list[float],
    dt: float,
    n_steps: int,
) -> list[dict[str, object]]:
    from gaugegap.flowgap_burgers import burgers_viscous_1d

    run_id = utc_run_id()
    git = git_state(ROOT)
    records: list[dict[str, object]] = []

    for nx in grid_sizes:
        for nu in viscosities:
            params = {
                "grid_size": nx,
                "viscosity": nu,
                "dt": dt,
                "n_steps": n_steps,
                "boundary": "periodic",
            }
            result = burgers_viscous_1d(nx=nx, nu=nu, dt=dt, n_steps=n_steps)
            ke_final = result["kinetic_history"][-1] if result["kinetic_history"] else float("nan")
            ke_initial = result["kinetic_history"][0] if result["kinetic_history"] else float("nan")

            records.append({
                "run_id": run_id,
                "hypothesis_id": hypothesis_id,
                "observable": "kinetic_energy_final",
                "value": ke_final,
                "params": params,
                "hamiltonian_hash": object_hash(params),
                "backend": {"provider": "classical", "method": "finite_difference"},
                "git": git,
                "extra": {
                    "kinetic_energy_initial": ke_initial,
                    "kinetic_energy_ratio": ke_final / ke_initial if ke_initial > 0 else float("nan"),
                    "residual_final": result["residual_history"][-1] if result["residual_history"] else float("nan"),
                },
            })

    return records


def build_quantum_records(
    hypothesis_id: str,
    nx: int,
    depth: int,
    max_iter: int,
) -> list[dict[str, object]]:
    from gaugegap.flowgap_qsubroutine import run_vqls_poisson_1d

    run_id = utc_run_id()
    git = git_state(ROOT)

    result = run_vqls_poisson_1d(nx=nx, depth=depth, max_iter=max_iter)

    params = {
        "grid_size": nx,
        "method": "vqls_poisson_1d",
        "depth": depth,
        "max_iter": max_iter,
    }

    records = [
        {
            "run_id": run_id,
            "hypothesis_id": hypothesis_id,
            "observable": "poisson_residual",
            "value": result["poisson_residual"],
            "params": params,
            "hamiltonian_hash": object_hash(params),
            "backend": {"provider": "qiskit", "method": "vqls_statevector"},
            "git": git,
            "extra": {
                "l2_error": result["l2_error"],
                "n_iter": result["n_iter"],
                "final_cost": result["cost_history"][-1] if result["cost_history"] else float("nan"),
            },
        },
        {
            "run_id": run_id,
            "hypothesis_id": hypothesis_id,
            "observable": "l2_error_vs_classical",
            "value": result["l2_error"],
            "params": params,
            "hamiltonian_hash": object_hash(params),
            "backend": {"provider": "qiskit", "method": "vqls_statevector"},
            "git": git,
        },
    ]
    return records


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run_id", "hypothesis_id", "observable", "value"]
    param_keys: set[str] = set()
    for r in records:
        if isinstance(r.get("params"), dict):
            param_keys.update(r["params"].keys())
    param_keys_sorted = sorted(param_keys)
    all_fields = fields + param_keys_sorted

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        for r in records:
            row = {k: r.get(k, "") for k in fields}
            if isinstance(r.get("params"), dict):
                for pk in param_keys_sorted:
                    row[pk] = r["params"].get(pk, "")
            writer.writerow(row)


def write_burgers_svg(path: Path, records: list[dict[str, object]]) -> None:
    from xml.sax.saxutils import escape

    grouped: dict[int, list[tuple[float, float]]] = {}
    for r in records:
        if r["observable"] != "kinetic_energy_final":
            continue
        params = r["params"]
        nx = int(params["grid_size"])
        nu = float(params["viscosity"])
        grouped.setdefault(nx, []).append((nu, float(r["value"])))

    for pts in grouped.values():
        pts.sort()

    if not grouped:
        return

    xs = [x for pts in grouped.values() for x, _ in pts]
    ys = [y for pts in grouped.values() for _, y in pts]

    width, height = 920, 560
    left, right, top, bottom = 80, 30, 45, 75
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = 0.0, max(ys) if ys else 1.0
    if x_min == x_max:
        x_max += 0.01
    if y_max == 0.0:
        y_max = 1.0

    def sx(x):
        return left + ((x - x_min) / (x_max - x_min)) * plot_w

    def sy(y):
        return top + (1.0 - ((y - y_min) / (y_max - y_min))) * plot_h

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]
    lines, legend = [], []
    for idx, nx in enumerate(sorted(grouped)):
        color = colors[idx % len(colors)]
        polyline = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in grouped[nx])
        lines.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2.5" />')
        for x, y in grouped[nx]:
            lines.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3.5" fill="{color}" />')
        ly = top + 22 * idx
        legend.append(f'<line x1="{width-170}" y1="{ly}" x2="{width-140}" y2="{ly}" stroke="{color}" stroke-width="3" />')
        legend.append(f'<text x="{width-132}" y="{ly+5}" font-size="14">nx={nx}</text>')

    def ticks(a, b, n):
        if n <= 1:
            return [a]
        s = (b - a) / (n - 1)
        return [a + i * s for i in range(n)]

    grid = []
    for x in ticks(x_min, x_max, 6):
        px = sx(x)
        grid.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top+plot_h}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{px:.2f}" y="{height-42}" font-size="12" text-anchor="middle">{x:.3g}</text>')
    for y in ticks(y_min, y_max, 6):
        py = sy(y)
        grid.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left+plot_w}" y2="{py:.2f}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{left-12}" y="{py+4:.2f}" font-size="12" text-anchor="end">{y:.3g}</text>')

    title = escape("FlowGap flowgap-0001: viscous Burgers kinetic energy")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left}" y="28" font-size="20" font-family="Arial, sans-serif" font-weight="700">{title}</text>
  <g font-family="Arial, sans-serif" fill="#111827">
    {''.join(grid)}
    <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#111827" stroke-width="1.2" />
    {''.join(lines)}
    {''.join(legend)}
    <text x="{left+plot_w/2:.2f}" y="{height-12}" font-size="14" text-anchor="middle">viscosity nu</text>
    <text x="22" y="{top+plot_h/2:.2f}" font-size="14" text-anchor="middle" transform="rotate(-90 22 {top+plot_h/2:.2f})">kinetic energy (final)</text>
  </g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="FlowGap Burgers benchmark sweep")
    parser.add_argument("--hypothesis", default="flowgap-0001")
    parser.add_argument("--sizes", type=parse_sizes, default=[16, 32, 64])
    parser.add_argument("--nu-range", type=float, nargs=2, default=[0.001, 0.1])
    parser.add_argument("--nu-points", type=int, default=5)
    parser.add_argument("--dt", type=float, default=0.0001)
    parser.add_argument("--n-steps", type=int, default=100)
    parser.add_argument("--quantum", action="store_true", help="Run VQLS pressure-Poisson subroutine")
    parser.add_argument("--quantum-nx", type=int, default=4)
    parser.add_argument("--quantum-depth", type=int, default=2)
    parser.add_argument("--quantum-max-iter", type=int, default=100)
    parser.add_argument("--output-dir", type=str, default=str(ROOT / "results" / "baselines"))
    args = parser.parse_args()

    viscosities = linspace(args.nu_range[0], args.nu_range[1], args.nu_points)
    records = build_classical_records(args.hypothesis, args.sizes, viscosities, args.dt, args.n_steps)

    if args.quantum:
        records.extend(build_quantum_records(
            args.hypothesis, args.quantum_nx, args.quantum_depth, args.quantum_max_iter
        ))

    out = Path(args.output_dir)
    prefix = f"{args.hypothesis}-burgers-sweep"
    write_jsonl(out / f"{prefix}.jsonl", records)
    write_csv(out / f"{prefix}.csv", records)
    write_burgers_svg(out / f"{prefix}.svg", [r for r in records if r["observable"] == "kinetic_energy_final"])

    print(f"wrote {len(records)} records to {out / prefix}.*")


if __name__ == "__main__":
    main()
