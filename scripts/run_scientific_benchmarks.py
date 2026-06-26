from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.scientific_benchmarks import run_suite


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=ROOT / "benchmarks" / "known_answers.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "quality" / "known_answers.json")
    args = parser.parse_args()
    result = run_suite(args.spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = result.summary()
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
