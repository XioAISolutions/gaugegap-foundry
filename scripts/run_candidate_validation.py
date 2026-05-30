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

from gaugegap.validation.candidate_validation import ValidationConfig, validate_z2_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gaugegap-0004 finite-candidate hardware-readiness validation.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0004")
    parser.add_argument("--n-plaquettes", type=int, default=1)
    parser.add_argument("--plaquette-coupling", type=float, default=1.0)
    parser.add_argument("--transverse-field", type=float, default=0.2)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--noise-strength", type=float, default=0.02)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--max-qubits", type=int, default=12)
    parser.add_argument("--disable-qiskit-probe", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "gaugegap-0004")
    args = parser.parse_args()

    result = validate_z2_candidate(
        ValidationConfig(
            hypothesis_id=args.hypothesis_id,
            n_plaquettes=args.n_plaquettes,
            plaquette_coupling=args.plaquette_coupling,
            transverse_field=args.transverse_field,
            shots=args.shots,
            noise_strength=args.noise_strength,
            run_id=args.run_id,
            max_qubits=args.max_qubits,
            enable_qiskit_probe=not args.disable_qiskit_probe,
        )
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "hardware_readiness.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    (args.output_dir / "VALIDATION_SUMMARY.md").write_text(to_markdown(result), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "pass",
                "verdict": result["hardware_readiness"]["verdict"],
                "score": result["hardware_readiness"]["score"],
                "output_dir": str(args.output_dir),
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


def to_markdown(result: dict[str, object]) -> str:
    readiness = result["hardware_readiness"]
    assert isinstance(readiness, dict)
    exact = result["exact"]
    assert isinstance(exact, dict)
    replica = result["pauli_replica"]
    assert isinstance(replica, dict)
    resource = result["resource_estimate"]
    assert isinstance(resource, dict)
    qiskit_probe = result["qiskit_probe"]
    assert isinstance(qiskit_probe, dict)
    reasons = readiness.get("reasons", [])
    if not isinstance(reasons, list):
        reasons = [str(reasons)]

    lines = [
        "# gaugegap-0004 Validation Summary",
        "",
        f"> {result.get('claim_boundary')}",
        "",
        "This is a finite-system hardware-readiness report. It does not submit to hardware and does not claim a continuum Yang-Mills mass gap.",
        "",
        "## Verdict",
        "",
        f"- Score: `{float(readiness.get('score', 0.0)):.6g}`",
        f"- Verdict: `{readiness.get('verdict')}`",
        f"- Next action: {readiness.get('next_action')}",
        "",
        "## Exact Baseline",
        "",
        f"- Ground energy: `{float(exact.get('ground_energy', 0.0)):.12g}`",
        f"- First excited energy: `{float(exact.get('first_excited_energy', 0.0)):.12g}`",
        f"- Gap: `{float(exact.get('gap', 0.0)):.12g}`",
        f"- Residual norm: `{float(exact.get('residual_norm', 0.0)):.4g}`",
        "",
        "## Pauli Replica",
        "",
        f"- Status: `{replica.get('status')}`",
        f"- Matrix delta: `{float(replica.get('matrix_delta', 0.0)):.4g}`",
        f"- Gap delta: `{float(replica.get('gap_delta', 0.0)):.4g}`",
        "",
        "## Resource Estimate",
        "",
        f"- Qubits: `{resource.get('n_qubits')}`",
        f"- Pauli terms: `{resource.get('n_pauli_terms')}`",
        f"- Depth proxy: `{resource.get('toy_ansatz_depth_proxy')}`",
        f"- Hardware scale: `{resource.get('hardware_scale')}`",
        "",
        "## Qiskit / IBM Alignment",
        "",
        f"- Qiskit available: `{qiskit_probe.get('qiskit_available')}`",
        f"- Status: `{qiskit_probe.get('status')}`",
        "",
        "The intended IBM/Qiskit pattern is: map finite operator/circuit, inspect/transpile resources, execute only after local checks, then analyze deviations.",
        "",
        "## Reasons",
        "",
    ]
    for reason in reasons:
        lines.append(f"- {reason}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
