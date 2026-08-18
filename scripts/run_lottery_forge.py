#!/usr/bin/env python3
"""Run Lottery Forge on official WCLC data, a CSV, or a deterministic fair null."""
from __future__ import annotations

import argparse
import csv
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from gaugegap.lottery_forge import (
    Draw,
    LotterySpec,
    analyse,
    generate_synthetic_draws,
    make_proofpack,
    verify_proofpack,
)
from gaugegap.lottery_sources import fetch_wclc_649, filter_draw_dates

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POPULARITY = ROOT / "data" / "lottery" / "olg_649_popular_2025-05-25_2026-05-25.csv"
DEFAULT_REFERENCE = "32,37,41,43,47,49"


def _columns(value: str) -> tuple[str, ...]:
    columns = tuple(item.strip() for item in value.split(",") if item.strip())
    if not columns:
        raise argparse.ArgumentTypeError("at least one number column is required")
    return columns


def _combination(value: str) -> tuple[int, ...]:
    try:
        return tuple(sorted(int(item.strip()) for item in value.split(",") if item.strip()))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("combination must be comma-separated integers") from exc


def _subtract_years(value: date, years: int) -> date:
    if years < 1:
        raise ValueError("years must be positive")
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def load_csv(path: Path, number_columns: tuple[str, ...], date_column: str | None, bonus_column: str | None) -> tuple[Draw, ...]:
    out: list[Draw] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header")
        missing = [column for column in number_columns if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"missing number columns: {missing}")
        if date_column and date_column not in reader.fieldnames:
            raise ValueError(f"missing date column: {date_column}")
        if bonus_column and bonus_column not in reader.fieldnames:
            raise ValueError(f"missing bonus column: {bonus_column}")
        for row_no, row in enumerate(reader, start=2):
            try:
                numbers = tuple(int(row[column]) for column in number_columns)
                bonus = int(row[bonus_column]) if bonus_column and row.get(bonus_column) not in (None, "") else None
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid number at CSV row {row_no}") from exc
            out.append(Draw.from_numbers(numbers, draw_date=row.get(date_column) if date_column else None, bonus=bonus))
    return tuple(out)


def load_popular_combinations(path: Path, spec: LotterySpec) -> dict[tuple[int, ...], int]:
    out: dict[tuple[int, ...], int] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [f"n{i}" for i in range(1, spec.pick_count + 1)] + ["plays"]
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in required):
            raise ValueError(f"popularity CSV must include: {required}")
        for row_no, row in enumerate(reader, start=2):
            try:
                combo = tuple(sorted(int(row[f"n{i}"]) for i in range(1, spec.pick_count + 1)))
                plays = int(row["plays"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid popularity row {row_no}") from exc
            if len(set(combo)) != spec.pick_count or combo[0] < 1 or combo[-1] > spec.pool_size or plays < 0:
                raise ValueError(f"invalid combination in popularity row {row_no}")
            out[combo] = plays
    return out


def write_draws_csv(path: Path, draws: tuple[Draw, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "n1", "n2", "n3", "n4", "n5", "n6", "bonus"])
        for draw in draws:
            writer.writerow([draw.draw_date or "", *draw.numbers, "" if draw.bonus is None else draw.bonus])


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Run verification-first GaugeGap Lottery Forge diagnostics.")
    source = command.add_mutually_exclusive_group(required=True)
    source.add_argument("--wclc-live", action="store_true", help="Fetch official LOTTO 6/49 Classic results from WCLC.")
    source.add_argument("--input", type=Path, help="Read normalized/custom CSV input.")
    source.add_argument("--demo-draws", type=int, help="Generate deterministic independent fair draws.")
    command.add_argument("--number-columns", type=_columns, default=("n1", "n2", "n3", "n4", "n5", "n6"))
    command.add_argument("--date-column", default="date")
    command.add_argument("--bonus-column", default="bonus")
    command.add_argument("--start-date", help="Inclusive ISO date YYYY-MM-DD.")
    command.add_argument("--end-date", help="Inclusive ISO date YYYY-MM-DD.")
    command.add_argument("--years", type=int, default=2, help="For --wclc-live, calendar-year lookback when --start-date is omitted.")
    command.add_argument("--game-name", default="lotto-6of49")
    command.add_argument("--pool-size", type=int, default=49)
    command.add_argument("--pick-count", type=int, default=6)
    command.add_argument("--null-trials", type=int, default=5000)
    command.add_argument("--dmd-trials", type=int, default=128)
    command.add_argument("--candidate-samples", type=int, default=250000)
    command.add_argument("--candidate-top-k", type=int, default=10)
    command.add_argument("--candidate-exhaustive", action="store_true")
    command.add_argument("--neutrality-weight", type=float, default=0.0)
    command.add_argument("--popularity-weight", type=float, default=0.35)
    command.add_argument("--popular-combinations", type=Path, default=None)
    command.add_argument("--no-popularity-data", action="store_true")
    command.add_argument("--compare", action="append", type=_combination, default=[])
    command.add_argument("--seed", type=int, default=649)
    command.add_argument("--windows", default="26,52,104")
    command.add_argument("--output-dir", type=Path, required=True)
    return command


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    spec = LotterySpec(args.game_name, args.pool_size, args.pick_count)
    spec.validate()
    if len(args.number_columns) != spec.pick_count:
        raise SystemExit("number-columns count must equal pick-count")

    if args.wclc_live:
        fetched, source_meta = fetch_wclc_649(start_date=args.start_date, end_date=args.end_date, spec=spec)
        if args.start_date is None:
            latest = date.fromisoformat(fetched[-1].draw_date or "")
            start = _subtract_years(latest, args.years).isoformat()
            draws = filter_draw_dates(fetched, start_date=start, end_date=args.end_date)
            source_meta["resolved_start_date"] = draws[0].draw_date
            source_meta["resolved_end_date"] = draws[-1].draw_date
            source_meta["records_selected"] = len(draws)
            source_meta["lookback_years"] = args.years
        else:
            draws = fetched
    elif args.input:
        raw = args.input.read_bytes()
        draws = load_csv(args.input, args.number_columns, args.date_column or None, args.bonus_column or None)
        if args.start_date or args.end_date:
            draws = filter_draw_dates(draws, start_date=args.start_date, end_date=args.end_date)
        source_meta = {"kind": "csv", "path": str(args.input), "sha256": sha256(raw).hexdigest(), "bytes": len(raw), "records_selected": len(draws)}
    else:
        if args.demo_draws is None or args.demo_draws < 3:
            raise SystemExit("--demo-draws must be at least 3")
        draws = generate_synthetic_draws(spec, count=args.demo_draws, seed=args.seed)
        source_meta = {"kind": "synthetic-independent-null", "count": args.demo_draws, "seed": args.seed}

    if args.no_popularity_data:
        popularity_path = None
    elif args.popular_combinations is not None:
        popularity_path = args.popular_combinations
    elif DEFAULT_POPULARITY.exists():
        popularity_path = DEFAULT_POPULARITY
    else:
        popularity_path = None
    popular = load_popular_combinations(popularity_path, spec) if popularity_path else None

    windows = tuple(int(value) for value in args.windows.split(",") if value.strip())
    references = list(args.compare)
    default_reference = _combination(DEFAULT_REFERENCE)
    if spec.pool_size == 49 and spec.pick_count == 6 and default_reference not in references:
        references.append(default_reference)
    for reference in references:
        if len(reference) != spec.pick_count:
            raise SystemExit(f"comparison {reference} does not contain {spec.pick_count} numbers")

    report = analyse(
        draws,
        spec,
        null_trials=args.null_trials,
        dmd_trials=args.dmd_trials,
        candidate_samples=args.candidate_samples,
        candidate_top_k=args.candidate_top_k,
        candidate_exhaustive=args.candidate_exhaustive,
        seed=args.seed,
        backtest_windows=windows,
        popular_combinations=popular,
        neutrality_weight=args.neutrality_weight,
        popularity_weight=args.popularity_weight,
        reference_combinations=references,
    )
    report["source"] = source_meta
    if popularity_path:
        popularity_bytes = popularity_path.read_bytes()
        report["crowd_data_source"] = {
            "kind": "measured-top-combinations",
            "path": str(popularity_path),
            "rows": len(popular or {}),
            "sha256": sha256(popularity_bytes).hexdigest(),
            "coverage_boundary": "Published top combinations only; not the full ticket-choice distribution.",
        }
    else:
        report["crowd_data_source"] = {"kind": "proxy-only"}

    pack = make_proofpack(report)
    if not verify_proofpack(pack):
        raise RuntimeError("internal proofpack verification failed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_draws_csv(args.output_dir / "draws.csv", tuple(draws))
    (args.output_dir / "analysis.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / "proofpack.json").write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gate = report["predictive_evidence_gate"]
    fib = report["fibonacci"]["null_test"]
    temporal = report["temporal_order"]
    dmd = report["dmd_temporal_order"]
    best = min(report["rolling_backtests"], key=lambda item: item["adjusted_p_value_bonferroni"], default=None)
    lines = [
        "# Lottery Forge result", "",
        f"- Draws: **{report['draw_count']}**",
        f"- Draw interval: **{draws[0].draw_date or 'undated'} → {draws[-1].draw_date or 'undated'}**",
        f"- Fibonacci null p-value: **{fib['empirical_p_value']:.6g}**",
        f"- Temporal-order null p-value: **{temporal['empirical_p_value']:.6g}**",
        f"- DMD lower-error permutation p-value: **{dmd['empirical_p_value_lower_error']:.6g}**",
        f"- Predictive evidence gate passed: **{gate['passed']}**",
    ]
    if best:
        lines += [
            f"- Best corrected holdout: **{best['model']} / {best['window']} draws**",
            f"- Mean hits: **{best['mean_hits']:.4f}** vs chance **{best['chance_mean_hits']:.4f}**",
            f"- Bonferroni-adjusted p-value: **{best['adjusted_p_value_bonferroni']:.6g}**",
        ]
    lines += ["", "## Anti-crowd candidate heuristics", ""]
    for index, candidate in enumerate(report["candidate_search"]["top"], 1):
        lines.append(f"{index}. {' - '.join(map(str, candidate['numbers']))} (score {candidate['combined_score']:.4f})")
    if report["candidate_search"].get("references"):
        lines += ["", "## Reference combinations", ""]
        for reference in report["candidate_search"]["references"]:
            lines.append(f"- {' - '.join(map(str, reference['numbers']))} (score {reference['combined_score']:.4f})")
    lines += ["", "## Claim boundary", "", report["claim_boundary"], ""]
    (args.output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "analysis": str(args.output_dir / "analysis.json"),
        "proofpack": str(args.output_dir / "proofpack.json"),
        "summary": str(args.output_dir / "summary.md"),
        "draws": str(args.output_dir / "draws.csv"),
        "proofpack_verified": True,
        "predictive_gate_passed": gate["passed"],
        "top_candidate": report["candidate_search"]["top"][0]["numbers"] if report["candidate_search"]["top"] else None,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
