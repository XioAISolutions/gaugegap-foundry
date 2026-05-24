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

from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl
from gaugegap.qiskit_dynamics import aer_sample_z_observables, build_tfim_trotter_circuit, statevector_z_observables


def parse_times(value: str) -> list[float]:
    times = [float(part.strip()) for part in value.split(",") if part.strip()]
    if not times:
        raise argparse.ArgumentTypeError("times must include at least one value")
    return times


def records_for_observables(args: argparse.Namespace) -> list[dict[str, object]]:
    run_id = utc_run_id()
    git = git_state(ROOT)
    records: list[dict[str, object]] = []

    for time in args.times:
        circuit = build_tfim_trotter_circuit(
            n_sites=args.n_sites,
            exchange_coupling=args.exchange,
            transverse_field=args.field,
            time=time,
            steps=args.steps,
            initial_state=args.initial_state,
            periodic=args.periodic,
            measure=args.backend == "aer-sampler",
        )
        if args.backend == "statevector":
            observed = statevector_z_observables(circuit, n_sites=args.n_sites, periodic=args.periodic)
            backend = {"provider": "ibm-qiskit", "name": "Statevector", "mode": "local_statevector", "shots": None}
        elif args.backend == "aer-sampler":
            observed = aer_sample_z_observables(
                circuit,
                n_sites=args.n_sites,
                shots=args.shots,
                periodic=args.periodic,
                seed=args.seed,
                noise=args.noise,
            )
            backend = {"provider": "ibm-qiskit-aer", "name": "AerSimulator", "mode": f"shot_sampler:{args.noise}", "shots": args.shots}
        else:
            raise ValueError(f"unsupported backend: {args.backend}")

        params = {
            "model": "z2_dual_chain",
            "lattice_size": args.n_sites,
            "exchange_coupling": args.exchange,
            "transverse_field": args.field,
            "time": time,
            "trotter_steps": args.steps,
            "initial_state": args.initial_state,
            "boundary": "periodic" if args.periodic else "open",
        }
        circuit_hash = object_hash({"params": params, "qasm": circuit.qasm() if hasattr(circuit, "qasm") else str(circuit)})

        for site, value in enumerate(observed["z"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend, "z_expectation", site, None, value))
        for bond, value in enumerate(observed["zz"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend, "zz_correlator", None, bond, value))
    return records


def _record(
    run_id: str,
    git: dict[str, object],
    hypothesis_id: str,
    params: dict[str, object],
    circuit_hash: str,
    backend: dict[str, object],
    observable: str,
    site: int | None,
    bond: int | None,
    value: float,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "hypothesis_id": hypothesis_id,
        "track": "GaugeGap",
        "model": "z2_dual_chain",
        "observable": observable,
        "site": site,
        "bond": bond,
        "params": params,
        "circuit_hash": circuit_hash,
        "value": value,
        "method": "qiskit_trotter_dynamics",
        "backend": backend,
        "git": git,
    }


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "run_id",
                "hypothesis_id",
                "backend",
                "observable",
                "site",
                "bond",
                "time",
                "value",
                "circuit_hash",
            ],
        )
        writer.writeheader()
        for record in records:
            params = record["params"]
            backend = record["backend"]
            assert isinstance(params, dict)
            assert isinstance(backend, dict)
            writer.writerow(
                {
                    "run_id": record["run_id"],
                    "hypothesis_id": record["hypothesis_id"],
                    "backend": backend["mode"],
                    "observable": record["observable"],
                    "site": "" if record["site"] is None else record["site"],
                    "bond": "" if record["bond"] is None else record["bond"],
                    "time": params["time"],
                    "value": f"{float(record['value']):.12g}",
                    "circuit_hash": record["circuit_hash"],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Qiskit TFIM dynamics observables.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0001")
    parser.add_argument("--backend", choices=["statevector", "aer-sampler"], default="statevector")
    parser.add_argument("--n-sites", type=int, default=4)
    parser.add_argument("--exchange", type=float, default=1.0)
    parser.add_argument("--field", type=float, default=0.8)
    parser.add_argument("--times", type=parse_times, default=parse_times("0,0.25,0.5,1.0"))
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--initial-state", choices=["zeros", "ones", "domain_wall"], default="domain_wall")
    parser.add_argument("--periodic", action="store_true")
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--noise", choices=["none", "depolarizing"], default="none")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "dynamics")
    args = parser.parse_args()

    records = records_for_observables(args)
    stem = f"{args.hypothesis_id}-{args.backend}-dynamics"
    jsonl_path = args.output_dir / f"{stem}.jsonl"
    csv_path = args.output_dir / f"{stem}.csv"
    write_jsonl(jsonl_path, records)
    write_csv(csv_path, records)

    print(json.dumps({"records": len(records), "jsonl": str(jsonl_path), "csv": str(csv_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
