"""Run one blinded pendulum holdout experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifact import dump_artifact
from .executive import ExecutiveConfig
from .pendulum_executive import PendulumAbductiveExecutive
from .report import render_discovery_html, write_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the blinded pendulum holdout")
    parser.add_argument("--seed", type=int, default=927451)
    parser.add_argument("--out", default="artifacts/pendulum-holdout.eja.json")
    parser.add_argument("--html", default="artifacts/pendulum-holdout.html")
    parser.add_argument("--no-salience", action="store_true")
    parser.add_argument("--no-early-stop", action="store_true")
    parser.add_argument("--max-interventions", type=int)
    args = parser.parse_args(argv)
    artifact = PendulumAbductiveExecutive(
        seed=args.seed,
        config=ExecutiveConfig(
            use_salience=not args.no_salience,
            early_stop=not args.no_early_stop,
            max_interventions=args.max_interventions,
            confidence_threshold=0.70,
        ),
    ).run()
    dump_artifact(artifact, args.out)
    if args.html:
        write_html(render_discovery_html(artifact), args.html)
    print(
        json.dumps(
            {
                "artifact": str(Path(args.out)),
                "html": str(Path(args.html)) if args.html else None,
                "winner": artifact["metrics"]["winner"],
                "winner_score": artifact["metrics"]["winner_score"],
                "blind_selection_correct": artifact["metrics"]["blind_selection_correct"],
                "discovery_complete": artifact["metrics"]["discovery_complete"],
                "leakage_hits": artifact["blind_protocol"]["leakage_hits"],
                "verdict": artifact["verification"]["verdict"],
                "hash": artifact["provenance"]["artifact_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
