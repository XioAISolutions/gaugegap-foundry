#!/usr/bin/env python3
"""Generate the deterministic Fractal Reality Lab evidence bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.fractal_reality import (  # noqa: E402
    ANALOGUE_LIBRARY,
    analyze_point,
    build_fractal_reality_manifest,
    compare_to_analogue,
    encode_brainsnn,
    julia_escape_grid,
)


def _parse_point(value: str) -> tuple[str, float, float]:
    try:
        name, real, imag = value.split(":", 2)
        return name, float(real), float(imag)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("point must be name:real:imag") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "site" / "fractal-reality-lab" / "data",
    )
    parser.add_argument("--max-iterations", type=int, default=256)
    parser.add_argument(
        "--point",
        action="append",
        type=_parse_point,
        help="Optional named point as name:real:imag; repeat for multiple points.",
    )
    parser.add_argument("--julia-width", type=int, default=160)
    parser.add_argument("--julia-height", type=int, default=120)
    args = parser.parse_args()

    if args.max_iterations < 8:
        parser.error("--max-iterations must be at least 8")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_fractal_reality_manifest(
        args.point,
        max_iterations=args.max_iterations,
    )
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    selected = manifest["experiments"][0]["orbit"]
    report = analyze_point(
        selected["c_real"],
        selected["c_imag"],
        max_iterations=args.max_iterations,
    )
    julia = julia_escape_grid(
        complex(report.c_real, report.c_imag),
        width=args.julia_width,
        height=args.julia_height,
        max_iterations=min(192, args.max_iterations),
    )
    compact = {
        "schema": "gaugegap.fractal_reality.compact.v1",
        "point": report.summary(),
        "julia": {
            "width": args.julia_width,
            "height": args.julia_height,
            "escape_counts": julia.tolist(),
        },
        "brainsnn": encode_brainsnn(report),
        "comparisons": {
            key: compare_to_analogue(report, key).summary()
            for key in ANALOGUE_LIBRARY
        },
        "manifest_sha256": manifest["content_sha256"],
    }
    compact_path = args.output_dir / "featured-experiment.json"
    compact_path.write_text(
        json.dumps(compact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "schema": manifest["schema"],
                "experiments": len(manifest["experiments"]),
                "analogues": len(manifest["analogues"]),
                "manifest": str(manifest_path),
                "featured": str(compact_path),
                "sha256": manifest["content_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
