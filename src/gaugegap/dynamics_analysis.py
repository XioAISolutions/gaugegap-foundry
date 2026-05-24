from __future__ import annotations

from collections import defaultdict
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape


REFERENCE_BACKEND = "local_statevector"
CLEAN_AER_BACKEND = "shot_sampler:none"
NOISY_AER_BACKEND = "shot_sampler:depolarizing"


def load_dynamics_csvs(input_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(input_dir.glob("*-dynamics.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                records.append(
                    {
                        "source_file": path.name,
                        "hypothesis_id": row["hypothesis_id"],
                        "backend": row["backend"],
                        "observable": row["observable"],
                        "site": _optional_int(row.get("site", "")),
                        "bond": _optional_int(row.get("bond", "")),
                        "time": float(row["time"]),
                        "value": float(row["value"]),
                    }
                )
    if not records:
        raise ValueError(f"no dynamics CSV files found in {input_dir}")
    return records


def analyze_records(
    records: list[dict[str, object]],
    shot_warning: float = 0.08,
    shot_fail: float = 0.18,
    noise_warning: float = 0.12,
    noise_fail: float = 0.28,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    indexed = {_key(record): record for record in records}
    backends = sorted({str(record["backend"]) for record in records})
    hypotheses = sorted({str(record["hypothesis_id"]) for record in records})
    rows: list[dict[str, object]] = []

    for key, reference in sorted(indexed.items()):
        hypothesis_id, observable, channel_kind, channel_index, time, backend = key
        if backend != REFERENCE_BACKEND:
            continue

        for candidate_backend in backends:
            if candidate_backend == REFERENCE_BACKEND:
                continue
            candidate_key = (hypothesis_id, observable, channel_kind, channel_index, time, candidate_backend)
            candidate = indexed.get(candidate_key)
            if candidate is None:
                continue
            abs_error = abs(float(candidate["value"]) - float(reference["value"]))
            rows.append(
                _analysis_row(
                    hypothesis_id=hypothesis_id,
                    comparison=f"{candidate_backend}_vs_{REFERENCE_BACKEND}",
                    baseline_backend=REFERENCE_BACKEND,
                    candidate_backend=candidate_backend,
                    observable=observable,
                    channel_kind=channel_kind,
                    channel_index=channel_index,
                    time=time,
                    baseline_value=float(reference["value"]),
                    candidate_value=float(candidate["value"]),
                    abs_error=abs_error,
                    drift_kind="shot_drift" if candidate_backend == CLEAN_AER_BACKEND else "abs_error",
                    warning=shot_warning if candidate_backend == CLEAN_AER_BACKEND else noise_warning,
                    fail=shot_fail if candidate_backend == CLEAN_AER_BACKEND else noise_fail,
                )
            )

        clean = indexed.get((hypothesis_id, observable, channel_kind, channel_index, time, CLEAN_AER_BACKEND))
        noisy = indexed.get((hypothesis_id, observable, channel_kind, channel_index, time, NOISY_AER_BACKEND))
        if clean is not None and noisy is not None:
            noise_drift = abs(float(noisy["value"]) - float(clean["value"]))
            rows.append(
                _analysis_row(
                    hypothesis_id=hypothesis_id,
                    comparison=f"{NOISY_AER_BACKEND}_vs_{CLEAN_AER_BACKEND}",
                    baseline_backend=CLEAN_AER_BACKEND,
                    candidate_backend=NOISY_AER_BACKEND,
                    observable=observable,
                    channel_kind=channel_kind,
                    channel_index=channel_index,
                    time=time,
                    baseline_value=float(clean["value"]),
                    candidate_value=float(noisy["value"]),
                    abs_error=noise_drift,
                    drift_kind="noise_drift",
                    warning=noise_warning,
                    fail=noise_fail,
                )
            )

    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["hypothesis_id"]), str(row["comparison"]), str(row["observable"]))].append(row)

    summaries = []
    for (hypothesis_id, comparison, observable), group_rows in sorted(groups.items()):
        max_error = max(float(row["abs_error"]) for row in group_rows)
        mean_error = sum(float(row["abs_error"]) for row in group_rows) / len(group_rows)
        verdict = _worst_verdict(str(row["verdict"]) for row in group_rows)
        summaries.append(
            {
                "hypothesis_id": hypothesis_id,
                "comparison": comparison,
                "observable": observable,
                "records": len(group_rows),
                "mean_abs_error": mean_error,
                "max_abs_error": max_error,
                "verdict": verdict,
            }
        )

    overall_verdict = _worst_verdict(summary["verdict"] for summary in summaries) if summaries else "fail"
    metadata = {
        "hypotheses": hypotheses,
        "backends": backends,
        "reference_backend": REFERENCE_BACKEND,
        "clean_aer_backend": CLEAN_AER_BACKEND,
        "noisy_aer_backend": NOISY_AER_BACKEND,
        "thresholds": {
            "shot_warning": shot_warning,
            "shot_fail": shot_fail,
            "noise_warning": noise_warning,
            "noise_fail": noise_fail,
        },
        "record_count": len(rows),
        "summary_count": len(summaries),
        "overall_verdict": overall_verdict,
    }
    return rows, summaries, metadata


def write_analysis_outputs(
    output_dir: Path,
    rows: list[dict[str, object]],
    summaries: list[dict[str, object]],
    metadata: dict[str, object],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "dynamics-analysis-summary.csv"
    details_csv = output_dir / "dynamics-analysis-details.csv"
    summary_json = output_dir / "dynamics-analysis-summary.json"
    plot_svg = output_dir / "dynamics-analysis-observables.svg"

    _write_csv(details_csv, rows)
    _write_csv(summary_csv, summaries)
    summary_json.write_text(json.dumps({"metadata": metadata, "summaries": summaries}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_observable_svg(plot_svg, rows)

    return {
        "details_csv": str(details_csv),
        "summary_csv": str(summary_csv),
        "summary_json": str(summary_json),
        "plot_svg": str(plot_svg),
    }


def write_observable_svg(path: Path, rows: list[dict[str, object]]) -> None:
    series: dict[tuple[str, str, str, int], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        comparison = str(row["comparison"])
        if not comparison.startswith(f"{CLEAN_AER_BACKEND}_vs_") and not comparison.startswith(f"{NOISY_AER_BACKEND}_vs_{REFERENCE_BACKEND}"):
            continue
        channel_index = int(row["channel_index"])
        series[(str(row["candidate_backend"]), str(row["observable"]), str(row["channel_kind"]), channel_index)].append(
            (float(row["time"]), float(row["candidate_value"]))
        )
        if row["candidate_backend"] == CLEAN_AER_BACKEND:
            series[(REFERENCE_BACKEND, str(row["observable"]), str(row["channel_kind"]), channel_index)].append(
                (float(row["time"]), float(row["baseline_value"]))
            )

    if not series:
        raise ValueError("no analysis rows available for plotting")

    for points in series.values():
        points.sort()

    width = 1040
    height = 640
    left = 80
    right = 260
    top = 55
    bottom = 75
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_x = [x for points in series.values() for x, _ in points]
    all_y = [y for points in series.values() for _, y in points]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(-1.05, min(all_y)), max(1.05, max(all_y))
    if x_min == x_max:
        x_max = x_min + 1.0

    def sx(x: float) -> float:
        return left + ((x - x_min) / (x_max - x_min)) * plot_w

    def sy(y: float) -> float:
        return top + (1.0 - ((y - y_min) / (y_max - y_min))) * plot_h

    colors = {
        REFERENCE_BACKEND: "#111827",
        CLEAN_AER_BACKEND: "#2563eb",
        NOISY_AER_BACKEND: "#dc2626",
    }
    stroke_dash = {
        REFERENCE_BACKEND: "",
        CLEAN_AER_BACKEND: "4 3",
        NOISY_AER_BACKEND: "2 4",
    }
    shapes: list[str] = []
    legend: list[str] = []
    for idx, key in enumerate(sorted(series)):
        backend, observable, channel_kind, channel_index = key
        color = colors.get(backend, "#6b7280")
        dash = stroke_dash.get(backend, "")
        points = series[key]
        polyline = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in points)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        shapes.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2.2"{dash_attr} />')
        for x, y in points:
            shapes.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3" fill="{color}" />')
        legend_y = top + idx * 18
        label = escape(f"{backend} {observable} {channel_kind}{channel_index}")
        legend.append(f'<line x1="{width - right + 25}" y1="{legend_y}" x2="{width - right + 50}" y2="{legend_y}" stroke="{color}" stroke-width="2.2"{dash_attr} />')
        legend.append(f'<text x="{width - right + 58}" y="{legend_y + 4}" font-size="11">{label}</text>')

    grid = []
    for tick in _ticks(x_min, x_max, 5):
        px = sx(tick)
        grid.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top + plot_h}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{px:.2f}" y="{height - 42}" font-size="12" text-anchor="middle">{tick:.2g}</text>')
    for tick in _ticks(y_min, y_max, 7):
        py = sy(tick)
        grid.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left + plot_w}" y2="{py:.2f}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{left - 10}" y="{py + 4:.2f}" font-size="12" text-anchor="end">{tick:.2g}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left}" y="30" font-size="20" font-family="Arial, sans-serif" font-weight="700">GaugeGap dynamics observables</text>
  <g font-family="Arial, sans-serif" fill="#111827">
    {''.join(grid)}
    <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#111827" stroke-width="1.2" />
    {''.join(shapes)}
    {''.join(legend)}
    <text x="{left + plot_w / 2:.2f}" y="{height - 12}" font-size="14" text-anchor="middle">time</text>
    <text x="22" y="{top + plot_h / 2:.2f}" font-size="14" text-anchor="middle" transform="rotate(-90 22 {top + plot_h / 2:.2f})">observable value</text>
  </g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def _analysis_row(
    hypothesis_id: str,
    comparison: str,
    baseline_backend: str,
    candidate_backend: str,
    observable: str,
    channel_kind: str,
    channel_index: int,
    time: float,
    baseline_value: float,
    candidate_value: float,
    abs_error: float,
    drift_kind: str,
    warning: float,
    fail: float,
) -> dict[str, object]:
    return {
        "hypothesis_id": hypothesis_id,
        "comparison": comparison,
        "baseline_backend": baseline_backend,
        "candidate_backend": candidate_backend,
        "observable": observable,
        "channel_kind": channel_kind,
        "channel_index": channel_index,
        "time": time,
        "baseline_value": baseline_value,
        "candidate_value": candidate_value,
        "abs_error": abs_error,
        "drift_kind": drift_kind,
        "warning_threshold": warning,
        "fail_threshold": fail,
        "verdict": _verdict(abs_error, warning, fail),
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _key(record: dict[str, object]) -> tuple[str, str, str, int, float, str]:
    observable = str(record["observable"])
    if observable == "z_expectation":
        channel_kind = "site"
        channel_index = int(record["site"])
    elif observable == "zz_correlator":
        channel_kind = "bond"
        channel_index = int(record["bond"])
    else:
        raise ValueError(f"unsupported observable: {observable}")
    return (
        str(record["hypothesis_id"]),
        observable,
        channel_kind,
        channel_index,
        float(record["time"]),
        str(record["backend"]),
    )


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _verdict(value: float, warning: float, fail: float) -> str:
    if value >= fail:
        return "fail"
    if value >= warning:
        return "warning"
    return "pass"


def _worst_verdict(verdicts) -> str:
    order = {"pass": 0, "warning": 1, "fail": 2}
    worst = "pass"
    for verdict in verdicts:
        if order[str(verdict)] > order[worst]:
            worst = str(verdict)
    return worst


def _ticks(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]
