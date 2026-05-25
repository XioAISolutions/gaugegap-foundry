#!/usr/bin/env python3
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

from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl


def parse_int_list(value: str) -> list[int]:
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def linspace(start: float, stop: float, points: int) -> list[float]:
    if points <= 1:
        return [start]
    step = (stop - start) / (points - 1)
    return [start + i * step for i in range(points)]


def build_records(
    hypothesis_id: str,
    n_links_list: list[int],
    g_electric: float,
    g_magnetic_values: list[float],
    truncations: list[int],
) -> list[dict[str, object]]:
    from gaugegap.gaugegap_u1 import u1_mass_gap

    run_id = utc_run_id()
    git = git_state(ROOT)
    records: list[dict[str, object]] = []

    for n_links in n_links_list:
        for trunc in truncations:
            for g_mag in g_magnetic_values:
                params = {
                    "n_links": n_links,
                    "g_electric": g_electric,
                    "g_magnetic": g_mag,
                    "truncation": trunc,
                }

                try:
                    gap, e0, e1 = u1_mass_gap(n_links, g_electric, g_mag, trunc)
                except Exception as exc:
                    print(f"skipping n_links={n_links} trunc={trunc} g_mag={g_mag}: {exc}")
                    continue

                records.append({
                    "run_id": run_id,
                    "hypothesis_id": hypothesis_id,
                    "observable": "mass_gap",
                    "value": gap,
                    "params": params,
                    "hamiltonian_hash": object_hash(params),
                    "backend": {"provider": "classical", "method": "exact_diagonalization"},
                    "git": git,
                    "extra": {
                        "ground_energy": e0,
                        "first_excited_energy": e1,
                        "hilbert_dim": (2 * trunc + 1) ** n_links,
                    },
                })

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


def write_u1_gap_svg(path: Path, records: list[dict[str, object]]) -> None:
    from xml.sax.saxutils import escape

    grouped: dict[str, list[tuple[float, float]]] = {}
    for r in records:
        p = r["params"]
        key = f"L={p['n_links']},T={p['truncation']}"
        grouped.setdefault(key, []).append((float(p["g_magnetic"]), float(r["value"])))

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
        x_max += 0.1
    if y_max == 0.0:
        y_max = 1.0

    def sx(x):
        return left + ((x - x_min) / (x_max - x_min)) * plot_w

    def sy(y):
        return top + (1.0 - ((y - y_min) / (y_max - y_min))) * plot_h

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#8c564b", "#e377c2"]
    lines, legend = [], []
    for idx, key in enumerate(sorted(grouped)):
        color = colors[idx % len(colors)]
        polyline = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in grouped[key])
        lines.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2.5" />')
        for x, y in grouped[key]:
            lines.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3.5" fill="{color}" />')
        ly = top + 22 * idx
        legend.append(f'<line x1="{width-170}" y1="{ly}" x2="{width-140}" y2="{ly}" stroke="{color}" stroke-width="3" />')
        legend.append(f'<text x="{width-132}" y="{ly+5}" font-size="14">{escape(key)}</text>')

    def ticks(a, b, n):
        if n <= 1:
            return [a]
        s = (b - a) / (n - 1)
        return [a + i * s for i in range(n)]

    grid = []
    for x in ticks(x_min, x_max, 6):
        px = sx(x)
        grid.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top+plot_h}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{px:.2f}" y="{height-42}" font-size="12" text-anchor="middle">{x:.2g}</text>')
    for y in ticks(y_min, y_max, 6):
        py = sy(y)
        grid.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left+plot_w}" y2="{py:.2f}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{left-12}" y="{py+4:.2f}" font-size="12" text-anchor="end">{y:.3g}</text>')

    title = escape("GaugeGap gaugegap-0002: U(1) mass gap vs magnetic coupling")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left}" y="28" font-size="20" font-family="Arial, sans-serif" font-weight="700">{title}</text>
  <g font-family="Arial, sans-serif" fill="#111827">
    {''.join(grid)}
    <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#111827" stroke-width="1.2" />
    {''.join(lines)}
    {''.join(legend)}
    <text x="{left+plot_w/2:.2f}" y="{height-12}" font-size="14" text-anchor="middle">magnetic coupling g_mag</text>
    <text x="22" y="{top+plot_h/2:.2f}" font-size="14" text-anchor="middle" transform="rotate(-90 22 {top+plot_h/2:.2f})">mass gap E1 - E0</text>
  </g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="GaugeGap U(1) mass gap sweep")
    parser.add_argument("--hypothesis", default="gaugegap-0002")
    parser.add_argument("--n-links", type=parse_int_list, default=[2, 3])
    parser.add_argument("--g-electric", type=float, default=1.0)
    parser.add_argument("--g-mag-range", type=float, nargs=2, default=[0.1, 3.0])
    parser.add_argument("--g-mag-points", type=int, default=10)
    parser.add_argument("--truncation", type=parse_int_list, default=[1, 2])
    parser.add_argument("--output-dir", type=str, default=str(ROOT / "results" / "baselines"))
    args = parser.parse_args()

    g_mag_values = linspace(args.g_mag_range[0], args.g_mag_range[1], args.g_mag_points)

    records = build_records(
        args.hypothesis, args.n_links, args.g_electric, g_mag_values, args.truncation
    )

    out = Path(args.output_dir)
    prefix = f"{args.hypothesis}-u1-gap-sweep"
    write_jsonl(out / f"{prefix}.jsonl", records)
    write_csv(out / f"{prefix}.csv", records)
    write_u1_gap_svg(out / f"{prefix}.svg", records)

    print(f"wrote {len(records)} records to {out / prefix}.*")


if __name__ == "__main__":
    main()
