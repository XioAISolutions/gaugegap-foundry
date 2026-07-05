#!/usr/bin/env python3
"""Run finite UQT-inspired algebra checks and emit evidence artifacts."""
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

from gaugegap.quantum.uqt_forge import iter_case_rows, run_uqt_forge  # noqa: E402


def _render_svg(payload: dict[str, object]) -> str:
    tasks = payload["tasks"]
    assert isinstance(tasks, list)
    bars = []
    for index, task in enumerate(tasks):
        assert isinstance(task, dict)
        x = 120 + index * 190
        height = 220 * float(task["accuracy"])
        color = "#ff8c8c" if task["negative_control"] else "#7ee787"
        bars.append(
            f'<rect x="{x}" y="{360 - height:.2f}" width="82" height="{height:.2f}" fill="{color}"/>'
            f'<text x="{x + 41}" y="392" fill="#fff" font-family="monospace" font-size="13" '
            f'text-anchor="middle">{task["task_id"]}</text>'
            f'<text x="{x + 41}" y="{340 - height:.2f}" fill="{color}" font-family="monospace" '
            f'font-size="13" text-anchor="middle">{float(task["row_permutation_fraction"]):.2f} reversible</text>'
        )
    circuit = payload["circuit"]
    assert isinstance(circuit, dict)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="560" viewBox="0 0 1100 560">
<rect width="1100" height="560" rx="20" fill="#050505"/>
<text x="550" y="56" fill="#fff" font-family="monospace" font-size="29" text-anchor="middle">UQT FORGE · FINITE ALGEBRA</text>
<text x="550" y="88" fill="#858585" font-family="monospace" font-size="14" text-anchor="middle">known-answer tasks · reversible controls · 5-qubit circuit accounting</text>
<line x1="90" y1="360" x2="1010" y2="360" stroke="#333"/>
{''.join(bars)}
<text x="550" y="462" fill="#7ee787" font-family="monospace" font-size="15" text-anchor="middle">parameters = {circuit["parameter_count"]} · unitary residual = {float(circuit["unitarity_residual"]):.3e}</text>
<text x="550" y="492" fill="#777" font-family="monospace" font-size="12" text-anchor="middle">negative control stays non-reversible; no training or hardware claim is made</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=["all", "mod11-add", "mod11-mul", "mod11-star-mul", "s4-cayley"],
        default="all",
    )
    parser.add_argument("--n-qubits", type=int, default=5)
    parser.add_argument("--embedding-qubits", type=int, default=None)
    parser.add_argument("--layers", type=int, default=None)
    parser.add_argument("--seed", type=int, default=260600045)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "uqt-0001-algebra",
    )
    args = parser.parse_args()

    report = run_uqt_forge(
        task=args.task,
        n_qubits=args.n_qubits,
        embedding_qubits=args.embedding_qubits,
        layers=args.layers,
        seed=args.seed,
    )
    payload = report.summary()
    payload["sources"] = [
        {
            "kind": "literature_reference",
            "title": "Universal Quantum Transformer",
            "identifier": "arXiv:2606.00045",
            "scope": "external inspiration only; this run is not a reproduction",
        }
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "cases.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "task",
            "left",
            "right",
            "expected",
            "observed",
            "passed",
            "task_passed",
            "negative_control",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in iter_case_rows(report):
            writer.writerow({key: row[key] for key in fieldnames})
    with (args.output_dir / "ledger.jsonl").open("w", encoding="utf-8") as handle:
        for task in payload["tasks"]:
            handle.write(json.dumps(task, sort_keys=True) + "\n")
    (args.output_dir / "uqt_forge.svg").write_text(_render_svg(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
