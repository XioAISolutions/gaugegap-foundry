"""Paired benchmark for salience-guided versus fixed intervention ordering."""

from __future__ import annotations

import argparse
from statistics import fmean
import json
from pathlib import Path
from typing import Any, Iterable

from .executive import AbductiveExecutive, ExecutiveConfig
from .report import render_benchmark_html, write_html

DEFAULT_SEEDS = (101, 202, 303, 404, 505, 927451)


def _metrics(artifact: dict[str, Any]) -> dict[str, Any]:
    metrics = artifact["metrics"]
    return {
        "experiments_run": metrics["experiments_run"],
        "discovery_complete": metrics["discovery_complete"],
        "winner": metrics["winner"],
        "winner_score": metrics["winner_score"],
        "scope_boundary_observed": metrics["scope_boundary_observed"],
        "local_invariance_tests": metrics["local_invariance_tests"],
        "verdict": artifact["verification"]["verdict"],
    }


def run_benchmark(seeds: Iterable[int] = DEFAULT_SEEDS) -> dict[str, Any]:
    """Run a paired deterministic A/B benchmark over the provided seeds.

    The two policies receive the same world, hypotheses, scoring updates, stop
    conditions, and verifier. Only intervention ordering changes.
    """
    rows: list[dict[str, Any]] = []
    for raw_seed in seeds:
        seed = int(raw_seed)
        salience = AbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=True, early_stop=True),
        ).run()
        baseline = AbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=False, early_stop=True),
        ).run()
        sm = _metrics(salience)
        bm = _metrics(baseline)
        rows.append(
            {
                "seed": seed,
                "salience": sm,
                "baseline": bm,
                "saved_experiments": bm["experiments_run"] - sm["experiments_run"],
                "same_winner": sm["winner"] == bm["winner"],
                "both_complete": bool(
                    sm["discovery_complete"] and bm["discovery_complete"]
                ),
                "same_verdict": sm["verdict"] == bm["verdict"],
            }
        )

    count = len(rows)
    if count == 0:
        raise ValueError("at least one seed is required")
    return {
        "benchmark": "jump-lab-salience-ab-v0.3",
        "world": "einstein-elevator-v0.3",
        "controlled_variable": "intervention_ordering_policy",
        "runs": rows,
        "paired_summary": {
            "run_count": count,
            "mean_experiments_saved": round(
                fmean(row["saved_experiments"] for row in rows), 6
            ),
            "same_winner_rate": round(
                fmean(1.0 if row["same_winner"] else 0.0 for row in rows), 6
            ),
            "both_complete_rate": round(
                fmean(1.0 if row["both_complete"] else 0.0 for row in rows), 6
            ),
            "same_verdict_rate": round(
                fmean(1.0 if row["same_verdict"] else 0.0 for row in rows), 6
            ),
            "salience_mean_experiments": round(
                fmean(row["salience"]["experiments_run"] for row in rows), 6
            ),
            "baseline_mean_experiments": round(
                fmean(row["baseline"]["experiments_run"] for row in rows), 6
            ),
        },
        "claim_boundary": (
            "This paired benchmark measures one hand-authored salience policy "
            "inside one deterministic elevator toy world. It is not evidence "
            "that spiking neural networks generally outperform other planners."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark Jump Lab salience ordering")
    parser.add_argument(
        "--seeds",
        default=",".join(str(seed) for seed in DEFAULT_SEEDS),
        help="comma-separated deterministic seeds",
    )
    parser.add_argument("--out", default="artifacts/jump-lab-benchmark.json")
    parser.add_argument("--html", default="artifacts/jump-lab-benchmark.html")
    args = parser.parse_args(argv)
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    report = run_benchmark(seeds)
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.html:
        write_html(render_benchmark_html(report), args.html)
    print(json.dumps(report["paired_summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
