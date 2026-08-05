"""Run the complete GaugeGap Jump Lab elevator demonstration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifact import dump_artifact
from .executive import AbductiveExecutive, ExecutiveConfig
from .report import render_discovery_html, write_html


def run_demo(
    *,
    seed: int = 927451,
    output: str | Path | None = None,
    html_output: str | Path | None = None,
    use_salience: bool = True,
    early_stop: bool = True,
    max_interventions: int | None = None,
) -> dict:
    artifact = AbductiveExecutive(
        seed=seed,
        config=ExecutiveConfig(
            use_salience=use_salience,
            early_stop=early_stop,
            max_interventions=max_interventions,
        ),
    ).run()
    if output is not None:
        dump_artifact(artifact, output)
    if html_output is not None:
        write_html(render_discovery_html(artifact), html_output)
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GaugeGap Jump Lab: The Elevator")
    parser.add_argument("--seed", type=int, default=927451)
    parser.add_argument("--out", default="artifacts/elevator-experiment.crumb.json")
    parser.add_argument("--html", default="artifacts/elevator-experiment.html")
    parser.add_argument("--no-salience", action="store_true")
    parser.add_argument("--no-early-stop", action="store_true")
    parser.add_argument("--max-interventions", type=int)
    args = parser.parse_args(argv)
    artifact = run_demo(
        seed=args.seed,
        output=args.out,
        html_output=args.html,
        use_salience=not args.no_salience,
        early_stop=not args.no_early_stop,
        max_interventions=args.max_interventions,
    )
    print(
        json.dumps(
            {
                "artifact": args.out,
                "html": args.html,
                "winner": artifact["metrics"]["winner"],
                "winner_score": artifact["metrics"]["winner_score"],
                "experiments_run": artifact["metrics"]["experiments_run"],
                "discovery_complete": artifact["metrics"]["discovery_complete"],
                "verdict": artifact["verification"]["verdict"],
                "hash": artifact["provenance"]["artifact_hash"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
