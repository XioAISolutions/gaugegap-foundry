#!/usr/bin/env python3
"""Evaluate a previously generated Lottery Forge weekly screen after a draw."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaugegap.lottery_evaluation import (
    EVALUATION_CLAIM_BOUNDARY,
    evaluate_ranked_lines,
    fixed_family_max_hit_null,
    overlap_tail_probability,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("screen", help="Path to pre-draw lottery_week.json")
    parser.add_argument("--game", choices=("lotto_max", "daily_grand"), required=True)
    parser.add_argument("--draw", nargs="+", type=int, required=True)
    parser.add_argument("--bonus", type=int)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--trials", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = json.loads(Path(args.screen).read_text(encoding="utf-8"))
    game = payload[args.game]
    pool_size = int(game["game"]["pool_size"])
    pick_count = int(game["game"]["pick_count"])
    frozen = [row["numbers"] for row in game["top_selections"][: args.top_k]]
    outcomes = evaluate_ranked_lines(
        frozen,
        args.draw,
        pool_size=pool_size,
        pick_count=pick_count,
        bonus=args.bonus,
    )
    maximum = max(row.hit_count for row in outcomes)
    family_null = fixed_family_max_hit_null(
        frozen,
        pool_size=pool_size,
        pick_count=pick_count,
        observed_max_hits=maximum,
        trials=args.trials,
        seed=args.seed,
    )
    report = {
        "schema": "gaugegap.lottery_outcome.v1",
        "claim_boundary": EVALUATION_CLAIM_BOUNDARY,
        "game": args.game,
        "draw": sorted(args.draw),
        "bonus": args.bonus,
        "top_k": len(frozen),
        "ranked_outcomes": [row.summary() for row in outcomes],
        "rank_1_single_line_tail_probability": overlap_tail_probability(
            pool_size=pool_size,
            pick_count=pick_count,
            at_least_hits=outcomes[0].hit_count,
        ),
        "observed_family_max_hits": maximum,
        "family_max_null_exploratory_unless_predeclared": family_null.summary(),
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
