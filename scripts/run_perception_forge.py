#!/usr/bin/env python3
"""Run finite fitness-vs-truth perception simulations and emit evidence artifacts."""
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

from gaugegap.perception_forge import run_perception_forge  # noqa: E402


def _render_svg(payload: dict[str, object]) -> str:
    worlds = payload["worlds"]
    assert isinstance(worlds, list)
    points = []
    for index, world in enumerate(worlds):
        assert isinstance(world, dict)
        x = 95 + index * (900 / max(len(worlds) - 1, 1))
        truth_y = 390 - 260 * float(world["truth_payoff"])
        interface_y = 390 - 260 * float(world["interface_payoff"])
        points.append(
            f'<circle cx="{x:.2f}" cy="{truth_y:.2f}" r="4" fill="#ff8c8c"/>'
            f'<circle cx="{x:.2f}" cy="{interface_y:.2f}" r="4" fill="#7ee787"/>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="560" viewBox="0 0 1100 560">
<rect width="1100" height="560" rx="20" fill="#050505"/>
<text x="550" y="56" fill="#fff" font-family="monospace" font-size="29" text-anchor="middle">PERCEPTION FORGE</text>
<text x="550" y="88" fill="#858585" font-family="monospace" font-size="14" text-anchor="middle">finite evolutionary game: truth-coded bins vs fitness interface bins</text>
<line x1="80" y1="390" x2="1020" y2="390" stroke="#333"/>
<line x1="80" y1="130" x2="80" y2="390" stroke="#333"/>
{''.join(points)}
<text x="175" y="446" fill="#ff8c8c" font-family="monospace" font-size="14">truth-coded payoff</text>
<text x="175" y="474" fill="#7ee787" font-family="monospace" font-size="14">fitness-interface payoff</text>
<text x="550" y="504" fill="#7ee787" font-family="monospace" font-size="15" text-anchor="middle">truth extinction fraction = {float(payload["truth_extinction_fraction"]):.2f} in this finite suite</text>
<text x="550" y="530" fill="#777" font-family="monospace" font-size="12" text-anchor="middle">not a neuroscience result or metaphysical proof</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-count", type=int, default=12)
    parser.add_argument("--state-count", type=int, default=64)
    parser.add_argument("--action-count", type=int, default=4)
    parser.add_argument("--percept-count", type=int, default=4)
    parser.add_argument("--generations", type=int, default=80)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "perception-0001-fitness-interface",
    )
    args = parser.parse_args()

    report = run_perception_forge(
        world_count=args.world_count,
        state_count=args.state_count,
        action_count=args.action_count,
        percept_count=args.percept_count,
        generations=args.generations,
    )
    payload = report.summary()
    payload["sources"] = [
        {
            "kind": "literature_reference",
            "title": "The Interface Theory of Perception",
            "identifier": "doi:10.3758/s13423-015-0890-8",
            "scope": "external inspiration; this script is a finite toy simulation",
        },
        {
            "kind": "literature_reference",
            "title": "Fitness Beats Truth in the Evolution of Perception",
            "identifier": "Acta Biotheoretica / PubMed 33231784",
            "scope": "external inspiration; not reproduced as a theorem proof here",
        },
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "worlds.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "world_id",
            "state_count",
            "action_count",
            "percept_count",
            "payoff_period",
            "truth_payoff",
            "interface_payoff",
            "payoff_advantage",
            "truth_extinct",
            "interface_dominates",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for world in report.worlds:
            row = world.summary()
            writer.writerow({key: row[key] for key in fieldnames})
    with (args.output_dir / "strategy_ledger.jsonl").open("w", encoding="utf-8") as handle:
        for world in payload["worlds"]:
            handle.write(json.dumps(world, sort_keys=True) + "\n")
    (args.output_dir / "perception_forge.svg").write_text(
        _render_svg(payload),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
