"""Run the complete GaugeGap Jump Lab elevator demonstration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifact import dump_artifact
from .executive import AbductiveExecutive


def run_demo(*, seed: int = 927451, output: str | Path | None = None) -> dict:
    artifact = AbductiveExecutive(seed=seed).run()
    if output is not None:
        dump_artifact(artifact, output)
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GaugeGap Jump Lab: The Elevator")
    parser.add_argument("--seed", type=int, default=927451)
    parser.add_argument("--out", default="artifacts/elevator-experiment.crumb.json")
    args = parser.parse_args(argv)
    artifact = run_demo(seed=args.seed, output=args.out)
    print(
        json.dumps(
            {
                "artifact": args.out,
                "winner": max(artifact["hypotheses"], key=lambda h: h["score"])["id"],
                "verdict": artifact["verification"]["verdict"],
                "hash": artifact["provenance"]["artifact_hash"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
