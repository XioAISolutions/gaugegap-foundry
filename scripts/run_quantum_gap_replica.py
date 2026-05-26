#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, object_hash
from gaugegap.models.z2_plaquette import hamiltonian_dense, model_metadata, pauli_terms
from gaugegap.quantum.pauli_export import pauli_terms_to_dense, qiskit_available, qiskit_matrix
from gaugegap.solvers.exact_gap import exact_gap
from gaugegap.verification.gap_certificate import make_gap_certificate, write_gap_certificate


def main() -> int:
    parser = argparse.ArgumentParser(description="Replicate the finite Z2 plaquette gap through Pauli/Qiskit operator paths.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0002")
    parser.add_argument("--n-plaquettes", type=int, default=1)
    parser.add_argument("--plaquette-coupling", type=float, default=1.0)
    parser.add_argument("--transverse-field", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "gaugegap-0002")
    args = parser.parse_args()

    metadata = model_metadata(args.n_plaquettes, args.plaquette_coupling, args.transverse_field)
    exact_matrix = hamiltonian_dense(args.n_plaquettes, args.plaquette_coupling, args.transverse_field)
    exact_result = exact_gap(exact_matrix)

    local_pauli_matrix = pauli_terms_to_dense(pauli_terms(args.n_plaquettes, args.plaquette_coupling, args.transverse_field))
    local_pauli_result = exact_gap(local_pauli_matrix)
    qiskit_result = None
    qiskit_error = None

    if qiskit_available():
        try:
            qiskit_result = exact_gap(qiskit_matrix(args.n_plaquettes, args.plaquette_coupling, args.transverse_field))
        except Exception as exc:  # pragma: no cover - defensive external dependency guard
            qiskit_error = repr(exc)

    matrix_delta = float(np.linalg.norm(exact_matrix - local_pauli_matrix))
    gap_delta = abs(exact_result.gap - local_pauli_result.gap)
    status = "pass" if matrix_delta <= 1e-9 and gap_delta <= 1e-9 else "fail"

    record = {
        "hypothesis_id": args.hypothesis_id,
        "metadata": metadata,
        "hamiltonian_hash": object_hash(metadata),
        "pauli_terms": pauli_terms(args.n_plaquettes, args.plaquette_coupling, args.transverse_field),
        "exact": exact_result.to_dict(),
        "local_pauli": local_pauli_result.to_dict(),
        "qiskit": None if qiskit_result is None else qiskit_result.to_dict(),
        "qiskit_error": qiskit_error,
        "matrix_delta": matrix_delta,
        "gap_delta": gap_delta,
        "status": status,
        "git": git_state(ROOT),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "z2_plaquette_quantum_replica.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (args.output_dir / "z2_plaquette_quantum_replica.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "gap", "ground_energy", "first_excited_energy", "status"])
        writer.writeheader()
        writer.writerow({"path": "exact_dense", "gap": exact_result.gap, "ground_energy": exact_result.ground_energy, "first_excited_energy": exact_result.first_excited_energy, "status": exact_result.status})
        writer.writerow({"path": "local_pauli_dense", "gap": local_pauli_result.gap, "ground_energy": local_pauli_result.ground_energy, "first_excited_energy": local_pauli_result.first_excited_energy, "status": local_pauli_result.status})
        if qiskit_result is not None:
            writer.writerow({"path": "qiskit_sparse_pauli", "gap": qiskit_result.gap, "ground_energy": qiskit_result.ground_energy, "first_excited_energy": qiskit_result.first_excited_energy, "status": qiskit_result.status})

    cert = make_gap_certificate(
        hypothesis_id=args.hypothesis_id,
        model=str(metadata["model"]),
        n_qubits=int(metadata["n_qubits"]),
        parameters=metadata,
        backend={"provider": "local", "name": "pauli_terms_to_dense", "mode": "operator_replica", "shots": None},
        ground_energy=local_pauli_result.ground_energy,
        first_excited_energy=local_pauli_result.first_excited_energy,
        gap=local_pauli_result.gap,
        residual_norm=local_pauli_result.residual_norm,
        status=f"replica_{status}",
        git=record["git"],
        claim_boundary=str(metadata["claim_boundary"]),
    )
    write_gap_certificate(args.output_dir / "z2_plaquette_quantum_replica_certificate.json", cert)

    print(json.dumps({"status": status, "matrix_delta": matrix_delta, "gap_delta": gap_delta, "qiskit_available": qiskit_available(), "output_dir": str(args.output_dir)}, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
