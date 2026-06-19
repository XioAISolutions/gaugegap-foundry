#!/usr/bin/env python3
"""CurveRank QPE on the IBM path — consolidated sweep + hardware staging.

Runs windowed, Trotterised quantum phase estimation for the Berry-Keating xp
truncations through the IBM provider and writes a consolidated results bundle
(JSON/CSV/SVG + JSONL ledger). The IBM **emulator** path is fully local (Aer, no
credentials, no cost) and runs now; the **hardware** path is staged behind a
credential check so it is one token away.

CLAIM BOUNDARY: this estimates eigenvalues of finite truncated toy operators and
benchmarks the quantum pipeline. It is spectral screening, not a proof of the
Riemann Hypothesis or the Hilbert-Polya conjecture.

Usage
-----
    # Real results now, no credentials (local IBM/Aer emulator):
    python scripts/run_curverank_ibm.py --emulator --n-basis 4,8 --yes

    # Real IBM hardware (needs a saved IBM Quantum token; queue applies):
    python scripts/run_curverank_ibm.py --device ibm_brisbane --n-basis 4 --yes
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import berry_keating_xp
from gaugegap.curverank_qpe import (
    build_qpe_circuit_trotter,
    choose_evolution_time_windowed,
    hamiltonian_to_sparse_pauli,
    extract_phase_from_counts,
    pad_to_power_of_two,
    unwrap_phase_to_eigenvalue,
)
from gaugegap.curverank_spectral import riemann_zero_targets, spectral_mismatch
from gaugegap.ledger import utc_run_id
from gaugegap.plot_svg import write_line_svg
from gaugegap.providers import get_provider

CLAIM_BOUNDARY = (
    "Spectral screening of finite truncated toy operators; not a proof of the "
    "Riemann Hypothesis or the Hilbert-Polya conjecture."
)


def _extract_counts(job) -> Dict[str, int]:
    result = job.result()
    if hasattr(result, "get_counts"):
        return result.get_counts()
    data = result[0].data
    if hasattr(data, "get_counts"):
        return data.get_counts()
    register = getattr(data, "c", None) or next(iter(vars(data).values()))
    return register.get_counts()


def run_one(
    n_basis: int,
    n_precision: int,
    shots: int,
    reps: int,
    window_radius: float,
    use_emulator: bool,
    device: str,
    method: str,
    *,
    H: "np.ndarray | None" = None,
    operator: str = "berry_keating_xp",
    target_index: "int | None" = None,
    mitigation: "dict | None" = None,
) -> Dict[str, object]:
    """Windowed QPE for one truncation, run through the IBM provider.

    ``method='dense'`` builds an exact controlled exp(-iH tau) (accurate, and per
    the hardware report actually cheaper in CX than Trotter up to n=16).
    ``method='trotter'`` is gate-efficient for scaling studies but, at the large
    windowed tau, accumulates Trotter error that can exceed the nominal phase
    resolution — reported honestly via absolute_error.

    ``H`` (optional) lets the caller supply any Hermitian operator; otherwise the
    named ``operator`` is built from the registry (default: Berry-Keating xp).
    ``target_index`` selects which eigenvalue to recover (default: the smallest
    positive one, matching the original behaviour).
    """
    from qiskit import transpile

    if H is None:
        from gaugegap.curverank_registry import get_operator

        spec = get_operator(operator)
        H = spec.build(n_basis)
        operator = spec.name
    H = np.asarray(H)
    evals, evecs = np.linalg.eigh(H)
    if target_index is None:
        idx = int(np.argmin(np.where(evals > 1e-9, evals, np.inf)))
    else:
        idx = int(target_index)
    target = float(evals[idx])

    # Windowed evolution time: precision spent on the target, not the full radius.
    tau = choose_evolution_time_windowed(window_radius)
    H_pad, vec_pad = pad_to_power_of_two(H, evecs[:, idx])
    if method == "trotter":
        pauli_op = hamiltonian_to_sparse_pauli(H_pad)
        qc = build_qpe_circuit_trotter(
            pauli_op, tau, n_precision=n_precision, reps=reps,
            initial_statevector=vec_pad,
        )
    else:
        from scipy.linalg import expm
        from gaugegap.curverank_qpe import build_qpe_circuit

        U = expm(-1j * H_pad * tau)
        qc = build_qpe_circuit(U, n_precision=n_precision, initial_statevector=vec_pad)
    # Decompose to a runnable basis; the hardware path re-transpiles to the device.
    tqc = transpile(qc, basis_gates=["u", "cx"], optimization_level=1)

    backend_name = "aer_simulator" if use_emulator else device
    provider = get_provider("ibm", backend_name=backend_name)
    if use_emulator:
        job, metadata = provider.submit_emulator(circuit=tqc, shots=shots)
    else:
        try:
            job, metadata = provider.submit_hardware(
                circuit=tqc, shots=shots, mitigation=mitigation
            )
        except TypeError:
            # Adapter without a mitigation kwarg.
            job, metadata = provider.submit_hardware(circuit=tqc, shots=shots)
    counts = _extract_counts(job)

    phase, phase_unc = extract_phase_from_counts(counts, n_precision)
    estimate = unwrap_phase_to_eigenvalue(phase, tau, target)
    resolution = (2 * np.pi / tau) / (2 ** n_precision)

    calibration = None
    cal = getattr(metadata, "calibration", None)
    if cal is not None and hasattr(cal, "to_dict"):
        try:
            calibration = cal.to_dict()
        except Exception:  # pragma: no cover - defensive
            calibration = None

    is_hardware = not use_emulator
    return {
        "operator": operator,
        "n_basis": n_basis,
        "target_index": idx,
        "n_qubits": tqc.num_qubits,
        "circuit_depth": tqc.depth(),
        "n_precision": n_precision,
        "shots": shots,
        "method": method,
        "evolution_time": tau,
        "target_eigenvalue": target,
        "estimated_eigenvalue": float(estimate),
        "absolute_error": abs(float(estimate) - target),
        "phase_resolution": float(resolution),
        "within_resolution": bool(abs(float(estimate) - target) <= 1.5 * resolution),
        "backend": metadata.backend_name,
        "job_id": metadata.job_id,
        "is_hardware": is_hardware,
        # Claim-boundary gate: only a real provider job id makes this a hardware result.
        "hardware_confirmed": bool(is_hardware and metadata.job_id),
        "mitigation": mitigation,
        "calibration": calibration,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--operator", type=str, default="berry_keating_xp",
                        help="Operator family from the registry "
                             "(berry_keating_xp, dirac_rindler, quantum_graph)")
    parser.add_argument("--n-basis", type=str, default="4,8",
                        help="Comma-separated power-of-two-friendly truncations")
    parser.add_argument("--n-precision", type=int, default=6)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--method", type=str, choices=["dense", "trotter"], default="dense",
                        help="dense exact controlled-U (accurate) or trotter (gate-efficient)")
    parser.add_argument("--trotter-reps", type=int, default=2)
    parser.add_argument("--window-radius", type=float, default=0.5,
                        help="Classical prior half-width around the target eigenvalue")
    parser.add_argument("--emulator", action="store_true",
                        help="Use the local IBM/Aer emulator (no credentials)")
    parser.add_argument("--device", type=str, default="ibm_brisbane",
                        help="IBM hardware device name (used when --emulator is absent)")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "results" / "curverank-ibm")
    args = parser.parse_args()

    n_basis_list = [int(x) for x in args.n_basis.split(",") if x.strip()]
    use_emulator = args.emulator

    print("=" * 72)
    print("CurveRank QPE on IBM — windowed Trotter eigenvalue recovery")
    print(f"  mode: {'emulator (local Aer, no credentials)' if use_emulator else f'hardware [{args.device}]'}")
    print("=" * 72)

    if not use_emulator:
        # Hardware path: verify credentials before doing work; otherwise stage.
        try:
            provider = get_provider("ibm", backend_name=args.device)
            has_creds = provider.check_credentials()
        except Exception as exc:  # pragma: no cover - depends on local install
            has_creds = False
            print(f"  IBM provider unavailable: {exc}")
        if not has_creds:
            print("\n  No IBM Quantum credentials found. Hardware run is STAGED.")
            print("  To run on real hardware (free Open plan works):")
            print("    1) Create an IBM Quantum account, copy your API token.")
            print("    2) python -c \"from qiskit_ibm_runtime import QiskitRuntimeService;"
                  " QiskitRuntimeService.save_account(channel='ibm_quantum', token='YOUR_TOKEN')\"")
            print(f"    3) python scripts/run_curverank_ibm.py --device {args.device} --yes")
            print("  See docs/curverank-ibm-runbook.md for details.")
            return 0

    rows: List[Dict[str, object]] = []
    for n in n_basis_list:
        row = run_one(
            n, args.n_precision, args.shots, args.trotter_reps,
            args.window_radius, use_emulator, args.device, args.method,
            operator=args.operator,
        )
        rows.append(row)
        print(
            f"n_basis={row['n_basis']:>3} | target={row['target_eigenvalue']:.5f} "
            f"est={row['estimated_eigenvalue']:.5f} err={row['absolute_error']:.5f} "
            f"(res {row['phase_resolution']:.4f}) | {row['n_qubits']}q d{row['circuit_depth']} "
            f"| {row['backend']}"
        )

    # Spectral-screening context: certified-targets mismatch for the recovered set.
    targets = riemann_zero_targets(max(2, len(rows)))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "generated": datetime.utcnow().isoformat(),
        "run_id": utc_run_id(),
        "mode": "emulator" if use_emulator else "hardware",
        "claim_boundary": CLAIM_BOUNDARY,
        "runs": rows,
    }
    (args.output_dir / "curverank-ibm-results.json").write_text(
        json.dumps(bundle, indent=2), encoding="utf-8"
    )

    header = ("n_basis,method,n_qubits,circuit_depth,n_precision,shots,evolution_time,"
              "target_eigenvalue,estimated_eigenvalue,absolute_error,phase_resolution,"
              "within_resolution,backend,job_id")
    lines = [header]
    for r in rows:
        lines.append(",".join(str(r[c]) for c in header.split(",")))
    (args.output_dir / "curverank-ibm-results.csv").write_text("\n".join(lines) + "\n")

    # Error-vs-resolution figure.
    write_line_svg(
        args.output_dir / "curverank-ibm-error.svg",
        {
            "abs error": [(r["n_basis"], r["absolute_error"]) for r in rows],
            "phase resolution": [(r["n_basis"], r["phase_resolution"]) for r in rows],
        },
        title="Windowed QPE eigenvalue error vs resolution (IBM path)",
        x_label="xp truncation size (n_basis)",
        y_label="eigenvalue (absolute)",
    )

    # Provenance ledger (append).
    with (args.output_dir / "curverank-ibm-ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "hypothesis_id": "curverank-0001",
            "result_type": "quantum_qpe_ibm",
            "run_id": bundle["run_id"],
            "mode": bundle["mode"],
            "runs": rows,
        }, sort_keys=True, default=str) + "\n")

    n_within = sum(1 for r in rows if r["within_resolution"])
    print("-" * 72)
    print(f"Recovered {n_within}/{len(rows)} eigenvalues within phase resolution.")
    print(f"Bundle: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
