#!/usr/bin/env python3
"""Run the finite radical-pair compass calculation and emit evidence artifacts."""
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

from gaugegap.radical_pair_forge import (  # noqa: E402
    INVENTORY_SLUGS,
    NUCLEAR_INVENTORIES,
    SOURCES,
    run_radical_pair_forge,
)

# The slug map lives with the inventories, since benchmark_id derives from it
# too; re-exported here under its original name for the default --output-dir.
OUTPUT_SLUGS = INVENTORY_SLUGS
assert set(OUTPUT_SLUGS) == set(NUCLEAR_INVENTORIES), "every inventory needs an output slug"
assert len(set(OUTPUT_SLUGS.values())) == len(OUTPUT_SLUGS), "inventory slugs must be distinct"


def _positive_float(raw: str) -> float:
    """Reject non-positive field magnitudes at the CLI boundary.

    --field-ut is documented as a magnitude, and the report publishes
    field_microtesla, larmor_frequency_mhz and the Zeeman/thermal ratio as
    magnitudes.  The model is polarity-invariant, so a negative value would run
    to completion and pass every check while serializing all three negative.
    """
    value = float(raw)
    if value <= 0.0:
        raise argparse.ArgumentTypeError(f"must be positive, got {value}")
    return value


def _render_svg(payload: dict[str, object]) -> str:
    sweep = payload["sweep"]
    assert isinstance(sweep, dict)
    samples = sweep["samples"]
    assert isinstance(samples, list)
    controls = payload["controls"]
    assert isinstance(controls, dict)

    low = float(sweep["minimum_yield"])
    high = float(sweep["maximum_yield"])
    span = max(high - low, 1e-12)

    # Main panel: each direction's yield against the yield at its TRUE antipode,
    # (180-theta, phi+180).  Points land on the identity line because
    # Phi_S(B) = Phi_S(-B) exactly, which is what makes this a demonstration
    # rather than an assertion.  Plotting against polar angle would NOT show the
    # symmetry: for a rhombic tensor the yield depends on azimuth too, so
    # samples at mirrored polar angles are not antipodal pairs.
    points = []
    for sample in samples:
        assert isinstance(sample, dict)
        x = 110 + ((float(sample["singlet_yield"]) - low) / span) * 235
        y = 360 - ((float(sample["antipodal_singlet_yield"]) - low) / span) * 210
        points.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.6" fill="#7ee787" opacity="0.85"/>')

    rate_sweep = payload["rate_sweep"]
    assert isinstance(rate_sweep, list)
    peak = max(float(point["anisotropy"]) for point in rate_sweep) or 1.0
    rate_path = []
    for index, point in enumerate(rate_sweep):
        assert isinstance(point, dict)
        x = 680 + index * (330 / max(len(rate_sweep) - 1, 1))
        y = 360 - (float(point["anisotropy"]) / peak) * 210
        rate_path.append(f"{'M' if index == 0 else 'L'}{x:.2f},{y:.2f}")

    # Axis endpoints must come from the sweep that actually ran, not a literal:
    # --rate-points 4 sweeps 1e3..1e6, not 1e3..1e10.
    def _decade(value: float) -> str:
        return f"10^{round(math.log10(value))} s-1"

    rate_first = _decade(float(rate_sweep[0]["rate_per_second"]))
    rate_last = _decade(float(rate_sweep[-1]["rate_per_second"]))

    grid = "".join(
        f'<line x1="110" y1="{360 - i * 52.5:.1f}" x2="580" y2="{360 - i * 52.5:.1f}" stroke="#1d1d1d"/>'
        f'<line x1="680" y1="{360 - i * 52.5:.1f}" x2="1010" y2="{360 - i * 52.5:.1f}" stroke="#1d1d1d"/>'
        for i in range(5)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="560" viewBox="0 0 1100 560">
<rect width="1100" height="560" rx="20" fill="#050505"/>
<text x="550" y="50" fill="#fff" font-family="monospace" font-size="29" text-anchor="middle">RADICAL PAIR FORGE</text>
<text x="550" y="80" fill="#858585" font-family="monospace" font-size="14" text-anchor="middle">finite two-electron spin Hamiltonian, dim {payload["hilbert_dimension"]}, inventory {payload["inventory"]}</text>
{grid}
<line x1="110" y1="360" x2="580" y2="360" stroke="#333"/>
<line x1="110" y1="140" x2="110" y2="360" stroke="#333"/>
<line x1="110" y1="360" x2="345" y2="150" stroke="#3a3a3a" stroke-dasharray="4 4"/>
{''.join(points)}
<text x="345" y="112" fill="#c9d1d9" font-family="monospace" font-size="14" text-anchor="middle">yield at B vs yield at the antipode &#8722;B</text>
<text x="110" y="382" fill="#666" font-family="monospace" font-size="12">&#934;(B) &#8594;</text>
<text x="345" y="400" fill="#8b949e" font-family="monospace" font-size="12" text-anchor="middle">on the dashed identity line: polarity carries no information</text>
<line x1="680" y1="360" x2="1010" y2="360" stroke="#333"/>
<line x1="680" y1="140" x2="680" y2="360" stroke="#333"/>
<path d="{''.join(rate_path)}" fill="none" stroke="#f0883e" stroke-width="2.4"/>
<text x="845" y="112" fill="#c9d1d9" font-family="monospace" font-size="14" text-anchor="middle">anisotropy vs recombination rate</text>
<text x="680" y="382" fill="#666" font-family="monospace" font-size="12">{rate_first}</text>
<text x="945" y="382" fill="#666" font-family="monospace" font-size="12">{rate_last}</text>
<text x="845" y="400" fill="#8b949e" font-family="monospace" font-size="12" text-anchor="middle">upper cutoff only &#183; no relaxation, so no long-lifetime side</text>
<text x="110" y="440" fill="#7ee787" font-family="monospace" font-size="15">anisotropy = {float(payload["anisotropy"]):.4e} at {float(payload["field_microtesla"]):.0f} &#181;T ({float(payload["relative_contrast"]) * 100:.2f}% contrast)</text>
<text x="110" y="464" fill="#8b949e" font-family="monospace" font-size="13">isotropic-hyperfine control = {float(controls["isotropic_hyperfine_anisotropy"]):.2e} &#183; polarity residual = {float(controls["polarity_residual"]):.2e}</text>
<text x="110" y="486" fill="#8b949e" font-family="monospace" font-size="13">closed form vs Liouvillian = {float(controls["closed_form_vs_liouvillian_residual"]):.2e} (dim {controls["cross_check_hilbert_dimension"]}) &#183; spin-free partner {float(controls["second_radical_suppression_factor"]):.1f}&#215; stronger (tensor-dependent)</text>
<text x="110" y="508" fill="#8b949e" font-family="monospace" font-size="13">Zeeman quantum / k_B T at 300 K = {float(controls["zeeman_thermal_ratio_300k"]):.3e}: no thermal mechanism is available</text>
<text x="550" y="536" fill="#777" font-family="monospace" font-size="12" text-anchor="middle">finite spin-Hamiltonian calculation only &#183; not a cryptochrome measurement and not a sensor design</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        choices=sorted(NUCLEAR_INVENTORIES),
        default="cryptochrome-like",
        help="declared nuclear inventory for the radical pair",
    )
    parser.add_argument(
        "--field-ut",
        type=_positive_float,
        default=50.0,
        help="field magnitude in microtesla (must be positive)",
    )
    parser.add_argument("--direction-count", type=int, default=200)
    parser.add_argument("--control-direction-count", type=int, default=60)
    parser.add_argument("--rate-points", type=int, default=8, help="decades of recombination rate from 1e3")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="defaults to results/radicalpair-0001-<inventory>, derived after parsing",
    )
    args = parser.parse_args()

    # The default must follow the selected inventory, not be fixed at parser
    # construction: otherwise `--inventory loaded` with no --output-dir would
    # overwrite the default inventory's committed evidence bundle with results
    # for a different model, under a directory name that still said
    # "cryptochrome-compass".
    if args.output_dir is None:
        args.output_dir = ROOT / "results" / f"radicalpair-0001-{OUTPUT_SLUGS[args.inventory]}"

    report = run_radical_pair_forge(
        inventory=args.inventory,
        field_tesla=args.field_ut * 1e-6,
        direction_count=args.direction_count,
        control_direction_count=args.control_direction_count,
        rate_points=tuple(10.0 ** (3 + index) for index in range(max(2, args.rate_points))),
    )
    payload = report.summary(include_samples=True)
    payload["sources"] = list(SOURCES)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "directions.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "index",
            "x",
            "y",
            "z",
            "polar_deg",
            "azimuth_deg",
            "singlet_yield",
            "antipodal_singlet_yield",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample in report.sweep.samples:
            row = sample.summary()
            writer.writerow({key: row[key] for key in fieldnames})
    with (args.output_dir / "rate_sweep.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["rate_per_second", "anisotropy", "mean_yield"])
        writer.writeheader()
        for point in report.rate_sweep:
            writer.writerow(point.summary())
    (args.output_dir / "radical_pair_forge.svg").write_text(
        _render_svg(payload),
        encoding="utf-8",
    )

    printable = report.summary(include_samples=False)
    printable["sources"] = list(SOURCES)
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
