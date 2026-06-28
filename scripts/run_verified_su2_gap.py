#!/usr/bin/env python3
"""Run the verified finite SU(2) one-plaquette gap benchmark."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.gap_forge import render_gap_forge_html  # noqa: E402
from gaugegap.verified_su2_gap import (  # noqa: E402
    CLAIM_BOUNDARY,
    as_fraction,
    fraction_text,
    sweep_verified_gaps,
    verify_gap,
)


def _fraction(value: str) -> Fraction:
    try:
        result = as_fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise argparse.ArgumentTypeError(f"invalid rational value: {value}") from exc
    return result


def _ints(value: str) -> list[int]:
    try:
        values = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated integers") from exc
    if not values or min(values) < 1:
        raise argparse.ArgumentTypeError("all max-two-j values must be positive")
    return values


def _fractions(value: str) -> list[Fraction]:
    values = [_fraction(item.strip()) for item in value.split(",") if item.strip()]
    if not values or min(values) <= 0:
        raise argparse.ArgumentTypeError("all electric couplings must be positive")
    return values


def _svg(rows: list[dict[str, object]]) -> str:
    width, height = 980, 560
    left, right, top, bottom = 90, 48, 90, 80
    chart_w, chart_h = width - left - right, height - top - bottom
    gaps = [float(row["gap_lower"]) for row in rows]
    max_gap = max(max(gaps), 1e-12)
    groups: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault(int(row["max_two_j"]), []).append(row)
    colors = ["#58d7ff", "#d2a8ff", "#7ee787", "#ffa657", "#ff7b72"]
    polylines: list[str] = []
    labels: list[str] = []
    all_electric = sorted({float(row["electric_float"]) for row in rows})
    x_min, x_max = min(all_electric), max(all_electric)
    x_span = max(x_max - x_min, 1e-12)
    for group_index, (max_two_j, group_rows) in enumerate(sorted(groups.items())):
        points: list[str] = []
        for row in sorted(group_rows, key=lambda item: float(item["electric_float"])):
            x = left + (float(row["electric_float"]) - x_min) / x_span * chart_w
            y = top + chart_h - float(row["gap_lower"]) / max_gap * chart_h
            points.append(f"{x:.2f},{y:.2f}")
        color = colors[group_index % len(colors)]
        polylines.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
            'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        labels.append(
            f'<text x="{left + 18 + group_index * 150}" y="48" fill="{color}" '
            f'font-size="15">j_max={max_two_j}/2</text>'
        )
    grid = "".join(
        f'<line x1="{left}" y1="{top + chart_h * i / 5:.2f}" x2="{left + chart_w}" '
        f'y2="{top + chart_h * i / 5:.2f}" stroke="#21262d"/>'
        for i in range(6)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="{width}" height="{height}" rx="24" fill="#0b0e14"/>
<text x="{width/2}" y="38" fill="#e6edf3" text-anchor="middle" font-family="system-ui" font-size="24" font-weight="700">Gap Forge · certified SU(2) one-plaquette separation</text>
{''.join(labels)}{grid}
<line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="#8b949e"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="#8b949e"/>
{''.join(polylines)}
<text x="{width/2}" y="{height-30}" fill="#8b949e" text-anchor="middle" font-family="monospace" font-size="14">electric coupling</text>
<text x="22" y="{height/2}" fill="#8b949e" text-anchor="middle" font-family="monospace" font-size="14" transform="rotate(-90 22 {height/2})">certified gap lower bound</text>
<text x="{width/2}" y="{height-8}" fill="#6e7681" text-anchor="middle" font-family="monospace" font-size="11">finite class-function truncations only · exact-rational Sturm enclosures</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-two-j", type=int, default=1)
    parser.add_argument("--electric", type=_fraction, default=Fraction(1))
    parser.add_argument("--magnetic", type=_fraction, default=Fraction(1, 2))
    parser.add_argument("--sturm-bits", type=int, default=96)
    parser.add_argument("--sweep-max-two-j", type=_ints, default=[1, 2, 3, 4])
    parser.add_argument(
        "--sweep-electric",
        type=_fractions,
        default=[Fraction(1, 2), Fraction(3, 4), Fraction(1), Fraction(3, 2), Fraction(2)],
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results/verified-su2-gap"))
    parser.add_argument("--require-positive", action="store_true")
    args = parser.parse_args()

    result = verify_gap(
        max_two_j=args.max_two_j,
        electric=args.electric,
        magnetic=args.magnetic,
        sturm_bits=args.sturm_bits,
    )
    sweep = sweep_verified_gaps(
        max_two_j_values=args.sweep_max_two_j,
        electric_values=args.sweep_electric,
        magnetic=args.magnetic,
        sturm_bits=max(64, args.sturm_bits),
    )
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    summary = result.summary()
    (output / "verified_gap.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    rows: list[dict[str, object]] = []
    for item in sweep:
        rows.append(
            {
                "max_two_j": item.basis.max_two_j,
                "j_max": fraction_text(Fraction(item.basis.max_two_j, 2)),
                "electric": fraction_text(item.electric),
                "electric_float": float(item.electric),
                "magnetic": fraction_text(item.magnetic),
                "dimension": item.basis.dimension,
                "gap_lower": float(item.gap.lower),
                "gap_upper": float(item.gap.upper),
                "gap_width": float(item.gap.width),
                "strictly_positive": item.strictly_positive,
                "matrix_digest": item.matrix_digest,
            }
        )
    with (output / "gap_sweep.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "gap_forge.svg").write_text(_svg(rows), encoding="utf-8")
    (output / "gap_forge.html").write_text(
        render_gap_forge_html(summary, rows), encoding="utf-8"
    )

    report = [
        "# Verified finite SU(2) gap benchmark",
        "",
        f"Status: {'PASS' if result.strictly_positive else 'FAIL'}",
        "",
        f"Basis: characters through j={fraction_text(Fraction(result.basis.max_two_j, 2))}",
        f"Dimension: {result.basis.dimension}",
        f"Electric coupling: {fraction_text(result.electric)}",
        f"Magnetic coupling: {fraction_text(result.magnetic)}",
        f"Ground interval: [{fraction_text(result.ground.lower)}, {fraction_text(result.ground.upper)}]",
        f"First-excited interval: [{fraction_text(result.first_excited.lower)}, {fraction_text(result.first_excited.upper)}]",
        f"Gap interval: [{fraction_text(result.gap.lower)}, {fraction_text(result.gap.upper)}]",
        f"Construction residual: {result.construction_residual:.3e}",
        f"Independent-spectrum residual: {result.spectrum_residual:.3e}",
        "",
        f"Claim boundary: {CLAIM_BOUNDARY}",
        "",
    ]
    (output / "report.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 2 if args.require_positive and not result.strictly_positive else 0


if __name__ == "__main__":
    raise SystemExit(main())
