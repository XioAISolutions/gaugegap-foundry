#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, object_hash
from gaugegap.models.z2_plaquette import hamiltonian_dense, model_metadata
from gaugegap.solvers.exact_gap import exact_gap
from gaugegap.verification.gap_certificate import make_gap_certificate, write_gap_certificate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gaugegap-0002 finite Z2 plaquette exact gap benchmark.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0002")
    parser.add_argument("--n-plaquettes", type=int, default=1)
    parser.add_argument("--plaquette-coupling", type=float, default=1.0)
    parser.add_argument("--transverse-field", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "gaugegap-0002")
    args = parser.parse_args()

    try:
        metadata = model_metadata(args.n_plaquettes, args.plaquette_coupling, args.transverse_field)
        matrix = hamiltonian_dense(args.n_plaquettes, args.plaquette_coupling, args.transverse_field)
        result = exact_gap(matrix)
    except ValueError as exc:
        parser.error(str(exc))

    record = {
        "hypothesis_id": args.hypothesis_id,
        "metadata": metadata,
        "hamiltonian_hash": object_hash(metadata),
        "result": result.to_dict(),
        "git": git_state(ROOT),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "z2_plaquette_gap.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (args.output_dir / "z2_plaquette_gap.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "hypothesis_id",
                "model",
                "n_qubits",
                "gap",
                "ground_energy",
                "first_excited_energy",
                "residual_norm",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "hypothesis_id": args.hypothesis_id,
                "model": metadata["model"],
                "n_qubits": metadata["n_qubits"],
                "gap": f"{result.gap:.12g}",
                "ground_energy": f"{result.ground_energy:.12g}",
                "first_excited_energy": f"{result.first_excited_energy:.12g}",
                "residual_norm": f"{result.residual_norm:.12g}",
                "status": result.status,
            }
        )

    cert = make_gap_certificate(
        hypothesis_id=args.hypothesis_id,
        model=str(metadata["model"]),
        n_qubits=int(metadata["n_qubits"]),
        parameters=metadata,
        backend={"provider": "local", "name": "numpy.linalg.eigh", "mode": "dense_exact", "shots": None},
        ground_energy=result.ground_energy,
        first_excited_energy=result.first_excited_energy,
        gap=result.gap,
        residual_norm=result.residual_norm,
        status=result.status,
        git=record["git"],
        claim_boundary=str(metadata["claim_boundary"]),
    )
    write_gap_certificate(args.output_dir / "z2_plaquette_gap_certificate.json", cert)

    print(
        json.dumps(
            {
                "claim_boundary": str(metadata["claim_boundary"]),
                "gap": result.gap,
                "output_dir": str(args.output_dir),
                "status": result.status,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
