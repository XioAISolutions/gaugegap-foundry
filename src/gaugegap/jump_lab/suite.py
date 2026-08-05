"""Multi-world Jump Lab suite with explicit cold, warm, and fixed policies."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

from .artifact import dump_artifact
from .cart_executive import CartAbductiveExecutive
from .executive import AbductiveExecutive, ExecutiveConfig

DEFAULT_SUITE_SEEDS = (101, 202, 303, 404, 505)


def registered_tasks() -> dict[str, str]:
    return {
        "elevator": "einstein-elevator-v0.3",
        "force_cart": "force-mass-cart-v0.3",
    }


def _metrics(artifact: dict[str, Any]) -> dict[str, Any]:
    metrics = artifact.get("metrics", {})
    return {
        "world": artifact.get("experiment", {}).get("world"),
        "experiment_id": artifact.get("experiment", {}).get("id"),
        "artifact_hash": artifact.get("provenance", {}).get("artifact_hash"),
        "winner": metrics.get("winner"),
        "winner_score": metrics.get("winner_score"),
        "verdict": artifact.get("verification", {}).get("verdict"),
        "discovery_complete": metrics.get("discovery_complete"),
        "experiments_run": metrics.get("experiments_run"),
        "local_invariance_tests": metrics.get("local_invariance_tests"),
        "scope_boundary_observed": metrics.get("scope_boundary_observed"),
        "policy": metrics.get("policy"),
    }


def _write_artifact(
    artifact: dict[str, Any],
    root: Path,
    filename: str,
) -> str:
    destination = root / filename
    dump_artifact(artifact, destination)
    return str(destination)


def run_suite(
    seeds: Iterable[int] = DEFAULT_SUITE_SEEDS,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run two worlds and measure bounded cross-world salience-memory transfer.

    The warm cart policy receives only semantic attention associations learned in
    the elevator task. It does not receive hypotheses, answers, hidden state, or
    verifier results. Cold salience and fixed-order cart runs remain paired
    controls. The suite reports transfer even when it is neutral or harmful.
    """
    resolved_seeds = [int(seed) for seed in seeds]
    if not resolved_seeds:
        raise ValueError("at least one seed is required")
    root = Path(output_dir) if output_dir is not None else None
    if root is not None:
        root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    artifact_index: list[dict[str, Any]] = []
    for seed in resolved_seeds:
        elevator = AbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=True, early_stop=True),
        ).run()
        memory = elevator["salience_memory"]["after"]
        parent_hash = elevator["provenance"]["artifact_hash"]

        cart_cold = CartAbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=True, early_stop=True),
        ).run()
        cart_warm = CartAbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=True, early_stop=True),
            salience_memory=memory,
            parent_artifact_hashes=[parent_hash],
        ).run()
        cart_baseline = CartAbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=False, early_stop=True),
        ).run()

        if root is not None:
            seed_root = root / f"seed-{seed}"
            seed_root.mkdir(parents=True, exist_ok=True)
            paths = {
                "elevator": _write_artifact(
                    elevator, seed_root, "elevator.eja.json"
                ),
                "cart_cold": _write_artifact(
                    cart_cold, seed_root, "cart-cold.eja.json"
                ),
                "cart_warm": _write_artifact(
                    cart_warm, seed_root, "cart-warm.eja.json"
                ),
                "cart_baseline": _write_artifact(
                    cart_baseline, seed_root, "cart-baseline.eja.json"
                ),
            }
            for role, artifact in (
                ("elevator", elevator),
                ("cart_cold", cart_cold),
                ("cart_warm", cart_warm),
                ("cart_baseline", cart_baseline),
            ):
                artifact_index.append(
                    {
                        "seed": seed,
                        "role": role,
                        "path": paths[role],
                        "hash": artifact["provenance"]["artifact_hash"],
                        "parents": artifact["provenance"].get(
                            "parent_artifact_hashes", []
                        ),
                    }
                )

        elevator_metrics = _metrics(elevator)
        cold_metrics = _metrics(cart_cold)
        warm_metrics = _metrics(cart_warm)
        baseline_metrics = _metrics(cart_baseline)
        rows.append(
            {
                "seed": seed,
                "elevator": elevator_metrics,
                "cart_cold": cold_metrics,
                "cart_warm": warm_metrics,
                "cart_baseline": baseline_metrics,
                "warm_vs_cold_experiments_saved": (
                    cold_metrics["experiments_run"]
                    - warm_metrics["experiments_run"]
                ),
                "warm_vs_baseline_experiments_saved": (
                    baseline_metrics["experiments_run"]
                    - warm_metrics["experiments_run"]
                ),
                "cart_same_winner": len(
                    {
                        cold_metrics["winner"],
                        warm_metrics["winner"],
                        baseline_metrics["winner"],
                    }
                )
                == 1,
                "cart_same_verdict": len(
                    {
                        cold_metrics["verdict"],
                        warm_metrics["verdict"],
                        baseline_metrics["verdict"],
                    }
                )
                == 1,
                "warm_parent_linked": parent_hash
                in cart_warm["provenance"].get("parent_artifact_hashes", []),
            }
        )

    summary = {
        "run_count": len(rows),
        "world_count": len(registered_tasks()),
        "all_world_discoveries_complete_rate": round(
            fmean(
                1.0
                if all(
                    row[key]["discovery_complete"]
                    for key in (
                        "elevator",
                        "cart_cold",
                        "cart_warm",
                        "cart_baseline",
                    )
                )
                else 0.0
                for row in rows
            ),
            6,
        ),
        "warm_vs_cold_mean_experiments_saved": round(
            fmean(row["warm_vs_cold_experiments_saved"] for row in rows), 6
        ),
        "warm_vs_baseline_mean_experiments_saved": round(
            fmean(row["warm_vs_baseline_experiments_saved"] for row in rows), 6
        ),
        "cart_same_winner_rate": round(
            fmean(1.0 if row["cart_same_winner"] else 0.0 for row in rows), 6
        ),
        "cart_same_verdict_rate": round(
            fmean(1.0 if row["cart_same_verdict"] else 0.0 for row in rows), 6
        ),
        "warm_parent_link_rate": round(
            fmean(1.0 if row["warm_parent_linked"] else 0.0 for row in rows), 6
        ),
    }
    return {
        "artifact_type": "jump_lab_multiworld_suite",
        "suite_version": "0.3",
        "tasks": registered_tasks(),
        "controlled_transfer": {
            "source": "elevator salience associations",
            "target": "force cart intervention ranking",
            "excluded": [
                "hidden world state",
                "hypothesis scores",
                "candidate axioms",
                "verification verdicts",
            ],
        },
        "runs": rows,
        "summary": summary,
        "artifact_index": artifact_index,
        "claim_boundary": (
            "This suite demonstrates that one E-J-A implementation can run across "
            "two hand-authored deterministic toy worlds and can measure bounded "
            "attention-memory transfer. It does not establish open-ended scientific "
            "discovery, real-world physical validity, or general transfer learning."
        ),
    }


def render_suite_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('seed')))}</td>"
        f"<td>{escape(str(row.get('elevator', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(row.get('cart_cold', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(row.get('cart_warm', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(row.get('cart_baseline', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(row.get('warm_vs_cold_experiments_saved')))}</td>"
        f"<td>{escape(str(row.get('cart_same_winner')))}</td>"
        "</tr>"
        for row in report.get("runs", [])
    )
    summary = report.get("summary", {})
    raw = escape(json.dumps(report, indent=2, sort_keys=True))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GaugeGap Jump Lab Multi-world Suite</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#07111f;color:#eef5ff}}main{{width:min(1200px,94vw);margin:36px auto}}section{{background:#101d31;border:1px solid #2a405f;border-radius:16px;padding:20px;margin:16px 0}}.stats{{display:flex;gap:10px;flex-wrap:wrap}}.stat{{padding:8px 12px;border:1px solid #2a405f;border-radius:999px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #2a405f;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#07111f;padding:14px;border-radius:10px}}strong{{color:#85e8b2}}</style></head><body><main><h1>GaugeGap Jump Lab v0.3 · Multi-world suite</h1><div class="stats"><span class="stat">Worlds <strong>{escape(str(summary.get('world_count')))}</strong></span><span class="stat">Seeds <strong>{escape(str(summary.get('run_count')))}</strong></span><span class="stat">Warm vs cold mean savings <strong>{escape(str(summary.get('warm_vs_cold_mean_experiments_saved')))}</strong></span><span class="stat">Same cart winner rate <strong>{escape(str(summary.get('cart_same_winner_rate')))}</strong></span></div><section><h2>Paired runs</h2><table><thead><tr><th>Seed</th><th>Elevator</th><th>Cart cold</th><th>Cart warm</th><th>Cart fixed</th><th>Warm saved</th><th>Same winner</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Raw suite record</h2><pre>{raw}</pre></section><p><strong>Claim boundary:</strong> {escape(str(report.get('claim_boundary', 'missing')))}</p></main></body></html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Jump Lab multi-world suite")
    parser.add_argument(
        "--seeds",
        default=",".join(str(seed) for seed in DEFAULT_SUITE_SEEDS),
        help="comma-separated deterministic seeds",
    )
    parser.add_argument("--out-dir", default="artifacts/jump-lab-suite")
    parser.add_argument("--report", default="artifacts/jump-lab-suite.json")
    parser.add_argument("--html", default="artifacts/jump-lab-suite.html")
    args = parser.parse_args(argv)
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    report = run_suite(seeds, output_dir=args.out_dir)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.html:
        html_path = Path(args.html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_suite_html(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
