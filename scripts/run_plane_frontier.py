#!/usr/bin/env python3
"""Run the (72,108) plane-Jacobian frontier audit."""
from __future__ import annotations

import argparse
from pathlib import Path

from gaugegap.plane_frontier import canonical_json, run_plane_frontier_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = run_plane_frontier_audit()
    payload = audit.to_dict()
    if not audit.passed:
        raise SystemExit("plane-frontier-0001 failed closed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "plane-frontier-0001.audit.json"
    output.write_text(canonical_json(payload), encoding="utf-8")

    print("plane-frontier-0001: PASS")
    print("evidence_label: INDEPENDENT_REPRODUCTION")
    print(f"lattice_points: P={audit.p_points}, Q={audit.q_points}")
    print(f"operators: {audit.operators}")
    print(f"base_rank: {audit.base_rank}")
    print(f"base_kernel_dimension: {audit.kernel_dimension}")
    print(f"degree1_exact_verified: {audit.degree1.verified}")
    print(f"degree1_rhs_pairing: {audit.degree1.rhs_pairing}")
    for item in audit.degree2:
        print(
            f"degree2_mod_{item.prime}: infeasible={item.infeasible}, "
            f"rank={item.rank}, shape={item.rows}x{item.columns}"
        )
    print(f"audit_digest: {payload['audit_digest']}")
    print(f"evidence: {output}")
    print(f"claim_boundary: {audit.claim_boundary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
