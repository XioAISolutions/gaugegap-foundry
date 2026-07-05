#!/usr/bin/env python3
"""Run the finite Bell-state entanglement forge."""
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

from gaugegap.entanglement_forge import run_entanglement_forge  # noqa: E402


def _render_svg(payload: dict[str, object]) -> str:
    chsh = float(payload["chsh_value"])
    classical = float(payload["classical_bound"])
    tsirelson = float(payload["tsirelson_bound"])
    residual = float(payload["no_signaling_residual"])
    scale = 700 / tsirelson
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="420" viewBox="0 0 960 420">'
        '<rect width="960" height="420" fill="#030303"/>'
        '<text x="48" y="54" fill="#f0f6fc" font-size="28" font-family="system-ui">Entanglement Forge</text>'
        '<text x="48" y="84" fill="#8b949e" font-size="14" font-family="monospace">Bell singlet · CHSH violation · no-signaling audit</text>'
        '<rect x="130" y="142" width="700" height="42" fill="#161b22" stroke="#30363d"/>'
        f'<rect x="130" y="142" width="{classical * scale:.1f}" height="42" fill="#8b949e"/>'
        f'<rect x="130" y="220" width="{chsh * scale:.1f}" height="42" fill="#d2a8ff"/>'
        '<line x1="830" y1="122" x2="830" y2="286" stroke="#f2cc60" stroke-width="2"/>'
        '<text x="48" y="170" fill="#8b949e" font-size="14" font-family="monospace">classical bound</text>'
        f'<text x="846" y="170" fill="#8b949e" font-size="14" font-family="monospace">{classical:.6f}</text>'
        '<text x="48" y="248" fill="#d2a8ff" font-size="14" font-family="monospace">Bell state CHSH</text>'
        f'<text x="846" y="248" fill="#d2a8ff" font-size="14" font-family="monospace">{chsh:.6f}</text>'
        f'<text x="48" y="330" fill="#f2cc60" font-size="14" font-family="monospace">Tsirelson bound {tsirelson:.6f}</text>'
        f'<text x="48" y="360" fill="#7ee787" font-size="14" font-family="monospace">no-signaling residual {residual:.3e}</text>'
        '<text x="48" y="390" fill="#f85149" font-size="12" font-family="monospace">Bluetooth is analogy only; no communication channel is claimed.</text>'
        '</svg>'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "entangle-0001")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    report = run_entanglement_forge()
    payload = report.summary()
    (args.output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "correlations.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(payload["correlations"][0].keys()))
        writer.writeheader()
        writer.writerows(payload["correlations"])
    with (args.output_dir / "joint_probabilities.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(payload["joint_probabilities"][0].keys()))
        writer.writeheader()
        writer.writerows(payload["joint_probabilities"])
    with (args.output_dir / "ledger.jsonl").open("w", encoding="utf-8") as handle:
        for row in payload["correlations"]:
            handle.write(json.dumps({"event": "correlation", **row}, sort_keys=True) + "\n")
        handle.write(
            json.dumps(
                {
                    "event": "claim_boundary",
                    "claim_boundary": payload["claim_boundary"],
                    "bluetooth_analogy_boundary": payload["bluetooth_analogy_boundary"],
                },
                sort_keys=True,
            )
            + "\n"
        )
    (args.output_dir / "entanglement_forge.svg").write_text(_render_svg(payload), encoding="utf-8")
    print(json.dumps({"passed": report.passed, "output_dir": str(args.output_dir)}, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
