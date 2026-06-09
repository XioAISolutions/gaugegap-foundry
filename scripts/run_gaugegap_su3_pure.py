#!/usr/bin/env python3
"""
Run SU(3) prototype scaffold sweep (gaugegap-0005).

This command exercises the finite-system SU(3)-adjacent pipeline. Outputs are
marked as prototype scaffold results and must not be presented as completed
SU(3) lattice gauge physics.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.gaugegap_su3_pure import (  # noqa: E402
    CLAIM_BOUNDARY,
    IMPLEMENTATION_STATUS,
    SU3PureGaugeConfig,
    SU3PureGaugeLattice,
)
from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl  # noqa: E402


def parse_lattice_size(size_str: str) -> tuple[int, int]:
    """Parse lattice size string like '2x2' into (2, 2)."""
    parts = size_str.lower().split("x")
    if len(parts) != 2:
        raise ValueError(f"Invalid lattice size format: {size_str}")
    return (int(parts[0]), int(parts[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SU(3) prototype scaffold sweep (gaugegap-0005)")
    parser.add_argument("--lattice-sizes", type=str, default="2x2", help="Comma-separated lattice sizes, e.g. '2x2,3x3'")
    parser.add_argument("--g-coupling-min", type=float, default=0.5, help="Minimum coupling")
    parser.add_argument("--g-coupling-max", type=float, default=3.0, help="Maximum coupling")
    parser.add_argument("--g-coupling-points", type=int, default=10, help="Number of coupling points")
    parser.add_argument("--truncation", type=float, default=0.5, help="Prototype truncation parameter")
    parser.add_argument("--boundary", type=str, default="periodic", choices=["periodic", "open"], help="Boundary conditions")
    parser.add_argument("--output-dir", type=str, default="results/baselines", help="Output directory")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run identifier")
    args = parser.parse_args()

    lattice_sizes = [parse_lattice_size(s.strip()) for s in args.lattice_sizes.split(",")]
    g_coupling_points = np.linspace(args.g_coupling_min, args.g_coupling_max, args.g_coupling_points).tolist()
    run_id = args.run_id or utc_run_id()
    git = git_state(ROOT)

    print("=" * 70)
    print("SU(3) Prototype Scaffold Sweep (gaugegap-0005)")
    print("=" * 70)
    print(f"Run ID: {run_id}")
    print(f"Lattice sizes: {lattice_sizes}")
    print(f"Coupling: [{args.g_coupling_min}, {args.g_coupling_max}] ({args.g_coupling_points} points)")
    print(f"Truncation: {args.truncation}")
    print(f"Boundary: {args.boundary}")
    print(f"Implementation status: {IMPLEMENTATION_STATUS}")
    print(f"Claim boundary: {CLAIM_BOUNDARY}")
    print("=" * 70)

    records: list[dict[str, object]] = []
    for nx, ny in lattice_sizes:
        for g_coupling in g_coupling_points:
            g_electric = g_coupling ** 2 / 2.0
            g_magnetic = 1.0 / (g_coupling ** 2)
            config = SU3PureGaugeConfig(
                nx=nx,
                ny=ny,
                g_electric=g_electric,
                g_magnetic=g_magnetic,
                truncation=args.truncation,
                boundary=args.boundary,
            )
            lattice = SU3PureGaugeLattice(config)
            result = lattice.compute_gap()

            record = {
                "run_id": run_id,
                "hypothesis_id": "gaugegap-0005",
                "track": "GaugeGap",
                "model": "su3_prototype_scaffold_2plus1d",
                "observable": "prototype_spectral_gap",
                "implementation_status": result.get("implementation_status", IMPLEMENTATION_STATUS),
                "claim_boundary": result.get("claim_boundary", CLAIM_BOUNDARY),
                "verified_complete_su3": result.get("verified_complete_su3", False),
                "verified_gauss_law": result.get("verified_gauss_law", False),
                "params": {
                    "nx": nx,
                    "ny": ny,
                    "g_coupling": g_coupling,
                    "g_electric": g_electric,
                    "g_magnetic": g_magnetic,
                    "truncation": args.truncation,
                    "boundary": args.boundary,
                },
                "hamiltonian_hash": object_hash(config.__dict__),
                "value": result.get("gap"),
                "ground_energy": result.get("E0"),
                "first_excited_energy": result.get("E1"),
                "method": result.get("method"),
                "hilbert_dim": result.get("hilbert_dim"),
                "n_links": result.get("n_links"),
                "n_plaquettes": result.get("n_plaquettes"),
                "status": "prototype" if result.get("gap") is not None else "failed",
                "error": result.get("error"),
                "git": git,
            }
            records.append(record)

            status_str = f"prototype_gap={result.get('gap', 'N/A')}"
            if result.get("error"):
                status_str = f"ERROR: {result.get('error')}"
            print(f"  {nx}x{ny}, g={g_coupling:.3f}: {status_str}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_base = output_dir / "gaugegap-0005-su3-prototype-sweep"

    jsonl_file = output_base.with_suffix(".jsonl")
    write_jsonl(jsonl_file, records)
    print(f"\nSaved JSONL: {jsonl_file}")

    csv_file = output_base.with_suffix(".csv")
    if records:
        flat_records = []
        for record in records:
            flat = {k: v for k, v in record.items() if k not in ["params", "git"]}
            params = record.get("params")
            if isinstance(params, dict):
                for key, value in params.items():
                    flat[f"param_{key}"] = value
            flat_records.append(flat)

        keys = flat_records[0].keys()
        with csv_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=keys)
            writer.writeheader()
            writer.writerows(flat_records)
        print(f"Saved CSV: {csv_file}")

    successful = [r for r in records if r.get("status") == "prototype"]
    failed = [r for r in records if r.get("status") != "prototype"]

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total runs: {len(records)}")
    print(f"Prototype runs: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Implementation status: {IMPLEMENTATION_STATUS}")

    if successful:
        gaps = [r["value"] for r in successful if r.get("value") is not None]
        if gaps:
            print("\nPrototype gap statistics:")
            print(f"  Min: {min(gaps):.6f}")
            print(f"  Max: {max(gaps):.6f}")
            print(f"  Mean: {np.mean(gaps):.6f}")
            print(f"  Std: {np.std(gaps):.6f}")

    if failed:
        print(f"\nFailed runs: {len(failed)}")
        for record in failed[:3]:
            print(f"  {record.get('params')}: {record.get('error')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
