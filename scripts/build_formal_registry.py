from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.formal_registry import build_formal_registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "quality" / "formal_registry.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    registry = build_formal_registry(args.root)
    payload = registry.summary()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if args.strict and registry.artifacts_with_holes else 0


if __name__ == "__main__":
    raise SystemExit(main())
