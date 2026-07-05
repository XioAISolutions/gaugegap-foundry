#!/usr/bin/env python3
"""Run the immediate cross-track Deep Boil integration benchmark.

This command exercises the shared scientific substrate added to GaugeGap
Foundry: canonical Hamiltonian construction, finite Koopman/DMD analysis,
validated interval ODE steps, the quantum-reality forges, topology and
entanglement forges, the finite Quantum Gap Functional, fail-closed research
manifests, and the generated complete Experience/Experiment interface.

It is an integration benchmark, not a Millennium Prize solution attempt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.flowgap_attractors import get_system, integrate  # noqa: E402
from gaugegap.entanglement_forge import run_entanglement_forge  # noqa: E402
from gaugegap.fractal_topology_forge import run_menger_forge  # noqa: E402
from gaugegap.hamiltonian_factory import build_and_audit  # noqa: E402
from gaugegap.koopman import dominant_modes, exact_dmd  # noqa: E402
from gaugegap.compactification_forge import run_compactification_suite  # noqa: E402
from gaugegap.perception_forge import run_perception_forge  # noqa: E402
from gaugegap.quantum.uqt_forge import run_uqt_forge  # noqa: E402
from gaugegap.quantum_gap import compute_quantum_gap  # noqa: E402
from gaugegap.research_manifest import (  # noqa: E402
    ClaimLevel,
    EvidenceArtifact,
    ResearchClaim,
    write_manifest,
)
from gaugegap.validated_dynamics import IntervalBox, picard_enclosure_step  # noqa: E402


CLAIM_BOUNDARY = (
    "cross-track finite integration benchmark only; no continuum theorem, global "
    "attractor proof, quantum-gravity law, cognitive-science proof, fractal-topology "
    "theorem, faster-than-light communication claim, or Millennium Prize problem "
    "solution claim"
)


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() or "unavailable-local-checkout"


def _dynamics_record(name: str, smoke: bool) -> dict[str, object]:
    system = get_system(name)
    params = system.parameters()
    dt = 0.01 if name != "thomas" else 0.02
    steps = 1600 if smoke else (9000 if name != "thomas" else 14000)
    transient = 300 if smoke else (1800 if name != "thomas" else 3000)
    _, states = integrate(system, params, system.default_state, dt=dt, steps=steps)
    retained = states[transient:]
    dmd = exact_dmd(retained[::2], dt=dt * 2, rank=3)
    enclosure = picard_enclosure_step(
        name,
        IntervalBox.from_point(system.default_state, radius=1e-15),
        params,
        dt=min(dt, 0.002),
    )
    return {
        "system": name,
        "samples": int(len(retained)),
        "dmd": dmd.summary(),
        "dominant_modes": dominant_modes(dmd, count=3),
        "validated_step": enclosure.summary(),
    }


def _hamiltonian_records() -> list[dict[str, object]]:
    requests = [
        ("z2-plaquette", {"n_plaquettes": 1, "plaquette_coupling": 1.0, "transverse_field": 0.35}),
        ("u1-plaquette", {"n_links": 2, "g_electric": 1.0, "g_magnetic": 0.5, "truncation": 1}),
    ]
    records: list[dict[str, object]] = []
    for model, parameters in requests:
        artifact, audit = build_and_audit(model, **parameters)
        records.append({
            "model": model,
            "parameters": parameters,
            "metadata": dict(artifact.metadata),
            "audit": audit.summary(),
        })
    return records


def _compact_uqt_summary(report) -> dict[str, object]:
    summary = report.summary()
    return {
        "schema": summary["schema"],
        "benchmark_id": summary["benchmark_id"],
        "passed": summary["passed"],
        "selected_task": summary["selected_task"],
        "circuit": summary["circuit"],
        "tasks": [
            {
                "task_id": task["task_id"],
                "vocab_size": task["vocab_size"],
                "case_count": task["case_count"],
                "accuracy": task["accuracy"],
                "row_permutation_fraction": task["row_permutation_fraction"],
                "reversible_by_rows": task["reversible_by_rows"],
                "negative_control": task["negative_control"],
                "passed": task["passed"],
            }
            for task in summary["tasks"]
        ],
        "claim_boundary": summary["claim_boundary"],
    }


def _compact_compactification_summary(reports) -> list[dict[str, object]]:
    compact: list[dict[str, object]] = []
    for report in reports:
        summary = report.summary()
        compact.append(
            {
                "schema": summary["schema"],
                "benchmark_id": summary["benchmark_id"],
                "geometry": summary["geometry"],
                "radii": summary["radii"],
                "cutoff": summary["cutoff"],
                "alpha_prime": summary["alpha_prime"],
                "mode_count": summary["mode_count"],
                "visible_mode_count": summary["visible_mode_count"],
                "first_excited_mass": summary["first_excited_mass"],
                "effective_dimension_label": summary["effective_dimension_label"],
                "passed": summary["passed"],
                "claim_boundary": summary["claim_boundary"],
            }
        )
    return compact


def _compact_perception_summary(report) -> dict[str, object]:
    summary = report.summary()
    return {
        "schema": summary["schema"],
        "benchmark_id": summary["benchmark_id"],
        "world_count": summary["world_count"],
        "truth_extinction_fraction": summary["truth_extinction_fraction"],
        "interface_win_fraction": summary["interface_win_fraction"],
        "minimum_payoff_advantage": summary["minimum_payoff_advantage"],
        "passed": summary["passed"],
        "controls": summary["controls"],
        "claim_boundary": summary["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "deep-boil-0001")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--generate-experience", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dynamics = [_dynamics_record(name, args.smoke) for name in ("rossler", "lorenz", "thomas")]
    hamiltonians = _hamiltonian_records()
    uqt_report = run_uqt_forge(task="all")
    compactification_reports = run_compactification_suite()
    perception_report = run_perception_forge(world_count=12)
    menger_report = run_menger_forge(iterations=4)
    entanglement_report = run_entanglement_forge()
    uqt_summary = _compact_uqt_summary(uqt_report)
    compactification_summary = _compact_compactification_summary(compactification_reports)
    perception_summary = _compact_perception_summary(perception_report)
    menger_summary = menger_report.summary()
    entanglement_summary = entanglement_report.summary()
    validated = all(bool(record["validated_step"]["validated"]) for record in dynamics)
    hermitian = all(bool(record["audit"]["hermitian"]) for record in hamiltonians)
    finite_dmd = all(
        np.isfinite(float(record["dmd"]["reconstruction_error"]))
        for record in dynamics
    )
    quantum_reality_passed = (
        bool(uqt_summary["passed"])
        and all(bool(report["passed"]) for report in compactification_summary)
        and bool(perception_summary["passed"])
    )
    topology_entanglement_passed = bool(menger_summary["passed"]) and bool(entanglement_summary["passed"])
    validation_gate = (
        validated
        and hermitian
        and finite_dmd
        and quantum_reality_passed
        and topology_entanglement_passed
    )
    quantum_gap = compute_quantum_gap(
        dynamics=dynamics,
        hamiltonians=hamiltonians,
        uqt_summary=uqt_summary,
        compact_summaries=compactification_summary,
        perception_summary=perception_summary,
        validation_gate=validation_gate,
        menger_summary=menger_summary,
        entanglement_summary=entanglement_summary,
    )

    experience_result: dict[str, object] | None = None
    if args.generate_experience:
        experience_dir = args.output_dir / "experience"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_foundry_experience_complete.py"),
                "--output-dir",
                str(experience_dir),
                "--preview",
                str(args.output_dir / "foundry_experience_preview.svg"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        experience_result = {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "output_dir": str(experience_dir),
        }

    payload = {
        "schema": "gaugegap.deep_boil.v1",
        "git_commit": _git_commit(),
        "smoke": args.smoke,
        "status": "pass" if validation_gate and quantum_gap.passed else "fail",
        "checks": {
            "all_interval_steps_validated": validated,
            "all_hamiltonians_hermitian": hermitian,
            "all_dmd_errors_finite": finite_dmd,
            "uqt_forge_passed": bool(uqt_summary["passed"]),
            "compactification_forge_passed": all(bool(report["passed"]) for report in compactification_summary),
            "perception_forge_passed": bool(perception_summary["passed"]),
            "menger_sponge_forge_passed": bool(menger_summary["passed"]),
            "entanglement_forge_passed": bool(entanglement_summary["passed"]),
            "quantum_gap_functional_passed": quantum_gap.passed,
        },
        "dynamics": dynamics,
        "hamiltonians": hamiltonians,
        "quantum_reality": {
            "uqt": uqt_summary,
            "compactification": compactification_summary,
            "perception": perception_summary,
        },
        "topology_entanglement": {
            "menger_sponge": menger_summary,
            "entanglement": entanglement_summary,
        },
        "quantum_gap": quantum_gap.summary(),
        "experience": experience_result,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    json_path = args.output_dir / "deep_boil.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# GaugeGap Foundry — Deep Boil 0001",
        "",
        f"> {CLAIM_BOUNDARY}",
        "",
        f"Status: **{payload['status'].upper()}**",
        "",
        "## Shared checks",
        "",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"- `{key}`: **{'PASS' if value else 'FAIL'}**")
    lines.extend(["", "## Nonlinear dynamics", "", "| system | DMD residual | validated finite step | endpoint width |", "|---|---:|:---:|---:|"])
    for record in dynamics:
        step = record["validated_step"]
        lines.append(
            f"| {record['system']} | {record['dmd']['reconstruction_error']:.6g} | "
            f"{'PASS' if step['validated'] else 'FAIL'} | {step['maximum_endpoint_width']:.6g} |"
        )
    lines.extend(["", "## Canonical Hamiltonians", "", "| model | dimension | Hermitian | gap | status |", "|---|---:|:---:|---:|---|"])
    for record in hamiltonians:
        audit = record["audit"]
        lines.append(
            f"| {record['model']} | {audit['dimension']} | "
            f"{'PASS' if audit['hermitian'] else 'FAIL'} | {audit['spectral_gap']:.6g} | "
            f"{audit['implementation_status']} |"
        )
    lines.extend(
        [
            "",
            "## Topology And Entanglement",
            "",
            "| forge | primary observable | boundary gate | status |",
            "|---|---:|---|:---:|",
            (
                f"| Menger sponge | dim_H {menger_summary['hausdorff_dimension']:.6g} | "
                "finite stages only | "
                f"{'PASS' if menger_summary['passed'] else 'FAIL'} |"
            ),
            (
                f"| Bell entanglement | CHSH {entanglement_summary['chsh_value']:.6g} | "
                "no signaling | "
                f"{'PASS' if entanglement_summary['passed'] else 'FAIL'} |"
            ),
        ]
    )
    lines.extend(
        [
            "",
            "## Quantum Gap Functional",
            "",
            "`Q_gap = B * exp((sum_i w_i log(eps + g_i)) / (sum_i w_i))`",
            "",
            f"Score: **{quantum_gap.score:.6g}**",
            "",
            "| term | value | weight | status |",
            "|---|---:|---:|:---:|",
        ]
    )
    for term in quantum_gap.terms:
        lines.append(
            f"| {term.name} | {term.value:.6g} | {term.weight:.3g} | "
            f"{'PASS' if term.passed else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            f"> {quantum_gap.claim_boundary}",
        ]
    )
    if experience_result is not None:
        lines.extend(["", "## Foundry Experience", "", f"Generator return code: `{experience_result['returncode']}`"])
    report_path = args.output_dir / "DEEP_BOIL.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    artifacts = (
        EvidenceArtifact.from_path(json_path, base=args.output_dir, kind="result"),
        EvidenceArtifact.from_path(report_path, base=args.output_dir, kind="report"),
    )
    claim = ResearchClaim(
        claim_id="deep-boil-0001",
        title="Cross-track finite integration benchmark",
        statement=(
            "The configured finite dynamics, Koopman, interval-step, Hamiltonian, "
            "quantum-reality, topology, entanglement, and Quantum Gap synthesis "
            "checks execute under a shared reproducible contract."
        ),
        level=ClaimLevel.REPRODUCIBLE_FINITE_RESULT,
        finite_scope=(
            "three finite-time ODE runs, two finite Hamiltonian matrices, finite UQT-inspired "
            "algebra tables, compactification toy spectra, finite perception games, "
            "finite Menger sponge stages, and a finite two-qubit Bell calculation"
        ),
        assumptions=("registered model equations and finite truncations",),
        exclusions=(
            "no continuum theorem",
            "no global strange-attractor proof",
            "no Yang-Mills or Navier-Stokes Millennium solution",
            "no physical law or universal quantum-gravity formula",
            "no UQT training reproduction or hardware result",
            "no evidence for extra dimensions or conscious realism",
            "no proof of completed fractal topology",
            "no faster-than-light communication",
        ),
        evidence=artifacts,
        methods=(
            "RK4",
            "exact DMD",
            "interval Picard inclusion",
            "exact diagonalization",
            "finite algebra known-answer tables",
            "finite compactification spectra",
            "replicator dynamics",
            "finite fractal stage algebra",
            "Bell-state CHSH/no-signaling calculation",
            "weighted geometric synthesis",
        ),
        parameters={"smoke": args.smoke, "quantum_gap_score": quantum_gap.score},
        git_commit=payload["git_commit"],
    )
    write_manifest(args.output_dir / "research_manifest.json", [claim])

    print(json.dumps({
        "status": payload["status"],
        "output_dir": str(args.output_dir),
        "checks": payload["checks"],
        "quantum_gap_score": quantum_gap.score,
        "claim_boundary": CLAIM_BOUNDARY,
    }, indent=2))
    if experience_result is not None and int(experience_result["returncode"]) != 0:
        return 1
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
