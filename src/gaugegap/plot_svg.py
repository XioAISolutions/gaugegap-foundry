from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape


def write_gap_svg(path: Path, records: list[dict[str, object]]) -> None:
    grouped: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for record in records:
        params = record["params"]
        assert isinstance(params, dict)
        grouped[int(params["lattice_size"])].append((float(params["transverse_field"]), float(record["value"])))

    for points in grouped.values():
        points.sort()

    xs = [x for points in grouped.values() for x, _ in points]
    ys = [y for points in grouped.values() for _, y in points]
    if not xs or not ys:
        raise ValueError("cannot plot empty records")

    width = 920
    height = 560
    left = 80
    right = 30
    top = 45
    bottom = 75
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = 0.0, max(ys)
    if x_min == x_max:
        x_max += 1.0
    if y_min == y_max:
        y_max += 1.0

    def sx(x: float) -> float:
        return left + ((x - x_min) / (x_max - x_min)) * plot_w

    def sy(y: float) -> float:
        return top + (1.0 - ((y - y_min) / (y_max - y_min))) * plot_h

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
    lines: list[str] = []
    legend: list[str] = []
    for idx, size in enumerate(sorted(grouped)):
        color = colors[idx % len(colors)]
        polyline = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in grouped[size])
        lines.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2.5" />')
        for x, y in grouped[size]:
            lines.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3.5" fill="{color}" />')
        legend_y = top + 22 * idx
        legend.append(f'<line x1="{width - 170}" y1="{legend_y}" x2="{width - 140}" y2="{legend_y}" stroke="{color}" stroke-width="3" />')
        legend.append(f'<text x="{width - 132}" y="{legend_y + 5}" font-size="14">L={size}</text>')

    x_ticks = _ticks(x_min, x_max, 6)
    y_ticks = _ticks(y_min, y_max, 6)
    grid: list[str] = []
    for x in x_ticks:
        px = sx(x)
        grid.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top + plot_h}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{px:.2f}" y="{height - 42}" font-size="12" text-anchor="middle">{x:.2g}</text>')
    for y in y_ticks:
        py = sy(y)
        grid.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left + plot_w}" y2="{py:.2f}" stroke="#e5e7eb" />')
        grid.append(f'<text x="{left - 12}" y="{py + 4:.2f}" font-size="12" text-anchor="end">{y:.2g}</text>')

    title = escape("GaugeGap gaugegap-0001: Z2 dual-chain mass gap sweep")
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


def _ticks(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]
