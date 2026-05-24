#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.dynamics_analysis import analyze_records, load_dynamics_csvs, write_analysis_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze GaugeGap dynamics backend drift.")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "results" / "dynamics")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "analysis")
    parser.add_argument("--shot-warning", type=float, default=0.08)
    parser.add_argument("--shot-fail", type=float, default=0.18)
    parser.add_argument("--noise-warning", type=float, default=0.12)
    parser.add_argument("--noise-fail", type=float, default=0.28)
    args = parser.parse_args()

    records = load_dynamics_csvs(args.input_dir)
    rows, summaries, metadata = analyze_records(
        records,
        shot_warning=args.shot_warning,
        shot_fail=args.shot_fail,
        noise_warning=args.noise_warning,
        noise_fail=args.noise_fail,
    )
    outputs = write_analysis_outputs(args.output_dir, rows, summaries, metadata)

    print(json.dumps({"metadata": metadata, "outputs": outputs}, indent=2, sort_keys=True))
    return 0 if metadata["overall_verdict"] != "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
