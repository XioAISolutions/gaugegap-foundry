#!/usr/bin/env python3
"""Run an exact Anomaly Forge audit and emit deterministic artifacts."""
from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.anomaly_audit import Hypercharges, audit, payload  # noqa: E402


def _fraction(value: str) -> Fraction:
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise argparse.ArgumentTypeError(f"invalid rational value: {value}") from exc


def _svg(report: dict[str, object]) -> str:
    anomaly = report["anomalies"]
    exact = anomaly["exact"]
    passed = bool(anomaly["passes"])
    accent = "#7ee787" if passed else "#ff6b6b"
    status = "ANOMALY FREE" if passed else "INCONSISTENT"
    rows = [
        ("SU(3)^2-U(1)", exact["SU(3)^2-U(1)"]),
        ("SU(2)^2-U(1)", exact["SU(2)^2-U(1)"]),
        ("U(1)^3", exact["U(1)^3"]),
        ("gravity^2-U(1)", exact["gravity^2-U(1)"]),
    ]
    row_svg = "".join(
        f'<text x="78" y="{214 + i * 54}" fill="#8b949e" font-size="17">{name}</text>'
        f'<text x="645" y="{214 + i * 54}" fill="{accent}" text-anchor="end" font-size="19">{value}</text>'
        for i, (name, value) in enumerate(rows)
    )
    charges = report["assignment"]["electric_charges"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="520" viewBox="0 0 720 520">
<rect width="720" height="520" rx="20" fill="#0b0e14"/>
<text x="44" y="52" fill="#e6edf3" font-family="system-ui" font-size="26" font-weight="700">Anomaly Forge</text>
<text x="44" y="82" fill="#8b949e" font-family="system-ui" font-size="15">exact rational consistency audit</text>
<circle cx="600" cy="62" r="28" fill="none" stroke="{accent}" stroke-width="4"/>
<text x="600" y="68" fill="{accent}" text-anchor="middle" font-family="monospace" font-size="12">{'PASS' if passed else 'FAIL'}</text>
<text x="360" y="144" fill="{accent}" text-anchor="middle" font-family="monospace" font-size="28">{status}</text>
<g font-family="ui-monospace,monospace">{row_svg}</g>
<line x1="72" y1="426" x2="648" y2="426" stroke="#30363d"/>
<text x="90" y="468" fill="#58d7ff" font-family="monospace" font-size="20">u = {charges['u']}</text>
<text x="250" y="468" fill="#58d7ff" font-family="monospace" font-size="20">d = {charges['d']}</text>
<text x="420" y="468" fill="{accent}" font-family="monospace" font-size="20">p = {report['composites']['proton']}</text>
<text x="560" y="468" fill="{accent}" font-family="monospace" font-size="20">n = {report['composites']['neutron']}</text>
<text x="360" y="503" fill="#6e7681" text-anchor="middle" font-family="monospace" font-size="11">finite field inventory · exact arithmetic · explicit claim boundary</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--colors", type=int, default=3)
    parser.add_argument("--generations", type=int, default=3)
    parser.add_argument("--y-q", type=_fraction, default=Fraction(1, 6))
    parser.add_argument("--y-u", type=_fraction, default=Fraction(2, 3))
    parser.add_argument("--y-d", type=_fraction, default=Fraction(-1, 3))
    parser.add_argument("--y-l", type=_fraction, default=Fraction(-1, 2))
    parser.add_argument("--y-e", type=_fraction, default=Fraction(-1))
    parser.add_argument("--y-nu", type=_fraction)
    parser.add_argument("--output-dir", type=Path, default=Path("results/anomaly-forge"))
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    assignment = Hypercharges(
        colors=args.colors,
        generations=args.generations,
        y_q=args.y_q,
        y_u=args.y_u,
        y_d=args.y_d,
        y_l=args.y_l,
        y_e=args.y_e,
        y_nu=args.y_nu,
    )
    report = payload(assignment)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "anomaly_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "anomaly_balance.svg").write_text(_svg(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if args.require_pass and not audit(assignment).passes else 0


if __name__ == "__main__":
    raise SystemExit(main())
