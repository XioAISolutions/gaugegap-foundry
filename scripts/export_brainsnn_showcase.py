#!/usr/bin/env python3
"""Export a bounded GaugeGap research-showcase package for BrainSNN."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.compactification_forge import run_compactification_suite  # noqa: E402
from gaugegap.entanglement_forge import run_entanglement_forge  # noqa: E402
from gaugegap.fractal_topology_forge import run_menger_forge  # noqa: E402
from gaugegap.perception_forge import run_perception_forge  # noqa: E402
from gaugegap.quantum.uqt_forge import run_uqt_forge  # noqa: E402
from gaugegap.quantum_gap import compute_quantum_gap  # noqa: E402


CLAIM_BOUNDARY = (
    "BrainSNN showcase handoff only; it packages finite GaugeGap evidence and "
    "claim boundaries for content/research presentation, not automatic marketing "
    "truth scoring or proof of the underlying physics claims"
)


def _card(
    title: str,
    artifact: str,
    observable: str,
    takeaway: str,
    boundary: str,
) -> dict[str, str]:
    return {
        "title": title,
        "artifact": artifact,
        "observable": observable,
        "brainsnn_use": takeaway,
        "claim_boundary": boundary,
    }


def build_showcase() -> dict[str, object]:
    uqt = run_uqt_forge(task="all").summary()
    compact = [report.summary() for report in run_compactification_suite()]
    perception = run_perception_forge(world_count=12).summary()
    menger = run_menger_forge(iterations=4).summary()
    entanglement = run_entanglement_forge().summary()
    quantum_gap = compute_quantum_gap(
        dynamics=[{"dmd": {"reconstruction_error": 0.01}, "validated_step": {"validated": True}}],
        hamiltonians=[
            {
                "audit": {
                    "spectral_gap": 0.5,
                    "ground_energy": -1.0,
                    "first_excited_energy": -0.5,
                }
            }
        ],
        uqt_summary=uqt,
        compact_summaries=compact,
        perception_summary=perception,
        menger_summary=menger,
        entanglement_summary=entanglement,
        validation_gate=True,
    ).summary()
    return {
        "schema": "gaugegap.brainsnn_showcase.v1",
        "title": "GaugeGap Foundry Research Showcase",
        "positioning": (
            "Verification-first finite research artifacts for BrainSNN-style "
            "content preflight: every strong claim carries an observable, control, "
            "evidence artifact, and boundary."
        ),
        "cards": [
            _card(
                "Quantum Gap Functional",
                "src/gaugegap/quantum_gap.py",
                f"score={quantum_gap['score']:.6g}; terms={len(quantum_gap['terms'])}",
                "Use as the flagship example of fail-closed synthesis.",
                quantum_gap["claim_boundary"],
            ),
            _card(
                "UQT Forge",
                "src/gaugegap/quantum/uqt_forge.py",
                f"tasks={len(uqt['tasks'])}; passed={uqt['passed']}",
                "Use as exact finite algebra and reversibility-control content.",
                uqt["claim_boundary"],
            ),
            _card(
                "Compactification Forge",
                "src/gaugegap/compactification_forge.py",
                f"geometries={len(compact)}; visible_modes={sum(item['visible_mode_count'] for item in compact)}",
                "Use as hidden-structure/cutoff-visibility explainer content.",
                compact[0]["claim_boundary"],
            ),
            _card(
                "Perception Forge",
                "src/gaugegap/perception_forge.py",
                f"truth_extinction_fraction={perception['truth_extinction_fraction']:.3g}",
                "Use as a finite interface-vs-truth claim-boundary example.",
                perception["claim_boundary"],
            ),
            _card(
                "Menger Sponge Forge",
                "src/gaugegap/fractal_topology_forge.py",
                f"dim_H={menger['hausdorff_dimension']:.6g}; voxel_sample={len(menger['voxel_sample'])}",
                "Use as fractal topology and intuition-gap content.",
                menger["claim_boundary"],
            ),
            _card(
                "Entanglement Forge",
                "src/gaugegap/entanglement_forge.py",
                f"CHSH={entanglement['chsh_value']:.6g}; no_signal={entanglement['no_signaling_residual']:.3g}",
                "Use as correlation-without-communication content.",
                entanglement["claim_boundary"],
            ),
        ],
        "do_not_claim": [
            "BrainSNN proves physics claims",
            "Quantum Gap is a universal truth score",
            "GaugeGap validates marketing claims automatically",
            "entanglement enables faster-than-light communication",
            "finite Menger stages prove the completed fractal topology",
        ],
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        str(payload["positioning"]),
        "",
        f"> {payload['claim_boundary']}",
        "",
        "## Showcase Cards",
        "",
    ]
    for card in payload["cards"]:
        lines.extend(
            [
                f"### {card['title']}",
                "",
                f"- Artifact: `{card['artifact']}`",
                f"- Observable: `{card['observable']}`",
                f"- BrainSNN use: {card['brainsnn_use']}",
                f"- Boundary: {card['claim_boundary']}",
                "",
            ]
        )
    lines.extend(["## Do Not Claim", ""])
    for item in payload["do_not_claim"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "site" / "brainsnn-gaugegap-showcase")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_showcase()
    (args.output_dir / "showcase.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "showcase.md").write_text(_markdown(payload), encoding="utf-8")
    print(json.dumps({"output_dir": str(args.output_dir), "cards": len(payload["cards"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
