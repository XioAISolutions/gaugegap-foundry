#!/usr/bin/env python3
"""Run the StyleGap finite linguistic-screening benchmark.

Tracks the protocol of Rodrigues, Sturm & Pinheiro (iScience 2026,
doi:10.1016/j.isci.2026.114976) on a supplied corpus.
CLAIM BOUNDARY: finite-corpus screening benchmark only; not a detector.

Usage:
  python scripts/run_stylegap_screen.py --output-dir /tmp/stylegap-smoke
  python scripts/run_stylegap_screen.py --input corpus.jsonl --output-dir out

corpus.jsonl: one JSON object per line: {"text": "...", "label": "human"|"ai"}
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaugegap.stylegap_linguistic import (  # noqa: E402
    corpus_summary,
    ngram_log_odds,
    relative_difference,
    screening_protocol,
)

DEMO_HUMAN = [
    "ok so the city budget meeting went long again. nobody could agree on the road repairs and honestly it was kind of a mess, people were angry and yelling. we'll see what happens next month i guess.",
    "the storm knocked out power for three days. my neighbor lost everything in his basement and he is devastated. crews say maybe monday. it sucks, we are all tired of this year honestly.",
    "the team lost again on saturday, 2-1. fans were furious, some threw stuff on the field. the coach said he is sad about it but will keep working. same story every week sadly.",
]
DEMO_AI = [
    "The municipal council convened to discuss infrastructure priorities. The proposed road maintenance program aims to ensure improved safety and to deliver significant long-term benefits for all residents. Furthermore, the initiative demonstrates the importance of sustainable planning.",
    "In conclusion, the recent weather event caused considerable disruption. Emergency services are actively working to restore essential utilities. It is essential to ensure that affected households receive support, and local authorities will provide further updates regarding recovery measures.",
    "The team demonstrated resilience despite the result. The coaching staff remains committed to continuous improvement and to achieve the best possible outcomes in the coming fixtures. The organization expresses full confidence in its athletes and their progress.",
]


def load_corpus(path):
    human, ai = [], []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        (ai if row.get("label") == "ai" else human).append(row["text"])
    return human, ai


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="corpus.jsonl {text,label}; omit for demo")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--seed", type=int, default=20260920)
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if args.input:
        human, ai = load_corpus(args.input)
        corpus_name = Path(args.input).name
    else:
        human, ai = DEMO_HUMAN, DEMO_AI
        corpus_name = "demo (builtin 3+3 docs; protocol smoke only)"
    rd = relative_difference(human, ai, seed=args.seed)
    uni = ngram_log_odds(human, ai, n=1, top_k=10)
    screen = screening_protocol(human, ai, seed=args.seed)
    report = {
        "corpus": corpus_name,
        "claim_boundary": "finite linguistic-screening benchmark; not a detection product",
        "gate_protocol": {
            "reference": "Rodrigues, Sturm & Pinheiro, iScience 29 (2026) 114976",
            "doi": "10.1016/j.isci.2026.114976",
        },
        "relative_difference": rd,
        "top_unigrams_toward_ai": uni["toward_b"],
        "top_unigrams_toward_human": uni["toward_a"],
        "screening": screen,
        "summary": {"human": corpus_summary(human), "ai": corpus_summary(ai)},
    }
    (out / "stylegap_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"documents: human={len(human)} ai={len(ai)}")
    print("feature                  delta% (AI vs human)  ci-excludes-0")
    for k, v in sorted(rd.items()):
        mark = "yes" if v["excludes_zero"] else "-"
        print(f"{k:24s} {v['delta_pct']:+9.2f}  {mark}")
    print(f"screening held-out: human={screen['accuracy_human_heldout']:.2f} "
          f"ai={screen['accuracy_ai_heldout']:.2f}")
    print("OUT:", out / "stylegap_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
