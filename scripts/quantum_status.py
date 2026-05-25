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

from gaugegap.quantum_boundary import (
    ibm_runtime_readiness,
    quantum_summary,
    quantum_usage_map,
    render_quantum_usage_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report where GaugeGap Foundry actually uses quantum tooling.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "analysis")
    parser.add_argument("--probe-ibm", action="store_true", help="Try to connect to IBM Runtime. Does not submit jobs.")
    args = parser.parse_args()

    payload = {
        "summary": quantum_summary(),
        "surfaces": quantum_usage_map(),
        "ibm_runtime": ibm_runtime_readiness(probe=args.probe_ibm),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "quantum-usage-map.json"
    md_path = args.output_dir / "quantum-usage-map.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_quantum_usage_markdown(payload), encoding="utf-8")

    print(json.dumps({"summary": payload["summary"], "ibm_runtime": payload["ibm_runtime"], "outputs": {"json": str(json_path), "markdown": str(md_path)}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
