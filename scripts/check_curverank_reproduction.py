#!/usr/bin/env python3
"""Fail closed unless a reproduced CurveRank CSV meets a finite mismatch floor."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def mismatch_values(path: Path) -> list[float]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    values: list[float] = []
    for row in rows:
        if row.get("mismatch"):
            values.append(float(row["mismatch"]))
        elif row.get("observable") == "spectral_mismatch" and row.get("value"):
            values.append(float(row["value"]))
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("threshold", type=float)
    args = parser.parse_args()

    path = args.output_dir / "curverank-0001-spectral-screen.csv"
    if not path.exists():
        parser.error(f"verification failed: output not found: {path}")
    values = mismatch_values(path)
    if not values:
        parser.error(f"verification failed: no spectral mismatch rows in {path}")
    minimum = min(values)
    print(f"reproduced finite-truncation minimum mismatch: {minimum:.12g}")
    if minimum < args.threshold:
        parser.error(
            f"verification failed: {minimum:.12g} < configured floor {args.threshold:.12g}"
        )
    print(f"verification passed: {minimum:.12g} >= {args.threshold:.12g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
