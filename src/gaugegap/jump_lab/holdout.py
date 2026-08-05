"""Blinded pendulum holdout suite with cold, warm, and fixed controls."""

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
from .pendulum_executive import PendulumAbductiveExecutive

DEFAULT_HOLDOUT_SEEDS = (111, 222, 333, 444, 555)


def _metrics(artifact: dict[str, Any]) -> dict[str, Any]:
    metrics = artifact.get("metrics", {})
    blind = artifact.get("blind_protocol", {})
    return {
        "experiment_id": artifact.get("experiment", {}).get("id"),
        "artifact_hash": artifact.get("provenance", {}).get("artifact_hash"),
        "experiments_run": metrics.get("experiments_run"),
        "discovery_complete": metrics.get("discovery_complete"),
        "winner": metrics.get("winner"),
        "winner_score": metrics.get("winner_score"),
        "semantic_key": metrics.get("evaluator_selected_semantic_key"),
        "blind_selection_correct": metrics.get("blind_selection_correct"),
        "verdict": artifact.get("verification", {}).get("verdict"),
        "leakage_free": not bool(blind.get("leakage_hits")),
        "policy": metrics.get("policy"),
    }


def run_holdout_suite(
    seeds: Iterable[int] = DEFAULT_HOLDOUT_SEEDS,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    resolved = [int(seed) for seed in seeds]
    if not resolved:
        raise ValueError("at least one seed is required")
    root = Path(output_dir) if output_dir is not None else None
    if root is not None:
        root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    artifact_index: list[dict[str, Any]] = []
    for seed in resolved:
        elevator = AbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=True, early_stop=True),
        ).run()
        cart = CartAbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(use_salience=True, early_stop=True),
            salience_memory=elevator["salience_memory"]["after"],
            parent_artifact_hashes=[elevator["provenance"]["artifact_hash"]],
        ).run()
        trained_memory = cart["salience_memory"]["after"]
        parents = [
            elevator["provenance"]["artifact_hash"],
            cart["provenance"]["artifact_hash"],
        ]

        cold = PendulumAbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(
                use_salience=True,
                early_stop=True,
                confidence_threshold=0.70,
            ),
        ).run()
        warm = PendulumAbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(
                use_salience=True,
                early_stop=True,
                confidence_threshold=0.70,
            ),
            salience_memory=trained_memory,
            parent_artifact_hashes=parents,
        ).run()
        fixed = PendulumAbductiveExecutive(
            seed=seed,
            config=ExecutiveConfig(
                use_salience=False,
                early_stop=True,
                confidence_threshold=0.70,
            ),
        ).run()

        if root is not None:
            seed_root = root / f"seed-{seed}"
            seed_root.mkdir(parents=True, exist_ok=True)
            artifacts = {
                "train_elevator": elevator,
                "train_cart": cart,
                "holdout_cold": cold,
                "holdout_warm": warm,
                "holdout_fixed": fixed,
            }
            for role, artifact in artifacts.items():
                path = seed_root / f"{role.replace('_', '-')}.eja.json"
                dump_artifact(artifact, path)
                artifact_index.append(
                    {
                        "seed": seed,
                        "role": role,
                        "path": str(path),
                        "hash": artifact["provenance"]["artifact_hash"],
                        "parents": artifact["provenance"].get(
                            "parent_artifact_hashes", []
                        ),
                    }
                )

        cold_metrics = _metrics(cold)
        warm_metrics = _metrics(warm)
        fixed_metrics = _metrics(fixed)
        rows.append(
            {
                "seed": seed,
                "cold": cold_metrics,
                "warm": warm_metrics,
                "fixed": fixed_metrics,
                "warm_vs_cold_experiments_saved": (
                    cold_metrics["experiments_run"] - warm_metrics["experiments_run"]
                ),
                "warm_vs_fixed_experiments_saved": (
                    fixed_metrics["experiments_run"] - warm_metrics["experiments_run"]
                ),
                "same_semantic_selection": len(
                    {
                        cold_metrics["semantic_key"],
                        warm_metrics["semantic_key"],
                        fixed_metrics["semantic_key"],
                    }
                )
                == 1,
                "warm_parent_linked": all(
                    parent in warm["provenance"].get("parent_artifact_hashes", [])
                    for parent in parents
                ),
            }
        )

    policies = ("cold", "warm", "fixed")
    summary: dict[str, Any] = {
        "run_count": len(rows),
        "training_world_count": 2,
        "holdout_world_count": 1,
        "same_semantic_selection_rate": round(
            fmean(1.0 if row["same_semantic_selection"] else 0.0 for row in rows), 6
        ),
        "warm_parent_link_rate": round(
            fmean(1.0 if row["warm_parent_linked"] else 0.0 for row in rows), 6
        ),
        "warm_vs_cold_mean_experiments_saved": round(
            fmean(row["warm_vs_cold_experiments_saved"] for row in rows), 6
        ),
        "warm_vs_fixed_mean_experiments_saved": round(
            fmean(row["warm_vs_fixed_experiments_saved"] for row in rows), 6
        ),
    }
    for policy in policies:
        summary[f"{policy}_selection_accuracy"] = round(
            fmean(
                1.0 if row[policy]["blind_selection_correct"] else 0.0
                for row in rows
            ),
            6,
        )
        summary[f"{policy}_completion_rate"] = round(
            fmean(
                1.0 if row[policy]["discovery_complete"] else 0.0
                for row in rows
            ),
            6,
        )
        summary[f"{policy}_mean_experiments"] = round(
            fmean(float(row[policy]["experiments_run"]) for row in rows), 6
        )
        summary[f"{policy}_leakage_free_rate"] = round(
            fmean(1.0 if row[policy]["leakage_free"] else 0.0 for row in rows), 6
        )

    return {
        "artifact_type": "jump_lab_blind_holdout_suite",
        "suite_version": "0.4",
        "training_worlds": ["einstein-elevator-v0.3", "force-mass-cart-v0.3"],
        "holdout_world": "simple-pendulum-holdout-v0.4",
        "blind_protocol": {
            "task": "anonymous pre-registered model selection",
            "semantic_model_statements_visible_during_run": False,
            "open_ended_abduction": False,
            "transfer_payload": "bounded semantic salience associations only",
        },
        "runs": rows,
        "summary": summary,
        "artifact_index": artifact_index,
        "claim_boundary": (
            "This suite measures blinded selection among pre-registered prediction "
            "models on one deterministic holdout world. It does not demonstrate "
            "open-ended hypothesis invention, real scientific discovery, or general "
            "cross-domain transfer."
        ),
    }


def render_holdout_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('seed')))}</td>"
        f"<td>{escape(str(row.get('cold', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(row.get('warm', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(row.get('fixed', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(row.get('warm', {}).get('blind_selection_correct')))}</td>"
        f"<td>{escape(str(row.get('warm_vs_cold_experiments_saved')))}</td>"
        f"<td>{escape(str(row.get('same_semantic_selection')))}</td>"
        "</tr>"
        for row in report.get("runs", [])
    )
    summary = report.get("summary", {})
    raw = escape(json.dumps(report, indent=2, sort_keys=True))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jump Lab Blind Holdout</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#06111f;color:#edf5ff}}main{{width:min(1220px,94vw);margin:36px auto}}section{{background:#101d31;border:1px solid #29415f;border-radius:16px;padding:20px;margin:16px 0}}.stats{{display:flex;gap:10px;flex-wrap:wrap}}.stat{{padding:8px 12px;border:1px solid #29415f;border-radius:999px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #29415f;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#06111f;padding:14px;border-radius:10px}}strong{{color:#86e8b3}}</style></head><body><main><h1>GaugeGap Jump Lab v0.4 · Blind holdout</h1><div class="stats"><span class="stat">Seeds <strong>{escape(str(summary.get('run_count')))}</strong></span><span class="stat">Warm accuracy <strong>{escape(str(summary.get('warm_selection_accuracy')))}</strong></span><span class="stat">Warm completion <strong>{escape(str(summary.get('warm_completion_rate')))}</strong></span><span class="stat">Leakage-free <strong>{escape(str(summary.get('warm_leakage_free_rate')))}</strong></span></div><section><h2>Paired holdout runs</h2><table><thead><tr><th>Seed</th><th>Cold</th><th>Warm</th><th>Fixed</th><th>Warm correct</th><th>Warm saved</th><th>Same model</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Raw suite record</h2><pre>{raw}</pre></section><p><strong>Claim boundary:</strong> {escape(str(report.get('claim_boundary', 'missing')))}</p></main></body></html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Jump Lab blind holdout suite")
    parser.add_argument(
        "--seeds",
        default=",".join(str(seed) for seed in DEFAULT_HOLDOUT_SEEDS),
        help="comma-separated deterministic seeds",
    )
    parser.add_argument("--out-dir", default="artifacts/jump-lab-holdout")
    parser.add_argument("--report", default="artifacts/jump-lab-holdout.json")
    parser.add_argument("--html", default="artifacts/jump-lab-holdout.html")
    args = parser.parse_args(argv)
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    report = run_holdout_suite(seeds, output_dir=args.out_dir)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.html:
        html_path = Path(args.html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_holdout_html(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
