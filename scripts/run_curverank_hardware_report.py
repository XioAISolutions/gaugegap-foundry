#!/usr/bin/env python3
"""Quantify CurveRank QPE circuit cost: dense vs Trotter vs iterative.

Replaces assertion with measurement: for each Berry-Keating ``xp`` truncation it
transpiles the three controlled-evolution circuit families to a fixed
``{u, cx}`` basis and records width, depth, and two-qubit (CX) gate count,
writing a CSV/JSON/SVG/Markdown report.

What the numbers actually show (and what they don't):

- The **iterative** single-ancilla variant uses far fewer *qubits* than the
  register-based variants (system + 1, vs system + n_precision). That width
  advantage is real at every size and is the headline NISQ benefit.
- At **small** truncations the **dense** controlled unitary is *cheaper in CX*
  than Trotter, because Qiskit synthesises a few-qubit unitary near-optimally
  while Trotter pays for many Pauli rotations. The dense cost grows like
  ``4^n_system`` though, so the Trotter/dense CX crossover is asymptotic --
  this report locates it rather than presupposing it.
- Dense synthesis also requires loading an arbitrary unitary, which is not a
  hardware primitive; Trotter/iterative use only native-style rotations.

This measures *circuit-resource cost only* (a transpilation-level proxy for
hardware feasibility); it does not run hardware and makes no scientific claim
about the operator spectra. See CLAIM BOUNDARY in the CurveRank modules.

Usage
-----
    python scripts/run_curverank_hardware_report.py \
        --n-basis 2,4,8 --n-precision 4 --output-dir results/curverank-hardware
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import berry_keating_xp
from gaugegap.curverank_qpe import (
    build_qpe_circuit,
    build_qpe_circuit_trotter,
    choose_evolution_time,
    hamiltonian_to_sparse_pauli,
    pad_to_power_of_two,
)
from gaugegap.plot_svg import write_line_svg


def _cx_count(circuit) -> int:
    ops = circuit.count_ops()
    return int(ops.get("cx", 0))


def _transpiled_metrics(circuit) -> Dict[str, int]:
    from qiskit import transpile

    tqc = transpile(circuit, basis_gates=["u", "cx"], optimization_level=1)
    return {
        "n_qubits": tqc.num_qubits,
        "depth": tqc.depth(),
        "cx": _cx_count(tqc),
    }


def _iterative_round_metrics(pauli_op, tau, k: int, reps: int, n_system: int) -> Dict[str, int]:
    """Cost of the most expensive iterative-QPE round (exponent ``k``).

    Iterative QPE runs ``n`` such single-ancilla rounds; the ``k = n-1`` round
    (longest controlled evolution) dominates and bounds the per-circuit cost.
    """
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.circuit.library import PauliEvolutionGate
    from qiskit.synthesis import LieTrotter

    ancilla = QuantumRegister(1, "ancilla")
    system = QuantumRegister(n_system, "system")
    creg = ClassicalRegister(1, "c")
    qc = QuantumCircuit(ancilla, system, creg)
    qc.h(ancilla[0])
    steps = max(1, reps * (2 ** k))
    evo = PauliEvolutionGate(pauli_op, time=tau * (2 ** k), synthesis=LieTrotter(reps=steps))
    qc.append(evo.control(1), [ancilla[0]] + list(system))
    qc.p(0.0, ancilla[0])
    qc.h(ancilla[0])
    qc.measure(ancilla[0], creg[0])
    return _transpiled_metrics(qc)


def build_report(n_basis_list: List[int], n_precision: int, reps: int) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for n_basis in n_basis_list:
        H = berry_keating_xp(n_basis)
        evals, evecs = np.linalg.eigh(H)
        idx = int(np.argmin(np.where(evals > 1e-9, evals, np.inf)))
        tau = choose_evolution_time(evals)
        H_pad, vec_pad = pad_to_power_of_two(H, evecs[:, idx])
        n_system = (H_pad.shape[0]).bit_length() - 1

        from scipy.linalg import expm

        # Dense controlled unitary.
        U = expm(-1j * H_pad * tau)
        dense = _transpiled_metrics(
            build_qpe_circuit(U, n_precision=n_precision, initial_statevector=vec_pad)
        )

        # Trotterised controlled Pauli evolution.
        pauli_op = hamiltonian_to_sparse_pauli(H_pad)
        trotter = _transpiled_metrics(
            build_qpe_circuit_trotter(
                pauli_op, tau, n_precision=n_precision, reps=reps,
                initial_statevector=vec_pad,
            )
        )

        # Iterative single-ancilla worst-case round.
        iterative = _iterative_round_metrics(
            pauli_op, tau, n_precision - 1, reps, n_system
        )

        row = {
            "n_basis": n_basis,
            "n_system_qubits": n_system,
            "n_pauli_terms": len(pauli_op),
            "dense_qubits": dense["n_qubits"],
            "dense_depth": dense["depth"],
            "dense_cx": dense["cx"],
            "trotter_qubits": trotter["n_qubits"],
            "trotter_depth": trotter["depth"],
            "trotter_cx": trotter["cx"],
            "iterative_qubits": iterative["n_qubits"],
            "iterative_depth": iterative["depth"],
            "iterative_cx": iterative["cx"],
        }
        rows.append(row)
        print(
            f"n_basis={n_basis:>3} | dense cx={dense['cx']:>6} depth={dense['depth']:>6} "
            f"| trotter cx={trotter['cx']:>6} depth={trotter['depth']:>6} "
            f"| iter-round cx={iterative['cx']:>5} qubits={iterative['n_qubits']}"
        )
    return rows


def write_outputs(rows: List[Dict[str, object]], output_dir: Path, n_precision: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated": datetime.utcnow().isoformat(),
        "n_precision": n_precision,
        "metric": "transpiled to {u, cx}, optimization_level=1",
        "claim_boundary": (
            "Circuit-resource proxy for hardware feasibility only; no hardware "
            "run and no scientific claim about operator spectra."
        ),
        "rows": rows,
    }
    (output_dir / "hardware_report.json").write_text(json.dumps(payload, indent=2))

    header = (
        "n_basis,n_system_qubits,n_pauli_terms,"
        "dense_qubits,dense_depth,dense_cx,"
        "trotter_qubits,trotter_depth,trotter_cx,"
        "iterative_qubits,iterative_depth,iterative_cx"
    )
    lines = [header]
    for r in rows:
        lines.append(",".join(str(r[c]) for c in header.split(",")))
    (output_dir / "hardware_report.csv").write_text("\n".join(lines) + "\n")

    # CX-count comparison plot (the headline hardware-feasibility metric).
    cx_series = {
        "dense (full QPE)": [(r["n_basis"], r["dense_cx"]) for r in rows],
        "trotter (full QPE)": [(r["n_basis"], r["trotter_cx"]) for r in rows],
        "iterative (per round)": [(r["n_basis"], r["iterative_cx"]) for r in rows],
    }
    write_line_svg(
        output_dir / "hardware_cx_counts.svg",
        cx_series,
        title="Two-qubit (CX) gate count: dense vs Trotter vs iterative",
        x_label="xp truncation size (n_basis)",
        y_label="CX gates (transpiled)",
    )

    # Honest narrative summary derived from the measured rows.
    widest = rows[-1]
    dense_cross = next(
        (r["n_basis"] for r in rows if r["trotter_cx"] < r["dense_cx"]), None
    )
    md = [
        "# CurveRank QPE hardware-feasibility report",
        "",
        f"Generated: {payload['generated']}  ",
        f"n_precision: {n_precision}; metric: {payload['metric']}",
        "",
        "## Findings",
        "",
        "- **Qubit width:** the iterative single-ancilla variant uses "
        f"{widest['iterative_qubits']} qubits at n_basis={widest['n_basis']} "
        f"versus {widest['dense_qubits']} for the register-based variants -- "
        "the consistent NISQ advantage.",
    ]
    if dense_cross is None:
        md.append(
            "- **CX count:** across the measured sizes the dense controlled "
            "unitary remains cheaper in CX than Trotter; the crossover lies "
            "beyond the largest n_basis tested (dense grows like 4^n_system, "
            "so extend the sweep to locate it)."
        )
    else:
        md.append(
            f"- **CX count:** Trotter overtakes dense in CX at n_basis="
            f"{dense_cross} and below."
        )
    md += [
        "- **Hardware primitive:** dense synthesis loads an arbitrary unitary "
        "(not a device primitive); Trotter/iterative use only rotation gates.",
        "",
        "## Measurements",
        "",
        "| n_basis | sys qubits | pauli terms | dense CX | trotter CX | iter-round CX | iter qubits |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        md.append(
            f"| {r['n_basis']} | {r['n_system_qubits']} | {r['n_pauli_terms']} | "
            f"{r['dense_cx']} | {r['trotter_cx']} | {r['iterative_cx']} | "
            f"{r['iterative_qubits']} |"
        )
    md += ["", f"Claim boundary: {payload['claim_boundary']}", ""]
    (output_dir / "hardware_report.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\nReport written to: {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n-basis", type=str, default="2,4,8", help="Comma-separated xp truncation sizes")
    parser.add_argument("--n-precision", type=int, default=4, help="QPE counting qubits")
    parser.add_argument("--trotter-reps", type=int, default=2, help="Trotter steps for the k=0 power")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "curverank-hardware")
    args = parser.parse_args()

    try:
        import qiskit  # noqa: F401
    except ImportError:
        print("This report requires the 'quantum' extra (qiskit). "
              "Install with: pip install -e '.[quantum]'")
        return 1

    n_basis_list = [int(x) for x in args.n_basis.split(",") if x.strip()]
    print("="*70)
    print("CurveRank QPE hardware-feasibility report")
    print(f"  n_precision={args.n_precision}, trotter_reps={args.trotter_reps}")
    print("="*70)
    rows = build_report(n_basis_list, args.n_precision, args.trotter_reps)
    write_outputs(rows, args.output_dir, args.n_precision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
