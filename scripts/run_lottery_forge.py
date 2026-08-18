#!/usr/bin/env python3
"""Run Lottery Forge from CSV or a deterministic synthetic fair-draw dataset."""
from __future__ import annotations

import argparse, csv, json
from pathlib import Path

from gaugegap.lottery_forge import Draw, LotterySpec, analyse, generate_synthetic_draws, make_proofpack, verify_proofpack


def _columns(value: str) -> tuple[str, ...]:
    cols=tuple(x.strip() for x in value.split(",") if x.strip())
    if not cols: raise argparse.ArgumentTypeError("at least one number column is required")
    return cols


def load_csv(path: Path, number_columns: tuple[str,...], date_column: str|None) -> tuple[Draw,...]:
    out=[]
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        if r.fieldnames is None: raise ValueError("CSV has no header")
        missing=[c for c in number_columns if c not in r.fieldnames]
        if missing: raise ValueError(f"missing number columns: {missing}")
        if date_column and date_column not in r.fieldnames: raise ValueError(f"missing date column: {date_column}")
        for row_no,row in enumerate(r,start=2):
            try: nums=tuple(int(row[c]) for c in number_columns)
            except (TypeError,ValueError) as exc: raise ValueError(f"invalid number at CSV row {row_no}") from exc
            out.append(Draw.from_numbers(nums,row.get(date_column) if date_column else None))
    return tuple(out)


def load_popular_combinations(path: Path, spec: LotterySpec) -> dict[tuple[int,...],int]:
    out={}
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f); required=[f"n{i}" for i in range(1,spec.pick_count+1)]+["plays"]
        if r.fieldnames is None or any(c not in r.fieldnames for c in required): raise ValueError(f"popularity CSV must include: {required}")
        for row_no,row in enumerate(r,start=2):
            try: combo=tuple(sorted(int(row[f"n{i}"]) for i in range(1,spec.pick_count+1))); plays=int(row["plays"])
            except (TypeError,ValueError) as exc: raise ValueError(f"invalid popularity row {row_no}") from exc
            if len(set(combo))!=spec.pick_count or combo[0]<1 or combo[-1]>spec.pool_size: raise ValueError(f"invalid combination in popularity row {row_no}")
            out[combo]=plays
    return out


def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(description="Run GaugeGap Lottery Forge diagnostics.")
    src=p.add_mutually_exclusive_group(required=True); src.add_argument("--input",type=Path); src.add_argument("--demo-draws",type=int)
    p.add_argument("--number-columns",type=_columns,default=("n1","n2","n3","n4","n5","n6")); p.add_argument("--date-column",default="date")
    p.add_argument("--game-name",default="lotto-6of49"); p.add_argument("--pool-size",type=int,default=49); p.add_argument("--pick-count",type=int,default=6)
    p.add_argument("--null-trials",type=int,default=2000); p.add_argument("--dmd-trials",type=int,default=64); p.add_argument("--candidate-samples",type=int,default=100000); p.add_argument("--candidate-top-k",type=int,default=10)
    p.add_argument("--popular-combinations",type=Path); p.add_argument("--seed",type=int,default=649); p.add_argument("--windows",default="26,52,104"); p.add_argument("--output-dir",type=Path,required=True)
    return p


def main(argv=None) -> int:
    args=parser().parse_args(argv); spec=LotterySpec(args.game_name,args.pool_size,args.pick_count)
    if len(args.number_columns)!=spec.pick_count: raise SystemExit("number-columns count must equal pick-count")
    if args.input:
        draws=load_csv(args.input,args.number_columns,args.date_column or None); source={"kind":"csv","path":str(args.input)}
    else:
        draws=generate_synthetic_draws(spec,count=args.demo_draws,seed=args.seed); source={"kind":"synthetic-independent-null","count":args.demo_draws,"seed":args.seed}
    popular=load_popular_combinations(args.popular_combinations,spec) if args.popular_combinations else None
    windows=tuple(int(v) for v in args.windows.split(",") if v.strip())
    report=analyse(draws,spec,null_trials=args.null_trials,dmd_trials=args.dmd_trials,candidate_samples=args.candidate_samples,candidate_top_k=args.candidate_top_k,seed=args.seed,backtest_windows=windows,popular_combinations=popular)
    report["source"]=source; report["crowd_data_source"]={"kind":"measured-top-combinations","path":str(args.popular_combinations),"rows":len(popular)} if popular else {"kind":"proxy-only"}
    pack=make_proofpack(report)
    if not verify_proofpack(pack): raise RuntimeError("internal proofpack verification failed")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"analysis.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (args.output_dir/"proofpack.json").write_text(json.dumps(pack,indent=2,sort_keys=True)+"\n")
    gate=report["predictive_evidence_gate"]; fib=report["fibonacci"]["null_test"]; temporal=report["temporal_order"]; dmd=report["dmd_temporal_order"]
    lines=["# Lottery Forge result","",f"- Draws: **{report['draw_count']}**",f"- Fibonacci null p-value: **{fib['empirical_p_value']:.6g}**",f"- Temporal-order null p-value: **{temporal['empirical_p_value']:.6g}**",f"- DMD lower-error permutation p-value: **{dmd['empirical_p_value_lower_error']:.6g}**",f"- Predictive evidence gate passed: **{gate['passed']}**","","## Anti-crowd candidate heuristics",""]
    for i,c in enumerate(report["candidate_search"]["top"],1): lines.append(f"{i}. {' - '.join(map(str,c['numbers']))} (score {c['combined_score']:.4f})")
    lines += ["","## Claim boundary","",report["claim_boundary"],""]
    (args.output_dir/"summary.md").write_text("\n".join(lines))
    print(json.dumps({"analysis":str(args.output_dir/"analysis.json"),"proofpack":str(args.output_dir/"proofpack.json"),"summary":str(args.output_dir/"summary.md"),"proofpack_verified":True,"predictive_gate_passed":gate["passed"]},indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
