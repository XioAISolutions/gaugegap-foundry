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


def build_records(
    hypothesis_id: str,
    family: str,
    n_basis_range: list[int],
    k_zeros: int,
    **family_kwargs,
) -> list[dict[str, object]]:
    from gaugegap.curverank_operators import generate_candidate_family
    from gaugegap.curverank_spectral import rank_candidates, truncation_stability

    run_id = utc_run_id()
    git = git_state(ROOT)

    candidates = generate_candidate_family(family, n_basis_range, **family_kwargs)
    ranked = rank_candidates(candidates, k=k_zeros)

    stability = truncation_stability(
        lambda n: generate_candidate_family(family, [n], **family_kwargs)[0]["operator"],
        n_basis_range,
        k=min(k_zeros, 10),
    )

    records: list[dict[str, object]] = []
    for score in ranked:
        params = {
            "family": score["family"],
            "n_basis": score["n_basis"],
            "k_zeros": k_zeros,
        }
        records.append({
            "run_id": run_id,
            "hypothesis_id": hypothesis_id,
            "observable": "spectral_mismatch",
            "value": score["spectral_mismatch"],
            "params": params,
            "hamiltonian_hash": object_hash(params),
            "backend": {"provider": "classical", "method": "exact_diagonalization"},
            "git": git,
            "extra": {
                "gue_mean_ratio": score["gue_mean_ratio"],
                "gue_std_ratio": score["gue_std_ratio"],
                "composite_score": score["composite_score"],
                "rank": score["rank"],
                "dim": score["dim"],
            },
        })

    for stab in stability:
        params = {
            "family": family,
            "n_basis": stab["n_basis"],
            "k_tracked": stab["n_tracked"],
        }
        records.append({
            "run_id": run_id,
            "hypothesis_id": hypothesis_id,
            "observable": "truncation_drift",
            "value": stab["drift_from_previous"],
            "params": params,
            "hamiltonian_hash": object_hash(params),
            "backend": {"provider": "classical", "method": "exact_diagonalization"},
            "git": git,
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


def write_screen_svg(path: Path, records: list[dict[str, object]]) -> None:
    from xml.sax.saxutils import escape

    mismatch_records = [r for r in records if r["observable"] == "spectral_mismatch"]
    if not mismatch_records:
        return

    xs = [int(r["params"]["n_basis"]) for r in mismatch_records]
    ys = [float(r["value"]) for r in mismatch_records]

    width, height = 920, 560
    left, right, top, bottom = 80, 30, 45, 75
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = 0.0, max(ys) if ys else 1.0
    if x_min == x_max:
        x_max += 1
    if y_max == 0.0:
        y_max = 1.0

    def sx(x):
        return left + ((x - x_min) / (x_max - x_min)) * plot_w

    def sy(y):
        return top + (1.0 - ((y - y_min) / (y_max - y_min))) * plot_h

    points_sorted = sorted(zip(xs, ys))
    polyline = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in points_sorted)

    def ticks(a, b, n):
        if n <= 1:
            return [a]
        s = (b - a) / (n - 1)
        return [a + i * s for i in range(n)]

    grid = []
    for x in ticks(float(x_min), float(x_max), 6):
        px = sx(x)
        grid.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top+plot_h}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{px:.2f}" y="{height-42}" font-size="12" text-anchor="middle">{x:.3g}</text>')
    for y in ticks(y_min, y_max, 6):
        py = sy(y)
        grid.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left+plot_w}" y2="{py:.2f}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{left-12}" y="{py+4:.2f}" font-size="12" text-anchor="end">{y:.3g}</text>')

    family = mismatch_records[0]["params"]["family"] if mismatch_records else "?"
    title = escape(f"CurveRank curverank-0001: {family} spectral mismatch vs truncation")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left}" y="28" font-size="20" font-family="Arial, sans-serif" font-weight="700">{title}</text>
  <g font-family="Arial, sans-serif" fill="#111827">
    {''.join(grid)}
    <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#111827" stroke-width="1.2" />
    <polyline points="{polyline}" fill="none" stroke="#1f77b4" stroke-width="2.5" />
    {''.join(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="4" fill="#1f77b4" />' for x, y in points_sorted)}
    <text x="{left+plot_w/2:.2f}" y="{height-12}" font-size="14" text-anchor="middle">truncation basis size</text>
    <text x="22" y="{top+plot_h/2:.2f}" font-size="14" text-anchor="middle" transform="rotate(-90 22 {top+plot_h/2:.2f})">spectral mismatch (RMS)</text>
  </g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="CurveRank spectral screening")
    parser.add_argument("--hypothesis", default="curverank-0001")
    parser.add_argument("--family", default="xp", choices=["xp", "quantum_graph", "dirac_rindler"])
    parser.add_argument("--n-basis", type=parse_int_list, default=[10, 20, 30, 40, 50])
    parser.add_argument("--k-zeros", type=int, default=20)
    parser.add_argument("--output-dir", type=str, default=str(ROOT / "results" / "baselines"))
    args = parser.parse_args()

    records = build_records(args.hypothesis, args.family, args.n_basis, args.k_zeros)

    out = Path(args.output_dir)
    prefix = f"{args.hypothesis}-spectral-screen"
    write_jsonl(out / f"{prefix}.jsonl", records)
    write_csv(out / f"{prefix}.csv", records)
    write_screen_svg(out / f"{prefix}.svg", records)

    print(f"wrote {len(records)} records to {out / prefix}.*")


if __name__ == "__main__":
    main()
