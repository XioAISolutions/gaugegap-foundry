#!/usr/bin/env python3
"""Run the NetGap finite photonic quantum-switch benchmark and emit evidence.

Assembles the exact unitary switch fabric (non-blocking routing realized as a coupler
mesh), an encoding-conversion round trip, and the coherence-preservation facts, then
writes a ledgered JSON bundle plus the discharged fidelity-preservation certificate.

Finite lossless unitary linear-optics model only; not a hardware, TFLN-materials,
loss/noise, or full quantum-network-protocol claim.
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
from gaugegap.quantum.photonic_switch import CLAIM_BOUNDARY, switch_report  # noqa: E402

HYPOTHESIS_ID = "netgap-0001"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--modes", type=int, default=4, help="number of photonic ports")
    ap.add_argument("--convert-theta", type=float, default=0.4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--emit-certificate", action="store_true", help="write the Lean/Coq files")
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / HYPOTHESIS_ID)
    args = ap.parse_args(argv)

    report = switch_report(n_modes=args.modes, convert_theta=args.convert_theta, seed=args.seed)
    certificate = report.pop("certificate")

    config = {"modes": args.modes, "convert_theta": args.convert_theta, "seed": args.seed}
    payload = {
        "hypothesis_id": HYPOTHESIS_ID,
        "track": "NetGap",
        "run_id": utc_run_id(),
        "git": git_state(ROOT),
        "config": config,
        "config_hash": object_hash(config),
        "claim_boundary": CLAIM_BOUNDARY,
        "report": report,
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{HYPOTHESIS_ID}-photonic-switch.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )
    write_jsonl(out / f"{HYPOTHESIS_ID}-records.jsonl", [payload])
    if args.emit_certificate:
        (out / f"{HYPOTHESIS_ID}_fidelity.lean").write_text(certificate["lean4"])
        (out / f"{HYPOTHESIS_ID}_fidelity.v").write_text(certificate["coq"])

    reach = report["reachability"]
    print("=" * 72)
    print(f"NetGap {HYPOTHESIS_ID}: finite photonic quantum switch ({args.modes} ports)")
    print(
        f"  fabric unitary={report['fabric_unitary']}  "
        f"mesh reconstruction error={report['mesh_reconstruction_error']:.2e}"
    )
    print(
        f"  non-blocking: {reach['num_routings']} routings, all realized="
        f"{reach['all_routings_realized_by_mesh']}"
    )
    print(
        f"  inner products preserved={report['inner_products_preserved']}  "
        f"round-trip fidelity={report['round_trip_fidelity']:.6f}"
    )
    print(
        f"  entanglement preserved={report['entanglement']['preserved']} "
        f"(S={report['entanglement']['entropy_after']:.6f})"
    )
    print(f"  CLAIM BOUNDARY: {CLAIM_BOUNDARY}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
