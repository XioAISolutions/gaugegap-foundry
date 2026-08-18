#!/usr/bin/env python3
"""Run the multi-game Lottery Forge selection screen for the current week."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date, timedelta
import json
from pathlib import Path

from gaugegap.lottery_forge import LotterySpec, _predict, rolling_backtest
from gaugegap.lottery_multigame_sources import fetch_wclc_daily_grand, fetch_wclc_max
from gaugegap.lottery_selection import (
    SELECTION_CLAIM_BOUNDARY,
    SelectionSpec,
    load_popular_combinations,
    search_selections,
)

MODELS = ("frequency", "cold-frequency", "recency", "hybrid")


def _backtests(draws, spec, windows, *, trials=2000, seed=649):
    windows = tuple(window for window in windows if 3 <= window < len(draws))
    family = max(1, len(windows) * len(MODELS))
    rows = []
    for window in windows:
        for index, model in enumerate(MODELS):
            result = rolling_backtest(
                draws, spec, model=model, window=window, trials=trials,
                seed=seed + window * 10 + index, family_size=family,
            )
            rows.append(result.summary())
    rows.sort(key=lambda row: (row["adjusted_p_value_bonferroni"], row["empirical_p_value"], -row["mean_hits"]))
    gate = any(
        row["adjusted_p_value_bonferroni"] < 0.01 and row["mean_hits"] > row["chance_mean_hits"]
        for row in rows
    )
    best = rows[0] if rows else None
    candidate = None
    if best:
        candidate = list(_predict(draws[-best["window"] :], spec, best["model"]))
    return {"family_size": family, "gate_passed": gate, "best": best, "candidate_from_best_model": candidate, "all": rows}


def _iso_two_year_start(latest: str) -> str:
    current = date.fromisoformat(latest)
    try:
        return current.replace(year=current.year - 2).isoformat()
    except ValueError:
        return (current - timedelta(days=730)).isoformat()


def run(output_dir: Path, *, selection_samples: int, backtest_trials: int, seed: int):
    output_dir.mkdir(parents=True, exist_ok=True)

    max_draws, max_source = fetch_wclc_max(start_date="2026-04-14")
    max_spec = LotterySpec(name="lotto-max-7of52", pool_size=52, pick_count=7)
    max_prediction = _backtests(max_draws, max_spec, (8, 13, 26), trials=backtest_trials, seed=seed)
    max_popular = load_popular_combinations("data/lottery/olg_max_popular_2025-05-25_2026-05-25.csv")
    max_ranked = search_selections(
        SelectionSpec("lotto-max", 52, 7), popular_combinations=max_popular,
        samples=selection_samples, top_k=20, seed=seed,
    )

    daily_all, _ = fetch_wclc_daily_grand()
    latest_daily = daily_all[-1].draw.draw_date
    daily_start = _iso_two_year_start(latest_daily)
    daily_rows, daily_source = fetch_wclc_daily_grand(start_date=daily_start)
    daily_draws = tuple(row.draw for row in daily_rows)
    daily_spec = LotterySpec(name="daily-grand-5of49", pool_size=49, pick_count=5)
    daily_prediction = _backtests(daily_draws, daily_spec, (26, 52, 104), trials=backtest_trials, seed=seed + 1000)
    daily_ranked = search_selections(
        SelectionSpec("daily-grand", 49, 5), samples=selection_samples,
        top_k=20, seed=seed + 1,
    )
    grand_counts = {number: 0 for number in range(1, 8)}
    for row in daily_rows:
        if row.grand_number is not None:
            grand_counts[row.grand_number] += 1

    grand_number = 4  # fixed low-salience heuristic; never chosen from draw frequency

    result = {
        "schema": "gaugegap.lottery_week.v1",
        "generated_from_official_sources": True,
        "claim_boundary": SELECTION_CLAIM_BOUNDARY,
        "lotto_max": {
            "game": asdict(max_spec),
            "draw_interval": [max_draws[0].draw_date, max_draws[-1].draw_date],
            "draw_count": len(max_draws),
            "source": max_source,
            "predictive_diagnostics": max_prediction,
            "recommended_selection": max_ranked[0].summary(),
            "top_selections": [row.summary() for row in max_ranked[:10]],
            "selection_basis": "sharing-risk heuristic only; predictive diagnostics are excluded unless the corrected gate passes",
        },
        "daily_grand": {
            "game": asdict(daily_spec),
            "draw_interval": [daily_draws[0].draw_date, daily_draws[-1].draw_date],
            "draw_count": len(daily_draws),
            "source": daily_source,
            "predictive_diagnostics": daily_prediction,
            "recommended_selection": daily_ranked[0].summary(),
            "top_selections": [row.summary() for row in daily_ranked[:10]],
            "grand_number": grand_number,
            "grand_number_historical_counts_descriptive_only": grand_counts,
            "grand_number_basis": "fixed low-salience heuristic only; no draw-frequency prediction",
        },
        "lotto_649": {
            "status": "existing sealed prospective protocol remains frozen",
            "instruction": "Do not replace the already-sealed 6/49 prediction with this selector during protocol 0002.",
        },
    }
    (output_dir / "lottery_week.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    max_rec = " - ".join(map(str, result["lotto_max"]["recommended_selection"]["numbers"]))
    daily_rec = " - ".join(map(str, result["daily_grand"]["recommended_selection"]["numbers"]))
    max_best = max_prediction["best"]
    daily_best = daily_prediction["best"]
    lines = [
        "# Lottery Forge weekly selection screen",
        "",
        f"- LOTTO MAX current-format draws: **{len(max_draws)}** ({max_draws[0].draw_date} → {max_draws[-1].draw_date})",
        f"- LOTTO MAX predictive gate: **{max_prediction['gate_passed']}**",
    ]
    if max_best:
        lines.append(
            f"- LOTTO MAX strongest tested holdout: **{max_best['model']} / {max_best['window']}**, "
            f"mean hits {max_best['mean_hits']:.4f} vs chance {max_best['chance_mean_hits']:.4f}, "
            f"adjusted p={max_best['adjusted_p_value_bonferroni']:.6g}"
        )
    lines += [
        f"- LOTTO MAX sharing-risk selection: **{max_rec}**",
        "",
        f"- DAILY GRAND analyzed draws: **{len(daily_draws)}** ({daily_draws[0].draw_date} → {daily_draws[-1].draw_date})",
        f"- DAILY GRAND predictive gate: **{daily_prediction['gate_passed']}**",
    ]
    if daily_best:
        lines.append(
            f"- DAILY GRAND strongest tested holdout: **{daily_best['model']} / {daily_best['window']}**, "
            f"mean hits {daily_best['mean_hits']:.4f} vs chance {daily_best['chance_mean_hits']:.4f}, "
            f"adjusted p={daily_best['adjusted_p_value_bonferroni']:.6g}"
        )
    lines += [
        f"- DAILY GRAND sharing-risk selection: **{daily_rec} + Grand Number {grand_number}**",
        "",
        "## Claim boundary",
        "",
        SELECTION_CLAIM_BOUNDARY,
        "",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results/lottery-week")
    parser.add_argument("--selection-samples", type=int, default=500_000)
    parser.add_argument("--backtest-trials", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260818)
    args = parser.parse_args()
    result = run(Path(args.output_dir), selection_samples=args.selection_samples, backtest_trials=args.backtest_trials, seed=args.seed)
    print(json.dumps({
        "lotto_max": result["lotto_max"]["recommended_selection"]["numbers"],
        "lotto_max_predictive_gate": result["lotto_max"]["predictive_diagnostics"]["gate_passed"],
        "daily_grand": result["daily_grand"]["recommended_selection"]["numbers"],
        "daily_grand_grand_number": result["daily_grand"]["grand_number"],
        "daily_grand_predictive_gate": result["daily_grand"]["predictive_diagnostics"]["gate_passed"],
        "summary": str(Path(args.output_dir) / "summary.md"),
    }, indent=2))


if __name__ == "__main__":
    main()
