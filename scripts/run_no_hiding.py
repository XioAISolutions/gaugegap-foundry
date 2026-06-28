#!/usr/bin/env python3
"""Run the finite no-hiding benchmark and emit reproducible evidence artifacts."""
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

from gaugegap.quantum_information.no_hiding import (  # noqa: E402
    audit_no_hiding,
    output_state,
    run_no_hiding_suite,
)
from gaugegap.quantum_provider import (  # noqa: E402
    LocalStatevectorProvider,
    QuantumExecutionRequest,
)


def _render_svg(payload: dict[str, object]) -> str:
    selected = payload["selected"]
    assert isinstance(selected, dict)
    fidelity = float(selected["recovery_fidelity"])
    distance = float(selected["system_bleaching_trace_distance"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="520" viewBox="0 0 1000 520">
<rect width="1000" height="520" rx="22" fill="#050505"/>
<text x="500" y="54" fill="#ffffff" font-family="monospace" font-size="28" text-anchor="middle">INFOGAP · NO-HIDING</text>
<text x="500" y="84" fill="#858585" font-family="monospace" font-size="14" text-anchor="middle">information leaves the system and is recoverable from the environment alone</text>
<circle cx="150" cy="260" r="70" fill="none" stroke="#58d7ff" stroke-width="3"/>
<path d="M150 260 L188 218" stroke="#58d7ff" stroke-width="5"/>
<text x="150" y="360" fill="#ffffff" font-family="monospace" font-size="18" text-anchor="middle">input |psi&gt;</text>
<path d="M235 260 H360" stroke="#ffffff" stroke-width="2" marker-end="url(#arrow)"/>
<rect x="370" y="190" width="180" height="140" rx="18" fill="#101010" stroke="#ffffff"/>
<text x="460" y="238" fill="#ffffff" font-family="monospace" font-size="17" text-anchor="middle">SWAP(S,B)</text>
<text x="460" y="268" fill="#ffffff" font-family="monospace" font-size="17" text-anchor="middle">H(S)</text>
<text x="460" y="298" fill="#ffffff" font-family="monospace" font-size="17" text-anchor="middle">CNOT(S,A)</text>
<path d="M560 260 H675" stroke="#ffffff" stroke-width="2" marker-end="url(#arrow)"/>
<circle cx="750" cy="190" r="54" fill="none" stroke="#777777" stroke-width="3"/>
<circle cx="750" cy="190" r="5" fill="#777777"/>
<text x="750" y="265" fill="#ffffff" font-family="monospace" font-size="17" text-anchor="middle">system = I/2</text>
<circle cx="850" cy="335" r="60" fill="none" stroke="#7ee787" stroke-width="3"/>
<path d="M850 335 L882 299" stroke="#7ee787" stroke-width="5"/>
<text x="850" y="420" fill="#ffffff" font-family="monospace" font-size="17" text-anchor="middle">environment recovers |psi&gt;</text>
<text x="500" y="470" fill="#7ee787" font-family="monospace" font-size="15" text-anchor="middle">recovery fidelity = {fidelity:.12f} · system dependence = {distance:.3e}</text>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#ffffff"/></marker></defs>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theta", type=float, default=1.1)
    parser.add_argument("--phi", type=float, default=0.7)
    parser.add_argument("--random-count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "infogap-0001-no-hiding",
    )
    args = parser.parse_args()

    selected = audit_no_hiding(
        args.theta,
        args.phi,
        label="selected",
        tolerance=args.tolerance,
    )
    suite = run_no_hiding_suite(
        random_count=args.random_count,
        seed=args.seed,
        tolerance=args.tolerance,
    )
    provider = LocalStatevectorProvider()
    sample = provider.execute(
        QuantumExecutionRequest(
            operation="sample_statevector",
            statevector=tuple(output_state(args.theta, args.phi)),
            shots=args.shots,
            seed=args.seed,
        )
    )
    payload = {
        "schema": "gaugegap.infogap.no_hiding.v1",
        "benchmark_id": "infogap-0001-no-hiding",
        "circuit": ["SWAP(S,B)", "H(S)", "CNOT(S,A)"],
        "subsystems": {"system": "S", "environment": ["A", "B"], "recovery_qubit": "B"},
        "parameters": {
            "theta": args.theta,
            "phi": args.phi,
            "random_count": args.random_count,
            "seed": args.seed,
            "tolerance": args.tolerance,
            "shots": args.shots,
        },
        "selected": selected.summary(),
        "suite": suite.summary(),
        "provider": {
            "capabilities": provider.capabilities().__dict__,
            "sample": sample.summary(),
        },
        "claim_level": "reproducible_finite_result",
        "claim_boundary": selected.claim_boundary,
        "exclusions": [
            "not a new proof of the general no-hiding theorem",
            "not a resolution of the black-hole information paradox",
            "not evidence that arbitrary macroscopic recovery is practical",
            "not a continuum quantum-gravity result",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "cases.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "label",
                "theta",
                "phi",
                "passed",
                "system_bleaching_trace_distance",
                "recovery_fidelity",
                "input_recovered_bloch_error",
                "unitarity_residual",
            ],
        )
        writer.writeheader()
        for case in suite.cases:
            row = case.summary()
            writer.writerow({key: row[key] for key in writer.fieldnames})
    (args.output_dir / "no_hiding_flow.svg").write_text(
        _render_svg(payload),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if selected.passed and suite.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
