#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import write_jsonl
from gaugegap.search.candidate_dossier import write_candidate_dossiers, write_markdown_summary
from gaugegap.search.gap_search import SearchConfig, linspace, search_gap_candidates


def parse_ints(value: str) -> tuple[int, ...]:
    try:
        items = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated integers") from exc
    if not items or any(item < 1 for item in items):
        raise argparse.ArgumentTypeError("values must be positive integers")
    return items


def parse_floats(value: str) -> tuple[float, ...]:
    try:
        items = tuple(float(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated numbers") from exc
    if not items:
        raise argparse.ArgumentTypeError("at least one value is required")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Search finite Z2 plaquette spectral-gap candidates.")
    parser.add_argument("--hypothesis-id", default="gaugegap-search-0001")
    parser.add_argument("--n-plaquettes", type=parse_ints, default=(1, 2, 3))
    parser.add_argument("--plaquette-couplings", type=parse_floats, default=(0.5, 1.0, 1.5))
    parser.add_argument("--transverse-fields", type=parse_floats, default=None)
    parser.add_argument("--field-start", type=float, default=0.05)
    parser.add_argument("--field-stop", type=float, default=2.0)
    parser.add_argument("--field-points", type=int, default=6)
    parser.add_argument("--random-samples", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-candidates", type=int, default=10)
    parser.add_argument("--max-qubits", type=int, default=12)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dossier-limit", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "gaugegap-search-0001")
    args = parser.parse_args()

    transverse_fields = args.transverse_fields
    if transverse_fields is None:
        transverse_fields = linspace(args.field_start, args.field_stop, args.field_points)

    config = SearchConfig(
        hypothesis_id=args.hypothesis_id,
        n_plaquettes=args.n_plaquettes,
        plaquette_couplings=args.plaquette_couplings,
        transverse_fields=transverse_fields,
        max_candidates=args.max_candidates,
        run_id=args.run_id,
        max_qubits=args.max_qubits,
        random_samples=args.random_samples,
        seed=args.seed,
    )
    candidates = search_gap_candidates(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(args.output_dir / "gaugegap-search-0001-candidates.jsonl", candidates)
    (args.output_dir / "gaugegap-search-0001-candidates.json").write_text(
        json.dumps(candidates, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    write_csv(args.output_dir / "gaugegap-search-0001-ranking.csv", candidates)
    write_markdown_summary(args.output_dir / "gaugegap-search-0001-ranking.md", candidates)
    written = write_candidate_dossiers(args.output_dir, candidates, limit=args.dossier_limit)

    print(
        json.dumps(
            {
                "status": "pass",
                "candidate_count": len(candidates),
                "top_candidate_id": candidates[0]["candidate_id"] if candidates else None,
                "top_score": candidates[0]["score"] if candidates else None,
                "output_dir": str(args.output_dir),
                "dossier_files": [str(path) for path in written],
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


def write_csv(path: Path, candidates: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rank",
                "candidate_id",
                "score",
                "status",
                "plaquette_coupling",
                "mean_gap",
                "min_gap",
                "finite_size_survival_score",
                "perturbation_stability_score",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for rank, candidate in enumerate(candidates, start=1):
            components = candidate.get("score_components", {})
            if not isinstance(components, dict):
                components = {}
            writer.writerow(
                {
                    "rank": rank,
                    "candidate_id": candidate.get("candidate_id"),
                    "score": f"{float(candidate.get('score', 0.0)):.12g}",
                    "status": candidate.get("status"),
                    "plaquette_coupling": f"{float(candidate.get('plaquette_coupling', 0.0)):.12g}",
                    "mean_gap": f"{float(components.get('mean_gap', 0.0)):.12g}",
                    "min_gap": f"{float(components.get('min_gap', 0.0)):.12g}",
                    "finite_size_survival_score": f"{float(components.get('finite_size_survival_score', 0.0)):.12g}",
                    "perturbation_stability_score": f"{float(components.get('perturbation_stability_score', 0.0)):.12g}",
                }
            )


if __name__ == "__main__":
    raise SystemExit(main())
