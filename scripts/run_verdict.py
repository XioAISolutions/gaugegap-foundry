#!/usr/bin/env python3
"""Run a Verdict program (.verdict file) — eval-first model-claim DSL.

Usage:
    python scripts/run_verdict.py examples/sentiment_eval.verdict
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.verdict_lang import VerdictError, run_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=Path, help="Path to a .verdict file")
    args = parser.parse_args()

    try:
        prog = run_file(args.program)
    except VerdictError as exc:
        print(f"Verdict error: {exc}", file=sys.stderr)
        return 1

    print(f"Verdict: {args.program}")
    for name, e in prog.evals.items():
        print(f"  eval {name}: model={e['model']} dataset={e['dataset']} "
              f"{e['metric']}={e['score']:.4f} ({len(e['log'])} cases)")
    for a in prog.assertions:
        if a["kind"] == "score":
            print(f"  assert score({a['eval']}) >= {a['threshold']}: "
                  f"OK (measured {a['score']:.4f}) -> backed by eval log")
        else:
            print(f"  assert no_regression({a['eval']}, baseline={a['baseline']}): "
                  f"OK (measured {a['score']:.4f})")
    if prog.report_dir:
        print(f"  report -> {prog.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
