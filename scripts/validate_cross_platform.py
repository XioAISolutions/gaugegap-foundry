#!/usr/bin/env python3
"""Cross-platform quantum simulator validation.

Runs identical TFIM Trotter circuits on all available local simulators,
compares observables against the Qiskit statevector reference, and
produces a verdict report.
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

WARNING_THRESHOLD = 0.08
FAIL_THRESHOLD = 0.18


def _verdict(error: float) -> str:
    if error >= FAIL_THRESHOLD:
        return "fail"
    if error >= WARNING_THRESHOLD:
        return "warning"
    return "pass"


def _detect_backends() -> dict[str, str]:
    backends = {}
    try:
        from qiskit.quantum_info import Statevector  # noqa: F401
        backends["statevector"] = "qiskit"
    except ImportError:
        pass
    try:
        from qiskit_aer import AerSimulator  # noqa: F401
        backends["aer-sampler"] = "qiskit-aer"
    except ImportError:
        pass
    try:
        from braket.devices import LocalSimulator  # noqa: F401
        backends["braket-local"] = "braket"
    except ImportError:
        pass
    try:
        import pyqpanda  # noqa: F401
        backends["originq-cpuqvm"] = "pyqpanda"
    except ImportError:
        pass
    return backends


def _run_statevector(n_sites, exchange, field, time, steps, initial_state):
    from gaugegap.qiskit_dynamics import build_tfim_trotter_circuit, statevector_z_observables
    circuit = build_tfim_trotter_circuit(
        n_sites=n_sites, exchange_coupling=exchange, transverse_field=field,
        time=time, steps=steps, initial_state=initial_state, measure=False,
    )
    return statevector_z_observables(circuit, n_sites=n_sites)


def _run_aer(n_sites, exchange, field, time, steps, initial_state, shots, seed):
    from gaugegap.qiskit_dynamics import aer_sample_z_observables, build_tfim_trotter_circuit
    circuit = build_tfim_trotter_circuit(
        n_sites=n_sites, exchange_coupling=exchange, transverse_field=field,
        time=time, steps=steps, initial_state=initial_state, measure=True,
    )
    return aer_sample_z_observables(circuit, n_sites=n_sites, shots=shots, seed=seed)


def _run_braket(n_sites, exchange, field, time, steps, initial_state, shots):
    from gaugegap.braket_runner import (
        braket_counts_to_z_observables, build_tfim_trotter_braket, run_local_simulator,
    )
    circuit = build_tfim_trotter_braket(
        n_sites=n_sites, exchange_coupling=exchange, transverse_field=field,
        time=time, steps=steps, initial_state=initial_state,
    )
    result = run_local_simulator(circuit, shots=shots)
    return braket_counts_to_z_observables(result["counts"], n_sites=n_sites)


def _run_originq(n_sites, exchange, field, time, steps, initial_state, shots):
    from gaugegap.originq_runner import originq_counts_to_z_observables, run_local_cpuqvm
    result = run_local_cpuqvm(
        n_sites=n_sites, exchange_coupling=exchange, transverse_field=field,
        time=time, steps=steps, initial_state=initial_state, shots=shots,
    )
    return originq_counts_to_z_observables(result["counts"], n_sites=n_sites)


def run_validation(
    n_sites: int = 4,
    exchange: float = 1.0,
    field: float = 0.8,
    times: list[float] | None = None,
    initial_states: list[str] | None = None,
    steps: int = 4,
    shots: int = 2048,
    seed: int = 42,
) -> dict[str, object]:
    if times is None:
        times = [0.0, 0.25, 0.5, 1.0]
    if initial_states is None:
        initial_states = ["zeros", "domain_wall"]

    backends = _detect_backends()
    if "statevector" not in backends:
        raise RuntimeError("Qiskit statevector backend is required as reference")

    run_id = utc_run_id()
    git = git_state(ROOT)
    comparisons: list[dict[str, object]] = []
    records: list[dict[str, object]] = []

    for init_state in initial_states:
        for time in times:
            ref = _run_statevector(n_sites, exchange, field, time, steps, init_state)

            backend_results: dict[str, dict] = {"statevector": ref}

            if "aer-sampler" in backends:
                backend_results["aer-sampler"] = _run_aer(
                    n_sites, exchange, field, time, steps, init_state, shots, seed
                )
            if "braket-local" in backends:
                backend_results["braket-local"] = _run_braket(
                    n_sites, exchange, field, time, steps, init_state, shots
                )
            if "originq-cpuqvm" in backends:
                backend_results["originq-cpuqvm"] = _run_originq(
                    n_sites, exchange, field, time, steps, init_state, shots
                )

            params = {
                "n_sites": n_sites, "exchange": exchange, "field": field,
                "time": time, "steps": steps, "initial_state": init_state,
            }

            for backend_name, obs in backend_results.items():
                for site, val in enumerate(obs["z"]):
                    records.append({
                        "run_id": run_id, "backend": backend_name,
                        "observable": "z_expectation", "site": site,
                        "bond": None, "time": time, "initial_state": init_state,
                        "value": val, "params": params, "git": git,
                    })
                for bond, val in enumerate(obs["zz"]):
                    records.append({
                        "run_id": run_id, "backend": backend_name,
                        "observable": "zz_correlator", "site": None,
                        "bond": bond, "time": time, "initial_state": init_state,
                        "value": val, "params": params, "git": git,
                    })

            for backend_name, obs in backend_results.items():
                if backend_name == "statevector":
                    continue
                for site in range(len(ref["z"])):
                    error = abs(obs["z"][site] - ref["z"][site])
                    comparisons.append({
                        "backend": backend_name, "observable": "z_expectation",
                        "channel": f"site_{site}", "time": time,
                        "initial_state": init_state,
                        "reference_value": ref["z"][site],
                        "backend_value": obs["z"][site],
                        "abs_error": error, "verdict": _verdict(error),
                    })
                for bond in range(len(ref["zz"])):
                    error = abs(obs["zz"][bond] - ref["zz"][bond])
                    comparisons.append({
                        "backend": backend_name, "observable": "zz_correlator",
                        "channel": f"bond_{bond}", "time": time,
                        "initial_state": init_state,
                        "reference_value": ref["zz"][bond],
                        "backend_value": obs["zz"][bond],
                        "abs_error": error, "verdict": _verdict(error),
                    })

    verdicts = [c["verdict"] for c in comparisons]
    pass_count = verdicts.count("pass")
    warn_count = verdicts.count("warning")
    fail_count = verdicts.count("fail")

    if fail_count > 0:
        overall = "FAIL"
    elif warn_count > 0:
        overall = "WARNING"
    else:
        overall = "PASS"

    shot_backends = [b for b in backends if b != "statevector"]

    summary = {
        "backends_tested": list(backends.keys()),
        "shot_backends": shot_backends,
        "reference": "statevector",
        "n_sites": n_sites,
        "shots": shots,
        "test_cases": len(times) * len(initial_states),
        "total_comparisons": len(comparisons),
        "pass_count": pass_count,
        "warning_count": warn_count,
        "fail_count": fail_count,
        "overall_verdict": overall,
        "warning_threshold": WARNING_THRESHOLD,
        "fail_threshold": FAIL_THRESHOLD,
    }

    return {
        "summary": summary,
        "comparisons": comparisons,
        "records": records,
        "run_id": run_id,
        "git": git,
    }


def write_csv_comparisons(path: Path, comparisons: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["backend", "observable", "channel", "time", "initial_state",
              "reference_value", "backend_value", "abs_error", "verdict"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in comparisons:
            writer.writerow({k: f"{v:.12g}" if isinstance(v, float) else v for k, v in row.items()})


def write_validation_svg(path: Path, comparisons: list[dict]) -> None:
    from xml.sax.saxutils import escape

    backends = sorted(set(c["backend"] for c in comparisons))
    if not backends:
        return

    errors_by_backend = {b: [] for b in backends}
    for c in comparisons:
        errors_by_backend[c["backend"]].append(c["abs_error"])

    width, height = 920, 400
    left, right, top, bottom = 120, 30, 45, 60
    plot_w = width - left - right
    plot_h = height - top - bottom

    bar_width = plot_w / (len(backends) * 2 + 1)
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]

    max_err = max(max(errs) for errs in errors_by_backend.values()) if any(errors_by_backend.values()) else 0.2
    max_err = max(max_err, FAIL_THRESHOLD * 1.2)

    def sy(y):
        return top + (1.0 - y / max_err) * plot_h

    bars = []
    legend = []
    for idx, backend in enumerate(backends):
        color = colors[idx % len(colors)]
        mean_err = sum(errors_by_backend[backend]) / len(errors_by_backend[backend])
        max_e = max(errors_by_backend[backend])
        x = left + (2 * idx + 1) * bar_width
        bars.append(f'<rect x="{x:.1f}" y="{sy(mean_err):.1f}" width="{bar_width:.1f}" height="{sy(0) - sy(mean_err):.1f}" fill="{color}" opacity="0.8" />')
        bars.append(f'<line x1="{x + bar_width/2:.1f}" y1="{sy(max_e):.1f}" x2="{x + bar_width/2:.1f}" y2="{sy(mean_err):.1f}" stroke="{color}" stroke-width="2" />')
        bars.append(f'<text x="{x + bar_width/2:.1f}" y="{sy(0) + 18}" font-size="11" text-anchor="middle">{escape(backend)}</text>')
        ly = top + 18 * idx
        legend.append(f'<rect x="{width-200}" y="{ly}" width="14" height="14" fill="{color}" />')
        legend.append(f'<text x="{width-180}" y="{ly+12}" font-size="12">{escape(backend)} (mean={mean_err:.4f})</text>')

    threshold_lines = [
        f'<line x1="{left}" y1="{sy(WARNING_THRESHOLD):.1f}" x2="{left+plot_w}" y2="{sy(WARNING_THRESHOLD):.1f}" stroke="#ff9800" stroke-dasharray="6,3" stroke-width="1.5" />',
        f'<text x="{left+4}" y="{sy(WARNING_THRESHOLD)-4}" font-size="10" fill="#ff9800">warning={WARNING_THRESHOLD}</text>',
        f'<line x1="{left}" y1="{sy(FAIL_THRESHOLD):.1f}" x2="{left+plot_w}" y2="{sy(FAIL_THRESHOLD):.1f}" stroke="#f44336" stroke-dasharray="6,3" stroke-width="1.5" />',
        f'<text x="{left+4}" y="{sy(FAIL_THRESHOLD)-4}" font-size="10" fill="#f44336">fail={FAIL_THRESHOLD}</text>',
    ]

    title = escape("Cross-Platform Validation: absolute error vs statevector reference")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left}" y="28" font-size="18" font-family="Arial, sans-serif" font-weight="700">{title}</text>
  <g font-family="Arial, sans-serif" fill="#111827">
    <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#111827" stroke-width="1" />
    {''.join(threshold_lines)}
    {''.join(bars)}
    {''.join(legend)}
    <text x="18" y="{top+plot_h/2:.0f}" font-size="13" text-anchor="middle" transform="rotate(-90 18 {top+plot_h/2:.0f})">absolute error</text>
  </g>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate cross-platform quantum simulator agreement.")
    parser.add_argument("--n-sites", type=int, default=4)
    parser.add_argument("--shots", type=int, default=2048)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "analysis")
    args = parser.parse_args()

    result = run_validation(n_sites=args.n_sites, shots=args.shots)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "cross-platform-validation.json"
    csv_path = out / "cross-platform-validation.csv"
    svg_path = out / "cross-platform-validation.svg"
    jsonl_path = out / "cross-platform-validation.jsonl"

    json_path.write_text(
        json.dumps({"summary": result["summary"], "comparisons": result["comparisons"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv_comparisons(csv_path, result["comparisons"])
    write_validation_svg(svg_path, result["comparisons"])
    write_jsonl(jsonl_path, result["records"])

    s = result["summary"]
    print(json.dumps({"summary": s, "outputs": {"json": str(json_path), "csv": str(csv_path), "svg": str(svg_path)}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
