#!/usr/bin/env python3
"""
Run SU(2) Pure Gauge Theory Sweep (gaugegap-0003)

Executes parameter sweeps for finite-lattice SU(2) pure gauge theory.

Usage:
    python scripts/run_gaugegap_su2_pure.py --output-dir results/baselines
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.gaugegap_su2_pure import (
    SU2PureGaugeConfig,
    SU2PureGaugeLattice,
)
from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl


def parse_lattice_size(size_str: str) -> tuple[int, int]:
    """Parse lattice size string like '2x2' into (2, 2)."""
    parts = size_str.lower().split('x')
    if len(parts) != 2:
        raise ValueError(f"Invalid lattice size format: {size_str}")
    return (int(parts[0]), int(parts[1]))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run SU(2) pure gauge theory sweep (gaugegap-0003)"
    )
    parser.add_argument(
        "--lattice-sizes",
        type=str,
        default="2x2",
        help="Comma-separated lattice sizes (e.g., '2x2')"
    )
    parser.add_argument(
        "--g-electric-min",
        type=float,
        default=0.5,
        help="Minimum electric coupling"
    )
    parser.add_argument(
        "--g-electric-max",
        type=float,
        default=2.0,
        help="Maximum electric coupling"
    )
    parser.add_argument(
        "--g-electric-points",
        type=int,
        default=5,
        help="Number of electric coupling points"
    )
    parser.add_argument(
        "--g-magnetic",
        type=float,
        default=1.0,
        help="Magnetic coupling (fixed)"
    )
    parser.add_argument(
        "--j-max",
        type=float,
        default=0.5,
        help="Truncation parameter"
    )
    parser.add_argument(
        "--boundary",
        type=str,
        default="periodic",
        choices=["periodic", "open"],
        help="Boundary conditions"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/baselines",
        help="Output directory for results"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional run identifier"
    )
    
    args = parser.parse_args()
    
    # Parse lattice sizes
    lattice_sizes = [parse_lattice_size(s.strip()) for s in args.lattice_sizes.split(',')]
    
    # Generate electric coupling points
    g_electric_points = np.linspace(
        args.g_electric_min,
        args.g_electric_max,
        args.g_electric_points
    ).tolist()
    
    run_id = args.run_id or utc_run_id()
    git = git_state(ROOT)
    
    print("=" * 70)
    print("SU(2) Pure Gauge Theory Sweep (gaugegap-0003)")
    print("=" * 70)
    print(f"Run ID: {run_id}")
    print(f"Lattice sizes: {lattice_sizes}")
    print(f"Electric coupling: [{args.g_electric_min}, {args.g_electric_max}] ({args.g_electric_points} points)")
    print(f"Magnetic coupling: {args.g_magnetic}")
    print(f"Truncation j_max: {args.j_max}")
    print(f"Boundary: {args.boundary}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 70)
    
    records: list[dict[str, object]] = []
    
    for nx, ny in lattice_sizes:
        for g_elec in g_electric_points:
            config = SU2PureGaugeConfig(
                nx=nx,
                ny=ny,
                g_electric=g_elec,
                g_magnetic=args.g_magnetic,
                j_max=args.j_max,
                boundary=args.boundary
            )
            
            lattice = SU2PureGaugeLattice(config)
            result = lattice.compute_gap()
            
            record = {
                "run_id": run_id,
                "hypothesis_id": "gaugegap-0003",
                "track": "GaugeGap",
                "model": "su2_pure_gauge_2plus1d",
                "observable": "mass_gap",
                "params": {
                    "nx": nx,
                    "ny": ny,
                    "g_electric": g_elec,
                    "g_magnetic": args.g_magnetic,
                    "j_max": args.j_max,
                    "boundary": args.boundary
                },
                "hamiltonian_hash": object_hash(config.__dict__),
                "value": result.get("gap"),
                "ground_energy": result.get("E0"),
                "first_excited_energy": result.get("E1"),
                "method": result.get("method"),
                "hilbert_dim": result.get("hilbert_dim"),
                "n_links": result.get("n_links"),
                "n_plaquettes": result.get("n_plaquettes"),
                "status": "pass" if result.get("gap") is not None else "fail",
                "error": result.get("error"),
                "git": git,
            }
            
            records.append(record)
            
            status_str = f"gap={result.get('gap', 'N/A')}"
            if result.get("error"):
                status_str = f"ERROR: {result.get('error')}"
            print(f"  {nx}x{ny}, g_e={g_elec:.3f}: {status_str}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    output_base = output_dir / f"gaugegap-0003-su2-pure-sweep"
    
    # Save JSONL
    jsonl_file = output_base.with_suffix(".jsonl")
    write_jsonl(jsonl_file, records)
    print(f"\nSaved JSONL: {jsonl_file}")
    
    # Save CSV
    csv_file = output_base.with_suffix(".csv")
    if records:
        # Flatten nested dicts for CSV
        flat_records = []
        for r in records:
            flat = {k: v for k, v in r.items() if k not in ["params", "git"]}
            if "params" in r and isinstance(r["params"], dict):
                for pk, pv in r["params"].items():
                    flat[f"param_{pk}"] = pv
            flat_records.append(flat)
        
        keys = flat_records[0].keys()
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(flat_records)
        print(f"Saved CSV: {csv_file}")
    
    # Summary statistics
    successful = [r for r in records if r.get("status") == "pass"]
    failed = [r for r in records if r.get("status") != "pass"]
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total runs: {len(records)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        gaps = [r["value"] for r in successful if r.get("value") is not None]
        if gaps:
            print(f"\nGap statistics:")
            print(f"  Min: {min(gaps):.6f}")
            print(f"  Max: {max(gaps):.6f}")
            print(f"  Mean: {np.mean(gaps):.6f}")
            print(f"  Std: {np.std(gaps):.6f}")
    
    if failed:
        print(f"\nFailed runs: {len(failed)}")
        for r in failed[:3]:
            params = r.get("params", {})
            print(f"  {params.get('nx')}x{params.get('ny')}, g_e={params.get('g_electric', 0):.3f}: {r.get('error', 'Unknown')}")
        if len(failed) > 3:
            print(f"  ... and {len(failed) - 3} more")
    
    print(f"\n{'='*70}")
    print("gaugegap-0003 sweep complete!")
    print(f"{'='*70}\n")
    
    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
