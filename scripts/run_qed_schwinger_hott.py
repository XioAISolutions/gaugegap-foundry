from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from gaugegap.cohesive_gauge import CLAIM_BOUNDARY as COH_BOUNDARY, audit_gauge_coherence
from gaugegap.qed_one_loop import (
    CLAIM_BOUNDARY as QED_BOUNDARY,
    QEDParameters,
    audit_qed,
    scan_qed,
    self_energy_dressings,
)
from gaugegap.schwinger_model import (
    CLAIM_BOUNDARY as SCH_BOUNDARY,
    SchwingerConfig,
    build_projected_hamiltonian,
    scan_mass,
    solve_schwinger,
)


def _json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _manifest(directory: Path, boundary: str) -> None:
    files = {}
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    _json(directory / "manifest.json", {"schema": "gaugegap.bundle.v1", "files": files, "claim_boundary": boundary})


def _qed(output: Path) -> bool:
    output.mkdir(parents=True, exist_ok=True)
    params = QEDParameters()
    q2 = np.linspace(0.0, 10.0, 61)
    rows = scan_qed(q2, params)
    self_rows = []
    for value in q2:
        dressing = self_energy_dressings(float(value), params)
        self_rows.append({
            "p_squared": dressing.p_squared,
            "vector_dressing": dressing.vector_dressing,
            "scalar_dressing": dressing.scalar_dressing,
        })
    audit = audit_qed(params=params)
    _csv(output / "qed_scan.csv", rows)
    _csv(output / "self_energy_dressings.csv", self_rows)
    _json(output / "ward_audit.json", audit.to_dict())
    _json(output / "summary.json", {
        "id": "qed-loop-0001",
        "parameters": params.__dict__,
        "ward_audit": audit.to_dict(),
        "implementation_status": "finite_perturbative_reference",
        "claim_boundary": QED_BOUNDARY,
    })
    (output / "report.md").write_text(
        "# qed-loop-0001\n\n"
        f"- Ward residual: `{audit.ward_takahashi_residual:.3e}`\n"
        f"- Transversality residual: `{audit.vacuum_transversality_residual:.3e}`\n"
        f"- Pauli zero residual: `{audit.pauli_zero_residual:.3e}`\n"
        f"- Passed: `{audit.passed}`\n\n**Boundary:** {QED_BOUNDARY}\n",
        encoding="utf-8",
    )
    _manifest(output, QED_BOUNDARY)
    return audit.passed


def _schwinger(output: Path) -> bool:
    output.mkdir(parents=True, exist_ok=True)
    config = SchwingerConfig()
    result = solve_schwinger(config)
    hamiltonian, basis, audit = build_projected_hamiltonian(config)
    spectrum = np.linalg.eigvalsh(hamiltonian)
    _json(output / "summary.json", {"id": "schwinger-matter-0001", **result.to_dict(), "implementation_status": "finite_gauss_projected_reference"})
    _json(output / "gauss_audit.json", result.gauss_audit)
    _csv(output / "physical_basis.csv", [
        {"index": index, "occupations": "".join(map(str, state.occupations)), "fluxes": " ".join(map(str, state.fluxes))}
        for index, state in enumerate(basis)
    ])
    _csv(output / "spectrum.csv", [{"level": i, "energy": float(e)} for i, e in enumerate(spectrum)])
    _csv(output / "mass_scan.csv", scan_mass(np.linspace(-1.0, 1.0, 31), config))
    (output / "report.md").write_text(
        "# schwinger-matter-0001\n\n"
        f"- Physical dimension: `{result.physical_dimension}`\n"
        f"- Gauss residual: `{result.gauss_audit['max_basis_residual']:.3e}`\n"
        f"- Sector leakage: `{result.gauss_audit['transition_leakage_count']}`\n"
        f"- Hermiticity residual: `{result.hermiticity_residual:.3e}`\n"
        f"- Finite spectral gap: `{result.spectral_gap:.12g}`\n\n**Boundary:** {SCH_BOUNDARY}\n",
        encoding="utf-8",
    )
    _manifest(output, SCH_BOUNDARY)
    return bool(audit.passed and result.hermiticity_residual < 1e-12)


def _cohesive(output: Path) -> bool:
    output.mkdir(parents=True, exist_ok=True)
    certificate = audit_gauge_coherence()
    _json(output / "summary.json", {
        "id": "cohesive-gauge-0001",
        "certificate": certificate.to_dict(),
        "formal_interface": "formal/hott/GaugeCoherence.agda",
        "formal_status": "interface_scaffold_not_ci_compiled",
        "claim_boundary": COH_BOUNDARY,
    })
    _manifest(output, COH_BOUNDARY)
    return certificate.passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("qed", "schwinger", "cohesive", "all"))
    parser.add_argument("--output-root", type=Path, default=Path("results"))
    args = parser.parse_args()
    runners = {
        "qed": lambda: _qed(args.output_root / "qed-loop-0001"),
        "schwinger": lambda: _schwinger(args.output_root / "schwinger-matter-0001"),
        "cohesive": lambda: _cohesive(args.output_root / "cohesive-gauge-0001"),
    }
    selected = runners if args.mode == "all" else {args.mode: runners[args.mode]}
    results = {name: bool(run()) for name, run in selected.items()}
    print(json.dumps(results, sort_keys=True))
    return 0 if all(results.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
