#!/usr/bin/env python3
"""Unified entry point for quantum hardware and cloud simulator runs.

Supports:
  --provider ibm      IBM Runtime SamplerV2 on real QPU
  --provider braket-local   Braket local StateVectorSimulator
  --provider braket-cloud   Braket cloud device (IonQ, Rigetti, QuEra, SV1, etc.)

Every run records provider, device/backend, job/task id, shots, and
circuit metadata in the standard JSONL/CSV ledger.
"""
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
from gaugegap.qiskit_dynamics import build_tfim_trotter_circuit, counts_z_observables


def parse_times(value: str) -> list[float]:
    return [float(x.strip()) for x in value.split(",") if x.strip()]


def run_ibm(args: argparse.Namespace) -> list[dict[str, object]]:
    from gaugegap.ibm_runtime_runner import run_sampler

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
            measure=True,
        )

        result = run_sampler(
            circuit,
            backend_name=args.backend_name,
            shots=args.shots,
            resilience_level=args.resilience_level,
            dynamical_decoupling=not args.no_dd,
        )

        observables = counts_z_observables(result["counts"], n_sites=args.n_sites)

        params = {
            "model": "z2_dual_chain",
            "lattice_size": args.n_sites,
            "exchange_coupling": args.exchange,
            "transverse_field": args.field,
            "time": time,
            "trotter_steps": args.steps,
            "initial_state": args.initial_state,
        }

        backend_info = {
            "provider": result["provider"],
            "name": result["backend_name"],
            "num_qubits": result["backend_num_qubits"],
            "mode": "hardware_sampler",
            "shots": result["shots"],
            "job_id": result["job_id"],
            "resilience_level": result["resilience_level"],
            "dynamical_decoupling": result["dynamical_decoupling"],
            "isa_circuit_depth": result["isa_circuit_depth"],
            "isa_circuit_size": result["isa_circuit_size"],
        }

        circuit_hash = object_hash({"params": params, "backend": backend_info["name"]})

        for site, val in enumerate(observables["z"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend_info, "z_expectation", site, None, val, time))
        for bond, val in enumerate(observables["zz"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend_info, "zz_correlator", None, bond, val, time))

    return records


def run_braket_local(args: argparse.Namespace) -> list[dict[str, object]]:
    from gaugegap.braket_runner import (
        braket_counts_to_z_observables,
        build_tfim_trotter_braket,
        run_local_simulator,
    )

    run_id = utc_run_id()
    git = git_state(ROOT)
    records: list[dict[str, object]] = []

    for time in args.times:
        circuit = build_tfim_trotter_braket(
            n_sites=args.n_sites,
            exchange_coupling=args.exchange,
            transverse_field=args.field,
            time=time,
            steps=args.steps,
            initial_state=args.initial_state,
        )

        result = run_local_simulator(circuit, shots=args.shots)
        observables = braket_counts_to_z_observables(result["counts"], n_sites=args.n_sites)

        params = {
            "model": "z2_dual_chain",
            "lattice_size": args.n_sites,
            "exchange_coupling": args.exchange,
            "transverse_field": args.field,
            "time": time,
            "trotter_steps": args.steps,
            "initial_state": args.initial_state,
        }

        backend_info = {
            "provider": result["provider"],
            "name": result["device"],
            "mode": "local_simulator",
            "shots": result["shots"],
            "device_arn": result["device_arn"],
        }

        circuit_hash = object_hash({"params": params, "backend": "braket-local"})

        for site, val in enumerate(observables["z"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend_info, "z_expectation", site, None, val, time))
        for bond, val in enumerate(observables["zz"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend_info, "zz_correlator", None, bond, val, time))

    return records


def run_braket_cloud(args: argparse.Namespace) -> list[dict[str, object]]:
    from gaugegap.braket_runner import (
        braket_counts_to_z_observables,
        build_tfim_trotter_braket,
        run_cloud_device,
    )

    run_id = utc_run_id()
    git = git_state(ROOT)
    records: list[dict[str, object]] = []

    for time in args.times:
        circuit = build_tfim_trotter_braket(
            n_sites=args.n_sites,
            exchange_coupling=args.exchange,
            transverse_field=args.field,
            time=time,
            steps=args.steps,
            initial_state=args.initial_state,
        )

        result = run_cloud_device(
            circuit,
            device_name=args.device_name,
            shots=args.shots,
            s3_bucket=args.s3_bucket,
        )
        observables = braket_counts_to_z_observables(result["counts"], n_sites=args.n_sites)

        params = {
            "model": "z2_dual_chain",
            "lattice_size": args.n_sites,
            "exchange_coupling": args.exchange,
            "transverse_field": args.field,
            "time": time,
            "trotter_steps": args.steps,
            "initial_state": args.initial_state,
        }

        backend_info = {
            "provider": result["provider"],
            "name": result["device"],
            "mode": "cloud_qpu",
            "shots": result["shots"],
            "device_arn": result["device_arn"],
            "task_id": result["task_id"],
        }

        circuit_hash = object_hash({"params": params, "backend": result["device_arn"]})

        for site, val in enumerate(observables["z"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend_info, "z_expectation", site, None, val, time))
        for bond, val in enumerate(observables["zz"]):
            records.append(_record(run_id, git, args.hypothesis_id, params, circuit_hash, backend_info, "zz_correlator", None, bond, val, time))

    return records


def _record(
    run_id, git, hypothesis_id, params, circuit_hash, backend, observable, site, bond, value, time,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "hypothesis_id": hypothesis_id,
        "track": "GaugeGap",
        "model": "z2_dual_chain",
        "observable": observable,
        "site": site,
        "bond": bond,
        "time": time,
        "params": params,
        "circuit_hash": circuit_hash,
        "value": value,
        "method": "hardware_trotter_dynamics",
        "backend": backend,
        "git": git,
    }


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["run_id", "hypothesis_id", "provider", "backend", "observable", "site", "bond", "time", "value", "circuit_hash", "job_id"],
            lineterminator="\n",
        )
        writer.writeheader()
        for r in records:
            backend = r["backend"]
            assert isinstance(backend, dict)
            writer.writerow({
                "run_id": r["run_id"],
                "hypothesis_id": r["hypothesis_id"],
                "provider": backend["provider"],
                "backend": backend["name"],
                "observable": r["observable"],
                "site": "" if r["site"] is None else r["site"],
                "bond": "" if r["bond"] is None else r["bond"],
                "time": r["time"],
                "value": f"{float(r['value']):.12g}",
                "circuit_hash": r["circuit_hash"],
                "job_id": backend.get("job_id", backend.get("task_id", "")),
            })


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TFIM dynamics on quantum hardware or cloud simulators.")
    parser.add_argument("--provider", required=True, choices=["ibm", "braket-local", "braket-cloud"])
    parser.add_argument("--hypothesis-id", default="gaugegap-0001")
    parser.add_argument("--n-sites", type=int, default=4)
    parser.add_argument("--exchange", type=float, default=1.0)
    parser.add_argument("--field", type=float, default=0.8)
    parser.add_argument("--times", type=parse_times, default=[0.0, 0.5, 1.0])
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--initial-state", choices=["zeros", "ones", "domain_wall"], default="domain_wall")
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "hardware")

    ibm_group = parser.add_argument_group("IBM Runtime")
    ibm_group.add_argument("--backend-name", type=str, default=None, help="IBM backend name (default: least busy)")
    ibm_group.add_argument("--resilience-level", type=int, default=1)
    ibm_group.add_argument("--no-dd", action="store_true", help="Disable dynamical decoupling")

    braket_group = parser.add_argument_group("Braket cloud")
    braket_group.add_argument("--device-name", type=str, default="sv1", help="Braket device short name or ARN")
    braket_group.add_argument("--s3-bucket", type=str, default=None)

    args = parser.parse_args()

    if args.provider == "ibm":
        records = run_ibm(args)
    elif args.provider == "braket-local":
        records = run_braket_local(args)
    elif args.provider == "braket-cloud":
        records = run_braket_cloud(args)
    else:
        raise ValueError(f"unknown provider: {args.provider}")

    out = args.output_dir
    slug = f"{args.hypothesis_id}-{args.provider}"
    write_jsonl(out / f"{slug}-hardware.jsonl", records)
    write_csv(out / f"{slug}-hardware.csv", records)

    print(json.dumps({
        "records": len(records),
        "provider": args.provider,
        "jsonl": str(out / f"{slug}-hardware.jsonl"),
        "csv": str(out / f"{slug}-hardware.csv"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
