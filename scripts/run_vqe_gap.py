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

from gaugegap.ledger import git_state, object_hash
from gaugegap.models.z2_plaquette import hamiltonian_dense, model_metadata
from gaugegap.quantum.vqe_gap import estimate_gap_statevector
from gaugegap.verification.gap_certificate import make_gap_certificate, write_gap_certificate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny local statevector VQE-style gap estimate for gaugegap-0002.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0002")
    parser.add_argument("--n-plaquettes", type=int, default=1)
    parser.add_argument("--plaquette-coupling", type=float, default=1.0)
    parser.add_argument("--transverse-field", type=float, default=0.2)
    parser.add_argument("--layers", type=int, default=3)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "gaugegap-0002")
    args = parser.parse_args()

    metadata = model_metadata(args.n_plaquettes, args.plaquette_coupling, args.transverse_field)
    matrix = hamiltonian_dense(args.n_plaquettes, args.plaquette_coupling, args.transverse_field)
    result = estimate_gap_statevector(
        matrix,
        n_qubits=int(metadata["n_qubits"]),
        layers=args.layers,
        samples=args.samples,
        seed=args.seed,
    )

    record = {
        "hypothesis_id": args.hypothesis_id,
        "metadata": metadata,
        "hamiltonian_hash": object_hash(metadata),
        "vqe": result.to_dict(),
        "git": git_state(ROOT),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "z2_plaquette_vqe_gap.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    cert = make_gap_certificate(
        hypothesis_id=args.hypothesis_id,
        model=str(metadata["model"]),
        n_qubits=int(metadata["n_qubits"]),
        parameters=metadata,
        backend={"provider": "local", "name": result.backend, "mode": "statevector_vqe_style", "shots": None},
        ground_energy=result.ground_energy,
        first_excited_energy=result.first_excited_energy,
        gap=result.gap,
        residual_norm=None,
        status=result.status,
        git=record["git"],
        claim_boundary=str(metadata["claim_boundary"]),
    )
    write_gap_certificate(args.output_dir / "z2_plaquette_vqe_gap_certificate.json", cert)

    print(
        json.dumps(
            {
                "status": result.status,
                "gap": result.gap,
                "exact_gap": result.exact_gap,
                "gap_error": result.gap_error,
                "output_dir": str(args.output_dir),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
