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

from gaugegap.quantum.ibm_runtime_adapter import RUNTIME_CLAIM_BOUNDARY, RuntimeSubmissionConfig, build_runtime_submission_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a guarded IBM Runtime plan for a finite GaugeGap candidate.")
    parser.add_argument("--hypothesis-id", default="gaugegap-0004")
    parser.add_argument("--n-plaquettes", type=int, default=1)
    parser.add_argument("--plaquette-coupling", type=float, default=1.0)
    parser.add_argument("--transverse-field", type=float, default=0.2)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--least-busy", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--submit-runtime", action="store_true")
    parser.add_argument("--i-understand-this-is-finite-system-only", action="store_true")
    parser.add_argument("--allow-service-probe", action="store_true")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "ibm-runtime-plan")
    args = parser.parse_args()

    dry_run = bool(args.dry_run or not args.submit_runtime)
    try:
        plan = build_runtime_submission_plan(
            RuntimeSubmissionConfig(
                hypothesis_id=args.hypothesis_id,
                n_plaquettes=args.n_plaquettes,
                plaquette_coupling=args.plaquette_coupling,
                transverse_field=args.transverse_field,
                shots=args.shots,
                backend=args.backend,
                least_busy=args.least_busy,
                dry_run=dry_run,
                submit_runtime=args.submit_runtime,
                finite_system_confirmation=args.i_understand_this_is_finite_system_only,
                allow_service_probe=args.allow_service_probe,
                run_id=args.run_id,
                seed=args.seed,
            )
        )
    except ValueError as exc:
        print(json.dumps({"status": "fail", "error": str(exc), "claim_boundary": RUNTIME_CLAIM_BOUNDARY}, indent=2), file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "runtime_submission_plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "RUNTIME_SUBMISSION_SUMMARY.md").write_text(to_markdown(plan), encoding="utf-8")

    job = plan.get("job", {})
    if not isinstance(job, dict):
        job = {}
    print(
        json.dumps(
            {
                "status": job.get("status", "dry_run_plan"),
                "submitted": job.get("submitted", False),
                "job_id": job.get("job_id"),
                "output_dir": str(args.output_dir),
                "claim_boundary": RUNTIME_CLAIM_BOUNDARY,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0 if not args.submit_runtime or bool(job.get("submitted")) else 1


def to_markdown(plan: dict[str, object]) -> str:
    resources = plan.get("resources", {})
    if not isinstance(resources, dict):
        resources = {}
    capabilities = plan.get("capabilities", {})
    if not isinstance(capabilities, dict):
        capabilities = {}
    service_probe = plan.get("service_probe", {})
    if not isinstance(service_probe, dict):
        service_probe = {}
    job = plan.get("job", {})
    if not isinstance(job, dict):
        job = {}
    warnings = plan.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = [str(warnings)]

    lines = [
        "# IBM Runtime Submission Plan",
        "",
        f"> {plan.get('claim_boundary', RUNTIME_CLAIM_BOUNDARY)}",
        "",
        "This is a finite-system exploratory job plan. It makes no continuum mass-gap claim, no proof claim, and treats any hardware data as noisy experimental output rather than theorem evidence.",
        "",
        "## Execution",
        "",
        f"- Dry run: `{plan.get('dry_run')}`",
        f"- Submit runtime: `{plan.get('submit_runtime')}`",
        f"- Submitted: `{job.get('submitted', False)}`",
        f"- Job id: `{job.get('job_id')}`",
        "",
        "## Resources",
        "",
        f"- Qubits: `{resources.get('n_qubits')}`",
        f"- Pauli terms: `{resources.get('n_pauli_terms')}`",
        f"- Shots: `{resources.get('shots')}`",
        f"- Depth proxy: `{resources.get('depth_proxy')}`",
        "",
        "## Runtime Safety",
        "",
        f"- Runtime import available: `{capabilities.get('qiskit_ibm_runtime_available')}`",
        f"- Credentials checked: `{service_probe.get('credentials_checked', False)}`",
        f"- Tokens printed or written: `{capabilities.get('tokens_printed_or_written', False)}`",
        "",
        "## Warnings",
        "",
    ]
    for warning in warnings:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
