#!/usr/bin/env python3
"""Run a Spectra program (.spectra file) — certified spectral screening DSL.

Usage:
    python scripts/run_spectra.py examples/curverank_screen.spectra
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.spectra_lang import SpectraError, run_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=Path, help="Path to a .spectra file")
    args = parser.parse_args()

    try:
        prog = run_file(args.program)
    except SpectraError as exc:
        print(f"Spectra error: {exc}", file=sys.stderr)
        return 1

    print(f"Spectra: {args.program}")
    for name, c in prog.certificates.items():
        print(f"  certify {name}: {c['family']} n={c['n']} "
              f"M in [{c['lower']:.6f}, {c['upper']:.6f}]")
    for a in prog.assertions:
        print(f"  assert separated({a['certificate']}, > {a['threshold']}): "
              f"OK (certified lower {a['certified_lower']:.6f}) "
              f"-> Lean/Coq certificate")
    for name, m in prog.measurements.items():
        print(f"  measure {name}: target={m['target_eigenvalue']:.5f} "
              f"est={m['estimated_eigenvalue']:.5f} err={m['absolute_error']:.5f}")
    if prog.report_dir:
        print(f"  report -> {prog.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
