#!/usr/bin/env python3
"""Run finite compactification toy spectra and emit evidence artifacts."""
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

from gaugegap.compactification_forge import (  # noqa: E402
    CLAIM_BOUNDARY,
    compact_spectrum,
    run_compactification_suite,
)


def _render_svg(payload: dict[str, object]) -> str:
    reports = payload["reports"]
    assert isinstance(reports, list)
    bars: list[str] = []
    for report_index, report in enumerate(reports):
        assert isinstance(report, dict)
        modes = report["modes"][:10]
        assert isinstance(modes, list)
        x0 = 120 + report_index * 450
        bars.append(
            f'<text x="{x0 + 160}" y="142" fill="#fff" font-family="monospace" '
            f'font-size="18" text-anchor="middle">{report["geometry"]}</text>'
        )
        max_mass = max(float(mode["mass"]) for mode in modes) or 1.0
        for index, mode in enumerate(modes):
            assert isinstance(mode, dict)
            x = x0 + index * 32
            y = 380 - 210 * float(mode["mass"]) / max_mass
            color = "#7ee787" if mode["visible_below_cutoff"] else "#777"
            bars.append(f'<line x1="{x}" y1="380" x2="{x}" y2="{y:.2f}" stroke="{color}" stroke-width="4"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="560" viewBox="0 0 1100 560">
<rect width="1100" height="560" rx="20" fill="#050505"/>
<text x="550" y="56" fill="#fff" font-family="monospace" font-size="29" text-anchor="middle">COMPACTIFICATION FORGE</text>
<text x="550" y="88" fill="#858585" font-family="monospace" font-size="14" text-anchor="middle">finite Kaluza-Klein / winding towers; hidden modes rise as radius shrinks</text>
<line x1="90" y1="380" x2="1010" y2="380" stroke="#333"/>
{''.join(bars)}
<text x="550" y="472" fill="#7ee787" font-family="monospace" font-size="15" text-anchor="middle">{payload["claim_level"]} · {payload["benchmark_id"]}</text>
<text x="550" y="502" fill="#777" font-family="monospace" font-size="12" text-anchor="middle">no Calabi-Yau vacuum or physical extra-dimension discovery claim</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", choices=["suite", "circle", "torus"], default="suite")
    parser.add_argument("--radius", type=float, default=0.08)
    parser.add_argument("--torus-radii", default="0.08,0.09")
    parser.add_argument("--cutoff", type=float, default=8.0)
    parser.add_argument("--max-mode", type=int, default=3)
    parser.add_argument("--alpha-prime", type=float, default=0.005)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "compact-0001-hidden-circle",
    )
    args = parser.parse_args()

    if args.geometry == "suite":
        torus_radii = tuple(float(part) for part in args.torus_radii.split(","))
        if len(torus_radii) != 2:
            raise ValueError("--torus-radii must contain two comma-separated floats")
        reports = run_compactification_suite(
            circle_radius=args.radius,
            torus_radii=(torus_radii[0], torus_radii[1]),
            cutoff=args.cutoff,
            max_mode=args.max_mode,
            alpha_prime=args.alpha_prime,
        )
    elif args.geometry == "circle":
        reports = (
            compact_spectrum(
                geometry="S1 circle",
                radii=(args.radius,),
                cutoff=args.cutoff,
                max_mode=args.max_mode,
                alpha_prime=args.alpha_prime,
            ),
        )
    else:
        torus_radii = tuple(float(part) for part in args.torus_radii.split(","))
        if len(torus_radii) != 2:
            raise ValueError("--torus-radii must contain two comma-separated floats")
        reports = (
            compact_spectrum(
                geometry="T2 torus",
                radii=(torus_radii[0], torus_radii[1]),
                cutoff=args.cutoff,
                max_mode=args.max_mode,
                alpha_prime=args.alpha_prime,
            ),
        )

    payload = {
        "schema": "gaugegap.compactification_forge.suite.v1",
        "benchmark_id": "compact-0001-hidden-circle",
        "claim_level": "reproducible_finite_result",
        "passed": all(report.passed for report in reports),
        "reports": [report.summary() for report in reports],
        "claim_boundary": CLAIM_BOUNDARY,
        "sources": [
            {
                "kind": "background_reference",
                "scope": "standard compactification/Kaluza-Klein educational model",
                "note": "The script intentionally avoids full string-vacuum or Calabi-Yau claims.",
            }
        ],
        "exclusions": [
            "not evidence that extra dimensions exist",
            "not a computation of the superstring landscape",
            "not a Calabi-Yau metric, moduli-stabilization, or particle-spectrum result",
            "not a unification claim",
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "modes.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "geometry",
            "momentum_numbers",
            "winding_numbers",
            "mass_squared",
            "mass",
            "visible_below_cutoff",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for report in reports:
            for mode in report.modes:
                row = mode.summary()
                writer.writerow({key: row[key] for key in fieldnames})
    (args.output_dir / "compactification_forge.svg").write_text(
        _render_svg(payload),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
