#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl
from gaugegap.plot_svg import write_gap_svg
from gaugegap.qiskit_backend import qiskit_mass_gap
from gaugegap.z2_chain import mass_gap


def parse_sizes(value: str) -> list[int]:
    sizes = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not sizes or any(size <= 1 for size in sizes):
        raise argparse.ArgumentTypeError("sizes must be comma-separated integers greater than 1")
    return sizes


def linspace(start: float, stop: float, points: int) -> list[float]:
    if points <= 1:
        return [start]
    step = (stop - start) / (points - 1)
    return [start + i * step for i in range(points)]


def build_records(
    hypothesis_id: str,
    sizes: list[int],
    fields: list[float],
    exchange: float,
    periodic: bool,
    method: str,
) -> list[dict[str, object]]:
    run_id = utc_run_id()
    git = git_state(ROOT)
    records: list[dict[str, object]] = []

    for size in sizes:
        for field in fields:
            params = {
                "model": "z2_dual_chain",
                "lattice_size": size,
                "exchange_coupling": exchange,
                "transverse_field": field,
                "boundary": "periodic" if periodic else "open",
            }
            if method == "exact":
                gap, e0, e1 = mass_gap(
                    n_sites=size,
                    exchange_coupling=exchange,
                    transverse_field=field,
                    periodic=periodic,
                )
                method_name = "dense_exact_diagonalization"
                backend = {"provider": "local", "name": "numpy.linalg.eigvalsh", "mode": "exact_dense", "shots": None}
            elif method == "qiskit-pauli":
                gap, e0, e1 = qiskit_mass_gap(
                    n_sites=size,
                    exchange_coupling=exchange,
                    transverse_field=field,
                    periodic=periodic,
                )
                method_name = "qiskit_sparse_pauli_dense_diagonalization"
                backend = {"provider": "ibm-qiskit", "name": "SparsePauliOp.to_matrix", "mode": "local_pauli_matrix", "shots": None}
            else:
                raise ValueError(f"unsupported method: {method}")
            records.append(
                {
                    "run_id": run_id,
                    "hypothesis_id": hypothesis_id,
                    "track": "GaugeGap",
                    "model": "z2_dual_chain",
                    "observable": "mass_gap",
                    "params": params,
                    "hamiltonian_hash": object_hash(params),
                    "value": gap,
                    "ground_energy": e0,
                    "first_excited_energy": e1,
                    "method": method_name,
                    "backend": backend,
                    "git": git,
                }
            )
    return records


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "run_id",
                "hypothesis_id",
                "model",
                "lattice_size",
                "transverse_field",
                "exchange_coupling",
                "boundary",
                "mass_gap",
                "ground_energy",
                "first_excited_energy",
                "hamiltonian_hash",
            ],
        )
        writer.writeheader()
        for record in records:
            params = record["params"]
            assert isinstance(params, dict)
            writer.writerow(
                {
                    "run_id": record["run_id"],
                    "hypothesis_id": record["hypothesis_id"],
                    "model": record["model"],
                    "lattice_size": params["lattice_size"],
                    "transverse_field": f"{float(params['transverse_field']):.12g}",
                    "exchange_coupling": f"{float(params['exchange_coupling']):.12g}",
                    "boundary": params["boundary"],
                    "mass_gap": f"{float(record['value']):.12g}",
                    "ground_energy": f"{float(record['ground_energy']):.12g}",
                    "first_excited_energy": f"{float(record['first_excited_energy']):.12g}",
                    "hamiltonian_hash": record["hamiltonian_hash"],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the GaugeGap z2_dual_chain gap sweep.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0001")
    parser.add_argument("--sizes", type=parse_sizes, default=parse_sizes("4,6,8,10"))
    parser.add_argument("--field-start", type=float, default=0.2)
    parser.add_argument("--field-stop", type=float, default=2.0)
    parser.add_argument("--field-points", type=int, default=10)
    parser.add_argument("--exchange", type=float, default=1.0)
    parser.add_argument("--periodic", action="store_true")
    parser.add_argument("--method", choices=["exact", "qiskit-pauli"], default="exact")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "baselines")
    args = parser.parse_args()

    if not math.isfinite(args.exchange):
        parser.error("--exchange must be finite")
    if args.field_points <= 0:
        parser.error("--field-points must be positive")

    fields = linspace(args.field_start, args.field_stop, args.field_points)
    records = build_records(
        hypothesis_id=args.hypothesis_id,
        sizes=args.sizes,
        fields=fields,
        exchange=args.exchange,
        periodic=args.periodic,
        method=args.method,
    )

    stem = f"{args.hypothesis_id}-gap-sweep"
    jsonl_path = args.output_dir / f"{stem}.jsonl"
    csv_path = args.output_dir / f"{stem}.csv"
    svg_path = args.output_dir / f"{stem}.svg"

    write_jsonl(jsonl_path, records)
    write_csv(csv_path, records)
    write_gap_svg(svg_path, records)

    print(json.dumps({"records": len(records), "jsonl": str(jsonl_path), "csv": str(csv_path), "svg": str(svg_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
