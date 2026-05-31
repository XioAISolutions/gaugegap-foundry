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

from gaugegap.quantum.qiskit_validation import QISKIT_CLAIM_BOUNDARY, QiskitValidationConfig, validate_qiskit_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run optional Qiskit/Aer/QPY validation for a finite Z2 GaugeGap candidate.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0004")
    parser.add_argument("--n-plaquettes", type=int, default=1)
    parser.add_argument("--plaquette-coupling", type=float, default=1.0)
    parser.add_argument("--transverse-field", type=float, default=0.2)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--noise-strength", type=float, default=0.001)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--max-qubits", type=int, default=12)
    parser.add_argument("--include-measurements", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "qiskit-validation")
    args = parser.parse_args()

    result = validate_qiskit_candidate(
        QiskitValidationConfig(
            hypothesis_id=args.hypothesis_id,
            n_plaquettes=args.n_plaquettes,
            plaquette_coupling=args.plaquette_coupling,
            transverse_field=args.transverse_field,
            shots=args.shots,
            noise_strength=args.noise_strength,
            layers=args.layers,
            seed=args.seed,
            run_id=args.run_id,
            include_measurements=args.include_measurements,
            max_qubits=args.max_qubits,
        ),
        output_dir=args.output_dir,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "qiskit_validation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    qpy_manifest = result.get("qpy_manifest", {})
    (args.output_dir / "qpy_manifest.json").write_text(
        json.dumps(qpy_manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "QISKIT_VALIDATION_SUMMARY.md").write_text(to_markdown(result), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": result.get("status"),
                "qiskit_available": result.get("capabilities", {}).get("qiskit_available")
                if isinstance(result.get("capabilities"), dict)
                else False,
                "aer_available": result.get("capabilities", {}).get("qiskit_aer_available")
                if isinstance(result.get("capabilities"), dict)
                else False,
                "output_dir": str(args.output_dir),
                "claim_boundary": QISKIT_CLAIM_BOUNDARY,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


def to_markdown(result: dict[str, object]) -> str:
    capabilities = result.get("capabilities", {})
    if not isinstance(capabilities, dict):
        capabilities = {}
    sparse = result.get("sparse_pauli_operator", {})
    if not isinstance(sparse, dict):
        sparse = {}
    transpilation = result.get("transpilation", {})
    if not isinstance(transpilation, dict):
        transpilation = {}
    aer = result.get("aer_simulation", {})
    if not isinstance(aer, dict):
        aer = {}
    qpy = result.get("qpy_manifest", {})
    if not isinstance(qpy, dict):
        qpy = {}

    lines = [
        "# Qiskit Candidate Validation",
        "",
        f"> {result.get('claim_boundary', QISKIT_CLAIM_BOUNDARY)}",
        "",
        "This is finite-system Qiskit validation only. It does not submit an IBM Runtime job and does not claim a continuum Yang-Mills mass gap.",
        "",
        "## Status",
        "",
        f"- Validation status: `{result.get('status')}`",
        f"- Qiskit available: `{capabilities.get('qiskit_available')}`",
        f"- QPY available: `{capabilities.get('qpy_available')}`",
        f"- Aer available: `{capabilities.get('qiskit_aer_available')}`",
        f"- IBM Runtime import available: `{capabilities.get('qiskit_ibm_runtime_available')}`",
        f"- Credentials checked: `{capabilities.get('credentials_checked')}`",
        "",
        "## SparsePauliOp Check",
        "",
        f"- Status: `{sparse.get('status', 'skipped')}`",
        f"- Matrix delta: `{float(sparse.get('matrix_delta', 0.0)):.4g}`",
        f"- Gap delta: `{float(sparse.get('gap_delta', 0.0)):.4g}`",
        "",
        "## Circuit Artifact",
        "",
        f"- QPY written: `{qpy.get('written', False)}`",
        f"- QPY sha256: `{qpy.get('sha256', 'n/a')}`",
        f"- Transpilation method: `{transpilation.get('method', 'skipped')}`",
        f"- Original depth: `{transpilation.get('original_depth', 'n/a')}`",
        f"- Transpiled depth: `{transpilation.get('transpiled_depth', 'n/a')}`",
        "",
        "## Aer",
        "",
        f"- Aer status: `{aer.get('status', 'pass' if aer.get('aer_available') else 'skipped')}`",
        f"- Aer available: `{aer.get('aer_available', False)}`",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
