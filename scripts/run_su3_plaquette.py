#!/usr/bin/env python3
"""Run the exact single-plaquette SU(3) benchmark (gaugegap-0006) and emit evidence.

Sweeps the gauge coupling, solving the exact character-basis Hamiltonian
H = (g^2/2) C2(p,q) - (1/(2 g^2))(M + M^T) at each point, and reports the mass gap,
the Wilson loop <(1/3) Re Tr U>, and the truncation convergence, then writes a
ledgered JSON/CSV bundle plus the discharged strong-coupling gap-positivity
certificate.

Exact finite single-plaquette SU(3) model in the character basis only; not a
multi-plaquette lattice, a continuum limit, or a Yang-Mills mass-gap claim.
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

from gaugegap.gaugegap_su3_plaquette import (  # noqa: E402
    CLAIM_BOUNDARY,
    emit_gap_certificate,
    solve_plaquette,
    truncation_convergence,
)
from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl  # noqa: E402

HYPOTHESIS_ID = "gaugegap-0006"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--couplings", type=float, nargs="+",
                    default=[0.7, 1.0, 1.5, 2.0, 3.0, 5.0], help="gauge couplings to sweep")
    ap.add_argument("--cutoff", type=int, default=8, help="irrep truncation p + q <= cutoff")
    ap.add_argument("--conv-couplings", type=float, nargs="+", default=[1.0],
                    help="couplings at which to report truncation convergence")
    ap.add_argument("--emit-certificate", action="store_true", help="write the Lean/Coq files")
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / HYPOTHESIS_ID)
    args = ap.parse_args(argv)

    sweep = []
    for g in args.couplings:
        r = solve_plaquette(coupling=g, cutoff=args.cutoff)
        sweep.append({
            "coupling": r.coupling,
            "basis_size": r.basis_size,
            "ground_energy": r.ground_energy,
            "gap": r.gap,
            "strong_coupling_gap": r.strong_coupling_gap,
            "wilson_loop_1x1": r.wilson_loop_1x1,
            "gap_positive": r.gap > 0.0,
        })

    convergence = {f"g={g}": truncation_convergence(g) for g in args.conv_couplings}
    lean, coq, floor = emit_gap_certificate(min(args.couplings))

    config = {"couplings": args.couplings, "cutoff": args.cutoff,
              "conv_couplings": args.conv_couplings}
    payload = {
        "hypothesis_id": HYPOTHESIS_ID,
        "track": "GaugeGap",
        "run_id": utc_run_id(),
        "git": git_state(ROOT),
        "config": config,
        "config_hash": object_hash(config),
        "claim_boundary": CLAIM_BOUNDARY,
        "report": {
            "coupling_sweep": sweep,
            "truncation_convergence": convergence,
            "all_gaps_positive": all(row["gap_positive"] for row in sweep),
            "wilson_loop_monotone": all(
                sweep[i]["wilson_loop_1x1"] <= sweep[i - 1]["wilson_loop_1x1"] + 1e-12
                for i in range(1, len(sweep))
            ),
            "strong_coupling_gap_floor": floor,
            "gauss_law_by_construction": True,
        },
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{HYPOTHESIS_ID}-plaquette.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )
    write_jsonl(out / f"{HYPOTHESIS_ID}-records.jsonl", [payload])
    csv_lines = ["coupling,basis_size,ground_energy,gap,strong_coupling_gap,wilson_loop_1x1"]
    for row in sweep:
        csv_lines.append(
            f"{row['coupling']},{row['basis_size']},{row['ground_energy']:.10f},"
            f"{row['gap']:.10f},{row['strong_coupling_gap']:.10f},{row['wilson_loop_1x1']:.10f}"
        )
    (out / f"{HYPOTHESIS_ID}-sweep.csv").write_text("\n".join(csv_lines) + "\n")
    if args.emit_certificate:
        (out / f"{HYPOTHESIS_ID}_gap.lean").write_text(lean)
        (out / f"{HYPOTHESIS_ID}_gap.v").write_text(coq)

    print("=" * 72)
    print(f"GaugeGap {HYPOTHESIS_ID}: exact single-plaquette SU(3) (cutoff p+q<={args.cutoff})")
    for row in sweep:
        print(
            f"  g={row['coupling']:<4}  gap={row['gap']:.6f}  "
            f"strong-gap={row['strong_coupling_gap']:.6f}  "
            f"W={row['wilson_loop_1x1']:.6f}"
        )
    print(f"  all gaps positive={payload['report']['all_gaps_positive']}  "
          f"Wilson monotone={payload['report']['wilson_loop_monotone']}  "
          f"Gauss law by construction=True")
    print(f"  CLAIM BOUNDARY: {CLAIM_BOUNDARY}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
