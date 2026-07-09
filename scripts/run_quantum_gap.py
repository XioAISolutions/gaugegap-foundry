#!/usr/bin/env python3
"""Run the unified Quantum Gap report (quantumgap-0001) -- the program end to end.

Pushes one representative observable from every Foundry track through the same
formula QG(O, floor) = lower(O) - floor and reports each as a
(low, floor, gap, certified) row, then writes a ledgered JSON/CSV bundle plus the
generic discharged QG-positivity certificate.

The Quantum Gap is a unifying bookkeeping functional over the repository's verified
finite enclosures; it is not new physics and proves nothing beyond each underlying
finite certificate. Each row keeps its own track's claim boundary.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl  # noqa: E402
from gaugegap.quantum_gap import (  # noqa: E402
    CLAIM_BOUNDARY,
    emit_quantum_gap_certificate,
    unified_gap_report,
)

HYPOTHESIS_ID = "quantumgap-0001"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit-certificate", action="store_true", help="write the Lean/Coq files")
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / HYPOTHESIS_ID)
    args = ap.parse_args(argv)

    report = unified_gap_report()

    payload = {
        "hypothesis_id": HYPOTHESIS_ID,
        "track": "QuantumGap",
        "run_id": utc_run_id(),
        "git": git_state(ROOT),
        "config": {},
        "config_hash": object_hash({}),
        "claim_boundary": CLAIM_BOUNDARY,
        "report": report,
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{HYPOTHESIS_ID}-unified.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )
    write_jsonl(out / f"{HYPOTHESIS_ID}-records.jsonl", [payload])
    csv_lines = ["track,observable,enclosure_low,floor,quantum_gap,certified"]
    for row in report["rows"]:
        obs = row["observable"].replace(",", ";")
        csv_lines.append(
            f"{row['track']},{obs},{row['enclosure_low']:.10f},{row['floor']:.10f},"
            f"{row['gap']:.10f},{row['certified']}"
        )
    (out / f"{HYPOTHESIS_ID}-rows.csv").write_text("\n".join(csv_lines) + "\n")
    if args.emit_certificate:
        lean, coq = emit_quantum_gap_certificate("unified", 1.0, 0.0)
        (out / f"{HYPOTHESIS_ID}_gap.lean").write_text(lean)
        (out / f"{HYPOTHESIS_ID}_gap.v").write_text(coq)

    print("=" * 72)
    print(f"QuantumGap {HYPOTHESIS_ID}: the unified formula, one row per track")
    print(f"  {report['formula']}")
    print("-" * 72)
    for row in report["rows"]:
        flag = "CERT" if row["certified"] else "FAIL"
        print(
            f"  [{row['track']:9}] low={row['enclosure_low']:+.5f} "
            f"floor={row['floor']:+.5f} QG={row['gap']:+.5f} {flag}  "
            f"{row['observable']}"
        )
    print("-" * 72)
    print(f"  certified {report['n_certified']}/{report['n_rows']}  "
          f"all_certified={report['all_certified']}")
    print(f"  CLAIM BOUNDARY: {CLAIM_BOUNDARY}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
